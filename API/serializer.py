from flask_restful import fields, marshal


def serialize_shop(shop):
    user_fields = {
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
        "product_level": fields.String,
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
        date_created=fields.String
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
