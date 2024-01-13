from flask import Blueprint, request, jsonify, make_response
from API.models import BarberShop, Employee
from API import db, bcrypt
from API.serializer import serialize_shop, serialize_services

employees_blueprint = Blueprint("employees", __name__, url_prefix="/API/employees")
