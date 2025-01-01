from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_admin import Admin


# Initialize SQLAlchemy
db = SQLAlchemy()
admin = Admin()


def create_app():
    app = Flask(__name__)
    CORS(app)

    # Configure database
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///academic_advising.db"
    app.config["SECRET_KEY"] = "mysecret"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Initialize extensions
    db.init_app(app)
    admin.init_app(app)

    # Import and register blueprints
    from .routes import main_bp

    app.register_blueprint(main_bp)
    app.debug = True

    return app
