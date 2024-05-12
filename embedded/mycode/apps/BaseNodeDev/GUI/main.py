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
    message.foo = 1023 

    # Serialize the message
    serialized_message = message.SerializeToString()

    length_byte = struct.pack('>B', len(serialized_message))

    ser.write(length_byte)
    
    # Send the serialized message over serial
    ser.write(serialized_message)

    print("Sent number:", message.foo)
    print(length_byte)
    print(serialized_message)

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
