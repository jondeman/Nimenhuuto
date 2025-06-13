# File: app/main.py

import os
from pathlib import Path
import logging

# Määrittele tilakansio (STATE_DIR) ympäristömuuttujasta tai oletus.
STATE_DIR = Path(os.getenv("STATE_DIR", "."))
STATE_DIR.mkdir(exist_ok=True)   # Varmistaa, että kansio on olemassa

# Lokitiedosto aina samaan kansioon
LOG_FILE = STATE_DIR / "app_run.log"

# Ota käyttöön tiedostologgaus, jos ei vielä käytössä
logger = logging.getLogger()
logger.setLevel(logging.INFO)
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(LOG_FILE) for h in logger.handlers):
    fh = logging.FileHandler(LOG_FILE, mode="a", encoding="utf-8")
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

from session import create_session
from scraper import get_events
from state import load_base_events, save_base_events
from notifier import notify_event_open


def main():
    # Käytä root loggeria, joka kirjoittaa tiedostoon STATE_DIR/app_run.log
    logger.info("Ohjelma käynnistyi")

    # 1) Ladataan baseline (id -> event-dict)
    base = load_base_events()  # base: dict[id] = event-dict
    logger.info(f"Baselinessa {len(base)} eventtiä")

    # 2) Kirjautuminen ja tapahtumien haku
    try:
        session = create_session()
        events = get_events(session)
        logger.info(f"Noudettu {len(events)} tapahtumaa")
    except Exception as e:
        logger.error(f"Virhe tapahtumien haussa: {e}")
        raise

    updated = {}
    status_changed = 0
    for ev in events:
        event_id = ev['id']
        old_event = base.get(event_id)
        # Jos event on uusi, lisää baselineen
        if not old_event:
            logger.info(f"Uusi eventti: {event_id} ({ev['name']}) lisätään baselineen")
            updated[event_id] = ev
            continue
        if not isinstance(old_event, dict):
            logger.warning(f"Virheellinen event base-tiedostossa: event_id={event_id}, old_event={old_event}, type={type(old_event)}")
            continue
            updated[event_id] = ev
            continue
        # Lähetä notifikaatio kun open muuttuu False -> True TAI registered 0 -> X (X>0)
        old_open = old_event.get('open', False)
        new_open = ev.get('open', False)
        old_registered = old_event.get('registered', 0)
        new_registered = ev['registered']
        if (not old_open and new_open) or (old_registered == 0 and new_registered > 0):
            status_changed += 1
            msg = f"Nimenhuuto-eventtiin “{ev['name']} {ev['date']}” voi nyt ilmoittautua!"
            logger.info(f"Notifikaatio: {event_id} open False→True tai registered 0→{new_registered}, viesti lähetetään: {msg}")
            try:
                notify_event_open(ev)
                logger.info(f"Viestin lähetys onnistui eventille {event_id}")
            except Exception as e:
                logger.error(f"Notifikaation lähetys epäonnistui ({event_id}): {e}")
        updated[event_id] = ev

    # Lisää baselineen mahdolliset vanhat eventit, joita ei enää löydy (ei häviä tietoa)
    for old_id, old_ev in base.items():
        if old_id not in updated:
            updated[old_id] = old_ev

    # 4) Poista menneet eventit (date < tänään)
    from datetime import datetime, date
    filtered_events = []
    now = date.today()
    removed_count = 0
    for ev in updated.values():
        # Poista virheelliset eventit (ei dict)
        if not isinstance(ev, dict):
            event_id = None
            if hasattr(ev, 'get'):
                event_id = ev.get('event_id', 'tuntematon')
            logger.warning(f"Virheellinen event base-tiedostossa: event_id={event_id}, type={type(ev)}")
            continue
        ev_date = None
        if isinstance(ev.get('date'), str):
            try:
                ev_date = datetime.fromisoformat(ev['date']).date()
            except Exception:
                ev_date = None
        elif hasattr(ev.get('date'), 'date'):
            ev_date = ev['date'].date()
        if ev_date is not None and ev_date < now:
            removed_count += 1
            continue
        filtered_events.append(ev)

    if filtered_events:
        # Laske lisätyt uudet eventit
        old_ids = set(base.keys())
        new_ids = set(ev['id'] for ev in filtered_events if isinstance(ev, dict) and 'id' in ev)
        added_event_ids = new_ids - old_ids
        added_count = len(added_event_ids)
        save_base_events(filtered_events)
        logger.info(f"Tallennettu päivitetty baseline base_events.json. Status-muuttuneita eventtejä: {status_changed}. Poistettu {removed_count} vanhaa eventtiä. Lisättyjä uusia eventtejä: {added_count}.")
        if status_changed > 0:
            logger.info(f"Lähetettyjä notifikaatioita: {status_changed} kpl.")
        else:
            logger.info("Notifikaatioita ei lähetetty yhdellekään eventille.")
    else:
        logger.warning("Ei tallennettu base_events.json:ia, koska uusia eventtejä ei löytynyt.")

if __name__ == '__main__':
    main()
