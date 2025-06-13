import json

BASE_EVENTS_PATH = "base_events.json"  # oikea polku projektin juuressa ajettuna

with open(BASE_EVENTS_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

fixed = {}

if isinstance(data, list):
    # Muutetaan lista dictiksi id:n perusteella
    for event in data:
        if isinstance(event, dict) and "id" in event:
            fixed[event["id"]] = event
        else:
            # Jos ei dict tai ei id:tä, ohitetaan
            continue
elif isinstance(data, dict):
    for event_id, event in data.items():
        if isinstance(event, dict):
            fixed[event_id] = event
        else:
            # Luo minimi-dict, johon tallennetaan alkuperäinen tila
            fixed[event_id] = {
                "id": event_id,
                "status": event,  # esim. "CLOSED" tai "OPEN"
                "name": "",
                "registered": 0,
                "date": None
            }
else:
    print("base_events.json on tuntemattomassa muodossa!")

with open(BASE_EVENTS_PATH, "w", encoding="utf-8") as f:
    json.dump(fixed, f, ensure_ascii=False, indent=2)

print("base_events.json korjattu!")

print("base_events.json korjattu!")