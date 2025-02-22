import cv2
import mediapipe as mp
import speech_recognition as sr
import time
import threading
from controller import Robot, Motion, Keyboard

class Nao(Robot):
    def __init__(self):
        Robot.__init__(self)
        self.findAndEnableDevices()  # Setup necessary robot devices
        self.loadMotionFiles()  # Load motion files (even though we're not using them right now)

        # Initialize Mediapipe for pose tracking (no hand tracking needed)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        self.mp_draw = mp.solutions.drawing_utils
        self.cap = cv2.VideoCapture(0)

    def loadMotionFiles(self):
        # Load motions for future use (although we aren't using them right now)
        self.forwards = Motion('../../motions/Forwards50.motion')
        self.backwards = Motion('../../motions/Backwards.motion')
        self.sideStepLeft = Motion('../../motions/SideStepLeft.motion')
        self.sideStepRight = Motion('../../motions/SideStepRight.motion')
        self.turnLeft60 = Motion('../../motions/TurnLeft60.motion')
        self.turnRight60 = Motion('../../motions/TurnRight60.motion')
        self.taiChi = Motion('../../motions/TaiChi.motion')
        self.wipeForhead = Motion('../../motions/WipeForehead.motion')

    def findAndEnableDevices(self):
        self.timeStep = int(self.getBasicTimeStep()) 

        # Enable necessary devices (camera and keyboard for this task)
        self.cameraTop = self.getDevice("CameraTop")
        self.cameraTop.enable(4 * self.timeStep)
        self.keyboard = self.getKeyboard()
        self.keyboard.enable(10 * self.timeStep)

        # Enable motors for shoulder control
        self.RShoulderPitch = self.getDevice("RShoulderPitch")
        self.LShoulderPitch = self.getDevice("LShoulderPitch")
        self.RHipPitch = self.getDevice("RHipPitch")
        self.LHipPitch = self.getDevice("LHipPitch")
        self.RElbowRoll = self.getDevice("RElbowRoll")
        self.LElbowRoll = self.getDevice("LElbowRoll")
        self.RElbowYaw = self.getDevice("RElbowYaw")
        self.LElbowYaw = self.getDevice("LElbowYaw")
        self.RShoulderRoll = self.getDevice("RShoulderRoll")
        self.LShoulderRoll = self.getDevice("LShoulderRoll")
        self.RWristYaw = self.getDevice("RWristYaw")
        self.LWristYaw = self.getDevice("LWristYaw")
        # Phalanx (fingers)
        self.RPhalanx1 = self.getDevice("RPhalanx1")
        self.LPhalanx1 = self.getDevice("LPhalanx1")
        self.RPhalanx2 = self.getDevice("RPhalanx2")
        self.LPhalanx2 = self.getDevice("LPhalanx2")
        self.RPhalanx3 = self.getDevice("RPhalanx3")
        self.LPhalanx3 = self.getDevice("LPhalanx3")
        self.RPhalanx4 = self.getDevice("RPhalanx4")
        self.LPhalanx4 = self.getDevice("LPhalanx4")
        self.RPhalanx5 = self.getDevice("RPhalanx5")
        self.LPhalanx5 = self.getDevice("LPhalanx5")
        self.RPhalanx6 = self.getDevice("RPhalanx6")
        self.LPhalanx6 = self.getDevice("LPhalanx6")
        self.RPhalanx7 = self.getDevice("RPhalanx7")
        self.LPhalanx7 = self.getDevice("LPhalanx7")
        self.RPhalanx8 = self.getDevice("RPhalanx8")
        self.LPhalanx8 = self.getDevice("LPhalanx8")

        # Enable motors for head control
        self.HeadYaw = self.getDevice("HeadYaw")  # Horizontal head rotation
        self.HeadPitch = self.getDevice("HeadPitch")  # Vertical head rotation

    def setNeutralPositions(self):
        # Set the shoulders to their neutral (resting) position
        self.RShoulderPitch.setPosition(0)
        self.LShoulderPitch.setPosition(0)
        self.RElbowRoll.setPosition(0)
        self.LElbowRoll.setPosition(0)
        self.RElbowYaw.setPosition(0)
        self.LElbowYaw.setPosition(0)
        self.RShoulderRoll.setPosition(0)
        self.LShoulderRoll.setPosition(0)
        self.RWristYaw.setPosition(0)
        self.LWristYaw.setPosition(0)

        # Set head to neutral position
        self.HeadYaw.setPosition(0)
        self.HeadPitch.setPosition(0)

    def detectPoseGestures(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        frame = cv2.flip(frame, 1)  # Mirror the frame horizontally
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        result_pose = self.pose.process(frame_rgb)
        result_hands = self.hands.process(frame_rgb)

        # Process Pose Landmarks, hand and head
        self.processPoseLandmarks(result_pose)

        # Process Hand Landmarks if detected, сжимать разжимать
        if result_hands.multi_hand_landmarks:
            self.processHandLandmarks(result_hands)

        cv2.imshow('Pose Tracking', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            self.cap.release()
            cv2.destroyAllWindows()

    def processPoseLandmarks(self, result_pose):
        if result_pose.pose_landmarks:
            # Right shoulder, elbow, and wrist landmarks (for right arm control)
            right_shoulder = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_SHOULDER]
            right_elbow = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_ELBOW]
            right_wrist = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.RIGHT_WRIST]

            # Left shoulder, elbow, and wrist landmarks (for left arm control)
            left_shoulder = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_SHOULDER]
            left_elbow = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_ELBOW]
            left_wrist = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.LEFT_WRIST]

            nose = result_pose.pose_landmarks.landmark[self.mp_pose.PoseLandmark.NOSE]
            # Head movements
            self.updateHeadPosition(nose)

            # Control arm movements
            self.updateArmJoints(right_shoulder, right_elbow, right_wrist,
                                 self.LShoulderPitch, self.LElbowRoll, self.RElbowYaw,
                                 self.LShoulderRoll, self.RWristYaw)

            self.updateArmJoints(left_shoulder, left_elbow, left_wrist,
                                 self.RShoulderPitch, self.RElbowRoll, self.LElbowYaw,
                                 self.RShoulderRoll, self.LWristYaw)

    def processHandLandmarks(self, result_hands):
        # Process first hand (Right hand)
        if len(result_hands.multi_hand_landmarks) > 0:
            hand_landmarks = result_hands.multi_hand_landmarks[0]
            thumb = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
            pinky = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
            index = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            if wrist.x < 0.5:  # If the wrist is on the left side of the image (for flipped view, x < 0.5 means left hand)
                self.updateFingerPhalanxPositions(thumb, pinky, index, False)  # Left hand (is_right_hand = False)
            else:
                self.updateFingerPhalanxPositions(thumb, pinky, index, True)

        # Process second hand (Left hand)
        if len(result_hands.multi_hand_landmarks) > 1:
            hand_landmarks = result_hands.multi_hand_landmarks[1]
            thumb = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
            pinky = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
            index = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
            wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
            if wrist.x < 0.5:  # If the wrist is on the left side of the image (for flipped view, x < 0.5 means left hand)
                self.updateFingerPhalanxPositions(thumb, pinky, index, False)  # Left hand (is_right_hand = False)
            else:
                self.updateFingerPhalanxPositions(thumb, pinky, index, True)

    def updateHeadPosition(self, nose):
        # Head yaw (horizontal rotation)
        head_yaw_angle = (0.5 - nose.x) * 1.8  # Adjusted for 90-degree range mapping
        self.HeadYaw.setPosition(max(min(head_yaw_angle, 1.57), -1.57))  # Limit to -90 to +90 degrees

        # Head pitch (vertical rotation)
        head_pitch_angle = (0.5 - nose.y) * -1.8  # Adjusted for 90-degree range mapping
        self.HeadPitch.setPosition(max(min(head_pitch_angle, 1.57), -1.57))  # Limit to -90 to +90 degrees

    def updateArmJoints(self, shoulder, elbow, wrist, 
                        shoulder_pitch, elbow_roll, elbow_yaw, shoulder_roll, wrist_yaw):
        # Calculate angles for each joint based on the shoulder, elbow, and wrist positions

        # Shoulder pitch (arm up and down)
        shoulder_angle = (wrist.y - shoulder.y) * 3  # Scaling factor
        shoulder_pitch.setPosition(max(min(shoulder_angle, shoulder_pitch.getMaxPosition()), shoulder_pitch.getMinPosition()))

        # Elbow roll (elbow rotation)
        elbow_roll_angle = (elbow.x - wrist.x) * 3  # Scaling factor
        elbow_roll.setPosition(max(min(elbow_roll_angle, elbow_roll.getMaxPosition()), elbow_roll.getMinPosition()))

        # Shoulder roll (shoulder rotation)
        shoulder_roll_angle = (shoulder.x - wrist.x) * 3  # Scaling factor
        shoulder_roll.setPosition(max(min(shoulder_roll_angle, shoulder_roll.getMaxPosition()), shoulder_roll.getMinPosition()))


    def updateFingerPhalanxPositions(self, thumb, pinky, index, is_right_hand):
        thumb_position = 1 if (abs(thumb.x - pinky.x) > 0.1) else 0
        pinky_position = 1 if (abs(thumb.x - pinky.x) > 0.1) else 0
        index_position = 1 if (abs(thumb.x - pinky.x) > 0.1) else 0

        thumb_position = max(min(thumb_position, 1), 0)
        pinky_position = max(min(pinky_position, 1), 0)
        index_position = max(min(index_position, 1), 0)

        if is_right_hand:
            # Update right hand phalanx positions
            self.RPhalanx1.setPosition(thumb_position)
            self.RPhalanx2.setPosition(thumb_position)
            self.RPhalanx3.setPosition(thumb_position)
            self.RPhalanx4.setPosition(pinky_position)
            self.RPhalanx5.setPosition(pinky_position)
            self.RPhalanx6.setPosition(pinky_position)
            self.RPhalanx7.setPosition(index_position)
            self.RPhalanx8.setPosition(index_position)
        else:
            # Update left hand phalanx positions
            self.LPhalanx1.setPosition(thumb_position)
            self.LPhalanx2.setPosition(thumb_position)
            self.LPhalanx3.setPosition(thumb_position)
            self.LPhalanx4.setPosition(pinky_position)
            self.LPhalanx5.setPosition(pinky_position)
            self.LPhalanx6.setPosition(pinky_position)
            self.LPhalanx7.setPosition(index_position)
            self.LPhalanx8.setPosition(index_position)

    def run(self):
        while self.step(self.timeStep) != -1:
            self.detectPoseGestures()  # Continuously check for pose gestures
            key = self.keyboard.getKey()
            if key > 0:
                break

# Initialize robot
robot = Nao()
timestep = int(robot.getBasicTimeStep())
stop_event = threading.Event()
event_counter = 0

# Function to handle the recognized speech (runs asynchronously)
def callback(recognizer, audio):
    global event_counter
    try:
        # Use Google's Web Speech API to recognize speech
        text = recognizer.recognize_google(audio)
        print("You said:", text)

        # Check if keywords are in the recognized text
        if "dancing" in text.lower() or "dance" in text.lower():
            print("Detected 'dancing'. Perform movement!")
            threading.Thread(target=perform_dance).start()
            event_counter += 1

        elif "stop" in text.lower():
            print("Detected 'stop'. Stop movement!")    
            threading.Thread(target=perform_stop).start()
            event_counter += 1
            
        elif "turn left" in text.lower():
            threading.Thread(target=perform_turn_left).start()
            event_counter += 1
            
        elif "stand" in text.lower():
            threading.Thread(target=perform_stand).start()
            event_counter += 1
            
        elif "turn right" in text.lower():
            threading.Thread(target=perform_turn_right).start()
            event_counter += 1
            
        elif "forward" in text.lower():
            threading.Thread(target=perform_forward).start()
            event_counter += 1
            
        elif "backward" in text.lower():
            threading.Thread(target=perform_backward).start()
            event_counter += 1
            
        elif "left" in text.lower():
            threading.Thread(target=perform_left).start()
            event_counter += 1
        
        elif "right" in text.lower():
            threading.Thread(target=perform_right).start()
            event_counter += 1
        
        elif "wipe" in text.lower() or "forehead" in text.lower() or "exhaust" in text.lower():
            threading.Thread(target=perform_wipe).start()
            event_counter += 1
        
        elif "hello" in text.lower() or "wave" in text.lower():
            threading.Thread(target=perform_wave).start()
            event_counter += 1
            
    except sr.UnknownValueError:
        print("Sorry, could not understand the audio")
    except sr.RequestError as e:
        print(f"Could not request results from Google Speech Recognition service; {e}")



# Define the functions to perform 
def perform_dance():
    stop_event.set()  
    stop_event.clear()
    taiChi_motion = Motion('../../motions/TaiChi.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        taiChi_motion.play()
    
def perform_stop():
    stop_event.set()  
    robot.setNeutralPositions()
    stop_event.clear()  

def perform_stand():
    stop_event.set()
    stand = Motion('../../motions/StandUpFromFront.motion') 
    counter_stand = 0
    while(robot.step(robot.timeStep) != -1 and counter_stand != 110):
        stand.play()
        counter_stand += 1
    robot.setNeutralPositions()
    stop_event.clear()

def perform_turn_left():
    stop_event.set()
    stop_event.clear()
    turnLeft60 = Motion('../../motions/TurnLeft60.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        turnLeft60.play()

def perform_turn_right():
    stop_event.set()
    stop_event.clear()
    turnRight60 = Motion('../../motions/TurnRight60.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        turnRight60.play()

def perform_forward():
    stop_event.set()
    stop_event.clear()
    forwards = Motion('../../motions/Forwards.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        forwards.play()

def perform_backward():
    stop_event.set()
    stop_event.clear()
    backwards = Motion('../../motions/Backwards.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        backwards.play()

def perform_left():
    stop_event.set()
    stop_event.clear()
    sideStepLeft = Motion('../../motions/SideStepLeft.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        sideStepLeft.play()
        
def perform_right():
    stop_event.set()
    stop_event.clear()
    sideStepRight = Motion('../../motions/SideStepRight.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        sideStepRight.play()

def perform_wipe():
    stop_event.set()
    stop_event.clear()
    wipeForehead = Motion('../../motions/WipeForehead.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        wipeForehead.play()

def perform_wave():
    stop_event.set()
    stop_event.clear()
    handWave = Motion('../../motions/HandWave.motion')
    while robot.step(robot.timeStep) != -1 and not stop_event.is_set():
        handWave.play()
        
        
        
        
# Start the microphone and listen in the background
recognizer = sr.Recognizer()
mic = sr.Microphone()

with mic as source:
    recognizer.adjust_for_ambient_noise(source)

# Start listening for commands asynchronously
print("Listening for commands... (press Ctrl+C to stop)")
recognizer.listen_in_background(mic, callback)

while True:
    robot.run()  # Continuously check for pose gestures