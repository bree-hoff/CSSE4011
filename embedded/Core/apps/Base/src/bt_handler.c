/**
 ******************************************************************************
 * @file bt_handler.c
 * @author Lewis Young
 * @date 14/52024 
 * @brief Scans packets from thingy52 checking for pb presses 
 ******************************************************************************
 **/

#include <stdio.h>
#include <string.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/kernel.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/conn.h>
#include <zephyr/bluetooth/uuid.h>
#include <zephyr/bluetooth/gatt.h>
#include <zephyr/sys/byteorder.h>
#include "hid.h"  

char *mobileAddr = "D4:02:7A:07:85:21"; // BT Address of Thingy:52

#define PUSH_BUTTON_STATE_INDEX 28 // Index of pb state byte in ble packet
#define PB_EVENT_BIT 0x001
static uint8_t pbState = 0; // prev state of the pb 

K_EVENT_DEFINE(pbEvent); // event group 

/*
 * BT scanner callback function; scans set ble address and checks for the byte
 * that indicates the pb state in the payload, if the byte is toggled, an event
 * bit is set to indicate the button is pressed.
 */
static void device_found(const bt_addr_le_t *addr, int8_t rssi, uint8_t type,
                         struct net_buf_simple *ad) {
  char addr_str[BT_ADDR_LE_STR_LEN];

  bt_addr_le_to_str(addr, addr_str, sizeof(addr_str));

  if (memcmp(mobileAddr, addr_str, 17) == 0) {
 
    if(pbState != (uint8_t)ad->data[PUSH_BUTTON_STATE_INDEX]) {
      
      pbState = (uint8_t)ad->data[PUSH_BUTTON_STATE_INDEX];
     
      k_event_set(&pbEvent, PB_EVENT_BIT);      
    }
  }
}

/*
 * Thread to handle the ble; inits the ble hardware and scanner, then waits
 * for the event bit to be set that indicates a press.
 */
void ble_thread(void) {

  uint32_t events;

  bt_enable(NULL); 

  struct bt_le_scan_param scan_param = {
      .type = BT_LE_SCAN_TYPE_PASSIVE,
      .options = BT_LE_SCAN_OPT_NONE,
      .interval = BT_GAP_SCAN_FAST_INTERVAL,
      .window = BT_GAP_SCAN_FAST_WINDOW,
  };

  bt_le_scan_start(&scan_param, device_found);
  
  while (true) {

    events = k_event_wait(&pbEvent, PB_EVENT_BIT, false, K_FOREVER);

    if(events & 0x001) {

      app_evt_add_new_command(MOUSE_RIGHT);
      clear_mouse_report();
      printk("PB Pressed\n");
      k_event_clear(&pbEvent, PB_EVENT_BIT);
    }
  }

}

K_THREAD_DEFINE(ble, 2048, ble_thread, NULL, NULL, NULL, 10, 0, 0);
