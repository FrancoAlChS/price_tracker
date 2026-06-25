import os
from dotenv import load_dotenv

load_dotenv()

preview_telegram_token = os.getenv("TELEGRAM_TOKEN")
preview_telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")

if not preview_telegram_token or not preview_telegram_chat_id:
    raise ValueError("❌ ERROR: Faltan configurar las variables de entorno en el archivo .env")



TELEGRAM_TOKEN = str(preview_telegram_token)
TELEGRAM_CHAT_ID = str(preview_telegram_chat_id)
MINIMUN_DISCOUNT = 50