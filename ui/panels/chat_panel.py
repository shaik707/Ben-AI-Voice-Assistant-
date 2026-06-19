# ui/panels/chat_panel.py — Chat Interface Panel

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, pyqtSignal
import datetime


class ChatPanel(QWidget):
    message_sent = pyqtSignal(str)

    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QLabel("💬 Chat with BENN AI")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Chat display
        self.chat_display = QTextEdit()
        self.chat_display.setObjectName("chatDisplay")
        self.chat_display.setReadOnly(True)
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #1a2332;
                border-radius: 12px;
                padding: 12px;
                color: #e0e6f0;
                font-size: 13px;
                line-height: 1.6;
            }
        """)
        layout.addWidget(self.chat_display, 1)

        # Input area
        input_layout = QHBoxLayout()
        input_layout.setSpacing(8)

        self.chat_input = QLineEdit()
        self.chat_input.setObjectName("chatInput")
        self.chat_input.setPlaceholderText("Type a message... (or use voice mode)")
        self.chat_input.setMinimumHeight(42)
        self.chat_input.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.chat_input, 1)

        self.send_btn = QPushButton("Send")
        self.send_btn.setObjectName("sendButton")
        self.send_btn.setMinimumHeight(42)
        self.send_btn.setMinimumWidth(80)
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        # Welcome message
        self.add_message("BENN AI",
            "Hey! I'm BENN AI, your intelligent assistant. "
            "Type a command or question, or switch to voice mode. What can I help you with?")

    def _send_message(self):
        text = self.chat_input.text().strip()
        if not text:
            return

        self.add_message("You", text, is_user=True)
        self.chat_input.clear()

        # Process through engine
        if self.engine:
            import threading
            def process():
                try:
                    self.engine.process_command(text)
                except Exception as e:
                    self.add_message("BENN AI", f"Error: {str(e)}")
            threading.Thread(target=process, daemon=True).start()
        else:
            self.add_message("BENN AI", "Engine not connected. Please restart the application.")

    def add_message(self, sender, text, is_user=False):
        """Add a message to the chat display."""
        timestamp = datetime.datetime.now().strftime("%I:%M %p")

        if is_user:
            color = "#00c8ff"
            bg = "rgba(0, 200, 255, 0.08)"
            align = "right"
        else:
            color = "#3fb950"
            bg = "rgba(63, 185, 80, 0.08)"
            align = "left"

        html = f"""
        <div style="text-align: {align}; margin: 6px 0;">
            <div style="display: inline-block; background-color: {bg};
                        padding: 8px 14px; border-radius: 12px; max-width: 75%;">
                <span style="color: {color}; font-size: 11px; font-weight: bold;">
                    {sender}
                </span>
                <span style="color: #6e7681; font-size: 10px;"> {timestamp}</span>
                <br/>
                <span style="color: #e0e6f0; font-size: 13px;">
                    {text}
                </span>
            </div>
        </div>
        """
        self.chat_display.append(html)

        # Auto-scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
