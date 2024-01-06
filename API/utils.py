import jwt
import os
from API.models import BarberShop
from flask import request, jsonify
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
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
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


def send_password_reset_email(recipient, reset_url, name):
    """
        Send password reset email
        :param recipient: Recipient Email
        :param reset_url: Reset Link
        :param name: Barbershop name
        :return: None
    """
    message = Message("My Kinyozi App password reset", sender="communication@mykinyozi.com", recipients=[recipient])
    message.body = f"""Hello {name.title()},
You are receiving this email because you requested a password reset for your My Kinyozi account.
Click on the link below to reset your password. If the link is not clickable, \
copy and paste it on your browser's address bar.\n
{reset_url}

Note: The password reset link is valid for 30 minutes only. If you did not initiate a password reset, \
please disregard and delete this email.
\n
Best,
The Kinyozi App Team
"""
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
