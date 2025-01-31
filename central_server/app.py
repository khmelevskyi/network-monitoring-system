from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

from config import SECRET_KEY, DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

# Initialize extensions (but don't tie them to an app yet)
db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    """Application Factory - Creates Flask app instance."""
    app = Flask(__name__)

    # Configure the app
    app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    app.config["SECRET_KEY"] = SECRET_KEY

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    login_manager.login_view = "login"

    from models import User, Router, Device
    from routes import auth_bp, main_bp

    # Register Blueprints (Modular Routes)
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)

    return app
