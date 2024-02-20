from flask import Blueprint, request, jsonify, make_response
from API.models import Employee, Service
from API import db, bcrypt
import os
import jwt
from API.serializer import serialize_employee, serialize_services, serialize_inventory
import secrets
from ..utils import shop_login_required, \
    send_employee_created_email, employee_login_required, auth_mobile_app, verify_api_key
import datetime
import requests

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
            url="https://mykinyozi.com/staff/setup",
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


@employees_blueprint.route("/setup", methods=["PUT"])
@verify_api_key
def setup_account_password():
    """
        Allow employee to complete setting up their password
        :return: 404, 200
    """
    data = request.get_json()
    employee = Employee.query.filter_by(email=data["email"]).first()
    if not employee:
        return jsonify(dict(message="Not Found")), 404

    hashed_password = bcrypt.generate_password_hash(data["password"].strip()).decode("utf-8")
    employee.password = hashed_password
    employee.active = True
    db.session.commit()
    return jsonify(dict(message="Action Complete")), 200


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


@employees_blueprint.route("/change-info/<string:public_id>", methods=["PUT"])
@employee_login_required
def update_employee_info(current_user, public_id):
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
    current_user.phone = data["phone"]
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
    services = current_user.shop.services
    inventory = current_user.shop.inventory
    all_services = []
    for service in services.order_by(Service.service):
        all_services.append(serialize_services(service))

    all_inventory = []
    for item in inventory:
        all_inventory.append(serialize_inventory(item))

    return jsonify(dict(employee=serialize_employee(current_user), services=all_services, inventory=all_inventory)), 200


@employees_blueprint.route("/login", methods=["POST"])
def employee_login():
    """
        Employee Login
        :return: 401, 404, 200
    """
    auth = request.get_json()
    employee = Employee.query.filter_by(email=auth["username"].strip()).first()
    if not auth or not auth["password"] or not auth["username"]:
        return make_response("Could not verify", 401, {"WWW.Authenticate": "Basic realm=Login required!"})
    if not employee:
        return make_response("Incorrect Email", 404, {"WWW.Authenticate": "Basic realm=Login required!"})
    if not employee.password:
        return make_response("Password not Set", 401, {"WWW.Authenticate": "Basic realm=Login required!"})
    if bcrypt.check_password_hash(employee.password, auth["password"].strip()):
        token = jwt.encode(
            {
                "public_id": employee.public_id,
                "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=120)
            },
            os.environ.get('SECRET'),
            algorithm="HS256"
        )
        return jsonify(
            {"Token": token, "public_id": employee.public_id, "shop_id": employee.shop.public_id, "role": employee.role}
        ), 200
    else:
        return make_response("Incorrect password", 401, {"WWW.Authenticate": "Basic realm=Login required!"})


# BARBERS
@employees_blueprint.route("/barbers/all/<string:public_id>", methods=["GET"])
@shop_login_required
def fetch_all_barbers(current_user, public_id):
    """
        Fetch all barbers for a specific shop
        :param current_user: Logged In shop owner
        :param public_id: shop public_id
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not allowed")), 401

    token = auth_mobile_app()
    url = r"https://app.mykinyozi.com/api/mobile/barbers"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        barbers = response.json().get("data")
    else:
        return jsonify(response.json()), response.status_code

    all_barbers = []
    for barber in barbers:
        if barber["barbershopId"] == current_user.id:
            all_barbers.append(barber)

    return jsonify(dict(barbers=all_barbers)), 200


@employees_blueprint.route("/barbers/verify/<string:barber_id>", methods=["PUT"])
@shop_login_required
def verify_barber(current_user, barber_id):
    """
        Verify Barber
        :param current_user:
        :param barber_id:
        :return: 400, 200
    """
    token = auth_mobile_app()
    url = f"https://app.mykinyozi.com/api/mobile/barbers/{barber_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {"status": "ACTIVE"}

    password = request.get_json()["password"]
    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(dict(error="Incorrect Password"))

    response = requests.put(url, json=data, headers=headers)
    if response.status_code != 200:
        return jsonify(response.json()), response.status_code
    return jsonify(response.json()), 200


@employees_blueprint.route("/barbers/deactivate/<string:barber_id>", methods=["PUT"])
@shop_login_required
def deactivate_barber(current_user, barber_id):
    """
        Deactivate barber
        :param current_user:
        :param barber_id:
        :return: 400, 200
    """
    token = auth_mobile_app()
    url = f"https://app.mykinyozi.com/api/mobile/barbers/{barber_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    data = {"status": "INACTIVE"}

    password = request.get_json()["password"]
    if not bcrypt.check_password_hash(current_user.password, password):
        return jsonify(dict(error="Incorrect Password"))

    response = requests.put(url, json=data, headers=headers)
    if response.status_code != 200:
        return jsonify(response.json()), response.status_code
    return jsonify(response.json()), 200


@employees_blueprint.route("/barbers/appointments/<string:public_id>", methods=["GET"])
@shop_login_required
def appointments(current_user, public_id):
    """
        Get barbers' appointments
        :param current_user: Logged in shop owner
        :param public_id: Shop public_id
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="Not Allowed")), 401

    token = auth_mobile_app()
    url = f"https://app.mykinyozi.com/api/mobile/appointments/barbershop/{current_user.id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        appointments = response.json().get("data")
    else:
        return jsonify(response.json()), response.status_code

    time_format = "%Y-%m-%dT%H:%M:%S.%fZ"
    all_appointments = []
    for appointment in appointments:
        converted_time = datetime.datetime.strptime(appointment["dateTime"], time_format)
        plus_one_hour = converted_time + datetime.timedelta(hours=1)
        appointment_details = dict(
            start=dict(
                year=converted_time.year,
                month=converted_time.month,
                day=converted_time.day,
                hour=converted_time.hour,
                minute=converted_time.minute
            ),
            end=dict(
                year=plus_one_hour.year,
                month=plus_one_hour.month,
                day=plus_one_hour.day,
                hour=plus_one_hour.hour,
                minute=plus_one_hour.minute
            ),
            title=appointment["barber"]["name"]
        )
        all_appointments.append(appointment_details)
    return jsonify(dict(data=all_appointments)), 200
