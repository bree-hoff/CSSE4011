/*
 * Copyright (c) 2019 Nordic Semiconductor ASA
 *
 * SPDX-License-Identifier: Apache-2.0
 */
#include "hid.h"

#define LOG_LEVEL LOG_LEVEL_DBG
LOG_MODULE_REGISTER(hid);

#define SW0_NODE DT_ALIAS(sw0)

#if DT_NODE_HAS_STATUS(SW0_NODE, okay)
static const struct gpio_dt_spec sw0_gpio = GPIO_DT_SPEC_GET(SW0_NODE, gpios);
#endif

#define SW1_NODE DT_ALIAS(sw1)

#if DT_NODE_HAS_STATUS(SW1_NODE, okay)
static const struct gpio_dt_spec sw1_gpio = GPIO_DT_SPEC_GET(SW1_NODE, gpios);
#endif

#define SW2_NODE DT_ALIAS(sw2)

#if DT_NODE_HAS_STATUS(SW2_NODE, okay)
static const struct gpio_dt_spec sw2_gpio = GPIO_DT_SPEC_GET(SW2_NODE, gpios);
#endif

#define SW3_NODE DT_ALIAS(sw3)

#if DT_NODE_HAS_STATUS(SW3_NODE, okay)
static const struct gpio_dt_spec sw3_gpio = GPIO_DT_SPEC_GET(SW3_NODE, gpios);
#endif

/* Event FIFO */

K_FIFO_DEFINE(evt_fifo);

#define FIFO_ELEM_MIN_SZ        sizeof(struct app_evt_t)
#define FIFO_ELEM_MAX_SZ        sizeof(struct app_evt_t)
#define FIFO_ELEM_COUNT         255
#define FIFO_ELEM_ALIGN         sizeof(unsigned int)

K_HEAP_DEFINE(event_elem_pool, FIFO_ELEM_MAX_SZ * FIFO_ELEM_COUNT + 256);

/* HID */
static const struct device *hid0_dev, *hid1_dev;
static const uint8_t hid_mouse_report_desc[] = HID_MOUSE_REPORT_DESC(2);
static const uint8_t hid_kbd_report_desc[] = HID_KEYBOARD_REPORT_DESC();
static char mapEvtToChar[10] = {'w', 's', 'a', 'd', '1', '2', '3', '4', '5', ' '};

static K_SEM_DEFINE(evt_sem, 0, 1);	/* starts off "not available" */
static K_SEM_DEFINE(usb_sem, 1, 1);	/* starts off "available" */
static struct gpio_callback gpio_callbacks[4];

#define MOUSE_BTN_REPORT_POS	0
#define MOUSE_X_REPORT_POS	1
#define MOUSE_Y_REPORT_POS	2

#define MOUSE_BTN_LEFT		BIT(0)
#define MOUSE_BTN_RIGHT		BIT(1)
#define MOUSE_BTN_MIDDLE	BIT(2)

static inline void app_evt_free(struct app_evt_t *ev)
{
	k_heap_free(&event_elem_pool, ev);
}

static inline void app_evt_put(struct app_evt_t *ev)
{
	k_fifo_put(&evt_fifo, ev);
}

static inline struct app_evt_t *app_evt_get(void)
{
	return k_fifo_get(&evt_fifo, K_NO_WAIT);
}

static inline void app_evt_flush(void)
{
	struct app_evt_t *ev;

	do {
		ev = app_evt_get();
		if (ev) {
			app_evt_free(ev);
		}
	} while (ev != NULL);
}

static inline struct app_evt_t *app_evt_alloc(void)
{
	struct app_evt_t *ev;

	ev = k_heap_alloc(&event_elem_pool,
			  sizeof(struct app_evt_t),
			  K_NO_WAIT);
	if (ev == NULL) {
		LOG_ERR("APP event allocation failed!");
		app_evt_flush();

		ev = k_heap_alloc(&event_elem_pool,
				  sizeof(struct app_evt_t),
				  K_NO_WAIT);
		if (ev == NULL) {
			LOG_ERR("APP event memory corrupted.");
			__ASSERT_NO_MSG(0);
			return NULL;
		}
		return NULL;
	}

	return ev;
}

void app_evt_add_new_command(enum evt_t event_type) {
    struct app_evt_t *ev2 = app_evt_alloc();
    ev2->event_type = event_type,
    app_evt_put(ev2);
    k_sem_give(&evt_sem);
}

static void in_ready_cb(const struct device *dev)
{
	ARG_UNUSED(dev);

	k_sem_give(&usb_sem);
}

static const struct hid_ops ops = {
	.int_in_ready = in_ready_cb,
};

void clear_mouse_report(void)
{
	struct app_evt_t *new_evt = app_evt_alloc();

	new_evt->event_type = MOUSE_CLEAR;
	app_evt_put(new_evt);
	k_sem_give(&evt_sem);
}

void clear_kbd_report(void)
{
	struct app_evt_t *new_evt = app_evt_alloc();

	new_evt->event_type = KBD_CLEAR;
	app_evt_put(new_evt);
	k_sem_give(&evt_sem);
}

static int ascii_to_hid(uint8_t ascii)
{
	if (ascii < 32) {
		/* Character not supported */
		return -1;
	} else if (ascii < 48) {
		/* Special characters */
		switch (ascii) {
		case 32:
			return HID_KEY_SPACE;
		case 33:
			return HID_KEY_1;
		case 34:
			return HID_KEY_APOSTROPHE;
		case 35:
			return HID_KEY_3;
		case 36:
			return HID_KEY_4;
		case 37:
			return HID_KEY_5;
		case 38:
			return HID_KEY_7;
		case 39:
			return HID_KEY_APOSTROPHE;
		case 40:
			return HID_KEY_9;
		case 41:
			return HID_KEY_0;
		case 42:
			return HID_KEY_8;
		case 43:
			return HID_KEY_EQUAL;
		case 44:
			return HID_KEY_COMMA;
		case 45:
			return HID_KEY_MINUS;
		case 46:
			return HID_KEY_DOT;
		case 47:
			return HID_KEY_SLASH;
		default:
			return -1;
		}
	} else if (ascii < 58) {
		/* Numbers */
		if (ascii == 48U) {
			return HID_KEY_0;
		} else {
			return ascii - 19;
		}
	} else if (ascii < 65) {
		/* Special characters #2 */
		switch (ascii) {
		case 58:
			return HID_KEY_SEMICOLON;
		case 59:
			return HID_KEY_SEMICOLON;
		case 60:
			return HID_KEY_COMMA;
		case 61:
			return HID_KEY_EQUAL;
		case 62:
			return HID_KEY_DOT;
		case 63:
			return HID_KEY_SLASH;
		case 64:
			return HID_KEY_2;
		default:
			return -1;
		}
	} else if (ascii < 91) {
		/* Uppercase characters */
		return ascii - 61U;
	} else if (ascii < 97) {
		/* Special characters #3 */
		switch (ascii) {
		case 91:
			return HID_KEY_LEFTBRACE;
		case 92:
			return HID_KEY_BACKSLASH;
		case 93:
			return HID_KEY_RIGHTBRACE;
		case 94:
			return HID_KEY_6;
		case 95:
			return HID_KEY_MINUS;
		case 96:
			return HID_KEY_GRAVE;
		default:
			return -1;
		}
	} else if (ascii < 123) {
		/* Lowercase letters */
		return ascii - 93;
	} else if (ascii < 128) {
		/* Special characters #4 */
		switch (ascii) {
		case 123:
			return HID_KEY_LEFTBRACE;
		case 124:
			return HID_KEY_BACKSLASH;
		case 125:
			return HID_KEY_RIGHTBRACE;
		case 126:
			return HID_KEY_GRAVE;
		case 127:
			return HID_KEY_DELETE;
		default:
			return -1;
		}
	}

	return -1;
}

static bool needs_shift(uint8_t ascii)
{
	if ((ascii < 33) || (ascii == 39U)) {
		return false;
	} else if ((ascii >= 33U) && (ascii < 44)) {
		return true;
	} else if ((ascii >= 44U) && (ascii < 58)) {
		return false;
	} else if ((ascii == 59U) || (ascii == 61U)) {
		return false;
	} else if ((ascii >= 58U) && (ascii < 91)) {
		return true;
	} else if ((ascii >= 91U) && (ascii < 94)) {
		return false;
	} else if ((ascii == 94U) || (ascii == 95U)) {
		return true;
	} else if ((ascii > 95) && (ascii < 123)) {
		return false;
	} else if ((ascii > 122) && (ascii < 127)) {
		return true;
	} else {
		return false;
	}
}

/* Devices */

static void btn0(const struct device *gpio, struct gpio_callback *cb,
		 uint32_t pins)
{
	app_evt_add_new_command(KBD_FORWARD);
    clear_kbd_report();
}

#if DT_NODE_HAS_STATUS(SW1_NODE, okay)
static void btn1(const struct device *gpio, struct gpio_callback *cb,
		 uint32_t pins)
{
	app_evt_add_new_command(KBD_BACKWARD);
    clear_kbd_report();
}
#endif

#if DT_NODE_HAS_STATUS(SW2_NODE, okay)
static void btn2(const struct device *gpio, struct gpio_callback *cb,
		 uint32_t pins)
{
	app_evt_add_new_command(MOUSE_LEFT_CLICK);
    clear_mouse_report();
}
#endif

#if DT_NODE_HAS_STATUS(SW3_NODE, okay)
static void btn3(const struct device *gpio, struct gpio_callback *cb,
		 uint32_t pins)
{
	app_evt_add_new_command(MOUSE_RIGHT_CLICK);
    clear_mouse_report();
}
#endif

int callbacks_configure(const struct gpio_dt_spec *gpio,
			void (*handler)(const struct device *, struct gpio_callback*,
					uint32_t),
			struct gpio_callback *callback)
{
	if (!device_is_ready(gpio->port)) {
		LOG_ERR("%s: device not ready.", gpio->port->name);
		return -ENODEV;
	}

	gpio_pin_configure_dt(gpio, GPIO_INPUT);

	gpio_init_callback(callback, handler, BIT(gpio->pin));
	gpio_add_callback(gpio->port, callback);
	gpio_pin_interrupt_configure_dt(gpio, GPIO_INT_EDGE_TO_ACTIVE);

	return 0;
}

static void status_cb(enum usb_dc_status_code status, const uint8_t *param)
{
	LOG_INF("Status %d", status);
}

static void transmit_key(char character) {
    int ch = ascii_to_hid(character);

    if (ch == -1) {
        LOG_WRN("Unsupported character: %d", character);
    } else {
        uint8_t rep[] = {0x00, 0x00, 0x00, 0x00,
                    0x00, 0x00, 0x00, 0x00};
        if (needs_shift(character)) {
            rep[0] |=
            HID_KBD_MODIFIER_RIGHT_SHIFT;
        }
        rep[7] = ch;

        k_sem_take(&usb_sem, K_FOREVER);
        hid_int_ep_write(hid1_dev, rep,
                sizeof(rep), NULL);
    }
}

#define DEVICE_AND_COMMA(node_id) DEVICE_DT_GET(node_id),

void hid_control_thread(void)
{
	struct app_evt_t *ev;
	int ret;

	/* Configure devices */

	hid0_dev = device_get_binding("HID_0");
	if (hid0_dev == NULL) {
		LOG_ERR("Cannot get USB HID 0 Device");
		return;
	}

	hid1_dev = device_get_binding("HID_1");
	if (hid1_dev == NULL) {
		LOG_ERR("Cannot get USB HID 1 Device");
		return;
	}

	if (callbacks_configure(&sw0_gpio, &btn0, &gpio_callbacks[0])) {
		LOG_ERR("Failed configuring button 0 callback.");
		return;
	}

#if DT_NODE_HAS_STATUS(SW1_NODE, okay)
	if (callbacks_configure(&sw1_gpio, &btn1, &gpio_callbacks[1])) {
		LOG_ERR("Failed configuring button 1 callback.");
		return;
	}
#endif

#if DT_NODE_HAS_STATUS(SW2_NODE, okay)
	if (callbacks_configure(&sw2_gpio, &btn2, &gpio_callbacks[2])) {
		LOG_ERR("Failed configuring button 2 callback.");
		return;
	}
#endif

#if DT_NODE_HAS_STATUS(SW3_NODE, okay)
	if (callbacks_configure(&sw3_gpio, &btn3, &gpio_callbacks[3])) {
		LOG_ERR("Failed configuring button 3 callback.");
		return;
	}
#endif

	/* Initialize HID */

	usb_hid_register_device(hid0_dev, hid_mouse_report_desc,
				sizeof(hid_mouse_report_desc), &ops);

	usb_hid_register_device(hid1_dev, hid_kbd_report_desc,
				sizeof(hid_kbd_report_desc), &ops);

	usb_hid_init(hid0_dev);
	usb_hid_init(hid1_dev);

	ret = usb_enable(status_cb);
	if (ret != 0) {
		LOG_ERR("Failed to enable USB");
		return;
	} 

	while (true) {

		k_sem_take(&evt_sem, K_FOREVER);

		while ((ev = app_evt_get()) != NULL) {

            if (ev->event_type < KEYBOARD_COMMANDS_INDEX) {
                char command_char = mapEvtToChar[ev->event_type];
                LOG_INF("Keyboard command: %c", command_char);
                LOG_INF("Keyboard command: %d", ev->event_type);
                transmit_key(command_char);
            } else if (ev->event_type == KBD_CLEAR) {
                /* Clear kbd report */
				uint8_t rep[] = {0x00, 0x00, 0x00, 0x00,
					      0x00, 0x00, 0x00, 0x00};

				k_sem_take(&usb_sem, K_FOREVER);
				hid_int_ep_write(hid1_dev, rep,
						 sizeof(rep), NULL);
            } else if (ev->event_type < MOUSE_COMMANDS_INDEX) {
                uint8_t rep[] = {0x00, 0x00, 0x00, 0x00};
                switch (ev->event_type) {
                    case MOUSE_UP:
                        rep[MOUSE_Y_REPORT_POS] = 0xE0;
                        break;
                    case MOUSE_DOWN:
                        rep[MOUSE_Y_REPORT_POS] = 0x20;
                        break;
                    case MOUSE_LEFT:
                        rep[MOUSE_X_REPORT_POS] = 0xE0;
                        break;
                    case MOUSE_RIGHT:
                        rep[MOUSE_X_REPORT_POS] = 0x20;
                        break;
                    default:
                        break;
                }
				k_sem_take(&usb_sem, K_FOREVER);
				hid_int_ep_write(hid0_dev, rep,
						 sizeof(rep), NULL);
            } else if (ev->event_type == MOUSE_CLEAR) {
                /* Clear mouse report */
				uint8_t rep[] = {0x00, 0x00, 0x00, 0x00};

				k_sem_take(&usb_sem, K_FOREVER);
				hid_int_ep_write(hid0_dev, rep,
						 sizeof(rep), NULL);
            } else if (ev->event_type == MOUSE_LEFT_CLICK) {
                /* Press left mouse button */
				uint8_t rep[] = {0x00, 0x00, 0x00, 0x00};

				rep[MOUSE_BTN_REPORT_POS] |= MOUSE_BTN_LEFT;
				k_sem_take(&usb_sem, K_FOREVER);
				hid_int_ep_write(hid0_dev, rep,
						 sizeof(rep), NULL);
            } else if (ev->event_type == MOUSE_RIGHT_CLICK) {
                /* Press right mouse button */
				uint8_t rep[] = {0x00, 0x00, 0x00, 0x00};

				rep[MOUSE_BTN_REPORT_POS] |= MOUSE_BTN_RIGHT;
				k_sem_take(&usb_sem, K_FOREVER);
				hid_int_ep_write(hid0_dev, rep,
						 sizeof(rep), NULL);
            } else {
                LOG_ERR("Invalid character command received");
            }
		}
	}
}
