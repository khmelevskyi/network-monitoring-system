from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required
from flask import Blueprint, render_template, redirect, url_for, request, flash

from decorators import admin_required
from models import db, User, Router, Device
from ssh_client import block_device, unblock_device
from app_init import login_manager

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

# Admin-Only Page
@main_bp.route("/admin")
@login_required
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

# Block/Unblock Device (Admin Only)
@main_bp.route("/block/<mac>")
@login_required
@admin_required
def block(mac):
    result = block_device(mac)
    flash(result, "info")
    return redirect(url_for("main.dashboard"))

@main_bp.route("/unblock/<mac>")
@login_required
@admin_required
def unblock(mac):
    result = unblock_device(mac)
    flash(result, "info")
    return redirect(url_for("main.dashboard"))
