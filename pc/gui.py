import tkinter as tk
import paho.mqtt.client as mqtt
import time
import queue
import threading
import gesture_detection as gd
# import uart as ut

MQTT_active = 0
CAM_active = 1
BLE_active = 0
rx_msg = ""

def on_message(client, userdata, message):
    """
    Message receipt from MQTT
    """
    try:
        rx_msg = message.payload.decode("utf-8")
        client.user_data_set(rx_msg)
        print(rx_msg)
    except:
        print("message receive error")


def on_connect(client, userdata, flags, reason_code, properties):
    """
    Subscribe on connect.
    """
    client.subscribe("tellusteal")
    
def handle_mqtt_data(mqtt_q, x_label, y_label, tracker, canvas):
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
            if data_list[0] == "x":
                x_label.configure(text = "X: " + str(data_list[1]))
            else:
                y_label.configure(text = "Y: " + str(data_list[1]))
            
            match data_list[1]:
                case 1: 
                    x = 17
                    y = 50
                case 2: 
                    x = 50
                    y = 82
                case 3: 
                    x = 50
                    y = 50
                case 4: 
                    x = 50
                    y = 17
                case 5: 
                    x = 82
                    y = 50
                case default:
                    x = 50
                    y = 50
            
            old_coords = canvas.coords(tracker)
            old_loc_x = old_coords[0] + 5
            old_loc_y = old_coords[1] + 5
            canvas.move(tracker, (x - old_loc_x), (y - old_loc_y))
        time.sleep(0.05)

class GUI:
    def __init__(self, master):
        self.master = master
        master.title("MQTT Data Display")
        master.geometry("600x400")

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
        self.label_button_pushed = tk.Label(master, text="Pressed: 0000")
        self.label_button_pushed.grid(row=1, column=1, padx=20, pady=10)

        self.label_camera = tk.Label(master, text="Webcam Data")
        self.label_camera.grid(row=0, column=2, padx=20, pady=10)
        self.label_gesture = tk.Label(master, text="Detected Gesture: 0000")
        self.label_gesture.grid(row=1, column=2, padx=20, pady=10)
          
        # if MQTT_active:
        #     mqtt_q = queue.Queue()
        #     ultrasonic_t = threading.Thread(target=handle_mqtt_data, args=(mqtt_q, self.label_ultrasonic_x,  self.label_ultrasonic_y, self.ls_tracker, self.display_canvas, ))
        #     ultrasonic_t.start()
        
        if CAM_active:
            gesture_q = queue.Queue()
            gesture_t = threading.Thread(target=gd.process_video, args=(gesture_q, self.label_gesture, ))
            gesture_t.start()
            
        # if BLE_active:
        #     button_q = queue.Queue()
        #     button_t = threading.Thread(target=ut.process_uart, args=(button_q, self.label_button_pushed, ))
        #     button_t.start()
        
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

if __name__ == "__main__":
    main()
