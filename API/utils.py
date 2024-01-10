import jwt
import os
from API.models import BarberShop
from flask import request, jsonify, render_template
from functools import wraps
import datetime
from flask_mail import Message
from API import mail


def verify_token(token):
    """
    Verifies the generated token
    :param token: Generated token
    :return: The BarberShop object
    """
    try:
        data = jwt.decode(token, os.environ.get('SECRET'), algorithms=["HS256"])
        shop = BarberShop.query.filter_by(public_id=data["public_id"]).first()
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    else:
        return shop


def shop_login_required(f):
    """
        Check is logged in
        :param f: route fuction
        :return:
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        api_key = None
        if "X-API-KEY" in request.headers:
            api_key = request.headers["X-API-KEY"]

        if not api_key:
            return jsonify({"message": "API KEY is missing"}), 401

        if api_key != os.environ.get("API_KEY"):
            return jsonify({"message": "Invalid API KEY"}), 401

        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        try:
            data = jwt.decode(token, os.environ.get('SECRET'), algorithms=["HS256"])
            current_user = BarberShop.query.filter_by(public_id=data["public_id"]).first()
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Expired token"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid token"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def verify_api_key(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        api_key = None
        if "X-API-KEY" in request.headers:
            api_key = request.headers["X-API-KEY"]

        if not api_key:
            return jsonify({"message": "API KEY is missing"}), 401

        if api_key != os.environ.get("API_KEY"):
            return jsonify({"message": "Invalid API KEY"}), 401
        return func(*args, **kwargs)
    return decorated


def send_password_reset_email(recipient, reset_url, name):
    """
        Send password reset email
        :param recipient: Recipient Email
        :param reset_url: Reset Link
        :param name: Barbershop name
        :return: None
    """
    message = Message("My Kinyozi App password reset", sender="communication@mykinyozi.com", recipients=[recipient])
    message.html = render_template("reset.html", name=name, url=reset_url)
    mail.send(message)


def generate_reset_token(public_id):
    """
    Generates JWT token for password reset
    :param public_id: Public id of the user resetting their password
    :return: signed token
    """
    reset_token = jwt.encode(
        {
            "public_id": public_id,
            "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        },
        os.environ.get('SECRET'),
        algorithm="HS256"
    )
    return reset_token


def send_low_inventory_email(recipient, inventory_name, shop_name, level):
    """
        Send email to owner when a product is marked as running low.
        :param recipient: Owner email.
        :param inventory_name: inventory running low.
        :param shop_name: name of the barbershop.
        :param level: Inventory level
        :return: None
    """
    levels = {
        "1": "CRITICALLY LOW",
        "2": "LOW",
        "3": "NORMAL"
    }

    message = Message(
        f"KINYOZI APP ALERT: PRODUCT RUNNING {levels[level]}",
        sender="communication@mykinyozi.com",
        recipients=[recipient]
    )
    message.html = render_template("inventory.html", name=shop_name, inventory=inventory_name, level=levels[level])
    mail.send(message)


def test_html():
    message = Message(
        f"KINYOZI APP ALERT: PRODUCT RUNNING TEST",
        sender="communication@mykinyozi.com",
        recipients=["regansomi@gmail.com"]
    )
    message.body = "test"
    message.html = render_template("reset.html", name="Regan")
    mail.send(message)
