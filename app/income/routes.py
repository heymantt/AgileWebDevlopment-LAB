from datetime import datetime, date, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user

from app.extensions import db
from app.models import Income

income_bp = Blueprint("income", __name__)

# Import Income model - will be created if needed
try:
    from app.models import Income
except ImportError:
    Income = None


@income_bp.route("/", methods=["GET", "POST"])
@login_required
def income_home():
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        start_date_raw = request.form.get("start_date", "").strip()
        end_date_raw = request.form.get("end_date", "").strip()
        frequency = request.form.get("frequency", "one-time").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        errors = []

        if not source:
            errors.append("Source is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not start_date_raw:
            errors.append("Start Date is required.")
        if not frequency:
            errors.append("Frequency is required.")
        if not category:
            errors.append("Category is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = 0

        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Start Date must be valid.")
            start_date = date.today()

        end_date = None
        if end_date_raw:
            try:
                end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
            except ValueError:
                errors.append("End Date must be valid.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            # Use start_date as income_date for backward compatibility
            entry = Income(
                user_id=current_user.id,
                source=source,
                amount=amount,
                income_date=start_date,  # Use start_date as income_date
                income_type=frequency,  # Store frequency in income_type for backward compatibility
                notes=description if description else None,
                frequency=frequency,
                category=category,
                start_date=start_date,
                end_date=end_date
            )
            db.session.add(entry)
            db.session.commit()
            flash("Income entry added successfully.", "success")
            return redirect(url_for("income.income_home"))

    incomes = (
        Income.query
        .filter_by(user_id=current_user.id)
        .order_by(Income.start_date.desc(), Income.created_at.desc())
        .all()
    )

    today = date.today()
    
    def should_count_income(item, current_date):
        """Check if income should be counted in the current month's total."""
        if not item.start_date:
            return False
        
        # Check if income has ended
        if item.end_date and item.end_date < current_date:
            return False
        
        # Get frequency value (handle both lowercase and any case variations)
        frequency = (item.frequency or "").lower().strip()
        
        # For one-time income, count only if it falls in the current month
        if frequency == "one-time":
            return (item.income_date.year == current_date.year and 
                    item.income_date.month == current_date.month)
        
        # For recurring income (daily, weekly, monthly, yearly), count if:
        # 1. It started on or before today
        # 2. It hasn't ended yet
        # 3. Frequency is one of the recurring types
        if item.start_date <= current_date and frequency in ["daily", "weekly", "monthly", "yearly"]:
            return True
        
        return False
    
    monthly_total = sum(
        item.amount for item in incomes
        if should_count_income(item, today)
    )

    return render_template(
        "income/index.html",
        page_title="Income",
        incomes=incomes,
        monthly_total=monthly_total,
        now=datetime.now(),
        timedelta=timedelta
    )


@income_bp.route("/<int:income_id>/edit", methods=["GET", "POST"])
@login_required
def edit_income(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    
    if request.method == "POST":
        source = request.form.get("source", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        start_date_raw = request.form.get("start_date", "").strip()
        end_date_raw = request.form.get("end_date", "").strip()
        frequency = request.form.get("frequency", "one-time").strip()
        category = request.form.get("category", "").strip()
        description = request.form.get("description", "").strip()

        errors = []

        if not source:
            errors.append("Source is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not start_date_raw:
            errors.append("Start Date is required.")
        if not frequency:
            errors.append("Frequency is required.")
        if not category:
            errors.append("Category is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = 0

        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Start Date must be valid.")
            start_date = date.today()

        end_date = None
        if end_date_raw:
            try:
                end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
            except ValueError:
                errors.append("End Date must be valid.")

        if errors:
            for error in errors:
                flash(error, "error")
        else:
            income.source = source
            income.amount = amount
            income.frequency = frequency
            income.category = category
            income.start_date = start_date
            income.end_date = end_date
            income.notes = description if description else None
            income.income_date = start_date  # Keep in sync
            income.income_type = frequency  # Keep in sync
            income.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash("Income entry updated successfully.", "success")
            return redirect(url_for("income.income_home"))
    
    return render_template(
        "income/edit.html",
        income=income,
        page_title="Edit Income"
    )


@income_bp.route("/<int:income_id>/delete", methods=["POST"])
@login_required
def delete_income(income_id):
    income = Income.query.filter_by(id=income_id, user_id=current_user.id).first_or_404()
    db.session.delete(income)
    db.session.commit()
    flash("Income entry deleted successfully.", "success")
    return redirect(url_for("income.income_home"))
