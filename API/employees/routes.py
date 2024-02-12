from flask import Blueprint, request, jsonify, make_response
from API.models import Employee
from API import db, bcrypt
import os
import jwt
from API.serializer import serialize_employee
import secrets
from ..utils import shop_login_required, send_employee_created_email, employee_login_required
import datetime

employees_blueprint = Blueprint("employees", __name__, url_prefix="/API/employees")


@employees_blueprint.route("/create/<string:public_id>", methods=["POST"])
@shop_login_required
def create_employee(current_user, public_id):
    """
        Create new Employee from shop dashboard
        :param current_user: Currently logged-in user
        :param public_id: Shop public ID
        :return: 401, 201, 409
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
        phone=data["phone"].strip(),
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
    except Exception:
        return jsonify(dict(message="Something went wrong. Try again")), 401
    return jsonify(dict(message="Employee Created")), 201


@employees_blueprint.route("/all/<string:public_id>", methods=["GET"])
@shop_login_required
def fetch_employees(current_user, public_id):
    """
        Fetch all employees associated with the current_shop
        :param current_user: Logged in user
        :param public_id:  Shop public_d
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not allowed")), 401

    all_staff = []
    for staff in current_user.employees:
        all_staff.append(serialize_employee(staff))

    return jsonify(dict(staff=all_staff)), 200


@employees_blueprint.route("/setup/<string:public_id>", methods=["PUT"])
def setup_account(public_id):
    """
        Allow employee to complete setting up their password
        :param public_id: Employee public_id
        :return: 404, 401, 200
    """
    employee = Employee.query.filter_by(public_id=public_id).first()
    if not employee:
        return jsonify(dict(message="Employee not found")), 404

    data = request.get_json()
    hashed_password = bcrypt.generate_password_hash(data["password"])
    employee.password = hashed_password
    employee.active = True
    db.session.commit()
    return jsonify(dict(message="Set up Complete")), 200


@employees_blueprint.route("/remove/<int:staff_id>", methods=["DELETE"])
@shop_login_required
def remove_employee(current_user, staff_id):
    """
        Remove employee from the shop
        :param staff_id: Employee id
        :param current_user: Logged in shop owner
        :return: 401, 404, 200
    """
    employee = Employee.query.filter_by(id=staff_id).first()
    if not employee:
        return jsonify(dict(message="Employee doesn't exist")), 404

    if employee.shop_id != current_user.id:
        return jsonify(dict(message="Not allowed")), 401

    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect Password")), 401

    db.session.delete(employee)
    db.session.commit()
    return jsonify(dict(message="Deleted successfully")), 200


@employees_blueprint.route("/change-email/<string:public_id>", methods=["PUT"])
@employee_login_required
def update_email(current_user, public_id):
    """
        Change employee email address ** By the employee
        :param public_id: Employee public_id
        :param current_user: Logged in employee
        :return: 404, 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not Allowed")), 401

    data = request.get_json()
    current_user.email = data["email"]
    db.session.commit()
    return jsonify(dict(message="Update Successful")), 200


@employees_blueprint.route("/update/<int:staff_id>", methods=["PUT"])
@shop_login_required
def update_employee(current_user, staff_id):
    """
        Update employee information by the shop owner
        :param current_user: Shop owner
        :param staff_id: employee public id
        :return: 404, 401, 200
    """
    employee = Employee.query.filter_by(id=staff_id).first()
    if not employee:
        return jsonify(dict(message="Not Found")), 404

    if employee.shop_id != current_user.id:
        return jsonify(dict(message="Not Allowed")), 401

    data = request.get_json()
    new_email = data["email"].strip().lower()
    email_exists = Employee.query.filter_by(email=new_email).first()
    if email_exists and new_email != employee.email:
        return jsonify(dict(message="Email already exists")), 409

    employee.email = data["email"].strip().lower()
    employee.phone = data["phone"].strip()
    employee.role = data["role"].strip().lower()
    employee.salary = data["salary"]
    db.session.commit()
    return jsonify(dict(message="Update Successful")), 200


@employees_blueprint.route("/fetch/<string:public_id>")
@employee_login_required
def fetch_single_employee(current_user, public_id):
    """
        Fetch individual employee
        :param current_user: Currently logged in employee
        :param public_id: Employee public_id
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(message="Not Allowed"), 401
    return jsonify(dict(employee=serialize_employee(current_user))), 200


@employees_blueprint.route("/login")
def employee_login():
    """
        Employee Login
        :return: 401, 404, 200
    """
    auth = request.authorization
    employee = Employee.query.filter_by(email=auth.username.strip()).first()
    if not auth or not auth.password or not auth.username:
        return make_response("Could not verify", 401, {"WWW.Authenticate": "Basic realm=Login required!"})
    if not employee:
        return make_response("Incorrect Email", 404, {"WWW.Authenticate": "Basic realm=Login required!"})
    if bcrypt.check_password_hash(employee.password, auth.password.strip()):
        token = jwt.encode(
            {
                "public_id": employee.public_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=120)
            },
            os.environ.get('SECRET'),
            algorithm="HS256"
        )
        return jsonify({"Token": token, "public_id": employee.public_id, "shop_id": employee.shop.public_id}), 200
    else:
        return make_response("Incorrect password", 401, {"WWW.Authenticate": "Basic realm=Login required!"})
