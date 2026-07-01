from flask import Blueprint, request, jsonify
from src.services.telegram_service import TelegramService

telegram_controller = Blueprint('telegram_config', __name__)

telegram_service = TelegramService()

@telegram_controller.route('/')
def get_config():
    response = telegram_service.get()
    return jsonify(response)

@telegram_controller.route('', methods=["POST"])
def create_or_update_config():
    body = request.get_json()
    response = telegram_service.create_or_update(body)
    return jsonify(response)
