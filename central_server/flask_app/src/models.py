from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Store hashed password
    role = db.Column(db.String(16), nullable=False, default="user")  # Either "admin" or "user"

# Router table
class Router(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(64), nullable=False)
    public_ip_address = db.Column(db.String(64), nullable=False)
    local_ip_address = db.Column(db.String(64), nullable=False)
    username = db.Column(db.String(64), nullable=False)
    last_updated_data = db.Column(db.DateTime)

# Device table (each device is linked to a router)
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(64), nullable=False)
    local_ip_address = db.Column(db.String(64), nullable=False)
    if_blocked = db.Column(db.Boolean, nullable=False, default=False)
    router_id = db.Column(db.Integer, db.ForeignKey('router.id'), nullable=False)
    last_updated_data = db.Column(db.DateTime)

    router = db.relationship("Router", backref="devices")
