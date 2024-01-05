import datetime
from flask import Blueprint, request, jsonify
from API import db
from API.models import Sale, BarberShop
from ..utils import shop_login_required
from ..serializer import serialize_sales

sales = Blueprint("sales", __name__)


@sales.route("/API/sales/create/<string:public_id>", methods=["POST"])
@shop_login_required
def record_sale(current_user, public_id):
    """
        Record a new sale
        :param current_user: Currently logged-in user
        :param public_id: Barbershop public_id
        :return: 404, 401, 200
    """
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    if not shop:
        return jsonify(dict(message="Barbershop doesn't exist")), 404

    if current_user.public_id != public_id:  # Add an or to check if an employee belongs to the shop
        return jsonify(dict(message="You do not have permission to perform this action")), 401

    data = request.get_json()
    new_sale = Sale(
        payment_method=data["paymentMethod"].strip().title(),
        description=data["paymentDescription"].strip().title(),
        year=datetime.datetime.utcnow().year,
        month=datetime.datetime.utcnow().month,
        service_id=data["service"],
    )
    db.session.add(new_sale)
    db.session.commit()
    return jsonify(dict(message="Sale has been recorded successfully.")), 201


@sales.route("/API/sales/fetch/<string:public_id>/<string:month>/<string:year>", methods=["GET"])
@shop_login_required
def fetch_sales(current_user, public_id, month, year):
    """
        Fetch all sales
        :param current_user: Currently logged-in user
        :param public_id: Barbershop public_id
        :param month: Month for which to fetch the sales for. if 'all' fetch data for all months
        :param year: Year for which to fetch the sales for. if 'all' fetch data for all years
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permission to perform this action")), 401

    shop_services = current_user.services
    all_shop_sales = []
    for service in shop_services:
        if year != "all" and month == "all":
            service_sales = service.sales.filter_by(year=int(year)).order_by(Sale.date_created.desc())
        elif year != "all" and month != "all":
            service_sales = service.sales.filter_by(year=int(year), month=int(month)).order_by(Sale.date_created.desc())
        else:
            service_sales = service.sales.order_by(Sale.date_created.desc())
        for sale in service_sales:
            sale_data = serialize_sales(sale)
            sale_data["amount"] = service.charges
            all_shop_sales.append(sale_data)

    return jsonify(dict(sales=all_shop_sales)), 200


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

    db.session.delete(sale)
    db.session.commit()
    return jsonify(dict(message="Sale deleted successfully")), 200
