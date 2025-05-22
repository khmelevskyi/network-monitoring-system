import json
from datetime import datetime

from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint, render_template, redirect, url_for, request, flash

from src.app import login_manager
from src.decorators import admin_required
from src.models import db, User, Router, Device, Custom_IP_List_Entry
from src.ssh_client import ssh_block_device, ssh_unblock_device
from src.api_endpoints import api_update_routers, api_update_devices, api_get_ip_details
# from src.anomaly_detectors import check_entropy_anomaly, check_botnet_activity


auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)


### Dashboard and login section
@login_manager.user_loader
def load_user(user_id):
	# Return the user object for the given user_id
	return User.query.get(int(user_id))

# User Login
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		user = User.query.filter_by(username=username).first()

		if user and check_password_hash(user.password, password):
			login_user(user)
			return redirect(url_for("main.dashboard"))
		else:
			flash("Invalid credentials!", "danger")

	return render_template("login.html")

# User Logout
@auth_bp.route("/logout")
@login_required
def logout():
	logout_user()
	return redirect(url_for("auth.login"))


# Dashboard (Available to both users & admins)
@main_bp.route("/")
@login_required
def first_page():
	return redirect(url_for("main.dashboard"))

# Dashboard (Available to both users & admins)
@main_bp.route("/dashboard")
@login_required
def dashboard():
	routers = Router.query.order_by(Router.last_seen_online.desc()).all()
	return render_template("dashboard.html", routers=routers)
### \


### Admin section
# Create init admin
@main_bp.route("/create_initial_admin", methods=["GET", "POST"])
def create_initial_admin():
	if User.query.first():
		flash("Initial admin already exists.", "warning")
		return redirect(url_for('main.dashboard'))

	if request.method == "POST":
		username = request.form["username"]
		password = request.form["password"]
		if User.query.filter_by(username=username).first():
			flash("Username already exists.", "danger")
		else:
			new_admin = User(username=username,
							 password=generate_password_hash(password),
							 role="admin")
			db.session.add(new_admin)
			db.session.commit()
			flash("Initial admin user created successfully!", "success")
			return redirect(url_for('auth.login'))

	flash("Sign up to create an initial admin", "info")
	return render_template("login.html")

# Admin-Only Page
@main_bp.route("/admin")
@admin_required
def admin_panel():
	users = User.query.all()
	return render_template("admin.html", users=users)

# Admin Creates a New User
@main_bp.route("/admin/create_user", methods=["POST"])
@login_required
@admin_required
def create_user():
	username = request.form["username"]
	password = generate_password_hash(request.form["password"])
	role = request.form["role"]

	if role not in ["admin", "user"]:
		flash("Invalid role!", "danger")
		return redirect(url_for("main.admin_panel"))

	new_user = User(username=username, password=password, role=role)
	db.session.add(new_user)
	db.session.commit()
	flash("User created successfully!", "success")
	return redirect(url_for("main.admin_panel"))
### \



# Public IPs whitelist / blacklist logic
# View IP Lists
@main_bp.route("/ip_lists")
@login_required
def view_ip_lists():
    blacklisted = Custom_IP_List_Entry.query.filter_by(label='blacklist').all()
    whitelisted = Custom_IP_List_Entry.query.filter_by(label='whitelist').all()
    return render_template("ip_lists.html", blacklisted=blacklisted, whitelisted=whitelisted)

# Add IP to List
@main_bp.route("/ip_lists/add", methods=["POST"])
@admin_required
def add_ip_to_list():
    ip_address = request.form["ip_address"]
    label = request.form["label"]
    reason = request.form.get("reason", "")

    if label not in ["blacklist", "whitelist"]:
        flash("Invalid label", "danger")
        return redirect(url_for("main.view_ip_lists"))

    if Custom_IP_List_Entry.query.filter_by(ip_address=ip_address).first():
        flash("IP address already exists in the list.", "warning")
    else:
        new_entry = Custom_IP_List_Entry(
            ip_address=ip_address,
            label=label,
            reason=reason,
            added_by=current_user.username
        )
        db.session.add(new_entry)
        db.session.commit()
        flash(f"{label.capitalize()} entry added for {ip_address}.", "success")

    return redirect(url_for("main.view_ip_lists"))

# Delete IP from List
@main_bp.route("/ip_lists/delete/<int:entry_id>")
@admin_required
def delete_ip_from_list(entry_id):
    entry = Custom_IP_List_Entry.query.get_or_404(entry_id)
    db.session.delete(entry)
    db.session.commit()
    flash("IP entry deleted successfully.", "info")
    return redirect(url_for("main.view_ip_lists"))
### \


### API endpoints for Grafana and also web-interface
# Update Routers
@main_bp.route('/api/update_routers', methods=["GET"])
# @login_required
def route_update_routers():
	result = api_update_routers()
	return result


# Update Devices
@main_bp.route('/api/update_devices', methods=["GET"])
# @login_required
def route_update_devices():
	result = api_update_devices()
	return result


# Get Enriched IPs details
@main_bp.route("/api/get_ip_details")
def route_get_ip_details():
	ip_to_lookup = request.args.get("public_ip")
	device_ips = request.args.get("device_ips")
	start_time = request.args.get("start")
	end_time = request.args.get("end")

	result = api_get_ip_details(ip_to_lookup, device_ips, start_time, end_time)

	return result
### \



### Blocking / Unblocking functionality
# Block/Unblock Device (Admin Only)
@main_bp.route('/block/<rpi_mac>/<mac>')
@admin_required
def route_block_device(rpi_mac, mac):
	ssh_block_device(rpi_mac, mac)

	flash(result, "info")
	return redirect(url_for("main.dashboard"))


@main_bp.route("/unblock/<rpi_mac>/<mac>")
@admin_required
def route_unblock_device(rpi_mac, mac):
	ssh_unblock_device(rpi_mac, mac)

	flash(result, "info")
	return redirect(url_for("main.dashboard"))
### \



### Testing functions
# GeoIP and Traceroute
# @main_bp.route("/get_ip_details")
# def route_get_ip_details():
# 	result = json.dumps({
# 		"ip": '1.1.1.1',
# 		"country": 'RU',
# 		"city": 'Moscow',
# 		"region": 'Moscow',
# 		"latitude": 55.7558,
# 		"longitude": 37.6173,
# 		"organization": 'bad org',
# 		"hostname": 'mail.ru',
# 		"timezone": 'Europe/Moscow',
# 		"postal": '103274'
# 	})
# 	return result


## testing routes
# @main_bp.route("/check_botnet_activity")
# def route_check_botnet_activity():
# 	result = check_botnet_activity()

# 	return result


