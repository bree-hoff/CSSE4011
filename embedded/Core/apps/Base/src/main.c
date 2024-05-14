/**
 **************************************************************
 * @file src/main.c
 * @author Lewis Luck - 46983932
 * @date 02052024
 * @brief Main entry point that initialises systems
 * REFERENCE: N/A
 **************************************************************
 */

#include "hid.h"

#define SETUP_SLEEP_TIME_MS 100

int main(void) {

  return 0;
}

K_THREAD_DEFINE(hid_control, 1024, hid_control_thread, NULL, NULL, NULL,
                3, 0, 0);

				
