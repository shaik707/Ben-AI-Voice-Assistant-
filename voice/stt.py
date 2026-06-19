# voice/stt.py — Speech-to-Text Engine
# Supports Whisper (offline) with Google Speech fallback

import tempfile
import os
import time
import speech_recognition as sr

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class STTEngine:
    """Speech-to-Text engine with Whisper and Google fallback."""

    NOISE_PHRASES = {"you", "thank you", "thanks for watching", "bye", ""}

    def __init__(self, use_whisper=True):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.use_whisper = use_whisper and WHISPER_AVAILABLE

        if self.use_whisper:
            try:
                # Reverting to tiny.en for maximum responsiveness and speed
                self.whisper_model = whisper.load_model("tiny.en")
                print("[STT] Whisper tiny.en model loaded.")
            except Exception as e:
                print(f"[STT] Whisper load failed: {e}, falling back to Google.")
                self.use_whisper = False

        # Calibrate microphone
        self._calibrate()

    def _calibrate(self):
        try:
            with self.microphone as source:
                print("[STT] Calibrating microphone...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                self.recognizer.energy_threshold = max(300, self.recognizer.energy_threshold * 1.5)
                self.recognizer.dynamic_energy_threshold = True
                # Quicker pause detection for faster responses
                self.recognizer.pause_threshold = 0.8
                self.recognizer.phrase_threshold = 0.3
                self.recognizer.non_speaking_duration = 0.4
                print(f"[STT] Energy threshold: {self.recognizer.energy_threshold:.0f}")
        except Exception as e:
            print(f"[STT] Microphone calibration failed: {e}")

    def listen(self, timeout=3, phrase_time_limit=15):
        """
        Listen for speech and return text.
        Returns None if no speech detected or noise filtered.
        """
        try:
            with self.microphone as source:
                # Periodic noise adjustment
                if not hasattr(self, '_last_adjust') or time.time() - self._last_adjust > 30:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.2)
                    self._last_adjust = time.time()

                audio = self.recognizer.listen(
                    source, timeout=timeout, phrase_time_limit=phrase_time_limit
                )

            if self.use_whisper:
                return self._recognize_whisper(audio)
            else:
                return self._recognize_google(audio)

        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[STT Error] {type(e).__name__}: {e}")
            return None

    def _recognize_whisper(self, audio):
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                tmp.write(audio.get_wav_data())
                tmp_path = tmp.name
            result = self.whisper_model.transcribe(tmp_path)
            os.remove(tmp_path)
            text = result["text"].strip().lower()
            if text and len(text) >= 2 and text not in self.NOISE_PHRASES:
                return text
            return None
        except Exception as e:
            print(f"[STT Whisper Error] {e}")
            return None

    def _recognize_google(self, audio):
        try:
            text = self.recognizer.recognize_google(audio, language="en-IN").lower()
            if text and len(text) >= 2 and text not in self.NOISE_PHRASES:
                return text
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[STT Google Error] {e}")
            return None


# Module-level convenience
_engine = None

def get_stt_engine():
    global _engine
    if _engine is None:
        _engine = STTEngine()
    return _engine

def listen_command(**kwargs):
    return get_stt_engine().listen(**kwargs)
