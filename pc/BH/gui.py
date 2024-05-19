import tkinter as tk
import paho.mqtt.client as mqtt
import time
import queue
import threading
import gesture_detection as gd
import serial_send as sl
import serial
from minecraftmessage_pb2 import MinecraftMessage, MessageType, GestureType
import os

MQTT_active = 1
CAM_active = 1
BLE_active = 1
rx_msg = ""
last_send_time = 0

#Colour scheme
MEDIUM_GRAY = "#808080"
LIGHT_GRAY = "#B3B3B3"
DARK_GRAY = "#323232"
WHITE = "#FFFFFF"

# Open serial port
if BLE_active:
    ser = serial.Serial('/dev/tty.usbmodem0010502125801', 115200)

# Class for tracking the current position provided from the ultrasonic sensors
class CurrentPositions:
    def __init__(self):
        self.x_coord = 0
        self.y_coord = 0
        self.x_raw = 0
        self.y_raw = 0

    # Add x coordinate (-1, 0 or 1)
    def add_x_coord(self, x_coord):
        self.x_coord = x_coord

    # Add y coordinate (-1, 0 or 1)
    def add_y_coord(self, y_coord):
        self.y_coord = y_coord

    # Add raw x value (cm)
    def add_x_raw(self, x_raw):
        self.x_raw = x_raw

    # Add raw y value (cm)
    def add_y_raw(self, y_raw):
        self.y_raw = y_raw
    
    # Return raw x, y values (cm) in a tuple
    def get_raw(self):
        return (self.x_raw, self.y_raw)

    # Return x, y coordinates (-1, 0 1) in a tuple
    def get_coords(self):
        return (self.x_coord, self.y_coord)

# Function for handling the incoming UART data
def handle_uart_data(ser, pushed_label):
    while True:
        # Read from serial port
        data = ser.readline() 
        # print("Received:", data)
        # If receive button press, update GUI with last time pressed
        if data == b'1\r\n':
            # print("1")
            current_time = time.localtime()
            pushed_label.configure(text = "Last Button Press At Time: " + time.strftime("%H:%M:%S", current_time))
            
# Function to retrieve topic's message from broker
def on_message(client, userdata, message):
    try:
        rx_msg = message.payload.decode("utf-8")
        client.user_data_set(rx_msg)
    except:
        print("message receive error")

# Function to subscribe to ultrasonic's topic when node is connected
def on_connect(client, userdata, flags, reason_code, properties):
    client.subscribe("tellusteal")

# Function to handle incoming MQTT messages from ultrasonic sensors   
def handle_mqtt_data(ser, mqtt_q, x_label, y_label, tracker, canvas):
    global last_send_time
    current_positions = CurrentPositions()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    # Connect to CSSE4011 MQTT broker
    client.user_data_set([])
    ssid = "infrastructure"
    password = "jEizUMsPiTD8"
    client.username_pw_set(ssid, password)
    client.connect("csse4011-iot.zones.eait.uq.edu.au")

    client.loop_start()
    while True:
        # Only process incoming message
        if client.user_data_get() != [] and client.user_data_get() != "nil":
            data = client.user_data_get()
            client.user_data_set("nil")

            # Split received string into X/Y, Raw and Coord fields
            data_list = data.split()

            # Record previous coordinates for sending constraints
            prev_coords = current_positions.get_coords()

            # Handle GUI update and CurrentPositions() update
            if data_list[0] == "x":
                x_label.configure(text = "X: " + str(data_list[1]))
                current_positions.add_x_raw(float(data_list[1]))
                current_positions.add_x_coord(int(data_list[2]))
            else:
                y_label.configure(text = "Y: " + str(data_list[1]))
                current_positions.add_y_raw(float(data_list[1]))
                current_positions.add_y_coord(int(data_list[2]))
            
            # Update tracker on GUI for position data
            match current_positions.get_coords(): # 18 , 50, 82
                case (0, 0):
                    x = 50
                    y = 50
                case (0, -1): 
                    x = 50
                    y = 82
                case (0, 1): 
                    x = 50
                    y = 17
                case (-1, 0): 
                    x = 17
                    y = 50
                case (1, 0): 
                    x = 82
                    y = 50
                case (1, 1):
                    x = 82
                    y = 17
                case (-1, -1):
                    x = 17
                    y = 82
                case (-1, 1):
                    x = 17
                    y = 17
                case (1, -1):
                    x = 82
                    y = 82
                case default:
                    x = 50
                    y = 50
            
            coords = current_positions.get_coords()

            # Send data if position changes and if it has been 500ms since last send
            if coords != prev_coords and time.time() > last_send_time + 0.5:
                last_send_time = time.time()
                sl.serial_send(ser, MessageType.ULTRASONIC, GestureType.NO_GESTURE, coords[0], coords[1])

            # Move GUI tracker according to coordinate provided
            old_coords = canvas.coords(tracker)
            old_loc_x = old_coords[0] + 5
            old_loc_y = old_coords[1] + 5
            canvas.move(tracker, (x - old_loc_x), (y - old_loc_y))
            
        time.sleep(0.05)

class GUI:
    def __init__(self, master):
        self.master = master
        master.title("MQTT Data Display")
        master.geometry("900x400")

        self.configure_theme()

        # Ultrasonic data 
        self.ultrasonic_lbl = tk.Label(master, text="Ultrasonic Sensor Data")
        self.ultrasonic_lbl.grid(row=0, column=0, padx=20, pady=10)
        self.ultrasonic_x_lbl = tk.Label(master, text="X: 0000")
        self.ultrasonic_x_lbl.grid(row=1, column=0, padx=20, pady=10)
        self.ultrasonic_y_lbl = tk.Label(master, text="Y: 0000")
        self.ultrasonic_y_lbl.grid(row=2, column=0, padx=20, pady=10)
        
        self.tracker_canvas = tk.Canvas(master, width=100, height=100, bg=MEDIUM_GRAY, highlightthickness=0)
        
        # Outline the grid in white
        self.tracker_canvas.create_rectangle(2, 2, 98, 98, outline=WHITE, width=2)


        # Divide the space into 9 smaller squares
        map_size = 96
        half_m_square_size = map_size / 3
        for i in range(0, 3):  # 3 squares per side
            for j in range(0, 3):  # 3 squares per side
                if (i + j) % 2 == 0: # Alternate shades
                    colour = LIGHT_GRAY
                else:
                    colour = MEDIUM_GRAY
                self.tracker_canvas.create_rectangle(i * half_m_square_size + 2, j * half_m_square_size + 2,
                                                (i + 1) * half_m_square_size + 2, (j + 1) * half_m_square_size + 2,
                                                fill=colour, outline="")
                
        # Create the tracking circles
        tracker_radius = 5
        tracker_centre = (50, 50)  # Some starting point on grid 17, 50, 82

        # Ultrasonic tracker
        tracker_x = tracker_centre[0]
        tracker_y = tracker_centre[1]

        # Create circle trackers
        self.ls_tracker = self.tracker_canvas.create_oval(tracker_centre[0] - tracker_radius, tracker_centre[1] - tracker_radius,
                                                tracker_centre[0] + tracker_radius, tracker_centre[1] + tracker_radius,
                                                fill=WHITE, outline="")

        self.tracker_canvas.grid(row=3, column=0, padx=20, pady=10)


        # Thingy:52 pushbutton data
        self.button_lbl = tk.Label(master, text="Push Button Data")
        self.button_lbl.grid(row=0, column=1, padx=20, pady=10)
        self.button_pushed_lbl = tk.Label(master, text="Last Button Press At Time: 0000")
        self.button_pushed_lbl.grid(row=1, column=1, padx=20, pady=10)
        
        # Webcam gesture detection data
        self.camera_lbl = tk.Label(master, text="Webcam Data")
        self.camera_lbl.grid(row=0, column=2, padx=20, pady=10)
        self.raw_gesture_lbl = tk.Label(master, text="Detected Gesture: 0000")
        self.raw_gesture_lbl.grid(row=1, column=2, padx=20, pady=10)
        self.filtered_gesture_lbl = tk.Label(master, text="Filtered Gesture: 0000")
        self.filtered_gesture_lbl.grid(row=2, column=2, padx=20, pady=10)
        self.detected_hand_lbl = tk.Label(master, text="Detected Hand: 0000")
        self.detected_hand_lbl.grid(row=3, column=2, padx=20, pady=10)

        # Review data section
        self.stars_prompt_lbl = tk.Label(master, text="Star rating out of 5: ")
        self.stars_prompt_lbl.grid(row=4, column=0, padx=20, pady=10)
        self.stars_entry = tk.Entry(master, width=40)
        self.stars_entry.grid(row=4, column=1, padx=20, pady=10)
        self.stars_enter_btn = tk.Button(master, text="Submit", command=self.write_response)
        self.stars_enter_btn.grid(row=4, column=2, padx=20, pady=10)

        # Start MQTT ultrasonic receipt thread
        if MQTT_active:
            mqtt_q = queue.Queue()
            ultrasonic_t = threading.Thread(target=handle_mqtt_data, args=(ser, mqtt_q, self.ultrasonic_x_lbl,  self.ultrasonic_y_lbl, self.ls_tracker, self.tracker_canvas, ))
            ultrasonic_t.start()
        
        # Start Webcam gesture detection thread
        if CAM_active:
            gesture_q = queue.Queue()
            gesture_t = threading.Thread(target=gd.process_video, args=(ser, gesture_q, self.raw_gesture_lbl, self.filtered_gesture_lbl, self.detected_hand_lbl, ))
            gesture_t.start()
        
        # Start THingy:52 button thread
        if BLE_active:
            button_t = threading.Thread(target=handle_uart_data, args=(ser, self.button_pushed_lbl, ))
            button_t.start()
    
    # Write user response into user_response.txt file for review
    def write_response(self):
        current_directory = os.getcwd()
        file_path = os.path.join(current_directory, 'user_response.txt')

        response = self.stars_entry.get()
        if not os.path.exists(file_path):
            open(file_path, 'w').close() 

        with open(file_path, 'a') as file:
            file.write(response + '\n')

        self.stars_entry.delete(0, tk.END)
    

    def configure_theme(self):
        self.master.configure(bg=DARK_GRAY)

        # Configure backgrounds and highlights
        self.master.option_add('*background', DARK_GRAY)
        self.master.option_add('*foreground', WHITE)
        self.master.option_add('*highlightBackground', DARK_GRAY)
        self.master.option_add('*highlightColor', DARK_GRAY)

        # Configure labels theme
        self.master.option_add('*Label.Background', DARK_GRAY)
        self.master.option_add('*Label.Foreground', WHITE)

        # Configure entry theme
        self.master.option_add('*Entry.Background', WHITE)
        self.master.option_add('*Entry.Foreground', DARK_GRAY)

        # Configure button theme
        self.master.option_add('*Button.Background', WHITE)
        self.master.option_add('*Button.Foreground', DARK_GRAY)
    


def main():
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()
    
    if BLE_active:
        ser.close()

if __name__ == "__main__":
    main()
