'''
Detecting hands!!!! And gestures!!!
'''
import cv2
import mediapipe as mp
from fastai.data.all import *
from fastai.vision.all import *
import cv2

'''
Predict the gesture from the frame containing a hand that is passed in.
'''
def get_prediction(frame):
    im_type,_,probs = learn.predict(frame)
    if im_type == "one":
        im_type = "um actually"
    return im_type


'''
Get bounding box of hand
'''
def find_hand(frame):
    
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
            
            # Show the square on video
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            detection_frame = frame_cpy[(y1):(y2), (x1):(x2)]
            detected_value = get_prediction(detection_frame)
            
            # Show the string on video
            vid_detection_str = f"This is a: {detected_value}"
            cv2.putText(frame, vid_detection_str, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2, cv2.LINE_AA) 
            return detected_value

    return None

mp_hands = mp.solutions.hands.Hands()
path_to_export = '/Users/brianna/Documents/2024/Semester 1/CSSE4011/Project/project_repo/CSSE4011/pc/trained_export.pkl'
learn = load_learner(path_to_export, cpu=False)
cap = cv2.VideoCapture(0)
    
'''
Process video frame by frame to detect gesture
'''
while True: 
    ret,img=cap.read()
    detection_type = find_hand(img)
    if detection_type:
        print("send this detection_type variable to dashboard")
    cv2.imshow('Video', img)
    if(cv2.waitKey(10) & 0xFF == ord('b')):
        break
    
    