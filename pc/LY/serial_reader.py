import serial
import threading
import queue

class SerialReader(threading.Thread):
    def __init__(self, serial_instance, parent_window):
        super().__init__()
        self.serial_instance = serial_instance
        self.parent_window = parent_window
        self._stop_event = threading.Event()
        self.message_queue = queue.Queue()
        self.message_rssi_queue = queue.Queue()

    def run(self):
        try:
            while not self._stop_event.is_set():
                if self.serial_instance and self.serial_instance.is_open:
                    data = self.serial_instance.readline() 
                    #print(data)
                    if data == b'\x30\r\n':
                        nodeData = self.serial_instance.readline().rstrip(b'\r\n')
                        print(nodeData)
                    else:
                        print("Unknown byte:", data)
        except serial.SerialException as e:
            print("Serial error:", e)

    def stop(self):
        self._stop_event.set()
