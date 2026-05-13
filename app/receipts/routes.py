import os
from datetime import datetime, date
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Receipt

receipts_bp = Blueprint("receipts", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@receipts_bp.route("/upload", methods=["GET", "POST"])
@login_required
def upload_receipt():
    if request.method == "POST":
        merchant = request.form.get("merchant", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date_raw = request.form.get("expense_date", "").strip()
        notes = request.form.get("notes", "").strip()
        file = request.files.get("receipt_image")

        errors = []

        if not merchant:
            errors.append("Merchant is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not category:
            errors.append("Category is required.")
        if not expense_date_raw:
            errors.append("Date is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = 0

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date must be valid.")
            expense_date = date.today()

        image_filename = None
        if file and file.filename:
            if not allowed_file(file.filename):
                errors.append("Only PNG, JPG, JPEG, WEBP, and PDF files are allowed.")
            else:
                original_name = secure_filename(file.filename)
                unique_name = f"{uuid4().hex}_{original_name}"
                image_filename = unique_name
                save_path = os.path.join(
                    current_app.config["RECEIPT_UPLOAD_FOLDER"],
                    unique_name
                )

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("receipts/upload.html", page_title="Upload Receipt")

        receipt = Receipt(
            user_id=current_user.id,
            merchant=merchant,
            amount=amount,
            category=category,
            expense_date=expense_date,
            notes=notes if notes else None,
            image_filename=image_filename
        )

        if file and file.filename and image_filename:
            save_path = os.path.join(
                current_app.config["RECEIPT_UPLOAD_FOLDER"],
                image_filename
            )
            file.save(save_path)

        db.session.add(receipt)
        db.session.commit()

        flash("Receipt uploaded successfully.", "success")
        return redirect(url_for("receipts.receipt_detail", receipt_id=receipt.id))

    return render_template("receipts/upload.html", page_title="Upload Receipt")




@receipts_bp.route("/archive")
@login_required
def archive():
    q = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()

    query = Receipt.query.filter_by(user_id=current_user.id)

    if q:
        like_term = f"%{q}%"
        query = query.filter(Receipt.merchant.ilike(like_term))

    if category:
        query = query.filter(Receipt.category == category)

    receipts = query.order_by(Receipt.expense_date.desc(), Receipt.created_at.desc()).all()

    categories = (
        db.session.query(Receipt.category)
        .filter_by(user_id=current_user.id)
        .distinct()
        .order_by(Receipt.category.asc())
        .all()
    )
    categories = [c[0] for c in categories]

    return render_template(
        "receipts/archive.html",
        page_title="Receipt Archive",
        receipts=receipts,
        categories=categories,
        selected_category=category,
        search_query=q
    )


@receipts_bp.route("/<int:receipt_id>")
@login_required
def receipt_detail(receipt_id):
    receipt = Receipt.query.filter_by(id=receipt_id, user_id=current_user.id).first_or_404()
    return render_template(
        "receipts/detail.html",
        page_title="Receipt Detail",
        receipt=receipt
    )


@receipts_bp.route("/<int:receipt_id>/edit", methods=["GET", "POST"])
@login_required
def edit_receipt(receipt_id):
    receipt = Receipt.query.filter_by(id=receipt_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        merchant = request.form.get("merchant", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date_raw = request.form.get("expense_date", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []

        if not merchant:
            errors.append("Merchant is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not category:
            errors.append("Category is required.")
        if not expense_date_raw:
            errors.append("Date is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = receipt.amount

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date must be valid.")
            expense_date = receipt.expense_date

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "receipts/edit.html",
                page_title="Edit Receipt",
                receipt=receipt
            )

        receipt.merchant = merchant
        receipt.amount = amount
        receipt.category = category
        receipt.expense_date = expense_date
        receipt.notes = notes if notes else None

        db.session.commit()

        flash("Receipt updated successfully.", "success")
        return redirect(url_for("receipts.receipt_detail", receipt_id=receipt.id))

    return render_template(
        "receipts/edit.html",
        page_title="Edit Receipt",
        receipt=receipt
    )