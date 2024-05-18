import serial
import threading
import pc_message_pb2
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
                    if data == b'\x01\r\n':
                        nodeData = self.serial_instance.readline().rstrip(b'\r\n')
                        nodeData = b'\x0a' + nodeData
                        print(nodeData)
                        message = pc_message_pb2.NodeMessage()
                        message.ParseFromString(nodeData)
                        self.message_queue.put(message)
                            
                    elif data == b'\x02\r\n':
                        rssiData = self.serial_instance.readline().rstrip(b'\r\n')
                        print(rssiData)
                        rssimessage = pc_message_pb2.RSSIMessage()
                        rssimessage.ParseFromString(rssiData)
                        self.message_rssi_queue.put(rssimessage)
        
                    else:
                        print("Unknown byte:", data)
        except serial.SerialException as e:
            print("Serial error:", e)

    def stop(self):
        self._stop_event.set()
