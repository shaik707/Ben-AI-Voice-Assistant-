# voice/tts.py — Text-to-Speech Engine
# Supports Edge TTS (high-quality) with pyttsx3 fallback

import threading
import time
import os
import tempfile
import asyncio

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False

try:
    import pyttsx3
except ImportError:
    pass

try:
    import pygame
except ImportError:
    pygame = None


class TTSEngine:
    """Text-to-Speech engine with Edge TTS and pyttsx3 fallback."""

    EDGE_VOICE = "en-US-GuyNeural"

    def __init__(self):
        self.is_speaking = False
        self._lock = threading.Lock()

        # Initialize Edge TTS
        if EDGE_TTS_AVAILABLE and pygame:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            print(f"[TTS] Edge TTS ready with voice: {self.EDGE_VOICE}")

        # Initialize pyttsx3
        try:
            self.pyttsx3_engine = pyttsx3.init()
            self.pyttsx3_engine.setProperty('rate', 160)
            voices = self.pyttsx3_engine.getProperty('voices')
            for voice in voices:
                if 'daniel' in voice.name.lower():
                    self.pyttsx3_engine.setProperty('voice', voice.id)
                    break
            else:
                if voices:
                    self.pyttsx3_engine.setProperty('voice', voices[0].id)
            print("[TTS] pyttsx3 ready.")
        except Exception as e:
            print(f"[TTS] pyttsx3 init failed: {e}")
            self.pyttsx3_engine = None

        if EDGE_TTS_AVAILABLE:
            self.active_voice_type = "edge_tts"
        elif hasattr(self, 'pyttsx3_engine') and self.pyttsx3_engine:
            self.active_voice_type = "pyttsx3"
        else:
            self.active_voice_type = "none"

    def toggle_voice(self):
        if self.active_voice_type == "pyttsx3" and EDGE_TTS_AVAILABLE:
            self.active_voice_type = "edge_tts"
            return "Switched to Edge TTS voice."
        elif hasattr(self, 'pyttsx3_engine') and self.pyttsx3_engine:
            self.active_voice_type = "pyttsx3"
            return "Switched to offline Daniel voice."
        else:
            return "No other voice engine available to switch to."

    def speak(self, text, callback=None):
        """Speak text asynchronously. Optional callback when done."""
        if not text:
            return
        if self.active_voice_type == "edge_tts" and EDGE_TTS_AVAILABLE:
            self._speak_edge(text, callback)
        else:
            self._speak_pyttsx3(text, callback)

    def _speak_edge(self, text, callback=None):
        def _run():
            self.is_speaking = True
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
                    tmp_path = tmp.name

                async def generate():
                    # medium speed for edge-tts (default or slightly tweaked if needed)
                    communicate = edge_tts.Communicate(text, self.EDGE_VOICE, rate="+0%")
                    await communicate.save(tmp_path)

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                loop.run_until_complete(generate())
                loop.close()

                if pygame and pygame.mixer.get_init():
                    pygame.mixer.music.load(tmp_path)
                    pygame.mixer.music.play()
                    while pygame.mixer.music.get_busy():
                        time.sleep(0.1)

                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

            except Exception as e:
                print(f"[TTS Error] {e}")
                self._speak_pyttsx3_sync(text)
            finally:
                self.is_speaking = False
                if callback:
                    callback()

        threading.Thread(target=_run, daemon=True).start()
        time.sleep(0.3)

    def _speak_pyttsx3(self, text, callback=None):
        def _run():
            self.is_speaking = True
            self._speak_pyttsx3_sync(text)
            self.is_speaking = False
            if callback:
                callback()
        threading.Thread(target=_run, daemon=True).start()

    def _speak_pyttsx3_sync(self, text):
        try:
            if hasattr(self, 'pyttsx3_engine') and self.pyttsx3_engine:
                self.pyttsx3_engine.say(text)
                self.pyttsx3_engine.runAndWait()
        except Exception as e:
            print(f"[TTS Fallback Error] {e}")

    def stop(self):
        """Stop any current speech."""
        try:
            if pygame and pygame.mixer.get_init():
                pygame.mixer.music.stop()
        except Exception:
            pass
        self.is_speaking = False


# Module-level convenience
_engine = None

def get_tts_engine():
    global _engine
    if _engine is None:
        _engine = TTSEngine()
    return _engine

def speak(text, callback=None):
    get_tts_engine().speak(text, callback)
