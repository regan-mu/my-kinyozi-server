import datetime
from flask import Blueprint, request, jsonify
from API import db
from API.models import Inventory, BarberShop
from ..utils import shop_login_required, send_low_inventory_email
from ..serializer import serialize_inventory

inventory = Blueprint("inventory", __name__)


@inventory.route("/API/inventory/create/<string:public_id>", methods=["POST"])
@shop_login_required
def add_inventory(current_user, public_id):
    """
        Create new inventory
        :param current_user: Currently logged-in user
        :param public_id: public_id for the barbershop
        :return: 401, 201
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permission to perform this action")), 401

    data = request.get_json()
    new_inventory = Inventory(
        product_name=data["productName"].strip().title(),
        product_level=data["productLevel"],
        modified_at=datetime.datetime.utcnow(),
        shop_id=current_user.id
    )
    db.session.add(new_inventory)
    db.session.commit()
    return jsonify(dict(message="Inventory has been Recorded")), 201


@inventory.route("/API/inventory/update/<int:inventory_id>", methods=["PUT"])
def update_inventory(inventory_id):
    """
        Update inventory
        :param inventory_id:
        :return: 404, 500, 200
    """
    inventory_record = Inventory.query.filter_by(id=inventory_id).first()
    if not inventory_record:
        return jsonify(dict(message="Record not found")), 404

    data = request.get_json()

    if data["productLevel"] <= 2 and inventory_record.product_level > 2:
        shop_email = inventory_record.shop.email
        product_name = inventory_record.product_name
        shop_name = inventory_record.shop.shop_name
        try:
            send_low_inventory_email(
                recipient=shop_email,
                inventory_name=product_name,
                shop_name=shop_name,
                level=str(data["productLevel"])
            )
        except:
            return jsonify(dict(message="An error occurred. Please try again")), 500

    inventory_record.product_level = data["productLevel"]
    inventory_record.modified_at = datetime.datetime.utcnow()
    db.session.commit()

    return jsonify(dict(message="Record updated successfully")), 200


@inventory.route("/API/inventory/fetch/<string:public_id>", methods=["GET"])
def fetch_all_inventory(public_id):
    """
        Fetch all inventory associated to the barbershop
        :param public_id: public_id of the shop
        :return:
    """
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    if not shop:
        return jsonify(dict(message="Barber shop not found")), 404

    all_inventory = []
    for inventory_data in shop.inventory:
        all_inventory.append(serialize_inventory(inventory_data))
    return jsonify(dict(inventory=all_inventory))


@inventory.route("/API/inventory/delete/<int:inventory_id>", methods=["DELETE"])
def delete_inventory(inventory_id):
    """
        Delete inventory item
        :param inventory_id: id of inventory to be deleted
        :return:
    """
    record = Inventory.query.filter_by(id=inventory_id).first()
    if not record:
        return jsonify(dict(message="Inventory Item not found")), 404

    db.session.delete(record)
    db.session.commit()
    return jsonify(dict(message="Item deleted successfully")), 200


@inventory.route("/API/inventory/replenish/<int:inventory_id>", methods=["PUT"])
def replenish_inventory(inventory_id):
    """
        Replenish the inventory item to normal levels
        :param inventory_id: Inventory item ID
        :return: 400, 200
    """
    inventory_record = Inventory.query.filter_by(id=inventory_id).first()
    if not inventory_record:
        return jsonify(dict(message="Record not found")), 404

    inventory_record.product_level = 3
    inventory_record.modified_at = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify(dict(message="Record replenished successfully")), 200
