from flask import Blueprint, render_template
from flask_login import login_required

income_bp = Blueprint("income", __name__)


@income_bp.route("/")
@login_required
def income_home():
    return render_template("income/index.html", page_title="Income")