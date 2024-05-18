import tkinter as tk
import serial
import time
from minecraftmessage_pb2 import MinecraftMessage, MessageType, GestureType
import threading
import struct
import time

mutex = threading.Lock()

def read_from_serial(ser):
    while True:
        data = ser.readline() 
        print("Received:", data)
        if data == b'1\r\n':
            print("Push Button!!")

def serial_send(ser, message_type, gesture, x_ultrasonic, y_ultrasonic):
    x_ultrasonic += 2
    y_ultrasonic += 2
    mutex.acquire()
    try:
        message = MinecraftMessage()
        message.message_type = message_type
        message.gesture = gesture
        message.x_ultrasonic = x_ultrasonic
        message.y_ultrasonic = y_ultrasonic

        

        serialized_message = message.SerializeToString()
        print(serialized_message)
        if len(serialized_message) == 0:
            return
        length_byte = len(serialized_message).to_bytes(1, 'big')

        ser.write(length_byte)
        
        for byte in serialized_message:
            ser.write(byte.to_bytes(1, 'big'))
            time.sleep(0.05)

        # print("Message Length:", len(serialized_message))
        # print("Message:", serialized_message)
        # print(str(message.gesture))
    finally:
        mutex.release()
