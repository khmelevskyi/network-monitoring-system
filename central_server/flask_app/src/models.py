from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

# User table
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

# Enriched Public IPs table
# Public IPs to which devices have connected at some point of time
class Public_IP_Detail(db.Model):
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
	last_updated_at = db.Column(db.DateTime)


# Anomaly Alerts table
class Anomaly_Alert(db.Model):
    __tablename__ = 'anomaly_alerts'

    id = db.Column(db.Integer, primary_key=True)
    alert_type = db.Column(db.String(64), nullable=False)  # 'suricata' or 'ips_entropy_anomaly', 'potential_botnet_activity'
    classification = db.Column(db.String(128), nullable=True)
    description = db.Column(db.Text, nullable=True)
    priority = db.Column(db.Integer, nullable=True)

    alert_time = db.Column(db.DateTime)

    src_ip = db.Column(db.String(64), nullable=True)
    src_port = db.Column(db.Integer, nullable=True)
    dst_ip = db.Column(db.String(64), nullable=True)
    dst_port = db.Column(db.Integer, nullable=True)
    protocol = db.Column(db.String(16), nullable=True)

    router_mac = db.Column(db.String(64), nullable=False)
    router_public_ip = db.Column(db.String(64), nullable=False)



# Blacklist / Whitelist table for public IPs
class Custom_IP_List_Entry(db.Model):
    __tablename__ = 'custom_ip_list_entries'

    id = db.Column(db.Integer, primary_key=True)
    ip_address = db.Column(db.String(64), nullable=False, unique=True)
    label = db.Column(db.String(16), nullable=False)  # 'blacklist' or 'whitelist'
    reason = db.Column(db.String(256), nullable=True)
    added_by = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)