//
// Created by moreveal on 06.12.2024.
//

#ifndef MEMHASH_WORKER_WORKER_H
#define MEMHASH_WORKER_WORKER_H

#include <string>
#include <vector>
#include <openssl/sha.h>
#include <boost/multiprecision/cpp_int.hpp>
#include <iomanip>
#include <sstream>
#include <shared_mutex>

class Worker {
private:
    inline static std::atomic<uint32_t> currentBlock{0};
public:
    Worker() = default;

    static void GetHash(uint8_t* buffer, const char* data) {
        SHA256_CTX ctx;
        SHA256_Init(&ctx);
        SHA256_Update(&ctx, reinterpret_cast<const uint8_t*>(data), strlen(data));
        SHA256_Final(buffer, &ctx);
    }

    static void ConvertToBytes(uint8_t* bytes, const char* value, const size_t size = SHA256_DIGEST_LENGTH)
    {
        boost::multiprecision::cpp_int bigNumber(value);
        for (size_t i = 0; i < size; i++)
        {
            bytes[size - i - 1] = static_cast<uint8_t>(bigNumber & 0xFF);
            bigNumber >>= 0x8;
            if (bigNumber == 0x0) break;
        }
    }

    static bool IsArrayLess(const uint8_t* a1, const uint8_t* a2, const size_t size = SHA256_DIGEST_LENGTH)
    {
        size_t i = 0, j = 0;
        while (i < size && a1[i] == 0) i++;
        while (j < size && a2[j] == 0) j++;

        size_t len1 = size, len2 = size;
        if (i != j) return len1 - i < len2 - j;

        while (i < size && j < size) {
            if (a1[i] != a2[j]) {
                return a1[i] < a2[j];
            }
            i++;
            j++;
        }

        return false;
    }

    static std::string BytesToHex(const uint8_t* hash, const size_t size = SHA256_DIGEST_LENGTH) {
        static const char hexDigits[] = "0123456789abcdef";
        std::string hexString(size * 2, '\0');

        for (size_t i = 0; i < size; ++i) {
            hexString[2 * i] = hexDigits[(hash[i] >> 4) & 0xF];
            hexString[2 * i + 1] = hexDigits[hash[i] & 0xF];
        }
        return hexString;
    }

    static void UpdateCurrentBlock(uint32_t block)
    {
        currentBlock.store(block);
    }

    static uint32_t GetCurrentBlock()
    {
        return currentBlock.load();
    }
};


#endif //MEMHASH_WORKER_WORKER_H
