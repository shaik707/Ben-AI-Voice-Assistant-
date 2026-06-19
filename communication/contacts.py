# communication/contacts.py — Contact Management

import json
import os


class ContactManager:
    """Unified contact manager for WhatsApp and Email."""

    def __init__(self, contacts_file="communication/contacts.json"):
        self.contacts_file = contacts_file
        self.contacts = self._load()

    def _load(self):
        try:
            if os.path.exists(self.contacts_file):
                with open(self.contacts_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Contacts] Load error: {e}")
        return {}

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.contacts_file) or '.', exist_ok=True)
            with open(self.contacts_file, 'w') as f:
                json.dump(self.contacts, f, indent=2)
        except Exception as e:
            print(f"[Contacts] Save error: {e}")

    def add(self, name, phone="", email_addr=""):
        """Add or update a contact."""
        key = name.lower()
        if key in self.contacts:
            # Update existing
            if phone:
                self.contacts[key]["phone"] = phone
            if email_addr:
                self.contacts[key]["email"] = email_addr
        else:
            self.contacts[key] = {
                "name": name,
                "phone": phone,
                "email": email_addr
            }
        self._save()
        return f"Contact '{name}' saved."

    def get(self, name):
        """Get contact by name (fuzzy)."""
        key = name.lower()
        if key in self.contacts:
            return self.contacts[key]
        for k, v in self.contacts.items():
            if key in k:
                return v
        return None

    def remove(self, name):
        key = name.lower()
        if key in self.contacts:
            del self.contacts[key]
            self._save()
            return f"Contact '{name}' removed."
        return f"Contact '{name}' not found."

    def list_all(self):
        if not self.contacts:
            return "No contacts saved."
        lines = ["Contacts:"]
        for key, val in self.contacts.items():
            phone = val.get('phone', '-')
            em = val.get('email', '-')
            lines.append(f"  • {val['name']} | Phone: {phone} | Email: {em}")
        return "\n".join(lines)

    def search(self, query):
        query = query.lower()
        results = []
        for key, val in self.contacts.items():
            if (query in key or
                query in val.get('phone', '') or
                query in val.get('email', '').lower()):
                results.append(val)
        return results
