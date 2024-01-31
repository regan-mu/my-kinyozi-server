from flask import Blueprint, request, jsonify
from API.models import Service, BarberShop
from API import db, bcrypt
import datetime
from ..utils import shop_login_required, verify_api_key
from ..serializer import serialize_services

services = Blueprint('services', __name__)


@services.route("/API/services/<string:public_id>/create-services", methods=["POST"])
@shop_login_required
def add_services(current_user, public_id):
    """
        Add services to the barbershop
        :param public_id: Barbershop's public_id
        :param current_user: Current logged-in barbershop owner
        :return: 404, 201
    """
    # NOTE: Avoid adding services that are already in created.
    data = request.get_json()
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permissions to access this resource")), 401
    print(data)
    if data["serviceName"].strip().lower() not in [service.service.lower() for service in current_user.services]:
        new_service = Service(
            service=data["serviceName"].strip().title(),
            charges=data["chargeAmount"],
            description=data["serviceDescription"].strip().title(),
            modified_at=datetime.datetime.utcnow(),
            shop_id=current_user.id
        )
        db.session.add(new_service)
        db.session.commit()
        return jsonify(dict(message="Service has been added successfully")), 201
    else:
        return jsonify(dict(message="This service already exists")), 401


@services.route("/API/service/update/<int:service_id>", methods=["PUT"])
@shop_login_required
def update_service(current_user, service_id):
    """
        Edit service info like charges or service name
        :param service_id: id of the service you are editing
        :param current_user: Logged in barbershop owner
        :return: 401, 404, 200
    """

    service_info = Service.query.filter_by(id=service_id).first()
    if not service_info:
        return jsonify(dict(message="This service doesn't exist")), 404

    if service_id not in [service.id for service in current_user.services]:
        return jsonify(dict(message="You do not have permissions to access this resource")), 401

    data = request.get_json()
    service_info.service = data["serviceName"].strip().title()
    service_info.charges = data["chargeAmount"]
    service_info.description = data["serviceDescription"].strip().title()
    service_info.modified_at = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify(dict(message="Service updated successfully")), 200


@services.route("/API/service/delete/<int:service_id>", methods=["DELETE"])
@shop_login_required
def delete_service(current_user, service_id):
    """
        Delete a service from a shop
        :param current_user: Logged in barbershop owner
        :param service_id: ID of service to be deleted
        :return: 404, 401, 200
    """

    service = Service.query.filter_by(id=service_id).first()
    if not service:
        return jsonify(dict(message="No service to delete")), 404

    if service_id not in [service.id for service in current_user.services]:
        return jsonify(dict(message="You do not have permissions to access this resource")), 401
    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect Password")), 401

    db.session.delete(service)
    db.session.commit()
    return jsonify(dict(message="Service deleted successfully")), 200


@services.route("/API/services/all/<string:public_id>", methods=["GET"])
@verify_api_key
def fetch_all_services(public_id):
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    all_services = []
    for service in shop.services.order_by(Service.modified_at.desc()):
        all_services.append(serialize_services(service))
    return jsonify(dict(services=all_services))
