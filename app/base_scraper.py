# File: app/base_scraper.py

import json
import logging
import re
from datetime import datetime
from requests import Session
from bs4 import BeautifulSoup

from session import create_session
from config import BASE_URL, EVENTS_PATH

# Tiedosto, johon tallennetaan baseline-eventit
OUTPUT_FILE = "base_events.json"


def parse_event_div(div) -> dict:
    """
    Parsii yhden event-divin ja palauttaa dict:
    {
      'id': str,
      'name': str,
      'date': str (ISO),
      'registered': int,
      'capacity': int,
      'status': 'OPEN'|'CLOSED'
    }
    """
    # Linkistä event-id ja nimi
    a = div.find('a', href=True)
    href = a['href']
    event_id = href.rstrip("/").split("/")[-1]
    name = a.get_text(strip=True)

    # Päivämäärä: yritä ensin <time>, muuten event-month + event-detailed-date
    time_tag = div.find('time')
    if time_tag and time_tag.has_attr('datetime'):
        date = datetime.fromisoformat(time_tag['datetime']).date().isoformat()
    else:
        MONTH_MAP = {
            "TAMMI": 1, "HELMI": 2, "MAALIS": 3, "HUHTI": 4, "TOUKO": 5, "KESÄ": 6,
            "HEINÄ": 7, "ELO": 8, "SYYS": 9, "LOKA": 10, "MARRAS": 11, "JOULU": 12
        }
        month_div = div.find('div', class_='event-month')
        day_div = div.find('div', class_='event-detailed-date')
        if month_div and day_div:
            month_str = month_div.get_text(strip=True).upper()
            day_str = day_div.get_text(strip=True)
            month = MONTH_MAP.get(month_str)
            try:
                day = int(day_str)
            except ValueError:
                day = None
            year = datetime.now().year
            if month and day:
                # Jos tapahtuma on joulukuussa ja nyt on tammikuu, oletetaan viime vuosi
                now = datetime.now()
                if month == 12 and now.month == 1:
                    year -= 1
                date = f"{year}-{month:02d}-{day:02d}"
            else:
                date = None
        else:
            date = None

    # Ilmoittautumismäärä
    text = div.get_text(separator=" ")
    m = re.search(r'Ilmoittautumiset:\s*(\d+)\s*/\s*(\d+)', text)
    if m:
        registered = int(m.group(1))
        capacity = int(m.group(2))
    else:
        registered = 0
        capacity = 0

    status = 'OPEN' if registered > 0 else 'CLOSED'

    return {
        'id': event_id,
        'name': name,
        'date': date,
        'registered': registered,
        'capacity': capacity,
        'status': status
    }


def fetch_events(session: Session) -> list:
    """
    Käy läpi kaikki event-sivut kirjautuneella sessiolla ja palauttaa listan event-diktioita.
    """
    events = []
    page = 1

    while True:
        url = f"{BASE_URL}{EVENTS_PATH}?page={page}"
        resp = session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        divs = soup.find_all('div', class_='event-detailed-container')
        if not divs:
            break

        for div in divs:
            events.append(parse_event_div(div))

        next_link = soup.find('a', rel='next')
        if not next_link:
            break
        page += 1

    return events


def save_base_events(events: list, filename: str = OUTPUT_FILE):
    """
    Tallentaa listan event-diktioita JSON-tiedostoon.
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
    logging.info("Aloitetaan base-scraper: haetaan nykyiset eventit ja tallennetaan niiden tila")

    session = create_session()
    events = fetch_events(session)
    logging.info(f"Löytyi {len(events)} tapahtumaa")
    save_base_events(events)
    logging.info(f"Tallennettu tiedostoon {OUTPUT_FILE}")