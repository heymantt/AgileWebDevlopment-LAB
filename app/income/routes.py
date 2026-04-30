from datetime import datetime, date

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Income

income_bp = Blueprint("income", __name__)


@income_bp.route("/", methods=["GET", "POST"])
@login_required
def income_home():
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        income_date_raw = request.form.get("income_date", "").strip()
        income_type = request.form.get("income_type", "").strip()
        notes = request.form.get("notes", "").strip()

        errors = []

        if not source:
            errors.append("Source is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not income_date_raw:
            errors.append("Date is required.")
        if not income_type:
            errors.append("Income type is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = 0

        try:
            income_date = datetime.strptime(income_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date must be valid.")
            income_date = date.today()

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            entry = Income(
                user_id=current_user.id,
                source=source,
                amount=amount,
                income_date=income_date,
                income_type=income_type,
                notes=notes if notes else None
            )
            db.session.add(entry)
            db.session.commit()
            flash("Income entry added successfully.", "success")
            return redirect(url_for("income.income_home"))

    incomes = (
        Income.query
        .filter_by(user_id=current_user.id)
        .order_by(Income.income_date.desc(), Income.created_at.desc())
        .all()
    )

    today = date.today()
    monthly_total = sum(
        item.amount for item in incomes
        if item.income_date.year == today.year and item.income_date.month == today.month
    )

    return render_template(
        "income/index.html",
        page_title="Income",
        incomes=incomes,
        monthly_total=monthly_total
    )