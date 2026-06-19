# main.py — BENN AI Entry Point
# Launches the JARVIS-style GUI with Omnitrix watch and AI engine

import sys
import os

# Ensure project root is in path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

os.chdir(PROJECT_ROOT)

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

# Initialize pygame mixer early
try:
    import pygame
    pygame.mixer.init()
except Exception:
    pass


def main():
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # Pre-emptively load QtWebEngineWidgets or Qt.AA_ShareOpenGLContexts before QApplication
    try:
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("BENN AI")
    app.setApplicationDisplayName("BENN AI — Intelligent Assistant")

    # Set app icon
    icon_path = os.path.join(PROJECT_ROOT, "ominitrix.icns")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"[Main] App icon loaded: {icon_path}")

    # Initialize engine
    print("[Main] Initializing BENN AI Engine...")
    engine = None
    try:
        from core.engine import BenTenison
        engine = BenTenison()
    except Exception as e:
        print(f"[Main] Engine init error: {e}")
        import traceback
        traceback.print_exc()

    # Create main window
    from ui.main_window import MainWindow
    window = MainWindow(engine)

    # Set window icon
    if os.path.exists(icon_path):
        window.setWindowIcon(QIcon(icon_path))

    # Connect engine signals to GUI
    if engine:
        def on_response(text):
            if "Chat" in window.panels:
                window.panels["Chat"].add_message("BENN AI", text)

        def on_user_said(text):
            if "Chat" in window.panels:
                window.panels["Chat"].add_message("You", text, is_user=True)

        def on_camera_frame(qimage):
            if "Camera" in window.panels:
                window.panels["Camera"].update_frame(qimage)

        def on_exit():
            app.quit()

        engine.response_signal.connect(on_response)
        engine.user_said_signal.connect(on_user_said)
        engine.camera_frame_signal.connect(on_camera_frame)
        engine.exit_signal.connect(on_exit)
        engine.open_panel_signal.connect(window.switch_panel_by_name)

        def play_theme():
            try:
                theme_path = os.path.join(PROJECT_ROOT, "assets", "theme.mp4")
                if os.path.exists(theme_path) and pygame.mixer.get_init():
                    pygame.mixer.music.load(theme_path)
                    pygame.mixer.music.play()
            except Exception as e:
                print(f"[Main] Theme error: {e}")

        engine.play_theme_signal.connect(play_theme)

    window.show()
    print("[Main] BENN AI is ready! Omnitrix activated.")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()