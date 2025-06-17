import requests
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_CHANNEL_ID

TELEGRAM_API_URL = "https://api.telegram.org/bot"

def send_telegram_message(token: str, chat_id: str, message: str):
    url = f"{TELEGRAM_API_URL}{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()


def notify_event_open(event):
    """
    Lähetä ilmoitus Telegramiin avatusta tapahtumasta.
    """
    name = event['name']
    # date voi olla string tai datetime
    date_value = event.get('date')
    if hasattr(date_value, 'strftime'):
        date_str = date_value.strftime('%-d.%m.%Y')
    elif isinstance(date_value, str) and date_value:
        try:
            from datetime import datetime
            date_str = datetime.fromisoformat(date_value).strftime('%-d.%m.%Y')
        except Exception:
            date_str = date_value
    else:
        date_str = ''
    reg = event.get('registered', 0)
    cap = event.get('capacity', 0)
    message = f"Nimenhuuto-eventtiin “{name} {date_str}” voi nyt ilmoittautua! Ilmoittautuneita: {reg}/{cap}"
    # Lähetetään viesti sekä käyttäjälle että kanavalle
    send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, message)
    send_telegram_message(TELEGRAM_TOKEN, TELEGRAM_CHANNEL_ID, message)
