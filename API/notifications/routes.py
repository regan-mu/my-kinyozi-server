from flask import Blueprint, request, jsonify
from API import db
from API.models import Notification, BarberShop
from ..utils import shop_login_required, verify_api_key
from ..serializer import serialize_notification

notifications_blueprint = Blueprint("notifications", __name__)


@notifications_blueprint.route("/API/notifications/create", methods=["POST"])
@verify_api_key
def create_notification():
    """
        Create New notification
        :return:400, 201
    """
    data = request.get_json()
    if not data["title"] or not data["message"] or not data["shopId"]:
        return jsonify(dict(message="Missing data")), 400

    notification = Notification(
        title=data["title"].strip().title(),
        message=data["message"].strip(),
        shop_id=data["shopId"]
    )
    db.session.add(notification)
    db.session.commit()

    return jsonify(dict(message="Notification Sent")), 201


@notifications_blueprint.route("/API/notifications/read/<int:notification_id>", methods=["PUT"])
@shop_login_required
def read_notification(current_user, notification_id):
    """
         Mark Notification as READ
        :param current_user: Currently logged-in user.
        :param notification_id: Notification ID
        :return: 404, 200
    """
    notification = Notification.query.filter_by(id=notification_id).first()
    if not notification:
        return jsonify(dict(message="Notification not FOUND")), 404

    if current_user.public_id != notification.shop.public_id:
        return jsonify(dict(message="Not Allowed")), 401

    notification.read = True
    db.session.commi()
    return jsonify(dict(message="Notification read")), 200


@notifications_blueprint.route("/API/notifications/fetch/all/<string:public_id>", methods=["GET"])
@shop_login_required
def fetch_all_notification(current_user, public_id):
    """
        Fetch all notifications for a
    :param current_user:
    :param public_id:
    :return: 404, 401, 200
    """
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    if not shop:
        return jsonify(dict(message="Barbershop doesn't exist")), 404

    if current_user.public_id != public_id:
        return jsonify(message="Not allowed"), 401

    all_notifications = []
    for notification in shop.notifications:
        all_notifications.append(serialize_notification(notification))

    return jsonify(dict(notifications=all_notifications)), 200


@notifications_blueprint.route("/API/notifications/fetch/<int:notification_id>", methods=["GET"])
@shop_login_required
def fetch_single_notification(current_user, notification_id):
    """
        Fetch a single notification
        :param current_user: Currently logged-in user.
        :param notification_id: Notification ID
        :return: 404, 200
    """
    notification = Notification.query.filter_by(id=notification_id).first()
    if not notification:
        return jsonify(dict(message="Not Found")), 404

    if notification.shop.public_id != current_user.public_id:
        return jsonify(dict(message="Not Allowed")), 401

    return jsonify(serialize_notification(notification))


@notifications_blueprint.route("/API/notifications/delete/<int:notification_id>", methods=["DELETE"])
@shop_login_required
def delete_single_notification(current_user, notification_id):
    """
        Delete a single notification
        :param current_user: Currently logged-in user.
        :param notification_id: Notification ID
        :return: 404, 200
    """
    notification = Notification.query.filter_by(id=notification_id).first()
    if not notification:
        return jsonify(dict(message="Not Found")), 404

    if notification.shop.public_id != current_user.public_id:
        return jsonify(dict(message="Not Allowed")), 401

    db.session.delete(notification)
    db.session.commit()
    return jsonify(dict(message="Delete Successful")), 200
