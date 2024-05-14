#include "nanopb_serial.h"
#include "hid.h"
#include "src/minecraftmessage.pb.h"

#define THREAD_DELAY 1

LOG_MODULE_REGISTER(nanopb);
static const struct gpio_dt_spec led0 = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static const struct device *const uart = DEVICE_DT_GET(DT_NODELABEL(uart0));

void interpret_gesture(GestureType gesture) {
  switch (gesture) {
    case GestureType_LEFT_CLICK:
      app_evt_add_new_command(MOUSE_LEFT_CLICK);
      break;
    case GestureType_LOOK_LEFT:
      app_evt_add_new_command(MOUSE_LEFT);
      break;
    case GestureType_LOOK_RIGHT:
      app_evt_add_new_command(MOUSE_RIGHT);
      break;
    case GestureType_ONE:
      app_evt_add_new_command(KBD_ONE);
      clear_kbd_report();
      break;
    case GestureType_TWO:
      app_evt_add_new_command(KBD_TWO);
      clear_kbd_report();
      break;
    case GestureType_THREE:
      app_evt_add_new_command(KBD_THREE);
      clear_kbd_report();
      break;
    case GestureType_FOUR:
      app_evt_add_new_command(KBD_FOUR);
      clear_kbd_report();
      break;
    case GestureType_FIVE:
      app_evt_add_new_command(KBD_FIVE);
      clear_kbd_report();
      break;
    case GestureType_JUMP:
      app_evt_add_new_command(KBD_SPACE);
      break;
    case GestureType_LOOK_UP:
      app_evt_add_new_command(MOUSE_UP);
      break;
    case GestureType_LOOK_DOWN:
      app_evt_add_new_command(MOUSE_RIGHT);
      break;
    default:
      clear_kbd_report();
      clear_mouse_report();
  }
}

void interpret_position(int32_t x, int32_t y) {
  if (y == -1) {
    app_evt_add_new_command(KBD_BACKWARD);
  } else if (y == 1) {
    app_evt_add_new_command(KBD_FORWARD);
  } else if (x == -1) {
    app_evt_add_new_command(KBD_LEFT);
  } else if (x == 1) {
    app_evt_add_new_command(KBD_RIGHT);
  } else {
    clear_kbd_report();
  }
}

void interpret_message(MinecraftMessage message) {
  if (message.message_type == MessageType_BOTH 
   || message.message_type == MessageType_ULTRASONIC) {
    interpret_position(message.x_ultrasonic, message.y_ultrasonic);
  }
  
  if (message.message_type == MessageType_BOTH 
  || message.message_type == MessageType_GESTURE) {
    interpret_gesture(message.gesture);
  }
}

void uart_rx_cb(const struct device *dev, void *user_data) {
    
    uint8_t c;
    static uint8_t count = 0;
    static uint8_t rx_buffer[128];
    static uint32_t rx_index = 0;

    if (!uart_irq_update(uart)) {
        return;
    }
    if (!uart_irq_rx_ready(uart)) {
        return;
    }

    while (uart_fifo_read(uart, &c, 1) == 1) {   

      if(count == 0) {
        rx_index = c;
        count++;

      } else {
        
    
        rx_buffer[count - 1] = c;

        count++;
       
   
        if (rx_index == (count - 1)) {
            
            MinecraftMessage message = MinecraftMessage_init_zero;
            pb_istream_t istream = pb_istream_from_buffer(rx_buffer, rx_index);
            if (!pb_decode(&istream, MinecraftMessage_fields, &message)) {
                LOG_ERR("Error decoding message\n");
        
                count = 0;
                break;
            }

            interpret_message(message);

            // printk("Message Type: %d\n", message.message_type);
            // printk("Gesture: %d\n", message.gesture);
            // printk("X Ultrasonic: %d\n", message.x_ultrasonic);
            // printk("Y Ultrasonic: %d\n", message.y_ultrasonic);
            count = 0;
            
        }
       
        
      }
 
  }
}


void init_nanopb(void) {
    int ret;
    if (!gpio_is_ready_dt(&led0)) {
        return; 
    }

    ret = gpio_pin_configure_dt(&led0, GPIO_OUTPUT_ACTIVE);
    if (ret < 0) {
        return;
    }

    uart_irq_callback_user_data_set(uart, uart_rx_cb, NULL);
    uart_irq_rx_enable(uart);

    return;
}