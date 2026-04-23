from flask import Blueprint, render_template

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup")
def signup():
    return render_template("auth/signup.html", page_title="Sign Up")


@auth_bp.route("/login")
def login():
    return render_template("auth/login.html", page_title="Login")


@auth_bp.route("/logout")
def logout():
    return render_template("auth/logout.html", page_title="Logout")