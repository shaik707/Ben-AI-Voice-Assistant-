# ui/panels/browser_panel.py — Embedded Web Browser Panel

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel
)
from PyQt6.QtCore import QUrl, Qt

try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    WEBENGINE_AVAILABLE = True
except ImportError:
    WEBENGINE_AVAILABLE = False


class BrowserPanel(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # Header
        header = QLabel("🌐 Web Browser")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Navigation bar
        nav_layout = QHBoxLayout()
        nav_layout.setSpacing(4)

        self.back_btn = QPushButton("◀")
        self.back_btn.setFixedSize(36, 36)
        self.back_btn.setToolTip("Back")
        nav_layout.addWidget(self.back_btn)

        self.forward_btn = QPushButton("▶")
        self.forward_btn.setFixedSize(36, 36)
        self.forward_btn.setToolTip("Forward")
        nav_layout.addWidget(self.forward_btn)

        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFixedSize(36, 36)
        self.refresh_btn.setToolTip("Refresh")
        nav_layout.addWidget(self.refresh_btn)

        self.home_btn = QPushButton("🏠")
        self.home_btn.setFixedSize(36, 36)
        self.home_btn.setToolTip("Home")
        nav_layout.addWidget(self.home_btn)

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Enter URL or search...")
        self.url_bar.setMinimumHeight(36)
        self.url_bar.returnPressed.connect(self._navigate)
        nav_layout.addWidget(self.url_bar, 1)

        self.go_btn = QPushButton("Go")
        self.go_btn.setObjectName("primaryBtn")
        self.go_btn.setFixedSize(50, 36)
        self.go_btn.clicked.connect(self._navigate)
        nav_layout.addWidget(self.go_btn)

        layout.addLayout(nav_layout)

        # Browser view
        if WEBENGINE_AVAILABLE:
            self.browser = QWebEngineView()
            self.browser.setUrl(QUrl("https://www.google.com"))
            self.browser.urlChanged.connect(self._url_changed)
            layout.addWidget(self.browser, 1)

            # Connect navigation buttons
            self.back_btn.clicked.connect(self.browser.back)
            self.forward_btn.clicked.connect(self.browser.forward)
            self.refresh_btn.clicked.connect(self.browser.reload)
            self.home_btn.clicked.connect(lambda: self.browser.setUrl(QUrl("https://www.google.com")))
        else:
            placeholder = QLabel(
                "⚠️ Web browser requires PyQt6-WebEngine\n\n"
                "Install with: pip install PyQt6-WebEngine"
            )
            placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setStyleSheet("color: #d29922; font-size: 16px; padding: 40px;")
            layout.addWidget(placeholder, 1)

    def _navigate(self):
        url = self.url_bar.text().strip()
        if not url:
            return
        if not url.startswith(("http://", "https://")):
            if "." in url:
                url = "https://" + url
            else:
                url = f"https://www.google.com/search?q={url.replace(' ', '+')}"
        if WEBENGINE_AVAILABLE:
            self.browser.setUrl(QUrl(url))

    def _url_changed(self, url):
        self.url_bar.setText(url.toString())

    def navigate_to(self, url):
        """Navigate to URL programmatically."""
        if WEBENGINE_AVAILABLE:
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
            self.browser.setUrl(QUrl(url))
            self.url_bar.setText(url)

    def cleanup(self):
        pass
