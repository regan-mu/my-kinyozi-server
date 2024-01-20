from flask import Blueprint, request, jsonify
from API import db, bcrypt
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
    equipment_cost = 0
    faulty_equipment = 0
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not allowed")), 401
    all_equipments = []
    equipments_query = current_user.equipments.order_by(Equipment.bought_on)
    for equipment in equipments_query:
        equipment_cost += equipment.price
        if equipment.faulty:
            faulty_equipment += 1
        all_equipments.append(serialize_equipment(equipment))
    oldest_equipment = equipments_query[0].equipment_name
    newest_equipment = current_user.equipments.order_by(Equipment.bought_on.desc()).first()
    return jsonify(dict(
        equipments=all_equipments,
        stats={
            "cost": equipment_cost,
            "faulty": faulty_equipment,
            "oldest": oldest_equipment,
            "newest": newest_equipment.equipment_name
    }
    )), 200


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

    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect Password")), 401

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

    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect Password")), 401

    db.session.delete(equipment)
    db.session.commit()
    return jsonify(dict(message="Deleted")), 200
