from flask import Blueprint, render_template_string

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/login")
def login():
    return render_template_string("<h1>Login page</h1>")