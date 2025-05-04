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


# Initializing extensions (not tied to an app yet)
login_manager = LoginManager()

def create_app():
    """Application Factory - Creating Flask app instance."""
    app = Flask(__name__)

    # Registering custom filters
    app.add_template_filter(time_ago_filter, name='time_ago')  # registering the filter

    # Configuring the app
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    app.config["SECRET_KEY"] = SECRET_KEY

    # Initializing extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    login_manager.init_app(app)

    login_manager.login_view = "auth.login"

    from src.models import User, Router, Device
    from src.routes import auth_bp, main_bp

    # Registering Blueprints (Modular Routes)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    # Registering Scheduler
    from src.scheduler import start_scheduler
    start_scheduler(app)

    return app
