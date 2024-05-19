'''
Detecting hands!!!! And gestures!!!
'''
import cv2
import mediapipe as mp
from fastai.data.all import *
from fastai.vision.all import *
import serial_send as sl
from collections import defaultdict
from minecraftmessage_pb2 import MinecraftMessage, MessageType, GestureType
import time

mp_hands = mp.solutions.hands.Hands()
last_gesture = 'relaxed'

types = ['call', 'dislike','fist','four','like','mute','ok','one','palm','peace', 'peace_inverted', 'rock', 'stop', 'stop_inverted', 'three', 'three2', 'two_up', 'two_up_inverted', 'relaxed']

# Record 5 most recent gestures
class RecentGestures:
    def __init__(self):
        self.gestures = []
        self.gesture_counts = defaultdict(int)

    def add_gesture(self, new_gesture):
        # Maintain list legnth of 5
        if len(self.gestures) >= 5:
            # Remove 6th gesture to maintain list length of 5
            sixth_gesture = self.gestures.pop(0)

            # Remove count from dictionary
            self.gesture_counts[sixth_gesture] -= 1
            if self.gesture_counts[sixth_gesture] == 0:
                del self.gesture_counts[sixth_gesture]
        
        # Add most recent gesture to list
        self.gestures.append(new_gesture)
        # Increase count of most recent gesture in dictionary
        self.gesture_counts[new_gesture] += 1

    def most_common_gesture(self):
        if len(self.gestures) == 0:
            return None
        
        # Return key (i.e., gesture string) for most common gesture in last 5 recorded
        return max(self.gesture_counts, key=self.gesture_counts.get)
    
    


# Predict the gesture from the frame containing a hand that is passed in.
def get_prediction(frame, learn):
    im_type,what,probs = learn.predict(frame)
    return im_type



# Get bounding box of hand
def find_hand(frame, learn):
    
    # Detect hands in frame
    processed_frame = mp_hands.process(frame)
    hands_detected = processed_frame.multi_hand_landmarks
    if hands_detected:
        for hand in hands_detected:
            frame_cpy = frame
            
            # Get min and max values for hand location
            x_min = min(landmark.x for landmark in hand.landmark)
            y_min = min(landmark.y for landmark in hand.landmark)
            x_max = max(landmark.x for landmark in hand.landmark)
            y_max = max(landmark.y for landmark in hand.landmark)
            
            # Find the centre of the hand
            x_centre = int((x_min + x_max) * frame.shape[1] / 2 )
            y_centre = int((y_min + y_max) * frame.shape[0] / 2 )
            
            # Determine side length of square
            padding = 1.5
            side = int(max((x_max - x_min) * frame.shape[1], (y_max - y_min) * frame.shape[0]) * padding)

            # Calculate the coordinates of the top-left and bottom-right corners of the square
            x1 = x_centre - side // 2
            y1 = y_centre - side // 2
            x2 = x_centre + side // 2
            y2 = y_centre + side // 2
            
            # # Show the square on video
            # cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            detection_frame = frame_cpy[(y1):(y2), (x1):(x2)]
            detected_value = get_prediction(detection_frame, learn)
            
            # Show the string on video
            vid_detection_str = f"This is a: {detected_value}"
            
            # cv2.putText(frame, vid_detection_str, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA) 
            return detected_value

    return None

# Mapping from gesture string to nanopb description
gesture_to_movement_map = {
    "fist": GestureType.LEFT_CLICK, 
    "stop": GestureType.LOOK_LEFT,
    "stop_inverted": GestureType.LOOK_RIGHT,
    "one": GestureType.ONE,
    "peace": GestureType.TWO,
    "three": GestureType.THREE,
    "four": GestureType.FOUR,
    "palm": GestureType.FIVE,
    "rock": GestureType.JUMP,
    "like": GestureType.LOOK_UP,
    "dislike": GestureType.LOOK_DOWN,
}


# Process video frame by frame to detect gesture
def process_video(ser, gesture_q, gesture_label, filtered_label, detected_label):
    global last_gesture

    # Track 5 most recent gestures for filtering
    gesture_tracker = RecentGestures()
    cap = cv2.VideoCapture(1)

    # Retrieve and load from exported ML trained model
    path_to_export = '/Users/lewisluck/csse4011/project_shared/CSSE4011/pc/BH/different_export.pkl'
    learn = load_learner(path_to_export, cpu=False)
    detection_type = None
    count = 0
    while True: 
        # Read frame by frame
        ret,img=cap.read()
        current_time = time.time()

        # Get prediction for gesture
        detection_type = find_hand(img, learn)

        # Update GUI label if no gesture detected
        if detection_type is None:
            detected_label.configure(text = "Detected Hand: False")
            detection_type = "no_gesture"
        else:
            detected_label.configure(text = "Detected Hand: True")

        # Updaye GUI according to raw and filtered detection
        gesture_tracker.add_gesture(detection_type)
        gesture_label.configure(text = "Detected Gesture: " + detection_type) #detection_type
        top_gesture = gesture_tracker.most_common_gesture()
        filtered_label.configure(text = "Filtered Gesture: " + top_gesture) #detection_type

        movement_type = gesture_to_movement_map.get(top_gesture, GestureType.NO_GESTURE)
        
        # Send gesture over UART if change in filtered gesture
        if last_gesture != top_gesture:
            sl.serial_send(ser, MessageType.GESTURE, movement_type, 0, 0)
            last_gesture = top_gesture

        detection_type = None

    
