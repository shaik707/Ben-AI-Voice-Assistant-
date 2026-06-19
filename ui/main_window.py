# ui/main_window.py — JARVIS-Style Main Window
# Premium dark theme with sidebar navigation and multi-panel layout

import sys
import os
import threading
import time

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QPushButton, QLabel, QApplication, QSizePolicy, QFrame
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QIcon, QPixmap

import os
from ui.styles import JARVIS_THEME, COLORS
from ui.panels.home_panel import HomePanel
from ui.panels.chat_panel import ChatPanel
from ui.panels.browser_panel import BrowserPanel
from ui.panels.youtube_panel import YouTubePanel
from ui.panels.files_panel import FilesPanel
from ui.panels.camera_panel import CameraPanel
from ui.panels.downloads_panel import DownloadsPanel
from ui.panels.communication_panel import CommunicationPanel
from ui.panels.terminal_panel import TerminalPanel


class AssistantThread(QThread):
    """Background thread for the AI engine."""
    response_signal = pyqtSignal(str)
    user_said_signal = pyqtSignal(str)
    camera_frame_signal = pyqtSignal(object)
    status_signal = pyqtSignal(str)

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def run(self):
        self.exec()

    def stop(self):
        if self.engine:
            self.engine.stop()
        self.quit()
        self.wait()


class MainWindow(QMainWindow):
    """JARVIS-style AI Assistant main window."""

    PANEL_ICONS = {
        "Home": "🏠",
        "Chat": "💬",
        "Browser": "🌐",
        "YouTube": "🎥",
        "Files": "📁",
        "Camera": "📷",
        "Downloads": "⬇️",
        "Comms": "📨",
        "Terminal": "⌨️",
    }

    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self.current_mode = "voice"  # "voice" or "chat"
        self.setWindowTitle("BENN AI — Intelligent Assistant")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Apply theme
        self.setStyleSheet(JARVIS_THEME)

        # Build UI
        self._build_ui()

        # Connect engine signals if available
        if self.engine:
            self._connect_engine()

        # Status timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_status)
        self.status_timer.start(1000)

    def _build_ui(self):
        """Build the main UI layout."""
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = self._build_sidebar()
        main_layout.addWidget(self.sidebar)

        # Content area (header + stacked panels)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Header
        self.header = self._build_header()
        content_layout.addWidget(self.header)

        # Stacked panels
        self.panel_stack = QStackedWidget()
        self.panel_stack.setContentsMargins(8, 8, 8, 8)

        # Create all panels
        self.panels = {}
        self.panels["Home"] = HomePanel(self.engine)
        self.panels["Chat"] = ChatPanel(self.engine)
        self.panels["Browser"] = BrowserPanel()
        self.panels["YouTube"] = YouTubePanel()
        self.panels["Files"] = FilesPanel()
        self.panels["Camera"] = CameraPanel(self.engine)
        self.panels["Downloads"] = DownloadsPanel()
        self.panels["Comms"] = CommunicationPanel(self.engine)
        self.panels["Terminal"] = TerminalPanel()

        for name, panel in self.panels.items():
            self.panel_stack.addWidget(panel)

        content_layout.addWidget(self.panel_stack)
        main_layout.addWidget(content_widget, 1)

        # Set default panel
        self._switch_panel("Home")

    def _build_sidebar(self):
        """Build the left sidebar with navigation icons."""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(72)
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        # Logo (Omnitrix icon)
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ominitrix.icns")
        logo_label = QLabel()
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio,
                                               Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(pixmap)
        else:
            logo_label.setText("🤖")
            logo_label.setStyleSheet("font-size: 24px; color: #00c8ff;")
        logo_label.setStyleSheet("padding: 10px;")
        layout.addWidget(logo_label)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background-color: #1a2332; margin: 4px 8px;")
        layout.addWidget(sep)

        # Navigation buttons
        self.nav_buttons = {}
        for name, icon in self.PANEL_ICONS.items():
            btn = QPushButton(icon)
            btn.setToolTip(name)
            btn.setCheckable(True)
            btn.setObjectName(f"nav_{name}")
            btn.setFixedSize(52, 48)
            btn.clicked.connect(lambda checked, n=name: self._switch_panel(n))
            layout.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
            self.nav_buttons[name] = btn

        layout.addStretch()

        # Mode toggle at bottom
        self.mode_btn = QPushButton("🎤")
        self.mode_btn.setToolTip("Toggle Voice/Chat Mode")
        self.mode_btn.setObjectName("modeToggle")
        self.mode_btn.setCheckable(True)
        self.mode_btn.setFixedSize(52, 32)
        self.mode_btn.clicked.connect(self._toggle_mode)
        layout.addWidget(self.mode_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        return sidebar

    def _build_header(self):
        """Build the top header bar."""
        header = QFrame()
        header.setObjectName("header")
        header.setFixedHeight(56)
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 0, 16, 0)

        # Title
        self.header_title = QLabel("BENN AI")
        self.header_title.setStyleSheet("color: #00c8ff; font-size: 20px; font-weight: bold;")
        layout.addWidget(self.header_title)

        # Panel name
        self.panel_label = QLabel("Home")
        self.panel_label.setStyleSheet("color: #8b949e; font-size: 14px; margin-left: 12px;")
        layout.addWidget(self.panel_label)

        layout.addStretch()

        # Status
        self.status_label = QLabel("● System Online")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setStyleSheet("color: #3fb950; font-size: 11px;")
        layout.addWidget(self.status_label)

        # Mode indicator
        self.mode_label = QLabel("🎤 Voice Mode")
        self.mode_label.setStyleSheet("color: #00c8ff; font-size: 11px; margin-left: 12px;")
        layout.addWidget(self.mode_label)

        return header

    def _switch_panel(self, name):
        """Switch to a specific panel."""
        if name in self.panels:
            idx = list(self.panels.keys()).index(name)
            self.panel_stack.setCurrentIndex(idx)
            self.panel_label.setText(name if name != "Comms" else "Communication")

            # Update button states
            for btn_name, btn in self.nav_buttons.items():
                btn.setChecked(btn_name == name)
                btn.setProperty("active", "true" if btn_name == name else "false")
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def _toggle_mode(self):
        """Toggle between voice and chat mode."""
        if self.current_mode == "voice":
            self.current_mode = "chat"
            self.mode_label.setText("⌨️ Chat Mode")
            self.mode_btn.setText("⌨️")
            self.mode_btn.setToolTip("Switch to Voice Mode")
            if self.engine:
                self.engine.listening = False
        else:
            self.current_mode = "voice"
            self.mode_label.setText("🎤 Voice Mode")
            self.mode_btn.setText("🎤")
            self.mode_btn.setToolTip("Switch to Chat Mode")
            if self.engine:
                self.engine.listening = True

        # Update home panel Omnitrix
        if "Home" in self.panels:
            self.panels["Home"].set_mode("Voice" if self.current_mode == "voice" else "Chat")

    def switch_panel_by_name(self, name):
        """Switch panel by name string (for voice commands like 'open chat')."""
        name_map = {
            "home": "Home", "chat": "Chat", "browser": "Browser",
            "youtube": "YouTube", "files": "Files", "camera": "Camera",
            "downloads": "Downloads", "communication": "Comms",
            "comms": "Comms", "terminal": "Terminal",
            "whatsapp": "Comms", "email": "Comms",
        }
        panel = name_map.get(name.lower().strip())
        if panel:
            self._switch_panel(panel)
            return f"Opened {panel} panel."
        return f"Unknown panel: {name}"

    def _connect_engine(self):
        """Connect engine signals to UI."""
        if hasattr(self.engine, 'response_signal'):
            self.engine.response_signal.connect(self._on_response)
        if hasattr(self.engine, 'user_said_signal'):
            self.engine.user_said_signal.connect(self._on_user_said)
        if hasattr(self.engine, 'camera_frame_signal'):
            self.engine.camera_frame_signal.connect(self._on_camera_frame)
        if hasattr(self.engine, 'play_youtube_signal'):
            self.engine.play_youtube_signal.connect(self._on_play_youtube)

    def _on_response(self, text):
        """Handle engine response."""
        if "Chat" in self.panels:
            self.panels["Chat"].add_message("BENN AI", text)
        self.status_label.setText(f"● {text[:50]}...")

    def _on_play_youtube(self, query):
        """Handle YouTube query."""
        self._switch_panel("YouTube")
        # Ensure we search for the video on the panel
        if "YouTube" in self.panels:
            self.panels["YouTube"].search_and_play(query)

    def _on_user_said(self, text):
        """Handle user speech."""
        if "Chat" in self.panels:
            self.panels["Chat"].add_message("You", text, is_user=True)

    def _on_camera_frame(self, qimage):
        """Handle camera frame."""
        if "Camera" in self.panels:
            self.panels["Camera"].update_frame(qimage)

    def _update_status(self):
        """Update status bar periodically."""
        import datetime
        now = datetime.datetime.now().strftime("%I:%M %p")
        mode = "🎤 Voice" if self.current_mode == "voice" else "⌨️ Chat"
        self.status_label.setText(f"● Online | {now}")

    def closeEvent(self, event):
        """Clean shutdown."""
        if self.engine:
            try:
                self.engine.stop()
            except Exception:
                pass

        # Cleanup panels
        for panel in self.panels.values():
            if hasattr(panel, 'cleanup'):
                panel.cleanup()

        event.accept()
