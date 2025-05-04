from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)  # Store hashed password
    role = db.Column(db.String(16), nullable=False, default='user')  # Either 'admin' or 'user'

# Router table
class Router(db.Model):
    __tablename__ = 'routers'

    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(64), nullable=False)
    description = db.Column(db.String(64), nullable=False)
    public_ip_address = db.Column(db.String(64), nullable=False)
    local_ip_address = db.Column(db.String(64), nullable=False)
    ssh_username = db.Column(db.String(64), nullable=False)
    last_seen_online = db.Column(db.DateTime)

# Device table (each device is linked to a router)
class Device(db.Model):
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True)
    mac_address = db.Column(db.String(64), nullable=False)
    local_ip_address = db.Column(db.String(64), nullable=False)
    if_blocked = db.Column(db.Boolean, nullable=False, default=False)
    last_seen_online = db.Column(db.DateTime)
    router_id = db.Column(db.Integer, db.ForeignKey('routers.id'), nullable=False)

    router = db.relationship('Router', backref='devices')


class public_IP_detail(db.Model):
    __tablename__ = 'public_ip_details'

    ip = db.Column(db.String(64), nullable=False, primary_key=True)
    country = db.Column(db.String(64), nullable=True)
    city = db.Column(db.String(64), nullable=True)
    region = db.Column(db.String(64), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    organization = db.Column(db.String(256), nullable=True)
    hostname = db.Column(db.String(256), nullable=True)
    timezone = db.Column(db.String(64), nullable=True)
    postal = db.Column(db.String(64), nullable=True)


