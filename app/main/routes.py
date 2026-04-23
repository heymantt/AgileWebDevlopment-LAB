from flask import Blueprint, render_template

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def landing():
    return render_template("landing.html", page_title="TrackMint")


@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", page_title="Dashboard")


@main_bp.route("/profile")
def profile():
    return render_template("profile.html", page_title="Profile")