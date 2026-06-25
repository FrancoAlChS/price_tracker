from flask import Blueprint, request, jsonify
from src.services.store_service import StoreService

store_controller = Blueprint('stores', __name__)

product_service = StoreService()

@store_controller.route('/')
def list_stores():
    response = product_service.list()
    return jsonify(response)

@store_controller.route("/", methods=["POST"])
def create_store():
    body = request.get_json()
    response = product_service.create(body)

    return jsonify(response)

@store_controller.route("/<int:id>", methods=["PUT"])
def update_store(id:int):
    body = request.get_json()
    response = product_service.update(id, body)

    return jsonify(response)

@store_controller.route("/<int:id>", methods=["DELETE"])
def delete_store(id:int):
    response = product_service.delete(id)

    return jsonify(response)

