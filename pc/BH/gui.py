import tkinter as tk
import paho.mqtt.client as mqtt
import time
import queue
import threading
import gesture_detection as gd
import serial_send as sl
import serial
from minecraftmessage_pb2 import MinecraftMessage, MessageType, GestureType

MQTT_active = 0
CAM_active = 1
BLE_active = 1
rx_msg = ""


last_send_time = 0

if BLE_active:
    ser = serial.Serial('/dev/tty.usbmodem0010502125801', 115200)

class CurrentPositions:
    def __init__(self):
        self.x_coord = 0
        self.y_coord = 0
        self.x_raw = 0
        self.y_raw = 0

    def add_x_coord(self, x_coord):
        self.x_coord = x_coord

    def add_y_coord(self, y_coord):
        self.y_coord = y_coord

    def add_x_raw(self, x_raw):
        self.x_raw = x_raw

    def add_y_raw(self, y_raw):
        self.y_raw = y_raw
    
    def get_raw(self):
        return (self.x_raw, self.y_raw)

    def get_coords(self):
        return (self.x_coord, self.y_coord)

def handle_uart_data(ser, pushed_label):
    while True:
        data = ser.readline() 
        print("Received:", data)
        if data == b'1\r\n':
            print("1")
            current_time = time.localtime()
            pushed_label.configure(text = "Last Button Press At Time: " + time.strftime("%H:%M:%S", current_time))
            

def on_message(client, userdata, message):
    """
    Message receipt from MQTT
    """
    try:
        rx_msg = message.payload.decode("utf-8")
        client.user_data_set(rx_msg)
    except:
        print("message receive error")


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subscribe on connect.
    """
    client.subscribe("tellusteal")
    
def handle_mqtt_data(ser, mqtt_q, x_label, y_label, tracker, canvas):
    global last_send_time
    current_positions = CurrentPositions()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.on_connect = on_connect
    client.on_message = on_message

    client.user_data_set([])
    ssid = "infrastructure"
    password = "jEizUMsPiTD8"
    client.username_pw_set(ssid, password)
    client.connect("csse4011-iot.zones.eait.uq.edu.au")

    client.loop_start()
    while True:
        
        if client.user_data_get() != [] and client.user_data_get() != "nil":
            data = client.user_data_get()
            mqtt_q.put(data)
            # print(data)
            client.user_data_set("nil")
            # # print(client.user_data_get())
            # data = self.client.user_data_get()
            data_list = data.split()
            prev_coords = current_positions.get_coords()
            if data_list[0] == "x":
                x_label.configure(text = "X: " + str(data_list[1]))
                current_positions.add_x_raw(float(data_list[1]))
                current_positions.add_x_coord(int(data_list[2]))
            else:
                y_label.configure(text = "Y: " + str(data_list[1]))
                current_positions.add_y_raw(float(data_list[1]))
                current_positions.add_y_coord(int(data_list[2]))
            
            
            match current_positions.get_coords(): # 18 , 50, 82
                case (0, 0): # good
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
            
            if coords != prev_coords and time.time() > last_send_time + 0.5:
                last_send_time = time.time()
                sl.serial_send(ser, MessageType.ULTRASONIC, GestureType.NO_GESTURE, coords[0], coords[1])
            old_coords = canvas.coords(tracker)
            old_loc_x = old_coords[0] + 5
            old_loc_y = old_coords[1] + 5
            canvas.move(tracker, (x - old_loc_x), (y - old_loc_y))
            
        time.sleep(0.05)

class GUI:
    def __init__(self, master):
        self.master = master
        master.title("MQTT Data Display")
        master.geometry("800x400")

        self.dark_theme()

        self.label_ultrasonic = tk.Label(master, text="Ultrasonic Sensor Data")
        self.label_ultrasonic.grid(row=0, column=0, padx=20, pady=10)
        self.label_ultrasonic_x = tk.Label(master, text="X: 0000")
        self.label_ultrasonic_x.grid(row=1, column=0, padx=20, pady=10)
        self.label_ultrasonic_y = tk.Label(master, text="Y: 0000")
        self.label_ultrasonic_y.grid(row=2, column=0, padx=20, pady=10)
        self.grid_frame = tk.Frame(master)
        self.grid_frame.grid(row=3, column=0, padx=20, pady=10)
        
        MEDIUM_GRAY = "#808080"
        LIGHT_GRAY = "#B3B3B3"
        LRG_TEXT_FONT = ("Arial", 16)
        MDM_TEXT_FONT = ("Arial", 12)
        SML_TEXT_FONT = ("Arial", 10)
        WHITE = "#FFFFFF"
        
        self.display_canvas = tk.Canvas(master, width=100, height=100, bg=MEDIUM_GRAY, highlightthickness=0)
        
        # Outline the grid in white
        self.display_canvas.create_rectangle(2, 2, 98, 98, outline=WHITE, width=2)


        # Divide the space into 64 smaller squares
        map_size = 96
        half_m_square_size = map_size / 3
        for i in range(0, 3):  # 8 squares per side
            for j in range(0, 3):  # 8 squares per side
                if (i + j) % 2 == 0: # Alternate shades
                    colour = LIGHT_GRAY
                else:
                    colour = MEDIUM_GRAY
                self.display_canvas.create_rectangle(i * half_m_square_size + 2, j * half_m_square_size + 2,
                                                (i + 1) * half_m_square_size + 2, (j + 1) * half_m_square_size + 2,
                                                fill=colour, outline="")
                
            # Create the tracking circles
        tracker_radius = 5
        tracker_centre = (50, 50)  # Some starting point on grid 17, 50, 82

        # Least squares tracker
        ls_x = tracker_centre[0]
        ls_y = tracker_centre[1]

        # Create circle trackers
        self.ls_tracker = self.display_canvas.create_oval(tracker_centre[0] - tracker_radius, tracker_centre[1] - tracker_radius,
                                                tracker_centre[0] + tracker_radius, tracker_centre[1] + tracker_radius,
                                                fill=WHITE, outline="")

        self.display_canvas.grid(row=3, column=0, padx=20, pady=10)


        self.label_button = tk.Label(master, text="Push Button Data")
        self.label_button.grid(row=0, column=1, padx=20, pady=10)
        self.label_button_pushed = tk.Label(master, text="Last Button Press At Time: 0000")
        self.label_button_pushed.grid(row=1, column=1, padx=20, pady=10)

        self.label_camera = tk.Label(master, text="Webcam Data")
        self.label_camera.grid(row=0, column=2, padx=20, pady=10)
        self.label_gesture = tk.Label(master, text="Detected Gesture: 0000")
        self.label_gesture.grid(row=1, column=2, padx=20, pady=10)
        self.label_filtered_gesture = tk.Label(master, text="Filtered Gesture: 0000")
        self.label_filtered_gesture.grid(row=2, column=2, padx=20, pady=10)
        self.label_detected = tk.Label(master, text="Detected Hand: 0000")
        self.label_detected.grid(row=3, column=2, padx=20, pady=10)
        if MQTT_active:
            mqtt_q = queue.Queue()
            ultrasonic_t = threading.Thread(target=handle_mqtt_data, args=(ser, mqtt_q, self.label_ultrasonic_x,  self.label_ultrasonic_y, self.ls_tracker, self.display_canvas, ))
            ultrasonic_t.start()
        
        if CAM_active:
            gesture_q = queue.Queue()
            gesture_t = threading.Thread(target=gd.process_video, args=(ser, gesture_q, self.label_gesture, self.label_filtered_gesture, self.label_detected, ))
            gesture_t.start()
            
        if BLE_active:
            button_t = threading.Thread(target=handle_uart_data, args=(ser, self.label_button_pushed, ))
            button_t.start()
        
        # self.handle_mqtt_data()

        # # MQTT setup
        # if MQTT_active:
        #     self.client = mqtt.Client()
        #     self.client.on_connect = self.on_connect
        #     self.client.on_message = self.on_message
        #     self.client.connect("mqtt_broker_address", 1883, 60)
        #     self.client.loop_start()

    def dark_theme(self):
        self.master.configure(bg='#212121')  # Dark Grey
        self.master.option_add('*background', '#212121')
        self.master.option_add('*foreground', 'white')
        self.master.option_add('*highlightBackground', '#212121')
        self.master.option_add('*highlightColor', '#212121')
        self.master.option_add('*font', 'TkDefaultFont')
        self.master.option_add('*Label.Font', 'TkDefaultFont')
        self.master.option_add('*Label.Background', '#212121')
        self.master.option_add('*Label.Foreground', 'white')
    


def main():
    root = tk.Tk()
    gui = GUI(root)
    root.mainloop()
    
    if BLE_active:
        ser.close()

if __name__ == "__main__":
    main()
