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
    app.register_blueprint(shops)
    app.register_blueprint(services)
    app.register_blueprint(expenses)
    app.register_blueprint(sales)
    app.register_blueprint(inventory)

    return app
