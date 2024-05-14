cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(base)

include_directories(../../include)
file (GLOB MYLIB_SOURCES 
    ../../mylib/hid.c,
    
)

list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)

zephyr_nanopb_sources(app src/minecraftmessage.proto)

target_sources(app PRIVATE src/main.c ${MYLIB_SOURCES}) 
