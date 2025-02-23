from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, redirect, url_for, request, flash

from src.decorators import admin_required
from src.models import db, User, Router, Device
from src.ssh_client import execute_ssh_command
from src.app import login_manager
from src.influxdb_funcs import update_devices


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


@main_bp.route('/update_devices', methods=["GET"])
@login_required
def route_update_devices():
    update_devices()
    return "Devices updated successfully"



# Route to Add Router
@main_bp.route("/add_router", methods=["GET", "POST"])
@admin_required
def add_router():
    if request.method == "POST":
        rpi_mac = request.form["rpi_mac"]
        public_ip = request.form["public_ip"]
        local_ip = request.form["local_ip"]
        username = request.form["username"]
        ssh_key_file = request.form["ssh_key_file"]  # Only filename

        # Store in DB
        new_router = Router(
            mac_address=rpi_mac,
            public_ip_address=public_ip,
            local_ip_address=local_ip,
            username=username,
            ssh_key_file=ssh_key_file
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
        return "Router not found", 404

    ip = router.public_ip_address  # Using local IP for internal SSH access (demo purposes)
    username = router.username
    ssh_key_path = f"/{router.ssh_key_file}"

    # ssh_command = f"sudo iptables -A INPUT -m mac --mac-source {mac} -j DROP && sudo iptables -A FORWARD -m mac --mac-source {mac} -j DROP"
    ssh_command = "arp -e"

    result = execute_ssh_command(ssh_command, "Blocked", ip, username, ssh_key_path)
    print(result)
    flash(result, "info")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/unblock/<rpi_mac>/<mac>")
@admin_required
def unblock_device(rpi_mac, mac):
    router = Router.query.filter_by(mac_address=rpi_mac).first()
    if not router:
        return "Router not found", 404

    ip = router.public_ip_address  # Using local IP for internal SSH access (demo purposes)
    username = router.username
    ssh_key_path = f"/{router.ssh_key_file}"

    ssh_command = f"sudo iptables -D INPUT -m mac --mac-source {mac} -j DROP && sudo iptables -D FORWARD -m mac --mac-source {mac} -j DROP"

    result = execute_ssh_command(ssh_command, "Unblocked", ip, username, ssh_key_path)
    print(result)
    flash(result, "info")
    return redirect(url_for("main.dashboard"))
