import tkinter as tk
import serial
import time
from minecraftmessage_pb2 import MinecraftMessage, MessageType, GestureType
import threading
import struct
import time

ser = serial.Serial('/dev/tty.usbmodem0010502125801', 115200)  

def send_number():
    # Create a protobuf message
    message = MinecraftMessage()
    message.message_type = MessageType.BOTH
    message.gesture = GestureType.JUMP
    message.x_ultrasonic = 150
    message.y_ultrasonic = 300

    # Serialize the message
    serialized_message = message.SerializeToString()

    length_byte = len(serialized_message).to_bytes(1, 'big')

    ser.write(length_byte)
    
    # Send the serialized message over serial

    for byte in serialized_message:
            ser.write(byte.to_bytes(1, 'big'))
            time.sleep(0.01)

    print("Message Length:", len(serialized_message))
    print("Message:", serialized_message)

def read_from_serial():
    while True:
        data = ser.readline() 
        print("Received:", data)


# GUI
root = tk.Tk()
root.title("Nanopb Test")
root.geometry("300x100")

button = tk.Button(root, text="Send Number", command=send_number)
button.pack()



# Start a separate thread to continuously read from the serial port
read_thread = threading.Thread(target=read_from_serial)
read_thread.daemon = True
read_thread.start()

root.mainloop()

ser.close()


## NEW FUNCTION
# def send_number(message_type, gesture, x_ultrasonic, y_ultrasonic):
   
#     message = MinecraftMessage()
#     message.message_type = message_type
#     message.gesture = gesture
#     message.x_ultrasonic = x_ultrasonic
#     message.y_ultrasonic = y_ultrasonic

#     serialized_message = message.SerializeToString()

#     length_byte = len(serialized_message).to_bytes(1, 'big')

#     ser.write(length_byte)
    
#     for byte in serialized_message:
#         ser.write(byte.to_bytes(1, 'big'))
#         time.sleep(0.01)

#     print("Message Length:", len(serialized_message))
#     print("Message:", serialized_message)
