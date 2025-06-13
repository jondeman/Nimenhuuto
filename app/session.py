import requests
from bs4 import BeautifulSoup
from config import BASE_URL, EVENTS_PATH, NIMENHUUTO_USER, NIMENHUUTO_PASS

def create_session() -> requests.Session:
    """
    Logs into nimenhuuto.com and returns an authenticated session.
    """

    session = requests.Session()
    # Yritetään kiertää consent-popup asettamalla eväste
    session.cookies.set("fcconsent", "1", domain="vantaanreservilaiset.nimenhuuto.com")
    # Hae CSRF-token events-sivulta
    csrf_url = BASE_URL + EVENTS_PATH
    resp = session.get(csrf_url)
    resp.raise_for_status()
    # DEBUG: tallenna sivun HTML
    with open("debug_events_page.html", "w", encoding="utf-8") as f:
        f.write(resp.text)

    soup = BeautifulSoup(resp.text, 'html.parser')
    token_input = soup.find('input', attrs={'name': 'authenticity_token'})
    csrf_token = token_input['value'] if token_input else None

    # POST lomakkeen actioniin /sessions
    login_url = BASE_URL + "/sessions"
    payload = {
        'login_name': NIMENHUUTO_USER,
        'password': NIMENHUUTO_PASS,
        'login_redirect_url': BASE_URL + EVENTS_PATH
    }
    if csrf_token:
        payload['authenticity_token'] = csrf_token

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
        'Referer': csrf_url
    }
    post_resp = session.post(login_url, data=payload, headers=headers)
    with open("debug_login_response.html", "w", encoding="utf-8") as f:
        f.write(post_resp.text)
    post_resp.raise_for_status()

    # Simple check for successful login
    if "Kirjaudu ulos" not in post_resp.text:
        raise RuntimeError("Login failed: check credentials")

    return session

