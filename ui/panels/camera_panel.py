# ui/panels/camera_panel.py — Camera & Object Detection Panel

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QImage


class CameraPanel(QWidget):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self.camera_active = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("📷 Camera & Object Detection")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Camera view
        self.camera_label = QLabel("Camera Off")
        self.camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.camera_label.setMinimumSize(640, 480)
        self.camera_label.setStyleSheet("""
            QLabel {
                background-color: #0d1117;
                border: 2px solid #1a2332;
                border-radius: 12px;
                color: #6e7681;
                font-size: 20px;
            }
        """)
        layout.addWidget(self.camera_label, 1)

        # Detection info
        self.detection_label = QLabel("No objects detected")
        self.detection_label.setStyleSheet("color: #3fb950; font-size: 13px; padding: 4px;")
        layout.addWidget(self.detection_label)

        # Controls
        controls = QHBoxLayout()

        self.toggle_btn = QPushButton("▶️ Start Camera")
        self.toggle_btn.setObjectName("primaryBtn")
        self.toggle_btn.setMinimumHeight(40)
        self.toggle_btn.clicked.connect(self._toggle_camera)
        controls.addWidget(self.toggle_btn)

        self.selfie_btn = QPushButton("📸 Take Selfie")
        self.selfie_btn.setMinimumHeight(40)
        self.selfie_btn.clicked.connect(self._take_selfie)
        controls.addWidget(self.selfie_btn)

        self.screenshot_btn = QPushButton("🖥️ Screenshot")
        self.screenshot_btn.setMinimumHeight(40)
        self.screenshot_btn.clicked.connect(self._take_screenshot)
        controls.addWidget(self.screenshot_btn)

        layout.addLayout(controls)

    def _toggle_camera(self):
        if self.engine:
            if not self.camera_active:
                self.engine.start_vision()
                self.camera_active = True
                self.toggle_btn.setText("⏹️ Stop Camera")
                self.camera_label.setStyleSheet("""
                    QLabel {
                        background-color: #0d1117;
                        border: 2px solid #3fb950;
                        border-radius: 12px;
                    }
                """)
            else:
                self.engine.stop_vision()
                self.camera_active = False
                self.toggle_btn.setText("▶️ Start Camera")
                self.camera_label.setText("Camera Off")
                self.camera_label.setStyleSheet("""
                    QLabel {
                        background-color: #0d1117;
                        border: 2px solid #1a2332;
                        border-radius: 12px;
                        color: #6e7681;
                        font-size: 20px;
                    }
                """)

    def _take_selfie(self):
        if self.engine:
            from system import take_selfie
            result = take_selfie()
            self.detection_label.setText(result)

    def _take_screenshot(self):
        if self.engine:
            from system import take_screenshot
            result = take_screenshot()
            self.detection_label.setText(result)

    def update_frame(self, qimage):
        """Update camera frame display."""
        if isinstance(qimage, QImage):
            pixmap = QPixmap.fromImage(qimage)
            scaled = pixmap.scaled(
                self.camera_label.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.camera_label.setPixmap(scaled)

    def update_detections(self, detections):
        """Update detected objects display."""
        if detections:
            self.detection_label.setText(f"Detected: {', '.join(detections)}")
        else:
            self.detection_label.setText("No objects detected")

    def cleanup(self):
        if self.camera_active and self.engine:
            self.engine.stop_vision()
