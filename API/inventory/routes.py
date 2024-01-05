import datetime
from flask import Blueprint, request, jsonify
from API import db
from API.models import Inventory
from ..utils import shop_login_required
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
        product_level=data["productLevel"].strip().title(),
        modified_at=datetime.datetime.utcnow(),
        shop_id=current_user.id
    )
    db.session.add(new_inventory)
    db.session.commit()
    return jsonify(dict(message="Inventory has been Recorded")), 201

# Update
# Fetch
# Delete
