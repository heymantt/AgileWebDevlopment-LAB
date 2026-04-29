from flask import Blueprint, render_template

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/")
def leaderboard_home():
    return render_template("leaderboard/index.html", page_title="Leaderboard")