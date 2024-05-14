import tkinter as tk
import serial
import time
import message_pb2 as pb  
import threading
import struct

ser = serial.Serial('/dev/tty.usbmodem0010502125801', 115200)  

def send_number():
    # Create a protobuf message
    message = pb.Message()
    message.foo = 13456 
    message.temp = "Hi"

    # Serialize the message
    serialized_message = message.SerializeToString()

    length_byte = len(serialized_message).to_bytes(1, 'big')

    print(length_byte)

    ser.write(length_byte)
    
    # Send the serialized message over serial
    ser.write(serialized_message)

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
