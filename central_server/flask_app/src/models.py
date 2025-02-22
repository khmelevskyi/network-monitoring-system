from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Store hashed password
    role = db.Column(db.String(10), nullable=False, default="user")  # Either "admin" or "user"

# Router table
class Router(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    ip_address = db.Column(db.String(15), nullable=False)

# Device table (each device is linked to a router)
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    mac_address = db.Column(db.String(17), unique=True, nullable=False)
    router_id = db.Column(db.Integer, db.ForeignKey('router.id'), nullable=False)

    router = db.relationship("Router", backref="devices")
