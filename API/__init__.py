from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_mail import Mail
from flask_cors import CORS
from flask_migrate import Migrate
from API.config import Config


db = SQLAlchemy()
mail = Mail()
bcrypt = Bcrypt()
migrate = Migrate()
cors = CORS()


def create_app():  # config_class=Config
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, supports_credentials=True)

    from API.shop.routes import shops
    from API.services.routes import services
    from API.expenses.routes import expenses
    from API.sales.routes import sales
    from API.inventory.routes import inventory
    from API.notifications.routes import notifications_blueprint
    from API.equipment.routes import equipment_blueprint
    from API.employees.routes import employees_blueprint
    app.register_blueprint(shops)
    app.register_blueprint(services)
    app.register_blueprint(expenses)
    app.register_blueprint(sales)
    app.register_blueprint(inventory)
    app.register_blueprint(notifications_blueprint)
    app.register_blueprint(equipment_blueprint)
    app.register_blueprint(employees_blueprint)

    return app
