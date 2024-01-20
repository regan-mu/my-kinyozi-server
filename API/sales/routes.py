import datetime
from flask import Blueprint, request, jsonify
from API import db, bcrypt
from API.models import Sale, BarberShop
from ..utils import shop_login_required, verify_api_key
from ..serializer import serialize_sales

sales = Blueprint("sales", __name__)


@sales.route("/API/sales/create/<string:public_id>", methods=["POST"])
@verify_api_key
def record_sale(public_id):
    """
        Record a new sale
        :param public_id: Barbershop public_id
        :return: 404, 401, 200
    """
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    if not shop:
        return jsonify(dict(message="Barbershop doesn't exist")), 404

    data = request.get_json()
    new_sale = Sale(
        payment_method=data["paymentMethod"].strip().title(),
        description=data["paymentDescription"].strip().title(),
        year=datetime.datetime.utcnow().year,
        month=datetime.datetime.utcnow().month,
        service_id=data["service"],
        shop_id=shop.id
    )
    db.session.add(new_sale)
    db.session.commit()
    return jsonify(dict(message="Sale has been recorded successfully.")), 201


@sales.route("/API/sales/fetch/<string:public_id>", methods=["GET"])
@shop_login_required
def fetch_sales(current_user, public_id):
    """
        Fetch all sales
        :param current_user: Currently logged-in user
        :param public_id: Barbershop public_id
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permission to perform this action")), 401

    shop_services = current_user.services
    all_shop_sales = []
    all_years = [sale.year for sale in Sale.query.all()]
    unique_years = list(set(all_years))
    all_services = []
    for service in shop_services:
        service_sales = service.sales.order_by(Sale.date_created.desc())
        all_services.append({"id": service.id, "service": service.service})
        for sale in service_sales:
            sale_data = serialize_sales(sale)
            sale_data["amount"] = service.charges
            sale_data["service"] = service.service
            all_shop_sales.append(sale_data)

    return jsonify(dict(sales=all_shop_sales, years=unique_years, services=all_services)), 200


@sales.route("/API/sales/delete/<int:sale_id>", methods=["DELETE"])
@shop_login_required
def delete_sale(current_user, sale_id):
    """
        Delete Sale record
        :param current_user: Logged-in user
        :param sale_id: ID of the sale to be deleted
        :return: 404, 401, 200
    """
    sale = Sale.query.filter_by(id=sale_id).first()
    if not sale:
        return jsonify(dict(message="Sale not Found")), 404
    if current_user.public_id != sale.service.shop.public_id:
        return jsonify(dict(message="You do not have permission to perform this action")), 401

    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect password")), 401

    db.session.delete(sale)
    db.session.commit()
    return jsonify(dict(message="Sale deleted successfully")), 200
