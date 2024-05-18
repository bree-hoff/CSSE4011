#ifndef HID_H
#define HID_H

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/uart.h>
#include <string.h>
#include <zephyr/random/random.h>

#include <zephyr/usb/usb_device.h>
#include <zephyr/usb/class/usb_hid.h>
#include <zephyr/usb/class/usb_cdc.h>

#define KEYBOARD_COMMANDS_INDEX 10
#define MOUSE_COMMANDS_INDEX 16

enum evt_t {
    KBD_FORWARD	        = 0x00,
    KBD_BACKWARD	    = 0x01,
    KBD_LEFT            = 0x02,
    KBD_RIGHT           = 0x03,
    KBD_ONE             = 0x04,
    KBD_TWO             = 0x05,
    KBD_THREE           = 0x06,
    KBD_FOUR            = 0x07,
    KBD_FIVE            = 0x08,
    KBD_SPACE           = 0x09,
    KBD_CLEAR	        = 0x0A,
	MOUSE_UP		    = 0x0B,
	MOUSE_DOWN	        = 0x0C,
	MOUSE_LEFT	        = 0x0D,
	MOUSE_RIGHT	        = 0x0E,
	MOUSE_CLEAR	        = 0x0F,
    MOUSE_LEFT_CLICK    = 0x10,
    MOUSE_RIGHT_CLICK   = 0x20
}; 

struct app_evt_t {
	sys_snode_t node;
	enum evt_t event_type;
};

extern void app_evt_add_new_command(enum evt_t event_type);

extern void clear_mouse_report(void);

extern void clear_kbd_report(void);

extern void hid_control_thread(void);

#endif
