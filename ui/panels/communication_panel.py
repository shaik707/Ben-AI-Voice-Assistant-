# ui/panels/communication_panel.py — WhatsApp + Email Panel

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget,
    QTextEdit, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QFrame, QFormLayout, QMessageBox
)
from PyQt6.QtCore import Qt
import json
import os


class CommunicationPanel(QWidget):
    def __init__(self, engine=None):
        super().__init__()
        self.engine = engine
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        header = QLabel("📨 Communication Center")
        header.setStyleSheet("color: #00c8ff; font-size: 18px; font-weight: bold; padding: 4px;")
        layout.addWidget(header)

        # Tabs: WhatsApp | Email
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_whatsapp_tab(), "💬 WhatsApp")
        self.tabs.addTab(self._build_email_tab(), "📧 Email")
        layout.addWidget(self.tabs, 1)

    # ==================== WHATSAPP TAB ====================

    def _build_whatsapp_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)

        # Left: Contact list
        left = QVBoxLayout()
        contacts_label = QLabel("Contacts")
        contacts_label.setStyleSheet("color: #00c8ff; font-weight: bold;")
        left.addWidget(contacts_label)

        self.wa_contacts = QListWidget()
        self.wa_contacts.setMaximumWidth(250)
        self.wa_contacts.setStyleSheet("""
            QListWidget { background-color: #0d1117; border: 1px solid #1a2332; border-radius: 8px; }
            QListWidget::item { padding: 10px; border-radius: 4px; margin: 1px; }
            QListWidget::item:hover { background-color: rgba(0, 200, 255, 0.08); }
            QListWidget::item:selected { background-color: rgba(0, 200, 255, 0.15); }
        """)
        self.wa_contacts.itemClicked.connect(self._wa_select_contact)
        left.addWidget(self.wa_contacts, 1)

        # Add contact
        add_layout = QHBoxLayout()
        self.wa_name_input = QLineEdit()
        self.wa_name_input.setPlaceholderText("Name")
        add_layout.addWidget(self.wa_name_input)
        self.wa_phone_input = QLineEdit()
        self.wa_phone_input.setPlaceholderText("+91...")
        add_layout.addWidget(self.wa_phone_input)
        add_btn = QPushButton("➕")
        add_btn.setFixedSize(36, 36)
        add_btn.clicked.connect(self._wa_add_contact)
        add_layout.addWidget(add_btn)
        left.addLayout(add_layout)

        layout.addLayout(left)

        # Right: Chat
        right = QVBoxLayout()

        self.wa_chat_header = QLabel("Select a contact")
        self.wa_chat_header.setStyleSheet("color: #e0e6f0; font-size: 14px; font-weight: bold; padding: 4px;")
        right.addWidget(self.wa_chat_header)

        self.wa_chat_display = QTextEdit()
        self.wa_chat_display.setReadOnly(True)
        self.wa_chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #0d1117;
                border: 1px solid #1a2332;
                border-radius: 8px;
                padding: 8px;
                color: #e0e6f0;
            }
        """)
        right.addWidget(self.wa_chat_display, 1)

        # Message input
        msg_layout = QHBoxLayout()
        self.wa_msg_input = QLineEdit()
        self.wa_msg_input.setPlaceholderText("Type a message...")
        self.wa_msg_input.setMinimumHeight(40)
        self.wa_msg_input.returnPressed.connect(self._wa_send)
        msg_layout.addWidget(self.wa_msg_input, 1)

        send_btn = QPushButton("📤 Send")
        send_btn.setObjectName("primaryBtn")
        send_btn.setMinimumHeight(40)
        send_btn.clicked.connect(self._wa_send)
        msg_layout.addWidget(send_btn)

        right.addLayout(msg_layout)

        layout.addLayout(right, 1)

        # Load contacts
        self._wa_load_contacts()

        return widget

    def _wa_load_contacts(self):
        self.wa_contacts.clear()
        contacts_file = "communication/whatsapp_contacts.json"
        if os.path.exists(contacts_file):
            try:
                with open(contacts_file, 'r') as f:
                    contacts = json.load(f)
                for key, val in contacts.items():
                    item = QListWidgetItem(f"👤 {val.get('name', key)}\n   {val.get('phone', '')}")
                    item.setData(Qt.ItemDataRole.UserRole, val)
                    self.wa_contacts.addItem(item)
            except Exception:
                pass

    def _wa_select_contact(self, item):
        contact = item.data(Qt.ItemDataRole.UserRole)
        if contact:
            self.wa_chat_header.setText(f"Chat with {contact.get('name', '?')} ({contact.get('phone', '')})")

    def _wa_add_contact(self):
        name = self.wa_name_input.text().strip()
        phone = self.wa_phone_input.text().strip()
        if not name or not phone:
            return
        contacts_file = "communication/whatsapp_contacts.json"
        contacts = {}
        if os.path.exists(contacts_file):
            with open(contacts_file, 'r') as f:
                contacts = json.load(f)
        if not phone.startswith('+'):
            phone = '+' + phone
        contacts[name.lower()] = {"name": name, "phone": phone}
        os.makedirs("communication", exist_ok=True)
        with open(contacts_file, 'w') as f:
            json.dump(contacts, f, indent=2)
        self._wa_load_contacts()
        self.wa_name_input.clear()
        self.wa_phone_input.clear()

    def _wa_send(self):
        msg = self.wa_msg_input.text().strip()
        if not msg:
            return

        # Get selected contact
        item = self.wa_contacts.currentItem()
        if not item:
            QMessageBox.warning(self, "No Contact", "Please select a contact first.")
            return

        contact = item.data(Qt.ItemDataRole.UserRole)
        phone = contact.get('phone', '')

        self.wa_chat_display.append(
            f'<div style="text-align: right; margin: 4px;">'
            f'<span style="color: #00c8ff; background: rgba(0,200,255,0.1); padding: 6px 12px; border-radius: 8px;">'
            f'{msg}</span></div>'
        )
        self.wa_msg_input.clear()

        # Send via WhatsApp handler
        import threading
        def send():
            try:
                from communication.whatsapp import WhatsAppHandler
                handler = WhatsAppHandler()
                result = handler.send_instant_message(phone, msg)
                print(f"[WhatsApp] {result}")
            except Exception as e:
                print(f"[WhatsApp] Error: {e}")
        threading.Thread(target=send, daemon=True).start()

    # ==================== EMAIL TAB ====================

    def _build_email_tab(self):
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setSpacing(8)

        # Left: Inbox list
        left = QVBoxLayout()
        inbox_header = QLabel("📥 Inbox")
        inbox_header.setStyleSheet("color: #00c8ff; font-weight: bold;")
        left.addWidget(inbox_header)

        self.email_list = QListWidget()
        self.email_list.setMaximumWidth(350)
        self.email_list.setStyleSheet("""
            QListWidget { background-color: #0d1117; border: 1px solid #1a2332; border-radius: 8px; }
            QListWidget::item { padding: 10px; border-radius: 4px; margin: 1px; }
            QListWidget::item:hover { background-color: rgba(0, 200, 255, 0.08); }
            QListWidget::item:selected { background-color: rgba(0, 200, 255, 0.15); }
        """)
        left.addWidget(self.email_list, 1)

        # Inbox actions
        inbox_actions = QHBoxLayout()
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.clicked.connect(self._email_refresh)
        inbox_actions.addWidget(refresh_btn)

        unread_btn = QPushButton("📬 Unread")
        unread_btn.clicked.connect(self._email_unread)
        inbox_actions.addWidget(unread_btn)

        left.addLayout(inbox_actions)
        layout.addLayout(left)

        # Right: Read / Compose
        right_tabs = QTabWidget()

        # Read tab
        read_widget = QWidget()
        read_layout = QVBoxLayout(read_widget)
        self.email_display = QTextEdit()
        self.email_display.setReadOnly(True)
        self.email_display.setStyleSheet("""
            QTextEdit { background-color: #0d1117; border: 1px solid #1a2332;
                       border-radius: 8px; padding: 8px; color: #e0e6f0; }
        """)
        self.email_display.setPlaceholderText("Select an email to read...")
        read_layout.addWidget(self.email_display)
        right_tabs.addTab(read_widget, "📖 Read")

        # Compose tab
        compose_widget = QWidget()
        compose_layout = QVBoxLayout(compose_widget)

        form = QFormLayout()
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("recipient@email.com")
        form.addRow("To:", self.to_input)

        self.subject_input = QLineEdit()
        self.subject_input.setPlaceholderText("Subject")
        form.addRow("Subject:", self.subject_input)

        compose_layout.addLayout(form)

        self.body_input = QTextEdit()
        self.body_input.setPlaceholderText("Write your email here...")
        self.body_input.setStyleSheet("""
            QTextEdit { background-color: #161b22; border: 1px solid #30363d;
                       border-radius: 8px; padding: 8px; color: #e0e6f0; }
        """)
        compose_layout.addWidget(self.body_input, 1)

        send_layout = QHBoxLayout()
        send_layout.addStretch()
        send_email_btn = QPushButton("📤 Send Email")
        send_email_btn.setObjectName("primaryBtn")
        send_email_btn.setMinimumHeight(40)
        send_email_btn.clicked.connect(self._email_send)
        send_layout.addWidget(send_email_btn)
        compose_layout.addLayout(send_layout)

        right_tabs.addTab(compose_widget, "✏️ Compose")

        layout.addWidget(right_tabs, 1)

        return widget

    def _email_refresh(self):
        self.email_list.clear()
        import threading
        def fetch():
            try:
                from communication.email_handler import EmailHandler
                config = self._load_email_config()
                handler = EmailHandler(config)
                if not handler.is_configured():
                    return
                result = handler.read_inbox(count=20)
                # We'll just display the text result
                self.email_display.setText(result)
            except Exception as e:
                print(f"[Email] Error: {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def _email_unread(self):
        import threading
        def fetch():
            try:
                from communication.email_handler import EmailHandler
                config = self._load_email_config()
                handler = EmailHandler(config)
                if not handler.is_configured():
                    return
                result = handler.read_unread(count=10)
                self.email_display.setText(result)
            except Exception as e:
                print(f"[Email] Error: {e}")
        threading.Thread(target=fetch, daemon=True).start()

    def _email_send(self):
        to = self.to_input.text().strip()
        subject = self.subject_input.text().strip()
        body = self.body_input.toPlainText().strip()

        if not to or not subject or not body:
            QMessageBox.warning(self, "Missing Info", "Please fill in To, Subject, and Body.")
            return

        import threading
        def send():
            try:
                from communication.email_handler import EmailHandler
                config = self._load_email_config()
                handler = EmailHandler(config)
                result = handler.send_email(to, subject, body)
                print(f"[Email] {result}")
            except Exception as e:
                print(f"[Email] Error: {e}")
        threading.Thread(target=send, daemon=True).start()

        QMessageBox.information(self, "Sending", "Email is being sent...")
        self.to_input.clear()
        self.subject_input.clear()
        self.body_input.clear()

    def _load_email_config(self):
        """Load email config from .env or config file."""
        config = {}
        env_file = ".env"
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, val = line.strip().split('=', 1)
                        config[key.strip().lower()] = val.strip()
        # Also check core/config.py values
        try:
            from core.config import (EMAIL_ADDRESS, EMAIL_PASSWORD,
                                     SMTP_SERVER, SMTP_PORT, IMAP_SERVER, IMAP_PORT)
            if EMAIL_ADDRESS and "your_email" not in EMAIL_ADDRESS:
                config.setdefault("email", EMAIL_ADDRESS)
                config.setdefault("password", EMAIL_PASSWORD)
                config.setdefault("smtp_server", SMTP_SERVER)
                config.setdefault("smtp_port", SMTP_PORT)
                config.setdefault("imap_server", IMAP_SERVER)
                config.setdefault("imap_port", IMAP_PORT)
        except Exception:
            pass
        return config

    def cleanup(self):
        pass
