from flask import Flask
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from src.filters import time_ago_filter

from src.models import db
from src.config import (
			POSTGRES_HOST, POSTGRES_PORT,
			POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
			SECRET_KEY)


# Initialize extensions (but don't tie them to an app yet)
login_manager = LoginManager()

def create_app():
    """Application Factory - Creates Flask app instance."""
    app = Flask(__name__)

    # Register custom filters
    app.add_template_filter(time_ago_filter, name='time_ago')  # Register the filter

    # Configure the app
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    app.config["SECRET_KEY"] = SECRET_KEY

    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from src.models import User, Router, Device
    from src.routes import auth_bp, main_bp

    # Register Blueprints (Modular Routes)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
