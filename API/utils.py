import jwt
import os
from API.models import BarberShop
from flask import request, jsonify
from functools import wraps


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
