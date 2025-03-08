from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify

from src.decorators import admin_required
from src.models import db, User, Router, Device
from src.ssh_client import execute_ssh_command
from src.app import login_manager
from src.influxdb_funcs import (
    batch_query_flux_last_seen, batch_query_flux_flows,
    batch_query_flux_traffic, update_devices, update_routers
)

from src.config import SSH_PRIVATE_KEY_PATH


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
    routers = Router.query.all()
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


@main_bp.route('/update_routers', methods=["GET"])
@login_required
def route_update_routers():
    update_routers()
    return redirect(url_for("main.dashboard"))


@main_bp.route('/update_devices', methods=["GET"])
@login_required
def route_update_devices():
    update_devices()
    return redirect(url_for("main.dashboard"))



# Route to Add Router
@main_bp.route("/add_router", methods=["GET", "POST"])
@admin_required
def add_router():
    if request.method == "POST":
        rpi_mac = request.form["rpi_mac"]
        public_ip = request.form["public_ip"]
        local_ip = request.form["local_ip"]
        username = request.form["username"]

        # Store in DB
        new_router = Router(
            mac_address=rpi_mac,
            public_ip_address=public_ip,
            local_ip_address=local_ip,
            username=username
        )
        db.session.add(new_router)
        db.session.commit()
        flash("Router added successfully!", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("add_router.html")


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
    username = router.username
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
    username = router.username
    ssh_key_path = SSH_PRIVATE_KEY_PATH

    # ssh_command = f"sudo iptables -D INPUT -m mac --mac-source {mac} -j DROP && sudo iptables -D FORWARD -m mac --mac-source {mac} -j DROP"
    ssh_command = "arp -e"

    result = execute_ssh_command(ssh_command, "Unblocked", rpi_mac, mac, ip, username, ssh_key_path)
    print(result)

    device.if_blocked = False
    db.session.commit()

    flash(result, "info")
    return redirect(url_for("main.dashboard"))



### INFLUXDB RELATED
@main_bp.route("/router/<router_mac>")
@login_required
def router_details(router_mac):
    router = Router.query.filter_by(mac_address=router_mac).first()
    if not router:
        flash("Router not found", "danger")
        return redirect(url_for("main.dashboard"))

    # Get all device IPs
    device_ips = [device.local_ip_address for device in router.devices]
    
    # Query all metrics for these devices in batch
    last_seen_map = batch_query_flux_last_seen(device_ips)
    flows_map = batch_query_flux_flows(device_ips)
    traffic_map = batch_query_flux_traffic(device_ips)

    devices = []
    for device in router.devices:
        ip = device.local_ip_address
        devices.append({
            "mac_address": device.mac_address,
            "local_ip_address": ip,
            "last_seen_active": last_seen_map.get(ip, "N/A"),
            "flows_last_hour": flows_map.get(ip, {}).get("1h", 0),
            "avg_flows_per_hour": flows_map.get(ip, {}).get("30d", 0),
            "incoming_traffic_last_hour": traffic_map.get(ip, {}).get("incoming_1h", "0 B"),
            "avg_incoming_traffic": traffic_map.get(ip, {}).get("incoming_30d", "0 B"),
            "outgoing_traffic_last_hour": traffic_map.get(ip, {}).get("outgoing_1h", "0 B"),
            "avg_outgoing_traffic": traffic_map.get(ip, {}).get("outgoing_30d", "0 B"),
        })

    return render_template("dashboard_router_detailed.html", router=router, devices=devices)


@main_bp.route("/router/<router_mac>/traffic")
@login_required
def get_router_traffic(router_mac):
    router = Router.query.filter_by(mac_address=router_mac).first()
    if not router:
        flash("Router not found", "danger")
        return redirect(url_for("main.dashboard"))

    incoming_traffic = query_flux_traffic("192.168.0.107", "incoming", "10m", with_timestamps=True)
    outgoing_traffic = query_flux_traffic("192.168.0.107", "outgoing", "10m", with_timestamps=True)

    print("###############################################################")
    print(router.local_ip_address)
    # print(incoming_traffic)

    return jsonify({"incoming": incoming_traffic, "outgoing": outgoing_traffic})
