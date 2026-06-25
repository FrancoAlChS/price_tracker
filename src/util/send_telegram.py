import requests
from src.config.enviroments import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID

def send_telegram(mensaje: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload: dict[str, str] = {"chat_id": TELEGRAM_CHAT_ID, "text": mensaje}
    try:
        resp = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  Error Telegram: {e}")
        return False
