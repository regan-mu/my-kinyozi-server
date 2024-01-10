from flask import Blueprint, request, jsonify
from API import db
from API.models import Equipment
from ..utils import shop_login_required
from ..serializer import serialize_equipment

equipment_blueprint = Blueprint("equipment", __name__, url_prefix="/API/equipments")


@equipment_blueprint.route("/create/<string:public_id>", methods=["POST"])
@shop_login_required
def new_equipment(current_user, public_id):
    """
        Record new equipment
        :param current_user: Currently logged-in user
        :param public_id: Barbershop public ID
        :return: 401, 201
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not allowed")), 401

    data = request.get_json()
    equipment = Equipment(
        equipment_name=data["name"].strip().title(),
        description=data["description"].strip().capitalize(),
        bought_on=data["buyDate"],
        price=data["price"],
        shop_id=current_user.id,
    )
    db.session.add(equipment)
    db.session.commit()

    return jsonify(dict(message="Equipment Recorded")), 201


@equipment_blueprint.route("/fetch/all/<string:public_id>", methods=["GET"])
@shop_login_required
def fetch_all_equipments(current_user, public_id):
    """
        Fetch all equipments for the barbershop with the public_id provided
        :param current_user: currently logged-in user
        :param public_id: Barbershop public_ID
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not allowed")), 401
    all_equipments = []
    for equipment in current_user.equipments:
        all_equipments.append(serialize_equipment(equipment))
    return jsonify(dict(equipments=all_equipments)), 200


@equipment_blueprint.route("/faulty/<int:equipment_id>", methods=["PUT"])
@shop_login_required
def mark_as_faulty(current_user, equipment_id):
    """
        Mark an equipment as faulty
        :param current_user: Logged-in user
        :param equipment_id: Equipment ID
        :return: 404, 401, 200
    """
    equipment = Equipment.query.filter_by(id=equipment_id).first()
    if not equipment:
        return jsonify(message="Not Found"), 404
    if current_user.public_id != equipment.shop.public_id:
        return jsonify(dict(message="Not allowed")), 401

    equipment.faulty = True
    db.session.commit()
    return jsonify(dict(message="Equipment marked as faulty")), 200


@equipment_blueprint.route("/remove/<int:equipment_id>", methods=["DELETE"])
@shop_login_required
def remove_equipment(current_user, equipment_id):
    """
        Remove equipment
        :param current_user: Logged-in user
        :param equipment_id: Equipment ID
        :return: 404, 401, 200
    """
    equipment = Equipment.query.filter_by(id=equipment_id).first()
    if not equipment:
        return jsonify(message="Not Found"), 404
    if current_user.public_id != equipment.shop.public_id:
        return jsonify(dict(message="Not allowed")), 401

    db.session.delete(equipment)
    db.session.commit()
    return jsonify(dict(message="Deleted")), 200
