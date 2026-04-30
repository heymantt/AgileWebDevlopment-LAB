from flask import Blueprint, render_template
from flask_login import login_required

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def landing():
    return render_template("landing.html", page_title="TrackMint")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", page_title="Dashboard")

@main_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", page_title="Profile")

from flask_login import current_user

@main_bp.route("/debug-auth")
def debug_auth():
    return f"""
    authenticated: {current_user.is_authenticated}<br>
    id: {getattr(current_user, 'id', None)}<br>
    username: {getattr(current_user, 'username', None)}
    """