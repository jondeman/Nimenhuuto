import os
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Nimenhuuto credentials
NIMENHUUTO_USER = os.getenv("NIMENHUUTO_USER")
NIMENHUUTO_PASS = os.getenv("NIMENHUUTO_PASS")

# Telegram credentials
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Comma-separated list of recipient phone numbers in international format
RECIPIENTS = os.getenv("RECIPIENTS", "").split(",")

# Events storage file
SEEN_EVENTS_FILE = os.getenv("SEEN_EVENTS_FILE", "events_seen.json")

# Bot settings
BASE_URL = "https://vantaanreservilaiset.nimenhuuto.com"
EVENTS_PATH = "/events"

