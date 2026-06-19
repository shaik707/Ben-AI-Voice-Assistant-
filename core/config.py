# core/config.py — Central Configuration
# Loads settings from .env file and provides defaults

import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# ==================== LLM Configuration ====================
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "LLM URL")
LLM_MODEL = os.getenv("LLM_MODEL", "LLM MODEL")
LLM_API_KEY = os.getenv("LLM_API_KEY", "choose-any-value")

# ==================== Email Configuration ====================
EMAIL_ADDRESS = os.getenv("EMAIL_ADDRESS", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
IMAP_SERVER = os.getenv("IMAP_SERVER", "imap.gmail.com")
IMAP_PORT = int(os.getenv("IMAP_PORT", "993"))

# ==================== WhatsApp Configuration ====================
WHATSAPP_DEFAULT_COUNTRY_CODE = os.getenv("WHATSAPP_COUNTRY_CODE", "+91")

# ==================== Paths ====================
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOWNLOADS_DIR = os.path.join(PROJECT_DIR, "downloads")
SCREENSHOTS_DIR = os.path.join(PROJECT_DIR, "screenshots")
SELFIES_DIR = os.path.join(PROJECT_DIR, "selfies")
KNOWLEDGE_DIR = os.path.join(PROJECT_DIR, "knowledge")
MEMORY_FILE = os.path.join(PROJECT_DIR, "memory.json")
CONTACTS_FILE = os.path.join(PROJECT_DIR, "communication", "contacts.json")

# Create directories
for d in [DOWNLOADS_DIR, SCREENSHOTS_DIR, SELFIES_DIR,
          os.path.join(DOWNLOADS_DIR, "images"), os.path.join(DOWNLOADS_DIR, "videos")]:
    os.makedirs(d, exist_ok=True)