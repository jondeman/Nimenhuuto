# File: app/state.py

import os
import json
from config import SEEN_EVENTS_FILE

BASE_EVENTS_FILE = "base_events.json"


def load_base_events(filename: str = BASE_EVENTS_FILE) -> dict:
    """
    Lataa baseline-tiedoston ja palauttaa dict {id: status}.
    """
    if not os.path.exists(filename):
        return {}
    if os.path.getsize(filename) == 0:
        return {}
    import logging
    run_logger = logging.getLogger("run")
    with open(filename, 'r', encoding='utf-8') as f:
        events = json.load(f)
    result = {}
    for ev in events:
        if isinstance(ev, dict) and 'id' in ev:
            result[ev['id']] = ev
        else:
            run_logger.warning(f"Virheellinen event base-tiedostossa (load_base_events): tyyppi={type(ev)} sisältö={ev}")
    return result


def save_base_events(events: list, filename: str = BASE_EVENTS_FILE):
    """
    Tallentaa listan event-diktioita (joissa 'id' ja 'status') JSON-tiedostoon.
    Tallennetaan vain dict-tyyppiset eventit, muut ohitetaan ja kirjataan varoitus.
    """
    import logging
    run_logger = logging.getLogger("run")
    cleaned_events = []
    for ev in events:
        if isinstance(ev, dict):
            cleaned_events.append(ev)
        else:
            run_logger.warning(f"Yritettiin tallentaa virheellinen event base_events.json-tiedostoon: tyyppi={type(ev)} sisältö={ev}")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_events, f, ensure_ascii=False, indent=2)


def load_seen_events() -> set:
    """
    Lataa JSON-tiedostosta ne event-ID:t, joista on jo lähetetty notifikaatio.
    """
    if not os.path.exists(SEEN_EVENTS_FILE):
        return set()
    with open(SEEN_EVENTS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return set(data)


def save_seen_events(seen: set):
    """
    Tallentaa seen-ID-setin JSON-tiedostoon.
    """
    with open(SEEN_EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(seen), f, ensure_ascii=False, indent=2)