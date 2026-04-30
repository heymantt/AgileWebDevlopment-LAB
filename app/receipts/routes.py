from flask import Blueprint, render_template
from flask_login import login_required

receipts_bp = Blueprint("receipts", __name__)


@receipts_bp.route("/upload")
@login_required
def upload_receipt():
    return render_template("receipts/upload.html", page_title="Upload Receipt")


@receipts_bp.route("/archive")
@login_required
def archive():
    return render_template("receipts/archive.html", page_title="Receipt Archive")


@receipts_bp.route("/<int:receipt_id>")
@login_required
def receipt_detail(receipt_id):
    return render_template(
        "receipts/detail.html",
        page_title="Receipt Detail",
        heading=f"Receipt Detail #{receipt_id}"
    )