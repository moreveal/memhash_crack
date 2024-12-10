cmake_minimum_required(VERSION 3.22)
project(memhash_worker)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

if (MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
endif ()

add_executable(memhash_worker main.cpp
        Server.h
        Worker.h
)
target_include_directories(memhash_worker PRIVATE
        ${CMAKE_SOURCE_DIR}/include
)

find_package(websocketpp REQUIRED CONFIG)
find_library(memhash_worker PRIVATE websocketpp::websocketpp)
target_include_directories(memhash_worker PRIVATE ${WEBSOCKETPP_INCLUDE_DIR})

find_package(boost_random REQUIRED CONFIG)
target_link_libraries(memhash_worker PRIVATE Boost::random)

target_link_directories(memhash_worker PRIVATE ${CMAKE_SOURCE_DIR}/lib)

find_package(nlohmann_json CONFIG REQUIRED)
target_link_libraries(memhash_worker PRIVATE nlohmann_json::nlohmann_json)

find_package(OpenSSL CONFIG REQUIRED)
target_link_libraries(memhash_worker PRIVATE ${OPENSSL_LIBRARIES})