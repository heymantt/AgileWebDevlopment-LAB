from flask import Blueprint, render_template
from flask_login import login_required

from app.models import User

leaderboard_bp = Blueprint("leaderboard", __name__)


@leaderboard_bp.route("/")
@login_required
def leaderboard_home():
    users = (
        User.query
        .filter(User.total_points > 0)
        .order_by(
            User.total_points.desc(),
            User.current_streak.desc(),
            User.username.asc()
        )
        .all()
    )

    return render_template(
        "leaderboard/index.html",
        page_title="Leaderboard",
        users=users
    )