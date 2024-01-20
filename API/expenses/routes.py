from flask import Blueprint, request, jsonify
from API.models import ExpenseAccounts, BarberShop, Expenses
from API import db, bcrypt
import datetime
from ..utils import shop_login_required, verify_api_key
from ..serializer import serialize_accounts, serialize_expenses

expenses = Blueprint('expenses', __name__)


@expenses.route("/API/expense-account/create/<string:public_id>", methods=["POST"])
@shop_login_required
def create_expense_account(current_user, public_id):
    """
        Create expense accounts for the barbershop
        :param current_user: Currently logged in barbershop owner
        :param public_id: Public id of the barbershop
        :return: 401, 201
    """
    # NOTE: Avoid adding services that are already in created.
    data = request.get_json()
    if current_user.public_id != public_id:
        return jsonify(dict(message="Permission Denied")), 401

    if data["accountName"].strip().lower() in [acc.account_name.lower() for acc in current_user.expense_accounts]:
        return jsonify(dict(
            message=f"{data['accountName']} account already exists."
        )), 409

    new_account = ExpenseAccounts(
        account_name=data["accountName"].strip().title(),
        description=data["accountDescription"].strip().title(),
        shop_id=current_user.id
    )
    db.session.add(new_account)
    db.session.commit()
    return jsonify(dict(message="Expense account has been created.")), 201


@expenses.route("/API/expense-accounts/fetch/<string:public_id>", methods=["GET"])
@verify_api_key
def fetch_all_expense_accounts(public_id):
    """
        Fetch all expense accounts for a certain shop
        :param public_id: public_id for the shop
        :return: 404, 200
    """
    all_accounts = []
    shop = BarberShop.query.filter_by(public_id=public_id).first()
    if not shop:
        return jsonify(dict(message="Barbershop not found")), 404
    for acc in shop.expense_accounts.order_by(ExpenseAccounts.id).all():
        all_accounts.append(serialize_accounts(acc))
    return jsonify(dict(accounts=all_accounts)), 200


@expenses.route("/API/expense-accounts/update/<int:account_id>", methods=["PUT"])
@shop_login_required
def update_expense_account(current_user, account_id):
    """
        Update an expense account
        :param current_user: Logged in shop owner
        :param account_id: ID of expense account being updated
        :return: 404, 401, 200
    """
    data = request.get_json()
    expense_account = ExpenseAccounts.query.filter_by(id=account_id).first()
    if not expense_account:
        return jsonify(dict(message="Expense Account not found")), 404

    if expense_account.shop.public_id != current_user.public_id:
        return jsonify(dict(message="You don't have the permission to perform this action")), 401

    expense_account.account_name = data["accountName"].strip().title()
    expense_account.description = data["accountDescription"].strip().title()
    db.session.commit()
    return jsonify(dict(message="Expense account updated successfully")), 200


@expenses.route("/API/expense-accounts/delete/<int:account_id>", methods=["DELETE"])
@shop_login_required
def delete_expense_account(current_user, account_id):
    """
        Delete an expense account.
        :param current_user: Logged-in user.
        :param account_id: ID for account to be deleted.
        :return: 404, 401, 200
    """
    expense_account = ExpenseAccounts.query.filter_by(id=account_id).first()
    if not expense_account:
        return jsonify(dict(message="Expense Account not found")), 404

    if account_id not in [acc.id for acc in current_user.expense_accounts]:
        return jsonify(dict(message="Permission Denied")), 401

    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect Password")), 401

    # Count to find id an account has any expenses associated cz we don't want to delete accounts that have expenses
    expenses_count = 0
    for _ in expense_account.expense:
        if expenses_count > 0:
            return jsonify(dict(message="Not Allowed! Delete associated expenses first")), 401
        expenses_count += 1

    db.session.delete(expense_account)
    db.session.commit()
    return jsonify(dict(message="Expense account deleted successfully")), 200


# EXPENSES
@expenses.route("/API/expenses/fetch/<string:public_id>", methods=["GET"])
@shop_login_required
def fetch_expenses(current_user, public_id):
    """
        Fetch the expenses for the barbershop
        :param public_id: public_id for the expenses
        :param current_user: Logged-in shop owner
        :return: 401, 200
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permission to perform this action")), 401

    all_expenses = Expenses.query.order_by(Expenses.created_at.desc()).all()
    all_years = [sale.year for sale in Expenses.query.all()]
    unique_years = list(set(all_years))
    all_accounts = [{"account": acc.account_name, "accountId": acc.id} for acc in current_user.expense_accounts]
    current_user_expenses = []
    for expense in all_expenses:
        if expense.account.shop.public_id == current_user.public_id:
            expense_info = serialize_expenses(expense)
            expense_info["account"] = expense.account.account_name
            current_user_expenses.append(expense_info)
    return jsonify(dict(expenses=current_user_expenses, years=unique_years, accounts=all_accounts)), 200


@expenses.route("/API/expense/create/<string:public_id>", methods=["POST"])
@shop_login_required
def create_expense(current_user, public_id):
    """
        Create expenses
        :param current_user: Logged-in user
        :param public_id:
        :return: 401, 201
    """
    if current_user.public_id != public_id:
        return jsonify(dict(message="You do not have permission to perform this action")), 401
    data = request.get_json()
    new_expense = Expenses(
        expense=data["expenseName"].strip().title(),
        amount=data["expenseAmount"],
        description=data["expenseDescription"],
        expense_account=data["expenseAccount"],
        month=datetime.datetime.utcnow().month,
        year=datetime.datetime.utcnow().year,
    )
    db.session.add(new_expense)
    db.session.commit()
    return jsonify(dict(message="Expense has been saved successfully")), 201


@expenses.route("/API/expense/delete/<int:expense_id>", methods=["DELETE"])
@shop_login_required
def delete_expense(current_user, expense_id):
    """
        Delete expense.
        :param current_user: Currently logged-in owner.
        :param expense_id: ID of the expense to be deleted.
        :return: 404, 401, 200.
    """
    expense = Expenses.query.filter_by(id=expense_id).first()
    if not expense:
        return jsonify(dict(message="This expense doesn't exist")), 404

    if expense.account.shop.public_id != current_user.public_id:
        return jsonify(dict(message="You don't permission to perform this action")), 401

    data = request.get_json()
    if not bcrypt.check_password_hash(current_user.password, data["password"].strip()):
        return jsonify(dict(message="Incorrect password")), 401

    db.session.delete(expense)
    db.session.commit()
    return jsonify(dict(message="Expense has been deleted successfully.")), 200


@expenses.route("/API/expense/update/<int:expense_id>", methods=["PUT"])
@shop_login_required
def update_expense(current_user, expense_id):
    """
        Update Expense
        :param current_user: Currently logged-in shop owner
        :param expense_id: ID of expense being updated
        :return: 404, 401, 200
    """
    current_expense = Expenses.query.filter_by(id=expense_id).first()
    if not current_expense:
        return jsonify(dict(message="This expense doesn't exist")), 404

    if current_expense.account.shop.public_id != current_user.public_id:
        return jsonify(dict(message="You don't permission to perform this action")), 401

    data = request.get_json()
    current_expense.expense = data["expenseName"].strip().title()
    current_expense.amount = data["expenseAmount"]
    current_expense.description = data["expenseDescription"].strip().title()
    current_expense.modified_at = datetime.datetime.utcnow()
    db.session.commit()
    return jsonify(dict(message="Expense has been successfully updated.")), 200
