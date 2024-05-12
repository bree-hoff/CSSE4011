/**
 ******************************************************************************
 * @file	main.c
 * @author  Lewis Young
 * @date    12/05/2024
 * @brief	Broadcast a BLE beacon using the eddystone UID framwork, the beacon
 * 			indicates a button press by toggling the final byte in the payload
 * 			on a press.
 ******************************************************************************
 **/

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/sys/util.h>
#include <zephyr/sys/printk.h>
#include <inttypes.h>
#include <zephyr/bluetooth/bluetooth.h>
#include <zephyr/bluetooth/hci.h>
#include <zephyr/bluetooth/gap.h>
#include <zephyr/bluetooth/uuid.h>

#define SLEEP_TIME_MS 1 // Loop sleep time
#define DEBOUNCE_TIME 220 // Button debounce time 
#define TOGGLE_BYTE_INDEX 19 // index of byte toggled in bt beacon

/* Zephyr BLE setup */
// BLE advertising setup 
#define ADV_PARAM                                                                                  \
  BT_LE_ADV_PARAM(BT_LE_ADV_OPT_USE_IDENTITY | BT_LE_ADV_OPT_USE_NAME, BT_GAP_ADV_FAST_INT_MIN_1,  \
                  BT_GAP_ADV_FAST_INT_MAX_1, NULL) 

// Eddystone UUID data
static uint8_t data[] = {0xaa, 0xfe, /* Eddystone UUID */
                         0x00,       /* Eddystone-UID frame type */
                         0x00,       /* Calibrated Tx power at 0m */
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
                         0x00, 0x00, 0x00, 0x00,              /* 10-byte Namespace */
                         0x00, 0x00, 0x00, 0x00, 0x00, 0x00}; /* 6-byte Instance */

//Eddystone beacon packet
static const struct bt_data ad[] = {BT_DATA_BYTES(BT_DATA_FLAGS, BT_LE_AD_NO_BREDR),
                                    BT_DATA_BYTES(BT_DATA_UUID16_ALL, 0xaa, 0xfe),
                                    BT_DATA(BT_DATA_MANUFACTURER_DATA, data, 20)};


/* Global Variables */
static uint32_t prev_tick; // Last recorded time of valied button press
static uint8_t buttonPressFlag; // Button press flag (set true when button pressed)

/* Zephyr Hardware Config*/
#define SW0_NODE DT_ALIAS(sw0) // On board pushbutton
#define LED_NODE DT_ALIAS(led2) // On board LED (Blue)

// Config hardware
static const struct gpio_dt_spec button = GPIO_DT_SPEC_GET_OR(SW0_NODE, gpios, {0});
static struct gpio_callback button_cb_data;
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(LED_NODE, gpios);

/*
 * Pushbutton ISR callback function 
 */
void button_pressed(const struct device *dev, struct gpio_callback *cb, uint32_t pins) {

  // Check that Button has not being recently pressed (debounce logic)
  if (k_uptime_get_32() - prev_tick > DEBOUNCE_TIME) {
	buttonPressFlag = 1; // set flag on valid press
  }

  // Update Time
  prev_tick = k_uptime_get_32();
}

/*
 * Main loop and device setup 
 */
int main(void) {

  int ret; //error flag

  /* Config pushbutton and pushbutton ISR*/
  if (!gpio_is_ready_dt(&button)) {
    printk("Error: button device %s is not ready\n", button.port->name);
    return 0;
  }
  ret = gpio_pin_configure_dt(&button, GPIO_INPUT);
  if (ret != 0) {
    printk("Error %d: failed to configure %s pin %d\n", ret, button.port->name, button.pin);
    return 0;
  }
  ret = gpio_pin_interrupt_configure_dt(&button, GPIO_INT_EDGE_TO_ACTIVE);
  if (ret != 0) {
    printk("Error %d: failed to configure interrupt on %s pin %d\n", ret, button.port->name,
           button.pin);
    return 0;
  }
  gpio_init_callback(&button_cb_data, button_pressed, BIT(button.pin));
  gpio_add_callback(button.port, &button_cb_data);

  /* Config LED*/
  if (!gpio_is_ready_dt(&led)) {
    return 0;
  }
  ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_ACTIVE);
  if (ret < 0) {
    return 0;
  }
  gpio_pin_set_dt(&led, true); //turn LED on

  /* Config and turn on BLE*/
  ret = bt_enable(NULL);
  if (ret) {
    printk("Bluetooth init failed (err %d)\n", ret);
  }
  ret = bt_le_adv_start(ADV_PARAM, ad, ARRAY_SIZE(ad), NULL, 0);
  if (ret) {
    printk("Advertising failed to start (err %d)\n", ret);
    return 0;
  }

  while (true) {
	// Button press 
	if(buttonPressFlag == 1) {

		buttonPressFlag = 0; // clear flag
		//toggle byte value in broadcasted bt packet
		if(data[TOGGLE_BYTE_INDEX] == 0x01) {
			data[TOGGLE_BYTE_INDEX] = 0x00;
		} else {
			data[TOGGLE_BYTE_INDEX] = 0x01;
		}
		bt_le_adv_update_data(ad, ARRAY_SIZE(ad), NULL, 0); //update bt adv
	}

    k_msleep(SLEEP_TIME_MS);
  }

  return 0;
}
