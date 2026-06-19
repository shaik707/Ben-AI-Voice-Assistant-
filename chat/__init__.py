# chat/__init__.py — Chat Mode Handler

class ChatHandler:
    """Handles text-based chat input (as opposed to voice)."""

    def __init__(self, engine=None):
        self.engine = engine
        self.history = []

    def process_message(self, text):
        """Process a chat message and return response."""
        self.history.append({"role": "user", "content": text})
        if self.engine:
            # Use the engine's command processing
            result = self.engine.process_command_sync(text)
            self.history.append({"role": "assistant", "content": result or ""})
            return result
        return "Chat engine not initialized."

    def get_history(self):
        return self.history

    def clear_history(self):
        self.history = []
