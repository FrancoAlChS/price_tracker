from flask import Blueprint, request, jsonify
from src.services.link_service import LinkService

link_controller = Blueprint('links', __name__)

link_service = LinkService()

@link_controller.route('/')
def list_links():
    response = link_service.list()
    return jsonify(response)

@link_controller.route("/", methods=["POST"])
def create_link():
    body = request.get_json()
    response = link_service.create(body)

    return jsonify(response)

@link_controller.route("/<int:id>", methods=["PUT"])
def update_link(id:int):
    body = request.get_json()
    response = link_service.update(id, body)

    return jsonify(response)

@link_controller.route("/<int:id>", methods=["DELETE"])
def delete_link(id:int):
    response = link_service.delete(id)

    return jsonify(response)

