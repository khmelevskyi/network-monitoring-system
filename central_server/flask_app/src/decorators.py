from functools import wraps

from flask_login import current_user
from flask import redirect, url_for, flash

from src.models import User


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not User.query.filter_by(role='admin').first():
            return redirect(url_for('main.create_initial_admin'))
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You do not have permission to access this page.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
