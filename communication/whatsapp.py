# communication/whatsapp.py — WhatsApp Messaging System
# Uses pywhatkit for WhatsApp Web automation

import json
import os
import datetime
import threading
import time

try:
    import pywhatkit
    PYWHATKIT_AVAILABLE = True
except ImportError:
    PYWHATKIT_AVAILABLE = False
    print("[WhatsApp] pywhatkit not installed. WhatsApp features limited.")


class WhatsAppHandler:
    """
    WhatsApp messaging via pywhatkit (WhatsApp Web automation).
    Supports: send messages, schedule messages, contact management.
    """

    def __init__(self, contacts_file="communication/whatsapp_contacts.json"):
        self.contacts_file = contacts_file
        self.contacts = self._load_contacts()
        self.message_log = []
        self.log_file = "communication/whatsapp_log.json"
        self._load_log()

    def _load_contacts(self):
        try:
            if os.path.exists(self.contacts_file):
                with open(self.contacts_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[WhatsApp] Error loading contacts: {e}")
        return {}

    def _save_contacts(self):
        try:
            os.makedirs(os.path.dirname(self.contacts_file) or '.', exist_ok=True)
            with open(self.contacts_file, 'w') as f:
                json.dump(self.contacts, f, indent=2)
        except Exception as e:
            print(f"[WhatsApp] Error saving contacts: {e}")

    def _load_log(self):
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.message_log = json.load(f)
        except Exception:
            self.message_log = []

    def _save_log(self):
        try:
            os.makedirs(os.path.dirname(self.log_file) or '.', exist_ok=True)
            with open(self.log_file, 'w') as f:
                json.dump(self.message_log[-500:], f, indent=2)
        except Exception:
            pass

    # ==================== Contact Management ====================

    def add_contact(self, name, phone_number):
        """Add a contact. Phone number must include country code (e.g., +91...)."""
        if not phone_number.startswith('+'):
            phone_number = '+' + phone_number
        self.contacts[name.lower()] = {
            "name": name,
            "phone": phone_number
        }
        self._save_contacts()
        return f"Contact '{name}' saved with number {phone_number}."

    def get_contact(self, name):
        """Get a contact by name."""
        contact = self.contacts.get(name.lower())
        if contact:
            return contact
        # Fuzzy search
        for key, val in self.contacts.items():
            if name.lower() in key:
                return val
        return None

    def list_contacts(self):
        """List all saved contacts."""
        if not self.contacts:
            return "No contacts saved."
        lines = ["Saved Contacts:"]
        for key, val in self.contacts.items():
            lines.append(f"  • {val['name']}: {val['phone']}")
        return "\n".join(lines)

    def remove_contact(self, name):
        """Remove a contact by name."""
        key = name.lower()
        if key in self.contacts:
            del self.contacts[key]
            self._save_contacts()
            return f"Contact '{name}' removed."
        return f"Contact '{name}' not found."

    # ==================== Send Messages ====================

    def send_message(self, recipient, message):
        """
        Send a WhatsApp message instantly.
        recipient: phone number (with country code) or contact name.
        """
        if not PYWHATKIT_AVAILABLE:
            return "WhatsApp messaging requires pywhatkit. Install with: pip install pywhatkit"

        # Resolve contact name to number
        phone = self._resolve_phone(recipient)
        if not phone:
            return f"Could not find contact '{recipient}'. Please provide phone number with country code."

        try:
            # Send message (opens WhatsApp Web, sends, and closes tab)
            now = datetime.datetime.now()
            send_hour = now.hour
            send_min = now.minute + 1  # Send 1 minute from now minimum
            if send_min >= 60:
                send_hour += 1
                send_min -= 60

            def _send():
                try:
                    pywhatkit.sendwhatmsg(phone, message, send_hour, send_min, wait_time=15, tab_close=True)
                    self._log_message("sent", phone, message)
                except Exception as e:
                    print(f"[WhatsApp] Send error: {e}")

            threading.Thread(target=_send, daemon=True).start()
            return f"Sending WhatsApp message to {phone}. WhatsApp Web will open shortly."

        except Exception as e:
            return f"WhatsApp send error: {str(e)}"

    def send_instant_message(self, recipient, message):
        """Send message instantly using pywhatkit instant send."""
        if not PYWHATKIT_AVAILABLE:
            return "WhatsApp messaging requires pywhatkit."

        phone = self._resolve_phone(recipient)
        if not phone:
            return f"Could not find contact '{recipient}'."

        try:
            def _send():
                try:
                    pywhatkit.sendwhatmsg_instantly(phone, message, wait_time=10, tab_close=True)
                    self._log_message("sent", phone, message)
                except Exception as e:
                    print(f"[WhatsApp] Instant send error: {e}")

            threading.Thread(target=_send, daemon=True).start()
            return f"Sending instant WhatsApp message to {phone}."
        except Exception as e:
            return f"Error: {str(e)}"

    def schedule_message(self, recipient, message, hour, minute):
        """Schedule a WhatsApp message for a specific time."""
        if not PYWHATKIT_AVAILABLE:
            return "WhatsApp messaging requires pywhatkit."

        phone = self._resolve_phone(recipient)
        if not phone:
            return f"Could not find contact '{recipient}'."

        try:
            def _send():
                try:
                    pywhatkit.sendwhatmsg(phone, message, hour, minute, wait_time=15, tab_close=True)
                    self._log_message("scheduled_sent", phone, message)
                except Exception as e:
                    print(f"[WhatsApp] Scheduled send error: {e}")

            threading.Thread(target=_send, daemon=True).start()
            return f"Message scheduled for {hour:02d}:{minute:02d} to {phone}."
        except Exception as e:
            return f"Schedule error: {str(e)}"

    # ==================== Read Messages ====================

    def get_message_log(self, count=10):
        """Get recent message log."""
        if not self.message_log:
            return "No messages in log."
        recent = self.message_log[-count:]
        lines = ["Recent WhatsApp Messages:"]
        for msg in recent:
            direction = "→" if msg.get("type") == "sent" else "←"
            lines.append(f"  {direction} {msg.get('phone', '?')}: {msg.get('message', '')[:80]}")
            lines.append(f"    ({msg.get('timestamp', '?')})")
        return "\n".join(lines)

    # ==================== Helpers ====================

    def _resolve_phone(self, recipient):
        """Resolve name or number to phone number."""
        if recipient.startswith('+') or recipient.replace(' ', '').isdigit():
            phone = recipient.replace(' ', '')
            if not phone.startswith('+'):
                phone = '+' + phone
            return phone
        contact = self.get_contact(recipient)
        return contact.get("phone") if contact else None

    def _log_message(self, msg_type, phone, message):
        """Log a message for history."""
        entry = {
            "type": msg_type,
            "phone": phone,
            "message": message,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.message_log.append(entry)
        self._save_log()
