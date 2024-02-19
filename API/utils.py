import jwt
import os
from API import db
from API.models import BarberShop, Employee, BarbersAppToken
from flask import request, jsonify, render_template
from functools import wraps
import datetime
from flask_mail import Message
from API import mail
import requests


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
            return jsonify({"message": "Expired Session! Login Again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid Token. Please Login Again"}), 401
        return f(current_user, *args, **kwargs)
    return decorated


def employee_login_required(func):
    @wraps(func)
    def decorated(*args, **kwargs):
        token = None
        api_key = None
        if "X-API-KEY" in request.headers:
            api_key = request.headers["X-API-KEY"]

        if not api_key:
            return jsonify({"message": "API KEY is missing"}), 403

        if api_key != os.environ.get("API_KEY"):
            return jsonify({"message": "Invalid API KEY"}), 403

        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]
        if not token:
            return jsonify({"message": "Token is missing"}), 401
        try:
            data = jwt.decode(token, os.environ.get('SECRET'), algorithms=["HS256"])
            current_user = Employee.query.filter_by(public_id=data["public_id"]).first()
        except jwt.ExpiredSignatureError:
            return jsonify({"message": "Expired Session! Login Again"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"message": "Invalid Token. Please Login Again"}), 401
        return func(current_user, *args, **kwargs)

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


def send_employee_created_email(recipient, name, url, shop_name):
    """
        Send email to employee after they are created by owner.
        The email contains the signup url that they can use to set up their password
        :param recipient: Employee email address
        :param name: Employee first name
        :param url: Employee signup url
        :param shop_name: Name of the Barber shop the employee belongs
        :return: None
    """
    message = Message(
        f"{shop_name.upper()} sign up.",
        sender="communication@mykinyozi.com",
        recipients=[recipient]
    )
    message.html = render_template("create_employee_email.html", name=name, url=url, shop_name=shop_name)
    mail.send(message)


def fetch_token_from_mobile_app():
    """
        Fetch the authentication token from the mobile app backend
        :return: jwt token
    """
    url = r"https://app.mykinyozi.com/api/auth/login"
    data = {
        "email": os.environ.get("KINYOZI_MOBILE_EMAIL"),
        "password": os.environ.get("KINYOZI_MOBILE_PASSWORD")
    }
    response = requests.post(url=url, json=data)
    token = response.json().get("token")
    return token


def auth_mobile_app():
    """
        Authentication to access the data from the app
        :return: JWT Token
    """

    bearer_token = BarbersAppToken.query.filter_by(name="bearer_token").first()
    if not bearer_token:
        # If no token, authenticate the app and save the token to db
        token = fetch_token_from_mobile_app()
        save_token = BarbersAppToken(name="bearer_token", token=token)
        db.session.add(save_token)
        db.session.commit()
        return token
    else:
        # Check if the token is expired, if expired/invalid, load new one
        try:
            decoded_token = jwt.decode(
                bearer_token.token,
                os.environ.get("JWT_SECRET"),
                algorithms=["HS256"],
                options={"verify_signature": False}
            )
            current_timestamp = datetime.datetime.utcnow()
            token_expiry = decoded_token.get('exp')
            # Generate new token if previous one is expired.
            if current_timestamp > datetime.datetime.utcfromtimestamp(token_expiry):
                token = fetch_token_from_mobile_app()
                bearer_token.token = token
                db.session.commit()
                return token
        except jwt.exceptions.InvalidTokenError:
            token = fetch_token_from_mobile_app()
            bearer_token.token = token
            db.session.commit()
            return token
    return bearer_token.token
