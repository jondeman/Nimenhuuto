from notifier import notify_event_open


def test_notify_event_open():
    test_event = {
        'id': 'TEST123',
        'name': 'Testitapahtuma',
        'date': '2025-06-20',
        'registered': 5,
        'capacity': 10,
        'status': 'OPEN'
    }
    print("Kutsutaan notify_event_open testitapahtumalla...")
    notify_event_open(test_event)
    print("Jos viesti näkyy vastaanottajalla, testi onnistui!")

if __name__ == "__main__":
    test_notify_event_open()
