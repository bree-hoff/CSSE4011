import tkinter as tk
import threading
import queue
import time

from pahomqttsub import read_from_mqtt

def get_position(queue):

    while True:
        rx_data = queue.get()

        print(f"Received from thread: {rx_data}")

        time.sleep(1)

# Start a separate thread to continuously read from the mqtt port
queue = queue.Queue()
mqtt_thread = threading.Thread(target=get_position, args=(queue,))
rx_thread = threading.Thread(target=read_from_mqtt, args=(queue,))
mqtt_thread.daemon = True
rx_thread.daemon = True
mqtt_thread.start()
rx_thread.start()

# GUI
root = tk.Tk()
root.title("Nanopb Test")
root.geometry("300x100")

button = tk.Button(root, text="Click Me", command=lambda: print("Button clicked!"))
button.pack()

root.mainloop()
