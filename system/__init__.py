# system/system_control.py — System-level controls
# Volume, brightness, power, app open/close, screenshots

import os
import subprocess
import platform
import datetime
import random
import pyautogui
import webbrowser
import cv2
import psutil

try:
    from screen_brightness_control import set_brightness, get_brightness
except ImportError:
    set_brightness = None
    get_brightness = None


def get_os():
    return platform.system()


# ==================== App Name Mapping ====================
APP_NAME_MAP = {
    "chrome": {"Windows": "chrome.exe", "Darwin": "Google Chrome", "Linux": "google-chrome"},
    "google chrome": {"Windows": "chrome.exe", "Darwin": "Google Chrome", "Linux": "google-chrome"},
    "firefox": {"Windows": "firefox.exe", "Darwin": "Firefox", "Linux": "firefox"},
    "safari": {"Windows": None, "Darwin": "Safari", "Linux": None},
    "edge": {"Windows": "msedge.exe", "Darwin": "Microsoft Edge", "Linux": "microsoft-edge"},
    "brave": {"Windows": "brave.exe", "Darwin": "Brave Browser", "Linux": "brave-browser"},
    "opera": {"Windows": "opera.exe", "Darwin": "Opera", "Linux": "opera"},
    "vscode": {"Windows": "Code.exe", "Darwin": "Visual Studio Code", "Linux": "code"},
    "visual studio code": {"Windows": "Code.exe", "Darwin": "Visual Studio Code", "Linux": "code"},
    "vs code": {"Windows": "Code.exe", "Darwin": "Visual Studio Code", "Linux": "code"},
    "code": {"Windows": "Code.exe", "Darwin": "Visual Studio Code", "Linux": "code"},
    "terminal": {"Windows": "cmd.exe", "Darwin": "Terminal", "Linux": "gnome-terminal"},
    "cmd": {"Windows": "cmd.exe", "Darwin": "Terminal", "Linux": "gnome-terminal"},
    "powershell": {"Windows": "powershell.exe", "Darwin": "Terminal", "Linux": "gnome-terminal"},
    "pycharm": {"Windows": "pycharm64.exe", "Darwin": "PyCharm", "Linux": "pycharm"},
    "whatsapp": {"Windows": "WhatsApp.exe", "Darwin": "WhatsApp", "Linux": "whatsapp"},
    "telegram": {"Windows": "Telegram.exe", "Darwin": "Telegram", "Linux": "telegram-desktop"},
    "discord": {"Windows": "Discord.exe", "Darwin": "Discord", "Linux": "discord"},
    "teams": {"Windows": "Teams.exe", "Darwin": "Microsoft Teams", "Linux": "teams"},
    "zoom": {"Windows": "Zoom.exe", "Darwin": "zoom.us", "Linux": "zoom"},
    "skype": {"Windows": "Skype.exe", "Darwin": "Skype", "Linux": "skype"},
    "spotify": {"Windows": "Spotify.exe", "Darwin": "Spotify", "Linux": "spotify"},
    "vlc": {"Windows": "vlc.exe", "Darwin": "VLC", "Linux": "vlc"},
    "itunes": {"Windows": "iTunes.exe", "Darwin": "Music", "Linux": None},
    "music": {"Windows": None, "Darwin": "Music", "Linux": None},
    "word": {"Windows": "WINWORD.EXE", "Darwin": "Microsoft Word", "Linux": "libreoffice --writer"},
    "excel": {"Windows": "EXCEL.EXE", "Darwin": "Microsoft Excel", "Linux": "libreoffice --calc"},
    "powerpoint": {"Windows": "POWERPNT.EXE", "Darwin": "Microsoft PowerPoint", "Linux": "libreoffice --impress"},
    "notepad": {"Windows": "notepad.exe", "Darwin": "TextEdit", "Linux": "gedit"},
    "notes": {"Windows": "notepad.exe", "Darwin": "Notes", "Linux": "gedit"},
    "calculator": {"Windows": "calc.exe", "Darwin": "Calculator", "Linux": "gnome-calculator"},
    "calc": {"Windows": "calc.exe", "Darwin": "Calculator", "Linux": "gnome-calculator"},
    "settings": {"Windows": "ms-settings:", "Darwin": "System Preferences", "Linux": "gnome-control-center"},
    "file manager": {"Windows": "explorer.exe", "Darwin": "Finder", "Linux": "nautilus"},
    "explorer": {"Windows": "explorer.exe", "Darwin": "Finder", "Linux": "nautilus"},
    "finder": {"Windows": "explorer.exe", "Darwin": "Finder", "Linux": "nautilus"},
    "task manager": {"Windows": "taskmgr.exe", "Darwin": "Activity Monitor", "Linux": "gnome-system-monitor"},
    "paint": {"Windows": "mspaint.exe", "Darwin": "Preview", "Linux": "gimp"},
    "photos": {"Windows": "ms-photos:", "Darwin": "Photos", "Linux": "eog"},
    "camera": {"Windows": "microsoft.windows.camera:", "Darwin": "FaceTime", "Linux": "cheese"},
    "store": {"Windows": "ms-windows-store:", "Darwin": "App Store", "Linux": None},
    "clock": {"Windows": "ms-clock:", "Darwin": "Clock", "Linux": "gnome-clocks"},
    "maps": {"Windows": "bingmaps:", "Darwin": "Maps", "Linux": None},
}


def _resolve_app_name(app_name, system=None):
    if system is None:
        system = get_os()
    key = app_name.lower().strip()
    if key in APP_NAME_MAP:
        resolved = APP_NAME_MAP[key].get(system)
        if resolved:
            return resolved
    return app_name


# ==================== Application Control ====================

def open_application(app_name):
    system = get_os()
    resolved_name = _resolve_app_name(app_name, system)
    try:
        if system == "Windows":
            if resolved_name.endswith(":"):
                os.system(f"start {resolved_name}")
            else:
                os.startfile(resolved_name)
        elif system == "Darwin":
            subprocess.Popen(["open", "-a", resolved_name])
        else:
            subprocess.Popen(resolved_name.split())
        return f"Opened {app_name}"
    except Exception as e:
        try:
            if system == "Windows":
                os.startfile(app_name)
            elif system == "Darwin":
                subprocess.Popen(["open", "-a", app_name])
            else:
                subprocess.Popen([app_name])
            return f"Opened {app_name}"
        except Exception:
            return f"Could not open {app_name}: {str(e)}"


def close_application(app_name):
    system = get_os()
    resolved_name = _resolve_app_name(app_name, system)
    try:
        if system == "Windows":
            proc = resolved_name if resolved_name.endswith(".exe") else f"{resolved_name}.exe"
            result = subprocess.run(["taskkill", "/f", "/im", proc], capture_output=True, text=True)
            if result.returncode != 0:
                subprocess.run(["taskkill", "/f", "/fi", f"WINDOWTITLE eq {app_name}*"],
                              capture_output=True, text=True)
            return f"Closed {app_name}"
        elif system == "Darwin":
            quit_result = subprocess.run(
                ["osascript", "-e", f'tell application "{resolved_name}" to quit'],
                capture_output=True, text=True, timeout=5
            )
            if quit_result.returncode != 0:
                subprocess.run(["pkill", "-f", resolved_name], capture_output=True, text=True)
            return f"Closed {app_name}"
        else:
            subprocess.run(["pkill", "-f", resolved_name], capture_output=True, text=True)
            return f"Closed {app_name}"
    except Exception as e:
        return f"Could not close {app_name}: {str(e)}"


# ==================== Volume Control ====================

def volume_up():
    try:
        system = get_os()
        if system == "Windows":
            pyautogui.press('volumeup', presses=2)
        elif system == "Darwin":
            os.system("osascript -e 'set volume output volume (output volume of (get volume settings) + 10)'")
        else:
            os.system("amixer set Master 5%+")
        return "Volume increased."
    except Exception as e:
        return f"Could not change volume: {str(e)}"


def volume_down():
    try:
        system = get_os()
        if system == "Windows":
            pyautogui.press('volumedown', presses=2)
        elif system == "Darwin":
            os.system("osascript -e 'set volume output volume (output volume of (get volume settings) - 10)'")
        else:
            os.system("amixer set Master 5%-")
        return "Volume decreased."
    except Exception as e:
        return f"Could not change volume: {str(e)}"


def volume_mute():
    try:
        system = get_os()
        if system == "Windows":
            pyautogui.press('volumemute')
        elif system == "Darwin":
            os.system("osascript -e 'set volume output volume 0'")
        else:
            os.system("amixer set Master mute")
        return "Volume muted."
    except Exception as e:
        return f"Could not mute: {str(e)}"


# ==================== Brightness Control ====================

def brightness_up():
    try:
        system = get_os()
        if system == "Windows" and set_brightness and get_brightness:
            current = get_brightness()
            if isinstance(current, list):
                current = current[0]
            new = min(100, current + 10)
            set_brightness(new)
            return f"Brightness increased to {new}%."
        elif system == "Darwin":
            os.system("brightness 1")
            return "Brightness set to maximum."
        else:
            os.system("xrandr --output eDP-1 --brightness 1.0")
            return "Brightness increased."
    except Exception as e:
        return f"Could not change brightness: {str(e)}"


def brightness_down():
    try:
        system = get_os()
        if system == "Windows" and set_brightness and get_brightness:
            current = get_brightness()
            if isinstance(current, list):
                current = current[0]
            new = max(0, current - 10)
            set_brightness(new)
            return f"Brightness decreased to {new}%."
        elif system == "Darwin":
            os.system("brightness 0.5")
            return "Brightness set to 50%."
        else:
            os.system("xrandr --output eDP-1 --brightness 0.5")
            return "Brightness decreased."
    except Exception as e:
        return f"Could not change brightness: {str(e)}"


# ==================== Power Management ====================

def shutdown_system():
    try:
        system = get_os()
        if system == "Windows":
            os.system("shutdown /s /t 5")
        elif system == "Darwin":
            os.system("sudo shutdown -h now")
        else:
            os.system("shutdown -h now")
        return "Shutting down in 5 seconds."
    except Exception as e:
        return f"Could not shutdown: {str(e)}"


def restart_system():
    try:
        system = get_os()
        if system == "Windows":
            os.system("shutdown /r /t 5")
        elif system == "Darwin":
            os.system("sudo shutdown -r now")
        else:
            os.system("reboot")
        return "Restarting in 5 seconds."
    except Exception as e:
        return f"Could not restart: {str(e)}"


def lock_screen():
    try:
        system = get_os()
        if system == "Windows":
            pyautogui.hotkey('win', 'l')
        elif system == "Darwin":
            os.system("pmset displaysleepnow")
        else:
            os.system("gnome-screensaver-command -l")
        return "Screen locked."
    except Exception as e:
        return f"Could not lock screen: {str(e)}"


# ==================== Screenshot & Selfie ====================

def take_screenshot(save_dir="screenshots"):
    try:
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(save_dir, f"screenshot_{timestamp}.png")
        pyautogui.screenshot(filename)
        return f"Screenshot saved as {filename}"
    except Exception as e:
        return f"Could not take screenshot: {str(e)}"


def take_selfie(save_dir="selfies"):
    try:
        os.makedirs(save_dir, exist_ok=True)
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "Could not open camera."
        ret, frame = cap.read()
        if ret:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(save_dir, f"selfie_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            cap.release()
            return f"Selfie saved as {filename}"
        else:
            cap.release()
            return "Failed to capture image."
    except Exception as e:
        return f"Error taking selfie: {str(e)}"


# ==================== Web Browsing ====================

def search_web(query):
    url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Searching for {query}"


def play_youtube(query):
    url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
    webbrowser.open(url)
    return f"Opening YouTube results for {query}"


def close_browser_tab():
    try:
        system = get_os()
        if system == "Darwin":
            pyautogui.hotkey('command', 'w')
        else:
            pyautogui.hotkey('ctrl', 'w')
        return "Closed current tab."
    except Exception as e:
        return f"Could not close tab: {str(e)}"


# ==================== System Info ====================

def get_system_info():
    try:
        uname = platform.uname()
        info = (f"System: {uname.system}\n"
                f"Node: {uname.node}\n"
                f"Release: {uname.release}\n"
                f"Version: {uname.version}\n"
                f"Machine: {uname.machine}\n"
                f"Processor: {uname.processor}")
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        info += f"\nCPU Usage: {cpu}%\nMemory: {mem.percent}% used"
        return info
    except Exception as e:
        return f"Could not get system info: {str(e)}"


# ==================== Time/Date/Jokes ====================

def get_time():
    return datetime.datetime.now().strftime("%I:%M %p")

def get_date():
    return datetime.datetime.now().strftime("%A, %B %d, %Y")

_jokes = [
    "Why don't scientists trust atoms? Because they make up everything!",
    "What do you call a fake noodle? An impasta!",
    "Why did the scarecrow win an award? Because he was outstanding in his field!",
    "How does a penguin build its house? Igloos it together!",
    "Why don't skeletons fight each other? They don't have the guts.",
    "Why did the developer go broke? Because he used up all his cache!",
    "What's a computer's favorite snack? Microchips!",
    "Why do Java developers wear glasses? Because they can't C#!",
]

def get_joke():
    return random.choice(_jokes)
