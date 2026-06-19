import os
import json
import threading

class MemoryManager:
    def __init__(self):
        self.facts = {}
        self.history = []
        self.knowledge = {}
        self._save_lock = threading.Lock()
        self._saving = False
        self.load_memory()
        self.load_knowledge()

    # ---------- Conversation history ----------
    def add_message(self, role, content):
        self.history.append({"role": role, "content": content})

    def get_recent(self, n=10):
        return self.history[-n:]

    # ---------- Facts (persistent memory) ----------
    def remember_fact(self, key, value):
        self.facts[key] = value
        self.save_memory()

    def get_fact(self, key):
        return self.facts.get(key)

    def get_all_facts(self):
        return self.facts

    # ---------- Knowledge files ----------
    def load_knowledge(self, folder="knowledge"):
        if not os.path.exists(folder):
            os.makedirs(folder, exist_ok=True)
            return
        for file in os.listdir(folder):
            if file.endswith(".txt"):
                topic = file[:-4]
                try:
                    with open(os.path.join(folder, file), 'r', encoding='utf-8') as f:
                        self.knowledge[topic] = f.read()
                except Exception as e:
                    print(f"Error loading knowledge file {file}: {e}")

    def get_knowledge(self, topic):
        return self.knowledge.get(topic)

    def get_all_knowledge_topics(self):
        return list(self.knowledge.keys())

    # ---------- Persistence to disk ----------
    def save_memory(self, path="memory.json"):
        # Prevent reentrant calls
        with self._save_lock:
            if self._saving:
                return
            self._saving = True
        try:
            data = {
                "facts": self.facts,
                "history": self.history[-100:]
            }
            # Pre-check for circular references
            try:
                json_string = json.dumps(data)
            except RecursionError:
                print("Memory contains circular reference – saving aborted.")
                return
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json_string)
        except Exception as e:
            print(f"Error saving memory: {e}")
        finally:
            with self._save_lock:
                self._saving = False

    def load_memory(self, path="memory.json"):
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.facts = data.get("facts", {})
                self.history = data.get("history", [])
            except json.JSONDecodeError:
                print("Memory file corrupted. Starting with fresh memory.")
                backup_path = path + ".backup"
                try:
                    os.rename(path, backup_path)
                    print(f"Corrupted memory file backed up as {backup_path}")
                except:
                    pass
                self.facts = {}
                self.history = []
            except Exception as e:
                print(f"Error loading memory: {e}")
                self.facts = {}
                self.history = []
        else:
            self.facts = {}
            self.history = []