from flask_restful import fields, marshal

# Data Serializers


def serialize_shop(shop):
    user_fields = {
        'id': fields.Integer,
        'public_id': fields.String,
        'shop_name': fields.String,
        'email': fields.String,
        'county': fields.String,
        'city': fields.String,
        'phone': fields.String,
        "active": fields.Boolean
    }
    return marshal(shop, user_fields)


def serialize_inventory(inventory):
    inventory_fields = {
        "id": fields.Integer,
        "product_name": fields.String,
        "product_level": fields.Integer,
        "modified_at": fields.DateTime
    }
    return marshal(inventory, inventory_fields)


def serialize_services(service):
    service_fields = dict(
        id=fields.Integer,
        service=fields.String,
        description=fields.String,
        charges=fields.Integer,
        modified_at=fields.DateTime
    )
    return marshal(service, service_fields)


def serialize_sales(sale):
    sale_fields = dict(
        id=fields.Integer,
        payment_method=fields.String,
        description=fields.String,
        date_created=fields.String,
        month=fields.Integer,
        year=fields.Integer
    )
    return marshal(sale, sale_fields)


def serialize_accounts(account):
    account_fields = dict(
        id=fields.Integer,
        account_name=fields.String,
        description=fields.String
    )
    return marshal(account, account_fields)


def serialize_expenses(expense):
    expense_fields = dict(
        id=fields.Integer,
        expense=fields.String,
        amount=fields.Integer,
        description=fields.String,
        month=fields.Integer,
        year=fields.Integer,
        created_at=fields.DateTime,
        modified_at=fields.DateTime
    )
    return marshal(expense, expense_fields)


def serialize_notification(notification):
    notification_fields = dict(
        id=fields.Integer,
        title=fields.String,
        message=fields.String,
        shop_id=fields.Integer,
        read=fields.Boolean,
        created_at=fields.DateTime
    )
    return marshal(notification, notification_fields)


def serialize_equipment(equipment):
    equipment_fields = dict(
        id=fields.Integer,
        equipment_name=fields.String,
        description=fields.String,
        faulty=fields.Boolean,
        bought_on=fields.DateTime,
        price=fields.Integer
    )
    return marshal(equipment, equipment_fields)


def serialize_employee(employee):
    employee_fields = dict(
        id=fields.Integer,
        public_id=fields.String,
        f_name=fields.String,
        l_name=fields.String,
        email=fields.String,
        role=fields.String,
        phone=fields.String,
        salary=fields.Integer,
        create_date=fields.DateTime,
        active=fields.Boolean
    )
    return marshal(employee, employee_fields)
