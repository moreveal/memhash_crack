cmake_minimum_required(VERSION 3.22)
project(memhash_worker)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(VMP_LIB_WINDOWS "${CMAKE_CURRENT_LIST_DIR}/lib/vmp/windows/VMProtectSDK32.lib")
set(VMP_LIB_LINUX "${CMAKE_CURRENT_LIST_DIR}/lib/vmp/linux/libVMProtectSDK64.so")
set(VMP_INCLUDE_DIR "${CMAKE_CURRENT_LIST_DIR}/include/vmp")

if (MSVC)
    set(CMAKE_MSVC_RUNTIME_LIBRARY "MultiThreaded$<$<CONFIG:Debug>:Debug>")
    set(CMAKE_CXX_FLAGS_RELEASE "/O2 /DNDEBUG /DEBUG:NO")
else()
    set(CMAKE_CXX_FLAGS_RELEASE "-O2 -DNDEBUG -fomit-frame-pointer -march=native")
    set(CMAKE_EXE_LINKER_FLAGS_RELEASE "-s")

    set(CMAKE_CXX_FLAGS_DEBUG "-g -O0 -DDEBUG")
    set(CMAKE_EXE_LINKER_FLAGS_DEBUG "")
endif()

add_executable(memhash_worker
        main.cpp
        Server.h
        Worker.h
)
target_include_directories(memhash_worker PRIVATE
        ${CMAKE_SOURCE_DIR}/include
        ${VMP_INCLUDE_DIR}
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

if (WIN32)
    target_link_libraries(memhash_worker PRIVATE ${VMP_LIB_WINDOWS})
    add_definitions(-DVM_WINDOWS)

elseif (UNIX)
    target_link_libraries(memhash_worker PRIVATE ${VMP_LIB_LINUX})
    add_definitions(-DVM_LINUX)
endif()