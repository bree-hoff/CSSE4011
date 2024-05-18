'''
Detecting hands!!!! And gestures!!!
'''
import cv2
import mediapipe as mp
from fastai.data.all import *
from fastai.vision.all import *
import cv2
from collections import defaultdict
import serial as sl
from minecraftmessage_pb2 import MinecraftMessage, MessageType, GestureType

mp_hands = mp.solutions.hands.Hands()


types = ['call', 'dislike','fist','four','like','mute','ok','one','palm','peace', 'peace_inverted', 'rock', 'stop', 'stop_inverted', 'three', 'three2', 'two_up', 'two_up_inverted', 'relaxed']

class RecentGestures:
    def __init__(self):
        self.gestures = []
        self.gesture_counts = defaultdict(int)

    def add_gesture(self, new_gesture):
        if len(self.gestures) >= 10:
            eleventh_gesture = self.gestures.pop(0)
            self.gesture_counts[eleventh_gesture] -= 1
            if self.gesture_counts[eleventh_gesture] == 0:
                del self.gesture_counts[eleventh_gesture]
        self.gestures.append(new_gesture)
        self.gesture_counts[new_gesture] += 1

    def most_common_gesture(self):
        if not self.gestures:
            return None
        return max(self.gesture_counts, key=self.gesture_counts.get)
    
    

'''
Predict the gesture from the frame containing a hand that is passed in.
'''
def get_prediction(frame, learn):
    im_type,what,probs = learn.predict(frame)
    print(im_type)
    print(probs)
    print(what)
    return im_type


'''
Get bounding box of hand
'''
def find_hand(frame, learn):
    
    # Detect hands in frame
    processed_frame = mp_hands.process(frame)
    hands_detected = processed_frame.multi_hand_landmarks
    if hands_detected:
        for hand in hands_detected:
            frame_cpy = frame
            
            # Get min and max values for hand location
            x_min = min(landmark.x for landmark in hand.landmark) #* frame.shape[1]
            y_min = min(landmark.y for landmark in hand.landmark) #* frame.shape[1]
            x_max = max(landmark.x for landmark in hand.landmark) #* frame.shape[0]
            y_max = max(landmark.y for landmark in hand.landmark) #* frame.shape[0]
            
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
    

'''
Process video frame by frame to detect gesture
'''
def process_video(ser, gesture_q, gesture_label, filtered_label, detected_label):
    gesture_tracker = RecentGestures()
    cap = cv2.VideoCapture(0)
    path_to_export = '/Users/brianna/Documents/2024/Semester 1/CSSE4011/Project/project_repo/CSSE4011/pc/different_export.pkl'
    learn = load_learner(path_to_export, cpu=False)
    detection_type = None
    while True: 
        ret,img=cap.read()
        detection_type = find_hand(img, learn)
        if detection_type is not None:
            gesture_tracker.add_gesture(detection_type)
            #print(detection_type)
            gesture_label.configure(text = "Detected Gesture: " + detection_type) #detection_type
            top_gesture = gesture_tracker.most_common_gesture()
            filtered_label.configure(text = "Filtered Gesture: " + top_gesture) #detection_type
            detected_label.configure(text = "Detected Hand: True")
            movement_type = gesture_to_movement_map.get(top_gesture, GestureType.NO_GESTURE)
            sl.serial_send(ser, MessageType.GESTURE, gesture_type, 0, 0)
            # gesture_q.put(detection_type)
            detection_type = None
        else:
            detected_label.configure(text = "Detected Hand: False")
    
    # print("send this detection_type variable to dashboard")
    # cv2.imshow('Video', img)
    # if(cv2.waitKey(10) & 0xFF == ord('b')):
    #     break
    
