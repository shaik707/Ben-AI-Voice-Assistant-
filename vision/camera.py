# vision.py
import cv2
import numpy as np
import threading
import time
import os
from collections import deque
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage

class VisionThread(QObject):
    frame_ready = pyqtSignal(object)
    object_detected = pyqtSignal(str)
    detections_ready = pyqtSignal(list)

    def __init__(self, detection_skip=2, smoothing_frames=5):
        super().__init__()
        self.running = False
        self.net = None
        self.classes = []
        self.output_layers = []
        self.detection_skip = detection_skip
        self.frame_count = 0
        self.smoothing_frames = smoothing_frames
        self.detection_history = deque(maxlen=smoothing_frames)
        self.load_model()

    def load_model(self):
        weights_file = "yolov3-tiny.weights"
        config_file = "yolov3-tiny.cfg"
        names_file = "coco.names"

        if not (os.path.exists(weights_file) and os.path.exists(config_file) and os.path.exists(names_file)):
            print("ERROR: Tiny YOLO files not found. Object detection disabled.")
            return

        try:
            self.net = cv2.dnn.readNet(weights_file, config_file)
            self.net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

            with open(names_file, "r") as f:
                self.classes = [line.strip() for line in f.readlines()]

            layer_names = self.net.getLayerNames()
            unconnected = self.net.getUnconnectedOutLayers()
            if isinstance(unconnected[0], list) or isinstance(unconnected[0], np.ndarray):
                self.output_layers = [layer_names[i[0] - 1] for i in unconnected]
            else:
                self.output_layers = [layer_names[i - 1] for i in unconnected]

            print(f"Tiny YOLO model loaded. {len(self.classes)} classes.")
        except Exception as e:
            print(f"Error loading Tiny YOLO model: {e}")

    def start(self):
        self.running = True
        threading.Thread(target=self.run, daemon=True).start()

    def stop(self):
        self.running = False

    def run(self):
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            print("Error: Could not open camera.")
            while self.running:
                self.detections_ready.emit([])
                time.sleep(1)
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(2)  # extra warm-up

        while self.running:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                self.detections_ready.emit([])
                time.sleep(0.1)
                continue

            self.frame_count += 1
            current_detections = set()

            if self.net is not None and self.frame_count % (self.detection_skip + 1) == 0:
                height, width = frame.shape[:2]
                blob = cv2.dnn.blobFromImage(frame, 1/255.0, (416, 416), swapRB=True, crop=False)
                self.net.setInput(blob)
                outputs = self.net.forward(self.output_layers)

                boxes = []
                confidences = []
                class_ids = []

                for output in outputs:
                    for detection in output:
                        scores = detection[5:]
                        class_id = np.argmax(scores)
                        confidence = scores[class_id]
                        if confidence > 0.15:  # even lower threshold
                            center_x = int(detection[0] * width)
                            center_y = int(detection[1] * height)
                            w = int(detection[2] * width)
                            h = int(detection[3] * height)
                            x = int(center_x - w / 2)
                            y = int(center_y - h / 2)
                            boxes.append([x, y, w, h])
                            confidences.append(float(confidence))
                            class_ids.append(class_id)

                indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.2, 0.4)
                for i in range(len(boxes)):
                    if i in indexes:
                        x, y, w, h = boxes[i]
                        label = str(self.classes[class_ids[i]])
                        current_detections.add(label)

                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
                        label_text = f"{label} {confidences[i]:.2f}"
                        (label_w, label_h), baseline = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
                        cv2.rectangle(frame, (x, y - label_h - 10), (x + label_w, y), (0, 255, 0), cv2.FILLED)
                        cv2.putText(frame, label_text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 2)
                        self.object_detected.emit(label)

                self.detection_history.append(current_detections)
                # Smooth: take objects appearing in at least 2 of the last smoothing_frames
                if len(self.detection_history) == self.smoothing_frames:
                    from collections import Counter
                    all_dets = []
                    for det_set in self.detection_history:
                        all_dets.extend(list(det_set))
                    counter = Counter(all_dets)
                    stable = [item for item, count in counter.items() if count >= 2]
                    self.detections_ready.emit(stable)
                    print(f"Stable detections: {stable}")
                else:
                    self.detections_ready.emit(list(current_detections))
            else:
                # On skipped frames, emit last known detections
                if self.detection_history:
                    self.detections_ready.emit(list(self.detection_history[-1]))
                else:
                    self.detections_ready.emit([])

            # Convert frame to QImage for GUI
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            self.frame_ready.emit(qt_image)

            time.sleep(0.03)

        cap.release()