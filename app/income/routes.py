from flask import Blueprint, render_template

income_bp = Blueprint("income", __name__)


@income_bp.route("/")
def income_home():
    return render_template("income/index.html", page_title="Income")