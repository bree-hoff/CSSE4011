#include "nanopb_serial.h"
#include "hid.h"

#define THREAD_DELAY 1

static const struct gpio_dt_spec led0 = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static const struct device *const uart = DEVICE_DT_GET(DT_NODELABEL(uart0));

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

      printk("Got %c\n",c);

      if(count == 0) {
        rx_index = c;
        count++;
        printk("First Char");

      } else {
        rx_buffer[count - 1] = c;

          
        if (rx_index == count) {
            MinecraftMessage message = MinecraftMessage_init_zero;
            pb_istream_t istream = pb_istream_from_buffer(rx_buffer, rx_index);
            if (!pb_decode(&istream, Message_fields, &message)) {
                printk("Error decoding message\n");
        
                count = 0;
                break;
            }

            printk("Received foo: %d\n", message.foo);
            printk("Received temp: %s\n", message.temp);
            if(message.foo == 29) {
              gpio_pin_toggle_dt(&led0);
              count = 0;
              break;

            }  
            
        }
        count++;
      }
 
  }
}

void nanopb_thread(void) {
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
