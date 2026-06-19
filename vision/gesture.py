# gesture.py
import cv2
import mediapipe as mp
import numpy as np
import threading
import time
import queue
from collections import deque

class GestureControl(threading.Thread):
    def __init__(self, command_queue):
        super().__init__()
        self.command_queue = command_queue
        self.running = False
        self.daemon = True
        self.cap = None
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Gesture smoothing
        self.gesture_history = deque(maxlen=5)
        self.prev_gesture = None
        self.gesture_cooldown = 0.5
        self.last_gesture_time = 0

        # Swipe detection
        self.prev_landmarks = None
        self.swipe_threshold = 50
        self.swipe_cooldown = 1.0
        self.last_swipe_time = 0

    def run(self):
        self.running = True
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            print("Gesture: Could not open camera")
            return

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue

            frame = cv2.flip(frame, 1)
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb)

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)

                    h, w, _ = frame.shape
                    landmarks = [(int(lm.x * w), int(lm.y * h)) for lm in hand_landmarks.landmark]

                    gesture = self.detect_gesture(landmarks)
                    self.detect_swipe(landmarks)

                    if gesture:
                        self.gesture_history.append(gesture)
                        if len(self.gesture_history) == self.gesture_history.maxlen:
                            smoothed = max(set(self.gesture_history), key=self.gesture_history.count)
                            if smoothed != self.prev_gesture or (time.time() - self.last_gesture_time) > self.gesture_cooldown:
                                self.last_gesture_time = time.time()
                                self.prev_gesture = smoothed
                                self.command_queue.put(smoothed)
                                print(f"Gesture detected: {smoothed}")

            # Optional display – comment out if not needed
            #cv2.imshow("Gesture Control", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            time.sleep(0.03)

        self.cap.release()
        cv2.destroyAllWindows()

    def detect_gesture(self, landmarks):
        fingers = []
        # Thumb
        if landmarks[4][0] > landmarks[3][0]:
            fingers.append(1)
        else:
            fingers.append(0)

        # Other fingers
        for tip in [8, 12, 16, 20]:
            if landmarks[tip][1] < landmarks[tip-2][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        total = sum(fingers)

        if total == 0:
            return "fist"
        elif total == 5:
            return "open_hand"
        elif total == 2 and fingers[1] == 1 and fingers[2] == 1:
            return "peace"
        elif total == 1 and fingers[1] == 1:
            return "point"
        else:
            return None

    def detect_swipe(self, landmarks):
        wrist = np.array(landmarks[0])
        middle_mcp = np.array(landmarks[9])
        palm_center = (wrist + middle_mcp) / 2

        if self.prev_landmarks is not None:
            prev_center = (np.array(self.prev_landmarks[0]) + np.array(self.prev_landmarks[9])) / 2
            dx = palm_center[0] - prev_center[0]
            dy = palm_center[1] - prev_center[1]

            if (abs(dx) > self.swipe_threshold or abs(dy) > self.swipe_threshold) and \
               (time.time() - self.last_swipe_time) > self.swipe_cooldown:
                if abs(dx) > abs(dy):
                    if dx > 0:
                        self.command_queue.put("swipe_right")
                        print("Swipe right")
                    else:
                        self.command_queue.put("swipe_left")
                        print("Swipe left")
                else:
                    if dy > 0:
                        self.command_queue.put("swipe_down")
                        print("Swipe down")
                    else:
                        self.command_queue.put("swipe_up")
                        print("Swipe up")
                self.last_swipe_time = time.time()

        self.prev_landmarks = landmarks

    def stop(self):
        self.running = False