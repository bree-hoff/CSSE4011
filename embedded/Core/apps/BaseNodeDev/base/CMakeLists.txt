cmake_minimum_required(VERSION 3.20.0)

set(BOARD nrf52840dk/nrf52840)


find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(base)

list(APPEND CMAKE_MODULE_PATH ${ZEPHYR_BASE}/modules/nanopb)
include(nanopb)

zephyr_nanopb_sources(app src/minecraftmessage.proto)

FILE(GLOB app_sources src/*.c)
target_sources(app PRIVATE ${app_sources})
