from flask import Blueprint, render_template
from flask_login import login_required


insights_bp = Blueprint("insights", __name__)


@insights_bp.route("/")
@login_required
def insights_home():
    return render_template("insights/index.html", page_title="Monthly Insights")