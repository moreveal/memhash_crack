#ifndef MEMHASH_WORKER_SERVER_H
#define MEMHASH_WORKER_SERVER_H

#define HASHES_PER_THREAD 60000

#define ENABLE_VMP
#ifdef ENABLE_VMP
    #define VMP_ULTRA VMProtectBeginUltra
    #define VMP_VIRT VMProtectBeginVirtualization
    #define VMP_MUTATION VMProtectBeginMutation
    #define VMP_END VMProtectEnd
#else
    #define VMP_ULTRA(string)
    #define VMP_VIRT(string)
    #define VMP_MUTATION(string)
    #define VMP_END
#endif

#include <iostream>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/config/asio_client.hpp>
#include <websocketpp/server.hpp>
#include <websocketpp/client.hpp>
#include <thread>
#include <limits>
#include <format>
#include <nlohmann/json.hpp>
#include <stdlib.h>
#include <inttypes.h>
#include <fstream>
#include <filesystem>
#include "VMProtectSDK.h"

#include "Worker.h"

typedef websocketpp::server<websocketpp::config::asio> server;

class Server {
private:
    static bool workerInit(uint64_t minerId)
    {
        using namespace std::chrono;

        if (VMProtectIsDebuggerPresent(true) || !VMProtectIsValidImageCRC()) return false;

        // Open .key file and read the serial
        std::string key(1024, '\0');
        {
            namespace fs = std::filesystem;

            const auto dir = fs::current_path();
            for (const auto& entry : fs::directory_iterator(dir))
            {
                if (entry.is_regular_file() && entry.path().extension() == ".key")
                {
                    std::ifstream file(entry.path(), std::ios::binary);
                    if (file) {
                        file.seekg(0, std::ios::end);
                        std::streampos fileSize = file.tellg();
                        file.seekg(0, std::ios::beg);

                        file.read(&key[0], fileSize);

                        file.close();
                    } else {
                        std::cerr << "Unable to open the .key file" << std::endl;
                        return false;
                    }
                }
            }
        }
        if (key.empty()) {
            std::cerr << "Invalid license key or could not find .key file" << std::endl;
            return false;
        }

        // Get license info
        int key_res = VMProtectSetSerialNumber(key.c_str());
        if (key_res) {
            std::cerr << "Invalid license key" << std::endl;
            return false;
        }
        VMProtectSerialNumberData licenseData = {0};
        VMProtectGetSerialNumberData(&licenseData, sizeof(licenseData));

        // Check minerid
        {
            uint64_t build_telegram_id = 0x0;

            for (size_t i = 0; i < 8; i++) {
                build_telegram_id = (build_telegram_id << 8) | licenseData.bUserData[i];
            }

            if (build_telegram_id != minerId)
            {
                std::cerr << "Invalid user identifier" << std::endl;
                return false;
            }
        }

        // Check expires
        uint64_t build_timestamp = 0x0;
        {
            for (size_t i = 8; i < 16; i++)
            {
                build_timestamp = (build_timestamp << 8) | licenseData.bUserData[i];
            }

            const auto current_timestamp = duration_cast<seconds>(high_resolution_clock::now().time_since_epoch()).count();
            if (current_timestamp > build_timestamp)
            {
                std::cerr << "License key has expired" << std::endl;
                return false;
            }
        }

        std::cout << "Telegram ID: " << minerId << std::endl;
        if (build_timestamp == 777) {
            std::cout << "Subscription: Lifetime" << std::endl;
        } else {
            const auto timestamp = static_cast<std::time_t>(build_timestamp);
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

            auto elapsedTime = build_timestamp - duration_cast<seconds>(system_clock::now().time_since_epoch()).count();
            std::thread stopLicense([elapsedTime]() {
                std::this_thread::sleep_for(std::chrono::seconds(elapsedTime));
                std::cout << "Subscription is ended" << std::endl;
                exit(0);
            });
            stopLicense.detach();
        }
        std::cout << "Good luck, collect as many blocks as you can!" << std::endl;

        return true;
    }

    void sendResult(const char* state, const uint8_t* hashBytes, const char* data, uint32_t nonce, long long int timestamp, uint64_t minerId)
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

    void processNonceRange(uint32_t currentBlock, uint64_t minerId, const char* previousHash, const char* data,
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

            // const s = timestamp + "-" + data + "-" + index + "-" + prevhash + "-" + nonce + "-" + minerid;
            char input[512];
            snprintf(input, sizeof(input), "%lld-%s-%u-%s-%u-%" PRIu64,
                     timestamp, data, currentBlock, previousHash, nonce, minerId);

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

        const auto minerId = data["data"]["minerId"].get<uint64_t>();
        const auto previousHash = data["data"]["previousHash"].get<std::string>();
        const auto inputData = data["data"]["data"].get<std::string>();
        const auto shareFactor = data["data"]["shareFactor"].get<std::string>();
        const auto mainFactor = data["data"]["mainFactor"].get<std::string>();

        VMP_ULTRA("CheckLicense");
        static bool init = false;
        if (!init)
        {
            if (!workerInit(minerId)) exit(0);
            init = true;
        }
        VMP_END();

        const uint32_t batchSize = HASHES_PER_THREAD * NUM_THREADS;
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
        } else if (data["event"] == "change_power") {
            auto ratio = data["power"].get<float>();
            if (ratio < 0) ratio = 0.0;
            else if (ratio > 1) ratio = 1.0;

            NUM_THREADS = static_cast<float>(std::thread::hardware_concurrency()) * ratio;
        }
    }

    server m_server;
    websocketpp::connection_hdl m_client_hdl;

    inline static std::atomic<bool> stopThreads{false};
    inline static std::mutex hdl_mutex;

    size_t NUM_THREADS;
public:
    Server(unsigned short port) : NUM_THREADS(std::thread::hardware_concurrency())
    {
        // WS server initialization
        m_server.init_asio();
        m_server.set_open_handler([this](auto && PH1) { on_open(std::forward<decltype(PH1)>(PH1)); });
        m_server.set_message_handler([this](auto && PH1, auto && PH2) { on_message(std::forward<decltype(PH1)>(PH1), std::forward<decltype(PH2)>(PH2)); });
        m_server.set_close_handler([this](auto && PH1) { on_close(std::forward<decltype(PH1)>(PH1)); });
        m_server.clear_access_channels(websocketpp::log::alevel::all);

        // Start server in a thread
        m_server.listen(port);
        m_server.start_accept();
        m_server.run();
    }

    ~Server() = default;
};

#endif // MEMHASH_WORKER_SERVER_H
