from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify

from src.decorators import admin_required
from src.models import db, User, Router, Device
from src.ssh_client import execute_ssh_command
from src.app import login_manager
from src.influxdb_funcs import flux_update_devices, flux_update_routers
from src.geoip_traceroute import enrich_flows

from src.config import SSH_PRIVATE_KEY_PATH

import json
from datetime import datetime


auth_bp = Blueprint("auth", __name__)
main_bp = Blueprint("main", __name__)


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


# Update Routers
@main_bp.route('/update_routers', methods=["GET"])
# @login_required
def update_routers():
    result = flux_update_routers()

    # Process results
    for table in result:
        for record in table.records:
            rpi_mac = record.values.get("rpi_mac")
            rpi_description = record.values.get("rpi_description")
            rpi_public_ip = record.values.get("rpi_public_ip")
            rpi_local_ip = record.values.get("rpi_local_ip")
            rpi_ssh_username = record.values.get("rpi_ssh_username")
            last_seen_online = record.values.get("_time")

            # Find the router
            router = Router.query.filter_by(mac_address=rpi_mac).first()
            if router:
                # Update existing router
                router.description = rpi_description
                router.public_ip_address = rpi_public_ip
                router.local_ip_address = rpi_local_ip
                router.ssh_username = rpi_ssh_username
                router.last_seen_online = last_seen_online
            else:
                # Add new device
                new_router = Router(
                    mac_address=rpi_mac,
                    description=rpi_description,
                    public_ip_address=rpi_public_ip,
                    local_ip_address=rpi_local_ip,
                    ssh_username=rpi_ssh_username,
                    last_seen_online=last_seen_online
                )
                db.session.add(new_router)

            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                print(f"Error updating router {rpi_mac}")

    # return redirect(url_for("main.dashboard"))
    return json.dumps({"status": "success", "last_checked_routers": str(datetime.utcnow())})


# Update Devices
@main_bp.route('/update_devices', methods=["GET"])
# @login_required
def update_devices():
    result = flux_update_devices()

    # Process results
    for table in result:
        for record in table.records:
            rpi_mac = record.values.get("rpi_mac")
            device_mac = record.values.get("mac")
            ip_address = record.values.get("_value")
            last_seen_online = record.values.get("_time")

            # Find the router
            router = Router.query.filter_by(mac_address=rpi_mac).first()
            if router:
                # Check if device exists
                device = Device.query.filter_by(mac_address=device_mac, router_id=router.id).first()
                if device:
                    # Update existing device
                    device.local_ip_address = ip_address
                    device.last_seen_online = last_seen_online
                else:
                    # Add new device
                    new_device = Device(
                        mac_address=device_mac,
                        local_ip_address=ip_address,
                        router_id=router.id,
                        last_seen_online=last_seen_online
                    )
                    db.session.add(new_device)

                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    print(f"Error updating device {device_mac} for router {rpi_mac}")

    # return redirect(url_for("main.dashboard"))
    return json.dumps({"status": "success", "last_checked_devices": str(datetime.utcnow())})



# Block/Unblock Device (Admin Only)
@main_bp.route('/block/<rpi_mac>/<mac>')
@admin_required
def block_device(rpi_mac, mac):
    router = Router.query.filter_by(mac_address=rpi_mac).first()
    if not router:
        flash("Router not found", "danger")
        return redirect(url_for("main.dashboard"))

    device = Device.query.filter_by(mac_address=mac).first()
    if not device:
        flash("Device not found", "danger")
        return redirect(url_for("main.dashboard"))

    if device.if_blocked == True:
        flash("Device is already blocked", "warning")
        return redirect(url_for("main.dashboard"))

    ip = router.public_ip_address  # Using local IP for internal SSH access (demo purposes)
    username = router.ssh_username
    ssh_key_path = SSH_PRIVATE_KEY_PATH
    print(ssh_key_path)

    # ssh_command = f"sudo iptables -A INPUT -m mac --mac-source {mac} -j DROP && sudo iptables -A FORWARD -m mac --mac-source {mac} -j DROP"
    ssh_command = "arp -e"

    result = execute_ssh_command(ssh_command, "Blocked", rpi_mac, mac, ip, username, ssh_key_path)
    print(result)

    device.if_blocked = True
    db.session.commit()

    flash(result, "info")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/unblock/<rpi_mac>/<mac>")
@admin_required
def unblock_device(rpi_mac, mac):
    router = Router.query.filter_by(mac_address=rpi_mac).first()
    if not router:
        flash("Router not found", "danger")
        return redirect(url_for("main.dashboard"))

    device = Device.query.filter_by(mac_address=mac).first()
    if not device:
        flash("Device not found", "danger")
        return redirect(url_for("main.dashboard"))

    if device.if_blocked == False:
        flash("Device is already unblocked", "warning")
        return redirect(url_for("main.dashboard"))

    ip = router.public_ip_address  # Using local IP for internal SSH access (demo purposes)
    username = router.ssh_username
    ssh_key_path = SSH_PRIVATE_KEY_PATH

    # ssh_command = f"sudo iptables -D INPUT -m mac --mac-source {mac} -j DROP && sudo iptables -D FORWARD -m mac --mac-source {mac} -j DROP"
    ssh_command = "arp -e"

    result = execute_ssh_command(ssh_command, "Unblocked", rpi_mac, mac, ip, username, ssh_key_path)
    print(result)

    device.if_blocked = False
    db.session.commit()

    flash(result, "info")
    return redirect(url_for("main.dashboard"))



# GeoIP and Traceroute
@main_bp.route("/enrich_flows")
def route_enrich_flows():
    result = enrich_flows()
    return result