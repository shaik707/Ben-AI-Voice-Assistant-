# brain/brain.py — LLM Integration (Refactored)
# Wraps OpenAI-compatible API for AI reasoning

import json
import os
import traceback

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("[Brain] OpenAI library not installed.")

# Load config
try:
    from core.config import LLM_BASE_URL, LLM_MODEL, LLM_API_KEY
except ImportError:
    LLM_BASE_URL = os.getenv("LLM_BASE_URL")
    LLM_MODEL = os.getenv("LLM_MODEL")
    LLM_API_KEY = os.getenv("LLM_API_KEY")


class BrainManager:
    """Manages LLM communication and conversation history."""

    def __init__(self, base_url=None, model=None, api_key=None):
        self.base_url = base_url or LLM_BASE_URL
        self.model = model or LLM_MODEL
        self.api_key = api_key or LLM_API_KEY
        self.conversation_history = []

        if OPENAI_AVAILABLE:
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key or "choose-any-value",
                timeout=120.0,
                max_retries=2
            )
            print(f"[Brain] Connected to {self.base_url} | Model: {self.model}")
        else:
            self.client = None
            print("[Brain] OpenAI client not available.")

    def ask(self, system_prompt, user_message, max_tokens=120):
        """Send a message to the LLM and get a response."""
        if not self.client:
            return self._fallback_response(user_message)

        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })

        messages = [
            {"role": "system", "content": system_prompt}
        ] + self.conversation_history[-10:]  # Keep last 10 messages

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content.strip()
            self.conversation_history.append({
                "role": "assistant",
                "content": content
            })

            # Trim conversation history
            if len(self.conversation_history) > 20:
                self.conversation_history = self.conversation_history[-20:]

            # Try to parse as JSON
            parsed = self._extract_json(content)
            if parsed is not None:
                return parsed

            return content

        except Exception as e:
            print(f"[Brain Error] {e}")
            traceback.print_exc()
            return self._fallback_response(user_message)

    def _extract_json(self, text):
        """Try to extract JSON from the response."""
        text = text.strip()

        # Direct JSON
        if text.startswith('{') or text.startswith('['):
            try:
                return json.loads(text)
            except json.JSONDecodeError:
                pass

        # JSON inside ```json...``` blocks
        import re
        json_match = re.search(r'```(?:json)?\s*\n([\s\S]*?)\n```', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # JSON embedded in text
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            start = text.find(start_char)
            if start != -1:
                depth = 0
                for i in range(start, len(text)):
                    if text[i] == start_char:
                        depth += 1
                    elif text[i] == end_char:
                        depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[start:i + 1])
                        except json.JSONDecodeError:
                            break

        return None

    def _fallback_response(self, user_message):
        """Fallback when LLM is not available."""
        msg = user_message.lower()
        if any(w in msg for w in ["hello", "hi", "hey"]):
            return "Hey! I'm BENN AI. I'm running in offline mode, but I can still help with system commands!"
        elif any(w in msg for w in ["how are you", "how do you do"]):
            return "I'm operational and ready to assist! What do you need?"
        elif any(w in msg for w in ["thank", "thanks"]):
            return "You're welcome! Anything else?"
        else:
            return "I'm running without my AI brain right now, but I can handle system commands. Try 'open chrome' or 'what time is it'."

    def clear_history(self):
        self.conversation_history = []


# Module-level singleton
_brain = None

def get_brain():
    global _brain
    if _brain is None:
        _brain = BrainManager()
    return _brain

def ask_brain(system_prompt, user_message, **kwargs):
    """Convenience function to ask the brain."""
    return get_brain().ask(system_prompt, user_message, **kwargs)