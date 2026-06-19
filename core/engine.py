# core/engine.py — BENN AI Core Engine (Refactored)
# Slim orchestrator that coordinates all modules

import subprocess
import threading
import time
import queue
import platform
import hashlib
import re
import json
import os
import traceback
from pathlib import Path
from PyQt6.QtCore import QObject, pyqtSignal

# Import from new modular structure
from brain.brain import ask_brain
from automation.automation_manager import AutomationManager
from memory.memory_manager import MemoryManager
from voice.tts import TTSEngine
from voice.stt import STTEngine
import system as sys_control
import files as file_ops

# Communication
try:
    from communication.whatsapp import WhatsAppHandler
    from communication.email_handler import EmailHandler
    COMM_AVAILABLE = True
except ImportError:
    COMM_AVAILABLE = False

# Vision
try:
    from vision.camera import VisionThread
    from vision.gesture import GestureControl
    VISION_AVAILABLE = True
except ImportError:
    VISION_AVAILABLE = False

# Pygame for sounds
try:
    import pygame
except ImportError:
    pygame = None

try:
    import pyautogui
except ImportError:
    pyautogui = None


class BenTenison(QObject):
    """BENN AI Core Engine — coordinates all modules."""

    response_signal = pyqtSignal(str)
    user_said_signal = pyqtSignal(str)
    transform_signal = pyqtSignal(str)
    camera_frame_signal = pyqtSignal(object)
    open_panel_signal = pyqtSignal(str)
    play_youtube_signal = pyqtSignal(str)
    play_theme_signal = pyqtSignal()
    exit_signal = pyqtSignal()

    def __init__(self):
        super().__init__()

        # ---------- Voice (TTS/STT) ----------
        self.tts = TTSEngine()
        self.stt = STTEngine()
        self.is_speaking = False
        self.running = True
        self.listening = True
        self.command_queue = queue.Queue()
        self.system = platform.system()

        # ---------- Knowledge & Training ----------
        self.knowledge_base = self._load_knowledge_base()
        self.training_data = self._load_training_data()

        # ---------- Vision ----------
        self.last_detections = []
        self.vision_thread = None

        # ---------- Memory ----------
        self.memory = MemoryManager()
        self.last_opened_app = None

        # ---------- Gesture Control ----------
        self.gesture_thread = None
        self.gesture_queue = queue.Queue()
        self.gesture_running = False

        # ---------- Communication ----------
        if COMM_AVAILABLE:
            self.whatsapp = WhatsAppHandler()
            email_config = self._load_email_config()
            self.email_handler = EmailHandler(email_config)
        else:
            self.whatsapp = None
            self.email_handler = None

        # ---------- Automation ----------
        self.automation_queue = queue.Queue()
        self.automation = AutomationManager(self.automation_queue)

        # ---------- Tools Registration ----------
        self.tools = self._register_tools()
        self.action_to_tool = self._build_action_map()

        # ---------- Command Cooldown ----------
        self.last_command_time = 0
        self.command_cooldown = 1.5

        # ---------- Start Threads ----------
        self.listen_thread = threading.Thread(target=self.listen_loop, daemon=True)
        self.listen_thread.start()
        self.process_thread = threading.Thread(target=self.process_loop, daemon=True)
        self.process_thread.start()

        self._play_sound("assets/sounds/startup.wav")
        self.speak("BENN AI activated!")

    def _play_sound(self, filepath):
        if pygame and os.path.exists(filepath):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                sound = pygame.mixer.Sound(filepath)
                sound.play()
            except Exception as e:
                print(f"[Engine] Could not play sound {filepath}: {e}")

    # ==================================================================
    # Loading
    # ==================================================================

    def _load_knowledge_base(self):
        knowledge = {}
        knowledge_path = Path("knowledge")
        if knowledge_path.exists():
            for file_path in knowledge_path.glob("*.txt"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        knowledge[file_path.stem] = f.read()
                except Exception as e:
                    print(f"Error loading knowledge file {file_path}: {e}")
        return knowledge

    def _load_training_data(self):
        for path in [Path("train.txt"), Path("training/train.txt")]:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        return f.read()
                except Exception as e:
                    print(f"Error loading training data: {e}")
        return ""

    def _load_email_config(self):
        config = {}
        try:
            from core.config import (EMAIL_ADDRESS, EMAIL_PASSWORD,
                                     SMTP_SERVER, SMTP_PORT, IMAP_SERVER, IMAP_PORT)
            if EMAIL_ADDRESS and "your_email" not in EMAIL_ADDRESS:
                config = {
                    "email": EMAIL_ADDRESS, "password": EMAIL_PASSWORD,
                    "smtp_server": SMTP_SERVER, "smtp_port": SMTP_PORT,
                    "imap_server": IMAP_SERVER, "imap_port": IMAP_PORT
                }
        except Exception:
            pass
        return config

    # ==================================================================
    # Action Map
    # ==================================================================

    def _build_action_map(self):
        return {
            "open_app": "open_application",
            "close_app": "close_application",
            "take_screenshot": "take_screenshot",
            "take_selfie": "take_selfie",
            "volume_up": "volume_up",
            "volume_down": "volume_down",
            "volume_mute": "volume_mute",
            "brightness_up": "brightness_up",
            "brightness_down": "brightness_down",
            "search_web": "search_web",
            "play_youtube": "play_youtube",
            "create_file": "create_file",
            "open_file": "open_file",
            "delete_file": "delete_file",
            "system_info": "get_system_info",
            "shutdown": "shutdown",
            "restart": "restart",
            "lock_screen": "lock_screen",
            "get_time": "get_time",
            "get_date": "get_date",
            "tell_joke": "tell_joke",
            "start_camera": "start_camera",
            "stop_camera": "stop_camera",
            "detect_objects": "detect_objects",
            "play_theme": "play_theme",
            "start_gesture_control": "start_gesture_control",
            "stop_gesture_control": "stop_gesture_control",
            "remember_fact": "remember_fact",
            "what_is_my": "recall_fact",
            "tell_me_about": "tell_me_about",
            "exit": "exit",
            "download_images": "download_images",
            "download_video": "download_video",
            "amazon_search": "amazon_search",
            "amazon_add_to_cart": "amazon_add_to_cart",
            "amazon_place_order": "amazon_place_order",
            "scrape_website": "scrape_website",
            "execute_shell": "execute_shell",
            "smart_create": "smart_create",
            "open_panel": "open_panel",
            # Communication actions
            "send_whatsapp": "send_whatsapp",
            "schedule_whatsapp": "schedule_whatsapp",
            "read_whatsapp": "read_whatsapp",
            "send_email": "send_email",
            "read_email": "read_email",
            "read_unread_email": "read_unread_email",
            "search_email": "search_email",
            "add_contact": "add_contact",
            "list_contacts": "list_contacts",
        }

    # ==================================================================
    # Tool Registration
    # ==================================================================

    def _register_tools(self):
        tools = {
            "execute_shell": {
                "func": self._tool_execute_shell,
                "args": {"command": "string"},
                "description": "Run any shell command."
            },
            "open_application": {
                "func": lambda app: sys_control.open_application(app_name=app),
                "args": {"app": "string"},
                "description": "Open an application by name."
            },
            "close_application": {
                "func": lambda app: sys_control.close_application(app_name=app),
                "args": {"app": "string"},
                "description": "Close an application by name."
            },
            "take_screenshot": {
                "func": sys_control.take_screenshot,
                "args": {},
                "description": "Take a screenshot."
            },
            "take_selfie": {
                "func": sys_control.take_selfie,
                "args": {},
                "description": "Take a selfie using camera."
            },
            "open_panel": {
                "func": self._tool_open_panel,
                "args": {"panel_name": "string"},
                "description": "Open a specific GUI panel (e.g. chat, browser, youtube, downloads)."
            },
            "volume_up": {"func": sys_control.volume_up, "args": {}, "description": "Increase volume."},
            "volume_down": {"func": sys_control.volume_down, "args": {}, "description": "Decrease volume."},
            "volume_mute": {"func": sys_control.volume_mute, "args": {}, "description": "Mute volume."},
            "brightness_up": {"func": sys_control.brightness_up, "args": {}, "description": "Increase brightness."},
            "brightness_down": {"func": sys_control.brightness_down, "args": {}, "description": "Decrease brightness."},
            "search_web": {
                "func": sys_control.search_web,
                "args": {"query": "string"},
                "description": "Search the web."
            },
            "play_youtube": {
                "func": self._tool_play_youtube,
                "args": {"query": "string"},
                "description": "Play YouTube video."
            },
            "create_file": {
                "func": file_ops.create_file,
                "args": {"filename": "string", "content": "string"},
                "description": "Create a file."
            },
            "open_file": {
                "func": file_ops.open_file,
                "args": {"filename": "string"},
                "description": "Open a file."
            },
            "delete_file": {
                "func": file_ops.delete_file,
                "args": {"filename": "string"},
                "description": "Delete a file."
            },
            "get_system_info": {"func": sys_control.get_system_info, "args": {}, "description": "Get system info."},
            "shutdown": {"func": sys_control.shutdown_system, "args": {}, "description": "Shut down computer."},
            "restart": {"func": sys_control.restart_system, "args": {}, "description": "Restart computer."},
            "lock_screen": {"func": sys_control.lock_screen, "args": {}, "description": "Lock screen."},
            "get_time": {"func": sys_control.get_time, "args": {}, "description": "Get current time."},
            "get_date": {"func": sys_control.get_date, "args": {}, "description": "Get current date."},
            "tell_joke": {"func": sys_control.get_joke, "args": {}, "description": "Tell a joke."},
            "start_camera": {"func": self.start_vision, "args": {}, "description": "Start camera."},
            "stop_camera": {"func": self.stop_vision, "args": {}, "description": "Stop camera."},
            "detect_objects": {"func": self._tool_detect_objects, "args": {}, "description": "Detect visible objects."},
            "play_theme": {"func": self._tool_play_theme, "args": {}, "description": "Play theme song."},
            "start_gesture_control": {"func": self.start_gesture_control, "args": {}, "description": "Start gesture control."},
            "stop_gesture_control": {"func": self.stop_gesture_control, "args": {}, "description": "Stop gesture control."},
            "remember_fact": {"func": self._tool_remember_fact, "args": {"fact": "string"}, "description": "Remember a fact."},
            "recall_fact": {"func": self._tool_recall_fact, "args": {"key": "string"}, "description": "Recall a fact."},
            "tell_me_about": {"func": self._tool_tell_me_about, "args": {"topic": "string"}, "description": "Tell about a topic."},
            "download_images": {"func": self._tool_download_images, "args": {"query": "string", "count": "integer"}, "description": "Download images."},
            "download_video": {"func": self._tool_download_video, "args": {"url": "string", "query": "string", "count": "integer"}, "description": "Download video from a URL, or download N videos matching a search query."},
            "amazon_search": {"func": self._tool_amazon_search, "args": {"product": "string"}, "description": "Search Amazon."},
            "amazon_add_to_cart": {"func": self._tool_amazon_add_to_cart, "args": {"asin": "string"}, "description": "Add to Amazon cart."},
            "amazon_place_order": {"func": self._tool_amazon_place_order, "args": {}, "description": "Place Amazon order."},
            "scrape_website": {"func": self._tool_scrape, "args": {"url": "string"}, "description": "Scrape a website."},
            "new_browser_tab": {"func": self._tool_new_tab, "args": {}, "description": "Open new browser tab."},
            "close_browser_tab": {"func": sys_control.close_browser_tab, "args": {}, "description": "Close browser tab."},
            "smart_create": {"func": self._tool_smart_create, "args": {"description": "string"}, "description": "Create file with AI content."},
            "toggle_voice": {"func": self._tool_toggle_voice, "args": {}, "description": "Toggle between offline and edge TTS voices."},
            "exit": {"func": self._tool_exit, "args": {}, "description": "Exit the program."},
        }

        # Communication tools
        if COMM_AVAILABLE:
            tools.update({
                "send_whatsapp": {
                    "func": self._tool_send_whatsapp,
                    "args": {"recipient": "string", "message": "string"},
                    "description": "Send a WhatsApp message."
                },
                "schedule_whatsapp": {
                    "func": self._tool_schedule_whatsapp,
                    "args": {"recipient": "string", "message": "string", "hour": "integer", "minute": "integer"},
                    "description": "Schedule a WhatsApp message."
                },
                "read_whatsapp": {
                    "func": self._tool_read_whatsapp,
                    "args": {"count": "integer"},
                    "description": "Read recent WhatsApp messages."
                },
                "send_email": {
                    "func": self._tool_send_email,
                    "args": {"to": "string", "subject": "string", "body": "string"},
                    "description": "Send an email."
                },
                "read_email": {
                    "func": self._tool_read_email,
                    "args": {"count": "integer"},
                    "description": "Read inbox emails."
                },
                "read_unread_email": {
                    "func": self._tool_read_unread_email,
                    "args": {"count": "integer"},
                    "description": "Read unread emails."
                },
                "search_email": {
                    "func": self._tool_search_email,
                    "args": {"query": "string"},
                    "description": "Search emails."
                },
                "add_contact": {
                    "func": self._tool_add_contact,
                    "args": {"name": "string", "phone": "string"},
                    "description": "Add a WhatsApp contact."
                },
                "list_contacts": {
                    "func": self._tool_list_contacts,
                    "args": {},
                    "description": "List WhatsApp contacts."
                },
            })

        return tools

    # ==================================================================
    # Tool Implementations
    # ==================================================================

    def _tool_execute_shell(self, command):
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=30)
            output = result.stdout + result.stderr
            return output.strip() if output.strip() else "Command executed."
        except Exception as e:
            return f"Shell error: {e}"

    def _tool_detect_objects(self):
        if self.vision_thread is None:
            self.start_vision()
            self.speak("Starting camera, give me a moment...")
        for _ in range(16):
            time.sleep(0.5)
            if self.last_detections:
                objects = list(set(self.last_detections))
                if objects:
                    return f"I can see: {', '.join(objects)}"
        return "Camera is running but I can't identify anything specific right now."

    def _tool_play_theme(self):
        self.play_theme_signal.emit()
        return "Playing theme song!"

    def _tool_remember_fact(self, fact):
        if " is " in fact:
            key, value = fact.split(" is ", 1)
            self.memory.remember_fact(key.strip(), value.strip())
            return f"Okay, I'll remember that {key.strip()} is {value.strip()}."
        else:
            key = f"note_{hashlib.md5(fact.encode()).hexdigest()[:8]}"
            self.memory.remember_fact(key, fact)
            return "I've stored that information."

    def _tool_recall_fact(self, key):
        value = self.memory.get_fact(key)
        if value:
            return f"{key} is {value}."
        for k, v in self.memory.get_all_facts().items():
            if key.lower() in k.lower() or key.lower() in v.lower():
                return f"I remember: {k} is {v}."
        return f"I don't know about {key}."

    def _tool_tell_me_about(self, topic):
        content = self.memory.get_knowledge(topic) or self.knowledge_base.get(topic)
        if content:
            preview = content[:500] + "..." if len(content) > 500 else content
            return f"Here's what I know about {topic}:\n{preview}"
        topics = list(self.knowledge_base.keys())
        if topics:
            return f"I have knowledge about: {', '.join(topics)}"
        return "No knowledge files found."

    # Automation
    def _tool_download_images(self, query, count=5):
        self.automation_queue.put({"action": "download_images", "query": query, "count": count})
        return f"Downloading {count} images of {query} in background."

    def _tool_download_video(self, url="", query="", count=1):
        if url:
            self.automation_queue.put({"action": "download_video", "url": url})
            return "Downloading video from URL in background."
        elif query:
            self.automation_queue.put({"action": "download_video", "query": query, "count": count})
            return f"Downloading {count} video(s) of {query} in background."
        return "Please provide a video URL or a search query."

    def _tool_amazon_search(self, product):
        self.automation_queue.put({"action": "amazon_search", "product": product})
        return f"Searching Amazon for {product}."

    def _tool_amazon_add_to_cart(self, asin):
        self.automation_queue.put({"action": "amazon_add_to_cart", "asin": asin})
        return f"Adding product {asin} to cart."

    def _tool_amazon_place_order(self):
        self.automation_queue.put({"action": "amazon_place_order"})
        return "Placing order with Cash on Delivery."

    def _tool_scrape(self, url, selector=None):
        if not url.startswith("http"):
            url = "https://" + url
        self.automation_queue.put({"action": "scrape", "url": url, "selector": selector})
        return f"Scraping {url} in background."

    def _tool_new_tab(self):
        if pyautogui:
            if platform.system() == "Darwin":
                pyautogui.hotkey('command', 't')
            else:
                pyautogui.hotkey('ctrl', 't')
        return "Opened a new tab."
        
    def _tool_open_panel(self, panel_name):
        self.open_panel_signal.emit(panel_name)
        return f"Opening {panel_name} panel."

    def _tool_play_youtube(self, query):
        self.play_youtube_signal.emit(query)
        return f"Now playing {query} on YouTube."

    # Communication tools
    def _tool_send_whatsapp(self, recipient, message):
        if self.whatsapp:
            return self.whatsapp.send_instant_message(recipient, message)
        return "WhatsApp not available."

    def _tool_schedule_whatsapp(self, recipient, message, hour, minute):
        if self.whatsapp:
            return self.whatsapp.schedule_message(recipient, message, hour, minute)
        return "WhatsApp not available."

    def _tool_read_whatsapp(self, count=10):
        if self.whatsapp:
            return self.whatsapp.get_message_log(count)
        return "WhatsApp not available."

    def _tool_send_email(self, to, subject, body, attachments=None):
        if self.email_handler:
            return self.email_handler.send_email(to, subject, body, attachments)
        return "Email not configured."

    def _tool_read_email(self, count=10):
        if self.email_handler:
            return self.email_handler.read_inbox(count)
        return "Email not configured."

    def _tool_read_unread_email(self, count=10):
        if self.email_handler:
            return self.email_handler.read_unread(count)
        return "Email not configured."

    def _tool_search_email(self, query):
        if self.email_handler:
            return self.email_handler.search_emails(query)
        return "Email not configured."

    def _tool_add_contact(self, name, phone=""):
        if self.whatsapp:
            return self.whatsapp.add_contact(name, phone)
        return "WhatsApp not available."

    def _tool_list_contacts(self):
        if self.whatsapp:
            return self.whatsapp.list_contacts()
        return "WhatsApp not available."

    def _tool_smart_create(self, description, filename=None):
        try:
            prompt = f"""Generate the COMPLETE code/content for: {description}

Rules:
- Output ONLY the raw code/content. No explanations, no markdown fences.
- Make it professional with modern design.
- Do NOT wrap in ```code blocks```. Just the raw content."""

            content = ask_brain(
                "You are a code generator. Output ONLY raw code, no explanations, no JSON.",
                prompt
            )
            if isinstance(content, str) and len(content) > 10:
                content = content.strip()
                if content.startswith('```'):
                    lines = content.split('\n')
                    if lines[-1].strip() == '```':
                        content = '\n'.join(lines[1:-1])
                    else:
                        content = '\n'.join(lines[1:])

                if not filename:
                    if '<html' in content.lower():
                        filename = 'index.html'
                    elif 'def ' in content or 'import ' in content:
                        filename = 'script.py'
                    else:
                        filename = 'output.txt'

                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                return f"Created {filename} with generated content!"
            return "I couldn't generate the content."
        except Exception as e:
            return f"Error creating file: {e}"

    def _tool_toggle_voice(self):
        return self.tts.toggle_voice()

    def _tool_exit(self):
        self.speak("BENN AI shutting down...")
        def delayed_stop():
            time.sleep(3)
            self.stop()
        threading.Thread(target=delayed_stop, daemon=True).start()
        return None

    # ==================================================================
    # Prompt Building
    # ==================================================================

    def get_context(self):
        return {
            "system": platform.system(),
            "platform": platform.platform(),
            "last_opened_app": self.last_opened_app,
            "camera_active": self.vision_thread is not None,
            "last_detections": self.last_detections[:5],
            "memory_facts": self.memory.get_all_facts(),
            "knowledge_topics": list(self.knowledge_base.keys()),
        }

    def get_tools_description(self):
        lines = []
        for name, tool in self.tools.items():
            args = tool["args"]
            if args:
                args_str = ', '.join([f"{k}: {v}" for k, v in args.items()])
                lines.append(f"- {name}({args_str}): {tool['description']}")
            else:
                lines.append(f"- {name}(): {tool['description']}")
        return "\n".join(lines)

    def build_system_prompt(self, context, tools_desc):
        knowledge_info = "\n".join([
            f"- {topic}: {content[:150]}..."
            for topic, content in self.knowledge_base.items()
        ]) if self.knowledge_base else "No knowledge files loaded."

        return f"""You are BENN AI — an intelligent personal AI assistant. Speak naturally, be helpful, energetic, and confident.

CRITICAL RULE: Keep all conversational text responses EXTREMELY short, concise, and straight to the point (1-2 sentences maximum) unless the user explicitly asks for a long explanation. Do NOT output lists or long paragraphs because your response will be spoken aloud to the user. Brevity is essential for a good user experience!

SYSTEM CONTEXT:
OS: {context['system']} | Platform: {context['platform']}
Camera active: {context.get('camera_active', False)}

AVAILABLE ACTIONS:
{tools_desc}

KNOWLEDGE TOPICS:
{knowledge_info}

TRAINING EXAMPLES:
{self.training_data[:1500] if self.training_data else 'No training data.'}

RESPONSE FORMAT RULES:
1. If the user wants an action, respond with ONLY a JSON object: {{"action": "<action_name>", "param1": "value1", ...}}
2. For multiple actions, respond with a JSON array: [{{"action": "...", ...}}, {{"action": "...", ...}}]
3. The "action" field must match one of: {', '.join(sorted(self.action_to_tool.keys()))}
4. If no action is needed (just chatting), respond with plain text.
5. NEVER mix JSON and plain text. Either return pure JSON OR pure text.
6. When asked to create full stack websites or big projects, ALWAYS implement them using Django, HTML, CSS, and JS.

EXAMPLES:
User: "open chrome" → {{"action": "open_app", "app": "chrome"}}
User: "send whatsapp to Alice saying hello" → {{"action": "send_whatsapp", "recipient": "Alice", "message": "hello"}}
User: "send email to test@gmail.com about meeting" → {{"action": "send_email", "to": "test@gmail.com", "subject": "Meeting", "body": "Let's schedule a meeting."}}
User: "read my emails" → {{"action": "read_email", "count": 10}}
User: "how are you" → "I'm doing great! Ready to help. What do you need?"
"""

    # ==================================================================
    # Command Parse & Execute
    # ==================================================================

    def parse_response(self, response):
        if isinstance(response, (dict, list)):
            return response
        if isinstance(response, str):
            response = response.strip()
            if response.startswith('[') or response.startswith('{'):
                try:
                    return json.loads(response)
                except json.JSONDecodeError:
                    pass
        return response

    def execute_action(self, action):
        if isinstance(action, str):
            self.speak(action)
            return

        if isinstance(action, list):
            for subaction in action:
                self.execute_action(subaction)
            return

        if isinstance(action, dict):
            if "action" in action:
                action_name = action["action"]
                tool_name = self.action_to_tool.get(action_name)

                if tool_name and tool_name in self.tools:
                    tool = self.tools[tool_name]
                    args = {k: v for k, v in action.items() if k != "action"}
                    try:
                        result = tool["func"](**args)
                        if result:
                            self.speak(str(result))
                    except TypeError as e:
                        print(f"[Engine] Arg mismatch for {tool_name}: {e}")
                        try:
                            result = tool["func"]()
                            if result:
                                self.speak(str(result))
                        except Exception as e2:
                            self.speak(f"Error executing {action_name}: {e2}")
                    except Exception as e:
                        self.speak(f"Error executing {action_name}: {e}")
                elif action_name in self.tools:
                    tool = self.tools[action_name]
                    args = {k: v for k, v in action.items() if k != "action"}
                    try:
                        result = tool["func"](**args)
                        if result:
                            self.speak(str(result))
                    except Exception as e:
                        self.speak(f"Error: {e}")
                else:
                    self.speak(f"Unknown action: {action_name}")
                return

            if "tool" in action:
                tool_name = action["tool"]
                args = action.get("args", {})
                mapped = self.action_to_tool.get(tool_name, tool_name)
                if mapped in self.tools:
                    tool = self.tools[mapped]
                    try:
                        result = tool["func"](**args)
                        if result:
                            self.speak(str(result))
                    except Exception as e:
                        self.speak(f"Error: {e}")
                return

        self.speak(str(action))

    # ==================================================================
    # Smart Local Command Matching
    # ==================================================================

    def smart_match_command(self, command):
        cmd = command.lower().strip()

        # EXIT
        if cmd in ("exit", "quit", "bye", "goodbye", "shutdown omnitrix", "close yourself",
                    "goodbye ben", "turn off", "go to sleep", "shut down", "power off"):
            return {"action": "exit"}

        # OPEN APP
        match = re.match(r"(?:open|launch|start|run)\s+(?:the\s+)?(?:app\s+)?(.+)", cmd)
        if match:
            app = match.group(1).strip()
            if app.startswith("file ") or app in ("camera", "the camera"):
                pass
            else:
                return {"action": "open_app", "app": app}

        # CLOSE APP
        match = re.match(r"(?:close|kill|stop|quit|terminate)\s+(?:the\s+)?(?:app\s+)?(.+)", cmd)
        if match:
            app = match.group(1).strip()
            if app in ("camera", "the camera"):
                return {"action": "stop_camera"}
            if app in ("gesture", "gesture control"):
                return {"action": "stop_gesture_control"}
            return {"action": "close_app", "app": app}

        # VOLUME
        if any(w in cmd for w in ["volume up", "increase volume", "louder"]):
            return {"action": "volume_up"}
        if any(w in cmd for w in ["volume down", "decrease volume", "quieter"]):
            return {"action": "volume_down"}
        if any(w in cmd for w in ["mute", "unmute", "silence"]):
            return {"action": "volume_mute"}

        # BRIGHTNESS
        if any(w in cmd for w in ["brightness up", "increase brightness", "brighter"]):
            return {"action": "brightness_up"}
        if any(w in cmd for w in ["brightness down", "decrease brightness", "dimmer"]):
            return {"action": "brightness_down"}

        # TIME / DATE
        if any(w in cmd for w in ["what time", "current time", "tell me the time"]):
            return {"action": "get_time"}
        if any(w in cmd for w in ["what date", "today's date", "what day", "current date"]):
            return {"action": "get_date"}

        # SCREENSHOT / SELFIE
        if any(w in cmd for w in ["screenshot", "capture screen", "take a screenshot"]):
            return {"action": "take_screenshot"}
        if any(w in cmd for w in ["selfie", "take a selfie", "take my photo"]):
            return {"action": "take_selfie"}

        # CAMERA
        if any(w in cmd for w in ["start camera", "open camera", "turn on camera"]):
            return {"action": "start_camera"}
        if any(w in cmd for w in ["stop camera", "turn off camera", "camera off"]):
            return {"action": "stop_camera"}
        if any(w in cmd for w in ["what do you see", "detect objects", "scan"]):
            return {"action": "detect_objects"}

        # PANEL NAVIGATION (voice command panel switching)
        match = re.match(r"(?:open|show|go to|switch to|navigate to)\s+(?:the\s+)?(.+?)\s+(?:panel|tab|screen|view|page)", cmd)
        if match:
            return {"action": "open_panel", "panel_name": match.group(1)}
        if cmd.startswith("open ") and cmd[5:].strip() in ["home", "chat", "browser", "youtube", "files", "camera", "downloads", "terminal", "communication", "whatsapp", "email", "comms"]:
            return {"action": "open_panel", "panel_name": cmd[5:].strip()}

        # WEB SEARCH
        match = re.match(r"(?:search|google|look up)\s+(?:for\s+)?(.+)", cmd)
        if match:
            query = match.group(1).strip()
            if query and len(query) > 1:
                return {"action": "search_web", "query": query}

        # YOUTUBE
        match = re.match(r"(?:play|play on youtube|youtube)\s+(.+)", cmd)
        if match:
            query = match.group(1).strip()
            return {"action": "play_youtube", "query": query}

        # WHATSAPP
        match = re.match(r"(?:send|whatsapp)\s+(?:message\s+)?(?:to\s+)?(.+?)\s+(?:saying|message)\s+(.+)", cmd)
        if match:
            return {"action": "send_whatsapp", "recipient": match.group(1), "message": match.group(2)}
        if any(w in cmd for w in ["read whatsapp", "whatsapp messages", "check whatsapp"]):
            return {"action": "read_whatsapp", "count": 10}

        # EMAIL
        match = re.match(r"send\s+(?:an?\s+)?email\s+to\s+(.+?)\s+(?:about|subject)\s+(.+)", cmd)
        if match:
            return {"action": "send_email", "to": match.group(1), "subject": match.group(2), "body": match.group(2)}
        if any(w in cmd for w in ["read email", "check email", "read my email", "inbox", "check inbox"]):
            return {"action": "read_email", "count": 10}
        if any(w in cmd for w in ["unread email", "new email", "unread mail"]):
            return {"action": "read_unread_email", "count": 10}

        # DOWNLOAD IMAGES
        match = re.match(r"download\s+(\d+)?\s*(?:images?|pictures?)\s+(?:of\s+)?(.+)", cmd)
        if match:
            count = int(match.group(1)) if match.group(1) else 5
            return {"action": "download_images", "query": match.group(2), "count": count}

        # DOWNLOAD VIDEO
        match = re.match(r"(?:download|search and download)\s+(\d+)?\s*videos?\s+(?:of|about|for\s+)?(.+)", cmd)
        if match:
            if not match.group(1):
                return "How many videos do you want to download?"
            count = int(match.group(1))
            query = match.group(2).strip()
            return {"action": "download_video", "query": query, "count": count}

        # MEMORY
        match = re.match(r"(?:remember|store|save)\s+(?:that\s+)?(.+)", cmd)
        if match:
            fact = match.group(1).strip()
            if len(fact) > 3:
                return {"action": "remember_fact", "fact": fact}

        match = re.match(r"what(?:'s|\s+is)\s+my\s+(.+)", cmd)
        if match:
            return {"action": "what_is_my", "key": match.group(1).strip()}

        # SYSTEM
        if any(w in cmd for w in ["system info", "system information"]):
            return {"action": "system_info"}
        if any(w in cmd for w in ["shutdown computer", "power off computer"]):
            return {"action": "shutdown"}
        if any(w in cmd for w in ["restart computer", "reboot"]):
            return {"action": "restart"}
        if any(w in cmd for w in ["lock screen", "lock computer"]):
            return {"action": "lock_screen"}

        # JOKE
        if any(w in cmd for w in ["tell me a joke", "joke", "make me laugh"]):
            return {"action": "tell_joke"}

        # THEME
        if any(w in cmd for w in ["play theme", "theme song"]):
            return {"action": "play_theme"}

        # GESTURE
        if any(w in cmd for w in ["start gesture", "gesture control on"]):
            return {"action": "start_gesture_control"}
        if any(w in cmd for w in ["stop gesture", "gesture control off"]):
            return {"action": "stop_gesture_control"}

        # VOICE TOGGLE
        if any(w in cmd for w in ["change voice", "change your voice", "switch voice"]):
            return {"action": "toggle_voice"}

        return None

    # ==================================================================
    # Main Command Processing
    # ==================================================================

    def process_command(self, command):
        self.memory.add_message("user", command)

        smart_action = self.smart_match_command(command)
        if smart_action:
            print(f"[Smart Match] {command} → {smart_action}")
            self.execute_action(smart_action)
            return

        print(f"[Brain Needed] {command}")
        self.handle_with_brain(command)

    def process_command_sync(self, command):
        """Synchronous version for chat mode."""
        self.memory.add_message("user", command)
        smart_action = self.smart_match_command(command)
        if smart_action:
            self.execute_action(smart_action)
            return
        self.handle_with_brain(command)

    def handle_with_brain(self, command):
        def think():
            context = self.get_context()
            tools_desc = self.get_tools_description()
            system_prompt = self.build_system_prompt(context, tools_desc)
            try:
                response = ask_brain(system_prompt, command)
                print(f"[Engine] Brain response: {response}")
            except Exception as e:
                print(f"Brain error: {e}")
                traceback.print_exc()
                self.speak("Sorry, I'm having trouble connecting. Try again!")
                return
            actions = self.parse_response(response)
            self.execute_action(actions)
        threading.Thread(target=think, daemon=True).start()

    # ==================================================================
    # Speech
    # ==================================================================

    def speak(self, text):
        if not text:
            return
        print(f"Speaking: {text}")
        self.response_signal.emit(text)
        self.memory.add_message("assistant", text)
        self.tts.speak(text)

    # ==================================================================
    # Listening Loop
    # ==================================================================

    def listen_loop(self):
        while self.running:
            if not self.listening or self.tts.is_speaking:
                time.sleep(0.1)
                continue
            if time.time() - self.last_command_time < self.command_cooldown:
                time.sleep(0.05)
                continue

            command = self.stt.listen()
            if command:
                print(f"User said: {command}")
                self.user_said_signal.emit(command)
                self.command_queue.put(command)
                self.last_command_time = time.time()

    # ==================================================================
    # Process Loop
    # ==================================================================

    def process_loop(self):
        while self.running:
            try:
                command = self.command_queue.get(timeout=0.05)
                threading.Thread(target=self.process_command, args=(command,), daemon=True).start()
            except queue.Empty:
                pass
            result = self.automation.get_result(block=False)
            if result:
                self._handle_automation_result(result)

    def _handle_automation_result(self, result):
        if isinstance(result, str) and result.strip().startswith(('{', '[')):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                pass
        if isinstance(result, dict):
            if "error" in result:
                self.speak(f"Automation error: {result['error']}")
            elif "results" in result and result["results"]:
                items = result["results"]
                first = items[0].get("title", "No title") if items else "Nothing"
                self.speak(f"Found {len(items)} items. First: {first}")
            elif "downloaded" in result:
                self.speak(f"Downloaded {result['downloaded']} items.")
            elif "status" in result:
                self.speak(f"Automation {result['status']}.")
        else:
            self.speak(f"Automation result: {result}")

    # ==================================================================
    # Gesture Control
    # ==================================================================

    def start_gesture_control(self):
        if VISION_AVAILABLE:
            if self.gesture_thread is None or not self.gesture_thread.is_alive():
                self.gesture_thread = GestureControl(self.gesture_queue)
                self.gesture_thread.start()
                self.gesture_running = True
                self.speak("Gesture control activated")
                threading.Thread(target=self.process_gestures, daemon=True).start()
        else:
            return "Vision module not available."

    def stop_gesture_control(self):
        if self.gesture_thread:
            self.gesture_thread.stop()
            self.gesture_thread = None
            self.gesture_running = False
            self.speak("Gesture control deactivated")

    def process_gestures(self):
        while self.gesture_running:
            try:
                gesture = self.gesture_queue.get(timeout=0.5)
                self.handle_gesture(gesture)
            except queue.Empty:
                continue

    def handle_gesture(self, gesture):
        if gesture == "swipe_up":
            self.speak(sys_control.volume_up())
        elif gesture == "swipe_down":
            self.speak(sys_control.volume_down())
        elif gesture == "swipe_left" and pyautogui:
            pyautogui.hotkey('ctrl', 'shift', 'tab')
            self.speak("Previous tab")
        elif gesture == "swipe_right" and pyautogui:
            pyautogui.hotkey('ctrl', 'tab')
            self.speak("Next tab")
        elif gesture == "fist":
            sys_control.close_browser_tab()
            self.speak("Closed tab")
        elif gesture == "open_hand" and pyautogui:
            pyautogui.press('playpause')
            self.speak("Toggled play/pause")
        elif gesture == "peace":
            self.speak(sys_control.take_screenshot())

    # ==================================================================
    # Vision
    # ==================================================================

    def start_vision(self):
        if VISION_AVAILABLE and self.vision_thread is None:
            self.vision_thread = VisionThread()
            self.vision_thread.frame_ready.connect(self.camera_frame_signal.emit)
            self.vision_thread.detections_ready.connect(self.on_detections_ready)
            self.vision_thread.start()

    def stop_vision(self):
        if self.vision_thread:
            self.vision_thread.stop()
            self.vision_thread = None
            self.last_detections = []

    def on_detections_ready(self, labels):
        self.last_detections = labels

    # ==================================================================
    # Shutdown
    # ==================================================================

    def stop(self):
        if not hasattr(self, '_stopping'):
            self._stopping = False
        if self._stopping:
            return
        self._stopping = True
        self.running = False
        
        self._play_sound("assets/sounds/exit.wav")
        time.sleep(1.5)  # Let sound play before fully closing

        self.memory.save_memory()
        if self.vision_thread:
            self.vision_thread.stop()
            self.vision_thread = None
        if self.gesture_thread:
            self.gesture_thread.stop()
            self.gesture_thread = None
        self.automation.stop()
        self.exit_signal.emit()