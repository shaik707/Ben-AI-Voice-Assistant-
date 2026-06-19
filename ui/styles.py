# ui/styles.py — JARVIS-Inspired Dark Theme
# Premium dark theme with cyan/green accents and glassmorphism effects

JARVIS_THEME = """
/* ================ GLOBAL ================ */
QWidget {
    background-color: #0a0e17;
    color: #e0e6f0;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

/* ================ MAIN WINDOW ================ */
QMainWindow {
    background-color: #0a0e17;
}

/* ================ SIDEBAR ================ */
#sidebar {
    background-color: #0d1117;
    border-right: 1px solid #1a2332;
    min-width: 72px;
    max-width: 72px;
}

#sidebar QPushButton {
    background-color: transparent;
    border: none;
    color: #6e7681;
    padding: 10px;
    font-size: 18px;
    border-radius: 8px;
    margin: 4px 6px;
    min-height: 40px;
}

#sidebar QPushButton:hover {
    background-color: rgba(0, 200, 255, 0.1);
    color: #00c8ff;
}

#sidebar QPushButton:checked,
#sidebar QPushButton[active="true"] {
    background-color: rgba(0, 200, 255, 0.15);
    color: #00c8ff;
    border-left: 3px solid #00c8ff;
}

/* ================ PANELS ================ */
.panel {
    background-color: #0d1117;
    border-radius: 12px;
    padding: 16px;
}

/* ================ HEADER ================ */
#header {
    background-color: #0d1117;
    border-bottom: 1px solid #1a2332;
    padding: 8px 16px;
    min-height: 50px;
}

#header QLabel {
    color: #00c8ff;
    font-size: 18px;
    font-weight: bold;
}

#statusLabel {
    color: #3fb950;
    font-size: 11px;
}

/* ================ CHAT PANEL ================ */
#chatDisplay {
    background-color: #0d1117;
    border: 1px solid #1a2332;
    border-radius: 12px;
    padding: 12px;
    color: #e0e6f0;
    font-size: 13px;
}

#chatInput {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 20px;
    padding: 10px 16px;
    color: #e0e6f0;
    font-size: 13px;
}

#chatInput:focus {
    border-color: #00c8ff;
}

#sendButton {
    background-color: #00c8ff;
    color: #0a0e17;
    border: none;
    border-radius: 20px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 13px;
}

#sendButton:hover {
    background-color: #33d6ff;
}

#sendButton:pressed {
    background-color: #0099cc;
}

/* ================ CARDS ================ */
.card {
    background-color: #161b22;
    border: 1px solid #1a2332;
    border-radius: 12px;
    padding: 16px;
}

.card:hover {
    border-color: #00c8ff;
}

/* ================ BUTTONS ================ */
QPushButton {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 16px;
    color: #e0e6f0;
    font-size: 13px;
}

QPushButton:hover {
    background-color: #1f2937;
    border-color: #00c8ff;
    color: #00c8ff;
}

QPushButton:pressed {
    background-color: #0d1117;
}

QPushButton#primaryBtn {
    background-color: #00c8ff;
    color: #0a0e17;
    border: none;
    font-weight: bold;
}

QPushButton#primaryBtn:hover {
    background-color: #33d6ff;
}

QPushButton#dangerBtn {
    background-color: #f85149;
    color: white;
    border: none;
}

/* ================ INPUT FIELDS ================ */
QLineEdit, QTextEdit, QPlainTextEdit {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e0e6f0;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
    border-color: #00c8ff;
}

/* ================ COMBOBOX ================ */
QComboBox {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
    padding: 8px;
    color: #e0e6f0;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #161b22;
    border: 1px solid #30363d;
    color: #e0e6f0;
    selection-background-color: rgba(0, 200, 255, 0.2);
}

/* ================ TABS ================ */
QTabWidget::pane {
    border: 1px solid #1a2332;
    border-radius: 8px;
    background-color: #0d1117;
}

QTabBar::tab {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-bottom: none;
    padding: 8px 16px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    color: #8b949e;
}

QTabBar::tab:selected {
    background-color: #0d1117;
    color: #00c8ff;
    border-color: #1a2332;
}

QTabBar::tab:hover {
    color: #e0e6f0;
}

/* ================ SCROLLBAR ================ */
QScrollBar:vertical {
    background-color: #0d1117;
    width: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background-color: #30363d;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background-color: #484f58;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background-color: #0d1117;
    height: 8px;
    margin: 0;
    border-radius: 4px;
}

QScrollBar::handle:horizontal {
    background-color: #30363d;
    border-radius: 4px;
    min-width: 30px;
}

/* ================ LIST WIDGET ================ */
QListWidget {
    background-color: #0d1117;
    border: 1px solid #1a2332;
    border-radius: 8px;
    padding: 4px;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    margin: 2px;
}

QListWidget::item:hover {
    background-color: rgba(0, 200, 255, 0.08);
}

QListWidget::item:selected {
    background-color: rgba(0, 200, 255, 0.15);
    color: #00c8ff;
}

/* ================ PROGRESS BAR ================ */
QProgressBar {
    background-color: #161b22;
    border: 1px solid #30363d;
    border-radius: 6px;
    text-align: center;
    color: #e0e6f0;
}

QProgressBar::chunk {
    background-color: #00c8ff;
    border-radius: 6px;
}

/* ================ GROUP BOX ================ */
QGroupBox {
    border: 1px solid #1a2332;
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 16px;
    color: #8b949e;
}

QGroupBox::title {
    color: #00c8ff;
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 8px;
}

/* ================ TOOLTIP ================ */
QToolTip {
    background-color: #161b22;
    border: 1px solid #30363d;
    color: #e0e6f0;
    padding: 6px;
    border-radius: 6px;
}

/* ================ LABELS ================ */
.heading {
    color: #00c8ff;
    font-size: 20px;
    font-weight: bold;
}

.subheading {
    color: #8b949e;
    font-size: 12px;
}

.accent {
    color: #3fb950;
}

.warning {
    color: #d29922;
}

.error {
    color: #f85149;
}

/* ================ MODE TOGGLE ================ */
#modeToggle {
    background-color: #161b22;
    border: 2px solid #00c8ff;
    border-radius: 14px;
    padding: 4px 12px;
    color: #00c8ff;
    font-weight: bold;
    font-size: 11px;
}

#modeToggle:checked {
    background-color: #00c8ff;
    color: #0a0e17;
}
"""

# Color constants for programmatic use
COLORS = {
    "bg_primary": "#0a0e17",
    "bg_secondary": "#0d1117",
    "bg_tertiary": "#161b22",
    "border": "#1a2332",
    "border_light": "#30363d",
    "text_primary": "#e0e6f0",
    "text_secondary": "#8b949e",
    "text_muted": "#6e7681",
    "accent_cyan": "#00c8ff",
    "accent_green": "#3fb950",
    "accent_orange": "#d29922",
    "accent_red": "#f85149",
    "accent_purple": "#8957e5",
}
