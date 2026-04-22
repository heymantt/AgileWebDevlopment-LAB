from flask import Blueprint, render_template_string

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    return render_template_string("<h1>TrackMint is running</h1>")