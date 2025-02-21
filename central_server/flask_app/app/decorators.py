from functools import wraps

from flask_login import current_user
from flask import redirect, url_for, flash


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.role != "admin":
            flash("Access denied. Admins only!", "danger")
            return redirect(url_for("main.dashboard"))
        return f(*args, **kwargs)
    return decorated_function
