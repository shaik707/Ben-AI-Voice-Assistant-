# ui/panels/home_panel.py — Omnitrix Watch Home Panel
# Default view showing the iconic Omnitrix watch display with BENN AI branding

import os
import math
import datetime
import platform
import psutil

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, QRectF, QPointF
from PyQt6.QtGui import (
    QPainter, QColor, QRadialGradient, QLinearGradient,
    QFont, QPen, QBrush, QConicalGradient, QPainterPath, QPixmap
)


class OmnitrixWidget(QWidget):
    """Custom widget that draws the Omnitrix watch face."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(350, 350)
        self.setMaximumSize(500, 500)
        self.pulse_angle = 0
        self.glow_intensity = 0.5
        self.glow_direction = 1
        self.status_text = "ONLINE"
        self.mode_text = "VOICE MODE"

        # Animation timer
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._animate)
        self.anim_timer.start(50)

    def _animate(self):
        self.pulse_angle = (self.pulse_angle + 2) % 360
        self.glow_intensity += 0.02 * self.glow_direction
        if self.glow_intensity >= 1.0:
            self.glow_direction = -1
        elif self.glow_intensity <= 0.3:
            self.glow_direction = 1
        self.update()

    def set_status(self, text):
        self.status_text = text
        self.update()

    def set_mode(self, text):
        self.mode_text = text
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx, cy = w / 2, h / 2
        radius = min(w, h) / 2 - 20

        # === Outer glow ===
        glow_color = QColor(0, 200, 255, int(40 * self.glow_intensity))
        for i in range(3):
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 200, 255, int(15 * self.glow_intensity))))
            painter.drawEllipse(QPointF(cx, cy), radius + 20 - i * 5, radius + 20 - i * 5)

        # === Outer ring ===
        gradient = QConicalGradient(cx, cy, self.pulse_angle)
        gradient.setColorAt(0.0, QColor(0, 200, 255, 200))
        gradient.setColorAt(0.25, QColor(0, 150, 200, 100))
        gradient.setColorAt(0.5, QColor(0, 100, 150, 200))
        gradient.setColorAt(0.75, QColor(0, 150, 200, 100))
        gradient.setColorAt(1.0, QColor(0, 200, 255, 200))

        pen = QPen(QBrush(gradient), 4)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(QPointF(cx, cy), radius, radius)

        # === Inner dark circle ===
        inner_radius = radius - 15
        bg_gradient = QRadialGradient(cx, cy, inner_radius)
        bg_gradient.setColorAt(0, QColor(15, 20, 30))
        bg_gradient.setColorAt(0.7, QColor(10, 15, 25))
        bg_gradient.setColorAt(1, QColor(5, 10, 20))

        painter.setPen(QPen(QColor(0, 200, 255, 80), 2))
        painter.setBrush(QBrush(bg_gradient))
        painter.drawEllipse(QPointF(cx, cy), inner_radius, inner_radius)

        # === Hourglass / Diamond shape (Omnitrix symbol) ===
        diamond_size = radius * 0.35
        path = QPainterPath()
        path.moveTo(cx, cy - diamond_size)          # Top
        path.lineTo(cx + diamond_size * 0.6, cy)    # Right
        path.lineTo(cx, cy + diamond_size)           # Bottom
        path.lineTo(cx - diamond_size * 0.6, cy)    # Left
        path.closeSubpath()

        diamond_gradient = QRadialGradient(cx, cy, diamond_size)
        diamond_gradient.setColorAt(0, QColor(0, 255, 200, int(180 * self.glow_intensity)))
        diamond_gradient.setColorAt(0.5, QColor(0, 200, 150, int(120 * self.glow_intensity)))
        diamond_gradient.setColorAt(1, QColor(0, 100, 80, int(60 * self.glow_intensity)))

        painter.setPen(QPen(QColor(0, 255, 200, 200), 2))
        painter.setBrush(QBrush(diamond_gradient))
        painter.drawPath(path)

        # === Horizontal line through diamond ===
        painter.setPen(QPen(QColor(0, 200, 255, 150), 2))
        painter.drawLine(
            QPointF(cx - diamond_size * 0.8, cy),
            QPointF(cx + diamond_size * 0.8, cy)
        )

        # === "BENN AI" text ===
        painter.setPen(QColor(0, 220, 255, 250))
        font = QFont("SF Pro Display", 14, QFont.Weight.Bold)
        if platform.system() != "Darwin":
            font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - 80, cy - diamond_size - 50, 160, 30),
            Qt.AlignmentFlag.AlignCenter, "BENN AI"
        )

        # === Status text below diamond ===
        painter.setPen(QColor(63, 185, 80, 220))
        font.setPointSize(10)
        font.setWeight(QFont.Weight.Normal)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - 80, cy + diamond_size + 15, 160, 25),
            Qt.AlignmentFlag.AlignCenter, f"● {self.status_text}"
        )

        # === Mode text ===
        painter.setPen(QColor(0, 200, 255, 180))
        font.setPointSize(9)
        painter.setFont(font)
        painter.drawText(
            QRectF(cx - 80, cy + diamond_size + 38, 160, 20),
            Qt.AlignmentFlag.AlignCenter, self.mode_text
        )

        # === Tick marks around the ring ===
        painter.setPen(QPen(QColor(0, 200, 255, 100), 1))
        for i in range(60):
            angle = math.radians(i * 6)
            if i % 5 == 0:
                inner = radius - 12
                painter.setPen(QPen(QColor(0, 200, 255, 200), 2))
            else:
                inner = radius - 6
                painter.setPen(QPen(QColor(0, 200, 255, 60), 1))
            x1 = cx + inner * math.cos(angle)
            y1 = cy + inner * math.sin(angle)
            x2 = cx + (radius - 2) * math.cos(angle)
            y2 = cy + (radius - 2) * math.sin(angle)
            painter.drawLine(QPointF(x1, y1), QPointF(x2, y2))

        painter.end()


class HomePanel(QWidget):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self._build_ui()

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_stats)
        self.update_timer.start(2000)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 16, 20, 16)

        # === Top: Omnitrix Watch Center ===
        watch_container = QHBoxLayout()
        watch_container.addStretch()

        self.omnitrix = OmnitrixWidget()
        watch_container.addWidget(self.omnitrix)

        watch_container.addStretch()
        layout.addLayout(watch_container, 1)

        # === Bottom: Stats Cards ===
        cards_layout = QGridLayout()
        cards_layout.setSpacing(10)

        self.time_card = self._create_card("🕐", "Time", "--:--")
        self.date_card = self._create_card("📅", "Date", "---")
        self.cpu_card = self._create_card("💻", "CPU", "--%")
        self.ram_card = self._create_card("🧠", "RAM", "--%")
        self.os_card = self._create_card("⚙️", "System", platform.system())
        self.mode_card = self._create_card("🎤", "Mode", "Voice")

        cards_layout.addWidget(self.time_card, 0, 0)
        cards_layout.addWidget(self.date_card, 0, 1)
        cards_layout.addWidget(self.cpu_card, 0, 2)
        cards_layout.addWidget(self.ram_card, 1, 0)
        cards_layout.addWidget(self.os_card, 1, 1)
        cards_layout.addWidget(self.mode_card, 1, 2)

        layout.addLayout(cards_layout)

        # === Capabilities ===
        cap_label = QLabel(
            "✅ Voice & Chat  •  ✅ Web & YouTube  •  ✅ WhatsApp & Email  •  "
            "✅ Camera & Detection  •  ✅ System Control"
        )
        cap_label.setStyleSheet("color: #6e7681; font-size: 11px; padding: 4px;")
        cap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cap_label.setWordWrap(True)
        layout.addWidget(cap_label)

    def _create_card(self, icon, title, value):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border: 1px solid #1a2332;
                border-radius: 10px;
                padding: 10px;
            }
            QFrame:hover { border-color: #00c8ff; }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(2)
        layout.setContentsMargins(10, 8, 10, 8)

        header = QLabel(f"{icon} {title}")
        header.setStyleSheet("color: #8b949e; font-size: 10px;")
        layout.addWidget(header)

        value_label = QLabel(value)
        value_label.setObjectName(f"val_{title}")
        value_label.setStyleSheet("color: #e0e6f0; font-size: 16px; font-weight: bold;")
        layout.addWidget(value_label)

        return card

    def _update_stats(self):
        now = datetime.datetime.now()
        self._set_card_value("Time", now.strftime("%I:%M %p"))
        self._set_card_value("Date", now.strftime("%b %d, %Y"))
        try:
            self._set_card_value("CPU", f"{psutil.cpu_percent():.0f}%")
            self._set_card_value("RAM", f"{psutil.virtual_memory().percent:.0f}%")
        except Exception:
            pass

    def _set_card_value(self, title, value):
        for card in [self.time_card, self.date_card, self.cpu_card,
                     self.ram_card, self.os_card, self.mode_card]:
            val_label = card.findChild(QLabel, f"val_{title}")
            if val_label:
                val_label.setText(value)

    def set_mode(self, mode):
        self._set_card_value("Mode", mode)
        self.omnitrix.set_mode(f"{mode.upper()} MODE")
