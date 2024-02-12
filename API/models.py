from API import db
from datetime import datetime


class BarberShop(db.Model):
    """Barbershop model"""
    __tablename__ = "barbershops"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(30), unique=True, nullable=False)
    shop_name = db.Column(db.String(100))
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(300), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    county = db.Column(db.String(20), nullable=False)
    city = db.Column(db.String(20), nullable=False)
    active = db.Column(db.Boolean(), default=False)
    join_date = db.Column(db.DateTime, default=datetime.utcnow)
    modified_date = db.Column(db.DateTime)
    services = db.relationship("Service", backref="shop", lazy="dynamic", cascade='all, delete-orphan')
    inventory = db.relationship("Inventory", backref="shop", lazy="dynamic", cascade='all, delete-orphan')
    expense_accounts = db.relationship("ExpenseAccounts", backref="shop", lazy="dynamic", cascade='all, delete-orphan')
    notifications = db.relationship("Notification", backref="shop", lazy="dynamic", cascade='all, delete-orphan')
    equipments = db.relationship("Equipment", backref="shop", lazy="dynamic", cascade="all, delete-orphan")
    employees = db.relationship("Employee", backref="shop", lazy="dynamic", cascade="all, delete-orphan")
    sales = db.relationship("Sale", backref="shop", lazy="dynamic", cascade="all, delete-orphan")

    def __repr__(self):
        return f"({self.name}, {self.email})"


class Inventory(db.Model):
    """Shop inventory"""
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    product_level = db.Column(db.Integer, nullable=False)
    modified_at = db.Column(db.DateTime)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))

    def __repr__(self):
        return f"Inventory({self.product_name}, {self.product_level})"


class Service(db.Model):
    """Shop Service"""
    __tablename__ = "services"

    id = db.Column(db.Integer, primary_key=True)
    service = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    charges = db.Column(db.Integer, nullable=False)
    modified_at = db.Column(db.DateTime)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))
    sales = db.relationship("Sale", backref="service", lazy="dynamic")

    def __str__(self):
        return f"Services({self.service})"


class Sale(db.Model):
    """Sales"""
    __tablename__ = "sales"

    id = db.Column(db.Integer, primary_key=True)
    payment_method = db.Column(db.String(30), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))
    service_id = db.Column(db.Integer, db.ForeignKey("services.id", ondelete='SET NULL'))

    def __repr__(self):
        return f"Sales({self.amount}, {self.payment_method})"


class ExpenseAccounts(db.Model):
    """Barbershop Expense accounts"""
    __tablename__ = "expenseaccounts"

    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))
    expense = db.relationship("Expenses", backref="account", lazy="dynamic")

    def __repr__(self):
        return f"ExpenseAccounts({self.account_name})"


class Expenses(db.Model):
    """Expenses"""
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)
    expense = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.Integer, nullable=False)
    modified_at = db.Column(db.DateTime)
    expense_account = db.Column(db.Integer, db.ForeignKey("expenseaccounts.id", ondelete='SET NULL'))

    def __repr__(self):
        return f"Expense({self.expense})"


class Equipment(db.Model):
    """Barber shop Equipment"""
    __tablename__ = "equipments"

    id = db.Column(db.Integer, primary_key=True)
    equipment_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    faulty = db.Column(db.Boolean, default=False)
    bought_on = db.Column(db.DateTime)
    price = db.Column(db.Integer, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))

    def __repr__(self):
        return f"Equipment({self.equipment_name})"


class Notification(db.Model):
    """Notifications"""
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Employee(db.Model):
    """Employee table"""
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(20), nullable=False)
    f_name = db.Column(db.String(20), nullable=False)
    l_name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    password = db.Column(db.Text, nullable=True)
    salary = db.Column(db.Integer, nullable=True)
    create_date = db.Column(db.DateTime, default=datetime.utcnow)
    phone = db.Column(db.String(20), nullable=True)
    active = db.Column(db.Boolean, default=False)
    shop_id = db.Column(db.Integer, db.ForeignKey("barbershops.id"))

    def __repr__(self):
        return f"Employee({self.f_name}, {self.l_name})"
