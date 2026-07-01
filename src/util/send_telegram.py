import requests


def send_telegram(mensaje: str, token: str, chat_id: str) -> bool:
    url: str = f"https://api.telegram.org/bot{token}/sendMessage"
    payload: dict[str, str] = {"chat_id": chat_id, "text": mensaje}
    try:
        resp: requests.Response = requests.post(url, json=payload, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"  Error Telegram: {e}")
        return False
