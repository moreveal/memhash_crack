#ifndef MEMHASH_WORKER_SERVER_H
#define MEMHASH_WORKER_SERVER_H

// Build info
volatile size_t BUILD_TELEGRAM_ID = 1425589338;
volatile unsigned long int BUILD_TIMESTAMP = 777; // 777 - unlimited

#include <iostream>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/config/asio_client.hpp>
#include <websocketpp/server.hpp>
#include <websocketpp/client.hpp>
#include <thread>
#include <limits>
#include <format>
#include <nlohmann/json.hpp>

#include "Worker.h"

typedef websocketpp::server<websocketpp::config::asio> server;

class Server {
private:
    void sendResult(const char* state, const uint8_t* hashBytes, const char* data, uint32_t nonce, long long int timestamp, uint32_t minerId)
    {
        auto hash = Worker::BytesToHex(hashBytes);
        auto client_hdl = [&] {
            std::lock_guard lock(hdl_mutex);
            return m_client_hdl.lock();
        }();
        if (!client_hdl) return;

        nlohmann::json response = {
                {"state", state},
                {"hash", hash},
                {"data", data},
                {"nonce", nonce},
                {"timestamp", timestamp},
                {"minerId", minerId}
        };

        m_server.send(client_hdl, response.dump(), websocketpp::frame::opcode::text);
    }

    void processNonceRange(uint32_t currentBlock, uint32_t minerId, const char* previousHash, const char* data,
                           const char* shareFactor, const char* mainFactor, uint32_t startNonce, uint32_t endNonce)
    {
        uint8_t shareFactorBytes[SHA256_DIGEST_LENGTH] = {0};
        uint8_t mainFactorBytes[SHA256_DIGEST_LENGTH] = {0};
        Worker::ConvertToBytes(shareFactorBytes, shareFactor);
        Worker::ConvertToBytes(mainFactorBytes, mainFactor);

        for (auto nonce = startNonce; nonce < endNonce; ++nonce)
        {
            if (currentBlock != Worker::GetCurrentBlock()) return;

            auto now = std::chrono::system_clock::now();
            long long int timestamp = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();

            // const input = `${index}-${previousHash}-${data}-${nonce}-${timestamp}-${minerId}`;
            char input[512];
            snprintf(input, sizeof(input), "%d-%s-%s-%d-%lld-%d",
                     currentBlock, previousHash, data, nonce, timestamp, minerId);

            uint8_t hashBytes[SHA256_DIGEST_LENGTH];
            Worker::GetHash(hashBytes, input);

            if (Worker::IsArrayLess(hashBytes, mainFactorBytes)) {
                sendResult("valid", hashBytes, data, nonce, timestamp, minerId);
            } else if (Worker::IsArrayLess(hashBytes, shareFactorBytes)) {
                sendResult("share", hashBytes, data, nonce, timestamp, minerId);
            }
        }
    }

    void workerThread(const nlohmann::json& data)
    {
        const auto currentBlock = data["data"]["index"].get<uint32_t>();
        if (currentBlock == Worker::GetCurrentBlock()) return;
        Worker::UpdateCurrentBlock(currentBlock);

        const auto minerId = data["data"]["minerId"].get<uint32_t>();
        const auto previousHash = data["data"]["previousHash"].get<std::string>();
        const auto inputData = data["data"]["data"].get<std::string>();
        const auto shareFactor = data["data"]["shareFactor"].get<std::string>();
        const auto mainFactor = data["data"]["mainFactor"].get<std::string>();

        static bool init = false;
        if (!init)
        {
            using namespace std::chrono;
            if (minerId > BUILD_TELEGRAM_ID || minerId < BUILD_TELEGRAM_ID) return;
            if (BUILD_TIMESTAMP != 777 && BUILD_TIMESTAMP < duration_cast<seconds>(system_clock::now().time_since_epoch()).count()) return;

            std::cout << "Telegram ID: " << minerId << std::endl;
            if (BUILD_TIMESTAMP == 777) {
                std::cout << "Subscription: Lifetime" << std::endl;
            } else {
                const auto timestamp = static_cast<std::time_t>(BUILD_TIMESTAMP);
                std::tm timeinfo{};

            #if defined(_MSC_VER)
                if (localtime_s(&timeinfo, &timestamp) == 0) {
            #else
                if (localtime_r(&timestamp, &timeinfo)) {
            #endif
                    char dateBuffer[100];
                    std::strftime(dateBuffer, sizeof(dateBuffer), "%d.%m.%Y %H:%M:%S", &timeinfo);
                    std::cout << "Subscription: " << dateBuffer << std::endl;
                }
            }
            std::cout << "Good luck, collect as many blocks as you can!" << std::endl;

            init = true;
        }

        const uint32_t batchSize = 60000 * NUM_THREADS; // 60000 hashes for 1 thread
        const auto totalNonces = std::numeric_limits<uint32_t>::max();

        for (size_t i = 0; i < totalNonces; i += batchSize * NUM_THREADS) {
            if (Worker::GetCurrentBlock() != currentBlock) return;

            std::vector<std::thread> threads;
            for (size_t j = 0; j < NUM_THREADS && (i + j * batchSize) < totalNonces; ++j) {
                size_t start = i + j * batchSize;
                size_t end = (start + batchSize > size_t(totalNonces)) ? size_t(totalNonces) : start + batchSize;

                threads.emplace_back(std::thread([=, this]() {
                    processNonceRange(currentBlock, minerId, previousHash.c_str(), inputData.c_str(),
                                      shareFactor.c_str(), mainFactor.c_str(), start, end);
                }));
            }

            for (auto& thread : threads)
            {
                if (thread.joinable()) thread.join();
            }
        }
    }

    void on_open(websocketpp::connection_hdl hdl) {
        m_client_hdl = hdl;
    }

    void on_close(websocketpp::connection_hdl hdl)
    {
        m_client_hdl.reset();
    }

    void on_message(websocketpp::connection_hdl hdl, const server::message_ptr& msg) {
        using nlohmann::json;

        json data = json::parse(msg->get_payload());
        if (data["event"] == "update_task") {
            std::thread([data = std::move(data), this]() { workerThread(data); }).detach();
        } else if (data["event"] == "stop_task") {
            Worker::UpdateCurrentBlock(0);
        }
    }

    server m_server;
    websocketpp::connection_hdl m_client_hdl;

    inline static std::atomic<bool> stopThreads{false};
    inline static std::mutex hdl_mutex;

    const size_t NUM_THREADS;
public:
    Server(unsigned short port) : NUM_THREADS(std::thread::hardware_concurrency())
    {
        // Инициализация WebSocket сервера
        m_server.init_asio();
        m_server.set_open_handler([this](auto && PH1) { on_open(std::forward<decltype(PH1)>(PH1)); });
        m_server.set_message_handler([this](auto && PH1, auto && PH2) { on_message(std::forward<decltype(PH1)>(PH1), std::forward<decltype(PH2)>(PH2)); });
        m_server.set_close_handler([this](auto && PH1) { on_close(std::forward<decltype(PH1)>(PH1)); });
        m_server.clear_access_channels(websocketpp::log::alevel::all);

        // Запуск сервера в отдельном потоке
        m_server.listen(port);
        m_server.start_accept();
        m_server.run();
    }

    ~Server() = default;
};

#endif // MEMHASH_WORKER_SERVER_H
