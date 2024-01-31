from flask import Blueprint, request, jsonify, make_response
from API.models import BarberShop, Service, Employee
from API import db, bcrypt
from API.serializer import serialize_shop, serialize_services
import secrets
import datetime
import jwt
import os
from ..utils import (
    shop_login_required,
    send_password_reset_email,
    generate_reset_token,
    verify_token,
    verify_api_key,
    send_employee_created_email
)

shops = Blueprint('shops', __name__)


@shops.route("/API/shop/<string:public_id>", methods=["GET"])
@shop_login_required
def get_shop(current_user, public_id):
    """
        Fetch all info about a barbershop
        :param current_user: Current logged-in user
        :param public_id: Barbershop public_id
        :return: 401, 404, 200
    """
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    if current_user.public_id != public_id:
        return jsonify(dict(message="You don't have permission to access the resource")), 401
    if not shop:
        return jsonify(dict(message="Shop doesn't exist")), 404
    shop_info = serialize_shop(shop)
    all_services = []
    for service in shop.services.order_by(Service.charges):
        all_services.append(serialize_services(service))
    return jsonify(shopInfo=shop_info, services=all_services), 200


@shops.route("/API/shops/all", methods=["GET"])
@verify_api_key
def all_shops():
    """
        Fetch all barbershops
        :return: 200
    """
    name = request.args.get("name", "").strip().title()
    shops_all = BarberShop.query.filter(BarberShop.shop_name.ilike(f'%{name}%'))\
        .order_by(BarberShop.shop_name.desc()).all()
    shops_data = []
    for shop in shops_all[:10]:
        shops_data.append(serialize_shop(shop))
    return jsonify(dict(data=shops_data)), 200


@shops.route("/API/create/shop", methods=["POST"])
@verify_api_key
def shop_signup():
    """
        Create a new barbershop
        :return: 409, 201
    """
    data = request.get_json()
    public_id = secrets.token_hex(6)
    matching_public_id_found = BarberShop.query.filter_by(public_id=public_id).first()
    if matching_public_id_found:
        public_id = secrets.token_hex(6)+secrets.token_hex(1)

    password_hash = bcrypt.generate_password_hash(data["password"].strip()).decode("utf-8")

    # Check email  doesn't exist
    email_exists = BarberShop.query.filter_by(email=data["email"]).first()
    if email_exists:
        return jsonify({"message": "Email already exists"}), 409

    shop = BarberShop(
        public_id=public_id,
        shop_name=data["name"].strip().title(),
        email=data["email"].strip(),
        password=password_hash,
        phone=data["phone"].strip(),
        county=data["county"].strip().title(),
        city=data["city"].strip().title()
    )
    db.session.add(shop)
    db.session.commit()
    return jsonify(dict(message="Account Created successfully", id=public_id)), 201


@shops.route("/API/login/shop", methods=["POST"])
@verify_api_key
def shop_login():
    """
       Logs the shop owner's in using their email and password
       :return: 401, 404, jwt authorization token
       """
    auth = request.authorization
    shop = BarberShop.query.filter_by(email=auth.username.strip()).first()
    if not auth or not auth.password or not auth.username:
        return make_response("Could not verify", 401, {"WWW.Authenticate": "Basic realm=Login required!"})
    if not shop:
        return make_response("Incorrect Email", 404, {"WWW.Authenticate": "Basic realm=Login required!"})
    if bcrypt.check_password_hash(shop.password, auth.password.strip()):
        token = jwt.encode(
            {
                "public_id": shop.public_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=120)
            },
            os.environ.get('SECRET'),
            algorithm="HS256"
        )
        return jsonify({"Token": token, "public_id": shop.public_id}), 200
    else:
        return make_response("Incorrect password", 401, {"WWW.Authenticate": "Basic realm=Login required!"})


@shops.route("/API/shop/update/<string:public_id>", methods=["POST"])
@shop_login_required
def update_shop(current_user, public_id):
    """
        Update shop info
        :param current_user: Currently logged-in user
        :param public_id: shop public id
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permissions to perform this action")), 401
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    data = request.get_json()
    shop.shop_name = data["shop_name"].strip().title()
    shop.email = data["email"].strip()
    shop.phone = data["phone"].strip()
    shop.county = data["county"].strip().title()
    shop.city = data["city"].strip().title()
    db.session.commit()
    return jsonify(dict(message="Update Successful")), 200


@shops.route("/API/token/verify", methods=["POST"])
@verify_api_key
def verify_login_token():
    """
        Verify that JWT token is valid
        :return:
    """
    data = request.get_json()
    try:
        payload = jwt.decode(
            data["token"],
            os.environ.get('SECRET'),
            algorithms=['HS256']
        )

        # Extract the expiration time from the payload
        expiration_time = payload['exp']

        # Get the current time
        current_time = datetime.datetime.utcnow().timestamp()

        # Check if the token has expired
        if current_time > expiration_time:
            return jsonify(dict(message="Token has expired")), 401
        else:
            return jsonify(dict(message="Valid Token")), 200

    except jwt.ExpiredSignatureError:
        return jsonify(dict(message="Token has expired")), 401
    except jwt.InvalidTokenError:
        return jsonify(dict(message="Invalid token")), 401


@shops.route("/API/shop/password/request-reset", methods=["POST"])
@verify_api_key
def request_password_reset():
    """
        Reset password.
        :return: 404, 500, 200
    """
    data = request.get_json()
    shop = BarberShop.query.filter_by(email=data["email"]).first()
    if not shop:
        return jsonify(dict(message="Email doesn't exist")), 404
    else:
        reset_token = generate_reset_token(shop.public_id)
        reset_url = f"https://www.mykinyozi.com/reset/{reset_token}"
        try:
            send_password_reset_email(recipient=shop.email, reset_url=reset_url, name=shop.shop_name)
        except:
            return jsonify(dict(message="An error occurred. Please try again")), 500
        else:
            return jsonify(dict(message="Reset link has been sent to your email.")), 200


@shops.route("/API/shop/password/reset/<string:reset_token>", methods=["POST"])
@verify_api_key
def reset_password(reset_token):
    """
        Reset shop password
        :param reset_token: Password reset token
        :return: 404, 200
    """
    shop = verify_token(reset_token)
    if not shop:
        return jsonify(dict(message="Token invalid or expired")), 403

    data = request.get_json()
    password_hash = bcrypt.generate_password_hash(data["password"].strip()).decode("utf-8")
    shop.password = password_hash
    db.session.commit()
    return jsonify(dict(message="Password reset successful")), 200


@shops.route("/API/shop/password/change/<string:public_id>", methods=["POST"])
@shop_login_required
def change_password(current_user, public_id):
    """
        Change shop password
        :param current_user: Currently logged-in user
        :param public_id: Shop public ID
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not Allowed")), 401

    data = request.get_json()
    if bcrypt.check_password_hash(current_user.password, data["oldPassword"].strip()):
        current_user.password = bcrypt.generate_password_hash(data["newPassword"].strip()).decode("utf-8")
        db.session.commit()
        return jsonify(dict(message="Password Change Successful")), 200
    else:
        return jsonify(dict(message="Old password is Incorrect")), 401


@shops.route("/API/shop/employee/create/<string:public_id>", methods=["POST"])
@shop_login_required
def create_employee(current_user, public_id):
    """
        Create new Employee from shop dashboard
        :param current_user: Currently logged-in user
        :param public_id: Shop public ID
        :return: 401, 201
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not Allowed")), 401

    data = request.get_json()
    check_employee = Employee.query.filter_by(email=data["email"].strip().lower()).first()
    if check_employee:
        return jsonify(dict(message="Email already exists")), 409

    employee_public_id = secrets.token_hex(6)
    matching_public_id_found = Employee.query.filter_by(public_id=employee_public_id).first()
    if matching_public_id_found:
        employee_public_id = secrets.token_hex(6) + secrets.token_hex(1)

    employee = Employee(
        f_name=data["fName"].strip().title(),
        l_name=data["lName"].strip().title(),
        public_id=employee_public_id,
        email=data["email"].strip().lower(),
        role=data["role"].strip().title(),
        salary=data["salary"],
        shop_id=current_user.id
    )
    db.session.add(employee)
    db.session.commit()
    try:
        send_employee_created_email(
            recipient=data["email"].strip().lower(),
            name=data["fName"].strip().title(),
            url="https://mykinyozi.com",
            shop_name=current_user.shop_name
        )
    except Exception as e:
        print(e)
        return jsonify(dict(message="Something went wrong. Try again")), 401
    return jsonify(dict(message="Employee Created")), 201
