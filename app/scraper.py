import re
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from config import BASE_URL, EVENTS_PATH


def parse_event_div(div) -> dict:
    """
    Parse a single event block into a dict.
    """
    # Extract link and ID
    a = div.find('a', href=True)
    href = a['href']
    event_id = href.split('/')[-1]
    name = a.get_text(strip=True)

    # Date parsing: try <time>, else event-month + event-detailed-date
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

    # Registrations text
    text = div.get_text(separator=' ')
    m = re.search(r'Ilmoittautumiset:\s*(\d+)\s*/\s*(\d+)', text)
    if m:
        registered = int(m.group(1))
        capacity = int(m.group(2))
    else:
        registered = 0
        capacity = 0

    # Luotettava ilmoittautumisstatuslogiikka
    enroll_buttons_div = div.find('div', class_='enroll-buttons')
    open_for_registration = False  # Oletus: kiinni
    if enroll_buttons_div:
        enroll_btn = enroll_buttons_div.select_one('a.btn-in')  # CSS selector, luokkajärjestys ei väliä
        print('ENROLL BUTTON:', enroll_btn)  # DEBUG
        if enroll_btn:
            title = enroll_btn.get('title', '')
            data_disabled = enroll_btn.get('data-disabled', 'false')
            print(f'TITLE: {title}, DATA_DISABLED: {data_disabled}')  # DEBUG
            if (
                'Tapahtumaan ei pysty ilmoittautumaan' not in title
                and data_disabled != 'true'
            ):
                open_for_registration = True
        else:
            print('No btn-in button found in:', enroll_buttons_div)  # DEBUG
    else:
        print('No enroll-buttons div found in event:', div)  # DEBUG

    return {
        'id': event_id,
        'name': name,
        'date': date,
        'registered': registered,
        'capacity': capacity,
        'open': open_for_registration,
    }


def get_events(session):
    """
    Crawl event pages until events older than 60 days from first event.
    Returns list of event dicts.
    """
    events = []
    page = 1
    first_date = None
    cutoff_days = 90

    while True:
        url = f"{BASE_URL}{EVENTS_PATH}?page={page}"
        resp = session.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        divs = soup.find_all('div', class_='event-detailed-container')
        if not divs:
            break

        for div in divs:
            ev = parse_event_div(div)
            if not first_date and ev['date']:
                first_date = ev['date']
            # Stop crawling if beyond cutoff
            if first_date and ev['date']:
                from datetime import datetime
                d1 = datetime.fromisoformat(ev['date']).date() if isinstance(ev['date'], str) else ev['date']
                d2 = datetime.fromisoformat(first_date).date() if isinstance(first_date, str) else first_date
                if (d1 - d2).days > cutoff_days:
                    return events
            events.append(ev)

        # Check for "Seuraava" link
        next_link = soup.find('a', rel='next')
        if not next_link:
            break
        page += 1

    return events
