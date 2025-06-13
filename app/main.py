# File: app/main.py

import logging
from session import create_session
from scraper import get_events
from state import load_base_events, save_base_events
from notifier import notify_event_open


def main():
    # Loggeri tiedostoon ja konsoliin, ei root loggeria
    run_logger = logging.getLogger("run_logger")
    run_logger.setLevel(logging.INFO)
    run_logger.propagate = False  # estää tuplakirjauksen
    file_handler = logging.FileHandler("app_run.log", mode="a", encoding="utf-8")
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    run_logger.addHandler(file_handler)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
    run_logger.addHandler(stream_handler)

    run_logger.info("Ohjelma käynnistyi")

    # 1) Ladataan baseline (id -> event-dict)
    base = load_base_events()  # base: dict[id] = event-dict
    run_logger.info(f"Baselinessa {len(base)} eventtiä")

    # 2) Kirjautuminen ja tapahtumien haku
    try:
        session = create_session()
        events = get_events(session)
        run_logger.info(f"Noudettu {len(events)} tapahtumaa")
    except Exception as e:
        run_logger.error(f"Virhe tapahtumien haussa: {e}")
        raise

    updated = {}
    status_changed = 0
    for ev in events:
        event_id = ev['id']
        old_event = base.get(event_id)
        # Jos event on uusi, lisää baselineen
        if not old_event:
            run_logger.info(f"Uusi eventti: {event_id} ({ev['name']}) lisätään baselineen")
            updated[event_id] = ev
            continue
        if not isinstance(old_event, dict):
            run_logger.warning(f"Virheellinen event base-tiedostossa: event_id={event_id}, old_event={old_event}, type={type(old_event)}")
            continue
            updated[event_id] = ev
            continue
        # Lähetä notifikaatio VAIN kun registered muuttuu 0 -> X (X>0)
        old_registered = old_event.get('registered', 0)
        new_registered = ev['registered']
        if old_registered == 0 and new_registered > 0:
            status_changed += 1
            msg = f"Nimenhuuto-eventtiin “{ev['name']} {ev['date'].strftime('%-d.%m.%Y') if ev['date'] else ''}” voi nyt ilmoittautua!"
            run_logger.info(f"Notifikaatio: {event_id} registered 0→{new_registered}, viesti lähetetään: {msg}")
            try:
                notify_event_open(ev)
                run_logger.info(f"Viestin lähetys onnistui eventille {event_id}")
            except Exception as e:
                run_logger.error(f"Notifikaation lähetys epäonnistui ({event_id}): {e}")
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
            run_logger.warning(f"Virheellinen event base-tiedostossa: event_id={event_id}, type={type(ev)}")
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
        run_logger.info(f"Tallennettu päivitetty baseline base_events.json. Status-muuttuneita eventtejä: {status_changed}. Poistettu {removed_count} vanhaa eventtiä. Lisättyjä uusia eventtejä: {added_count}.")
        if status_changed > 0:
            run_logger.info(f"Lähetettyjä notifikaatioita: {status_changed} kpl.")
        else:
            run_logger.info("Notifikaatioita ei lähetetty yhdellekään eventille.")
    else:
        run_logger.warning("Ei tallennettu base_events.json:ia, koska uusia eventtejä ei löytynyt.")

if __name__ == '__main__':
    main()