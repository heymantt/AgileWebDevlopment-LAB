from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models import Income

income_bp = Blueprint("income", __name__)


@income_bp.route("/", methods=["GET", "POST"])
@login_required
def income_home():
    """Display income tracking page and handle adding new income."""
    if request.method == "POST":
        try:
            source = request.form.get("source", "").strip()
            amount = request.form.get("amount", "0")
            category = request.form.get("category", "Other")
            description = request.form.get("description", "").strip()
            income_date_str = request.form.get("income_date", "")

            # Validate inputs
            errors = []
            
            if not source:
                errors.append("Income source is required.")
            
            try:
                amount = Decimal(amount)
                if amount <= 0:
                    errors.append("Amount must be greater than 0.")
            except:
                errors.append("Please enter a valid amount.")
            
            if not income_date_str:
                errors.append("Date is required.")
            
            if errors:
                for error in errors:
                    flash(error, "error")
                return render_template("income/index.html", page_title="Income")

            # Parse the date
            try:
                income_date = datetime.strptime(income_date_str, "%Y-%m-%d").date()
            except:
                flash("Invalid date format.", "error")
                return render_template("income/index.html", page_title="Income")

            # Create new income record
            new_income = Income(
                user_id=current_user.id,
                source=source,
                amount=amount,
                category=category,
                description=description if description else None,
                income_date=income_date
            )

            db.session.add(new_income)
            db.session.commit()

            flash(f"✓ Income from '{source}' (${amount}) added successfully!", "success")
            return redirect(url_for("income.income_home"))

        except Exception as e:
            db.session.rollback()
            flash(f"Error adding income: {str(e)}", "error")
            return render_template("income/index.html", page_title="Income")

    # GET request - display income list
    incomes = Income.query.filter_by(user_id=current_user.id).order_by(Income.income_date.desc()).all()
    
    # Calculate total income
    total_income = sum(income.amount for income in incomes)
    
    # Group by category
    income_by_category = {}
    for income in incomes:
        cat = income.category
        if cat not in income_by_category:
            income_by_category[cat] = []
        income_by_category[cat].append(income)

    return render_template(
        "income/index.html", 
        page_title="Income",
        incomes=incomes,
        total_income=total_income,
        income_by_category=income_by_category
    )


@income_bp.route("/delete/<int:income_id>", methods=["POST"])
@login_required
def delete_income(income_id):
    """Delete an income record."""
    income = Income.query.get_or_404(income_id)
    
    # Check if user owns this income
    if income.user_id != current_user.id:
        flash("Unauthorized access.", "error")
        return redirect(url_for("income.income_home"))
    
    try:
        db.session.delete(income)
        db.session.commit()
        flash(f"✓ Income '{income.source}' deleted successfully!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting income: {str(e)}", "error")
    
    return redirect(url_for("income.income_home"))