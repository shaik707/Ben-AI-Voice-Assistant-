# ui/panels/youtube_panel.py — YouTube Player Panel

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSignal
import urllib.request
import re

class YouTubeSearchWorker(QThread):
    videoFound = pyqtSignal(str)

    def __init__(self, query):
        super().__init__()
        self.query = query

    def run(self):
        try:
            url = f"https://www.youtube.com/results?search_query={self.query.replace(' ', '+')}"
            html = urllib.request.urlopen(url, timeout=10).read().decode('utf-8')
            match = re.search(r'"videoId":"([a-zA-Z0-9_-]{11})"', html)
            if match:
                self.videoFound.emit(match.group(1))
            else:
                self.videoFound.emit("")
        except Exception as e:
            print(f"YouTube search error: {e}")
            self.videoFound.emit("")

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class YouTubePanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QLabel("🎥 YouTube Player")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search YouTube...")
        self.search_input.setMinimumHeight(40)
        self.search_input.returnPressed.connect(self._search)
        search_layout.addWidget(self.search_input, 1)

        self.search_btn = QPushButton("🔍 Search")
        self.search_btn.setObjectName("primaryBtn")
        self.search_btn.setMinimumHeight(40)
        self.search_btn.clicked.connect(self._search)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Player area
        if WEBENGINE_AVAILABLE:
            self.player = QWebEngineView()
            self.player.setUrl(QUrl("https://www.youtube.com"))
            self.player.setStyleSheet("border-radius: 12px;")
            layout.addWidget(self.player, 1)
        else:
            placeholder = QLabel(
                "⚠️ YouTube player requires PyQt6-WebEngine\n\n"
                "Install with: pip install PyQt6-WebEngine"
            )
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #d29922; font-size: 16px; padding: 40px;")
            layout.addWidget(placeholder, 1)

    def _search(self):
        query = self.search_input.text().strip()
        if not query:
            return
            
        self.search_btn.setText("⏳ Processing...")
        self.search_btn.setEnabled(False)
        
        self.worker = YouTubeSearchWorker(query)
        self.worker.videoFound.connect(self._on_video_found)
        self.worker.start()

    def _on_video_found(self, video_id):
        self.search_btn.setText("🔍 Search")
        self.search_btn.setEnabled(True)
        if WEBENGINE_AVAILABLE:
            if video_id:
                url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
                self.player.setUrl(QUrl(url))
            else:
                query = self.search_input.text().strip()
                url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
                self.player.setUrl(QUrl(url))

    def play_video(self, video_id):
        """Play a specific YouTube video by ID."""
        if WEBENGINE_AVAILABLE:
            url = f"https://www.youtube.com/embed/{video_id}?autoplay=1"
            self.player.setUrl(QUrl(url))

    def search_and_play(self, query):
        """Search YouTube for query."""
        self.search_input.setText(query)
        self._search()

    def cleanup(self):
        pass
