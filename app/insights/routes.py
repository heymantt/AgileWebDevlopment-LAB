from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date

from app.models import Receipt, Income
from . import insights_bp


@insights_bp.route("/")
@login_required
def insights_home():
    today = date.today()
    month_start = today.replace(day=1)

    monthly_income = (
        Income.query
        .filter(Income.user_id == current_user.id)
        .filter(Income.income_date >= month_start)
        .with_entities(func.coalesce(func.sum(Income.amount), 0))
        .scalar()
    )

    monthly_expenses = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= month_start)
        .with_entities(func.coalesce(func.sum(Receipt.amount), 0))
        .scalar()
    )

    balance = monthly_income - monthly_expenses

    savings_rate = 0
    if monthly_income > 0:
        savings_rate = (balance / monthly_income) * 100

    category_totals = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= month_start)
        .with_entities(
            Receipt.category,
            func.sum(Receipt.amount).label("total")
        )
        .group_by(Receipt.category)
        .order_by(func.sum(Receipt.amount).desc())
        .all()
    )

    recent_receipts = (
        Receipt.query
        .filter_by(user_id=current_user.id)
        .order_by(Receipt.expense_date.desc())
        .limit(5)
        .all()
    )

    receipt_count = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= month_start)
        .count()
    )

    average_daily_spend = 0
    if today.day > 0:
        average_daily_spend = monthly_expenses / today.day

    largest_expense = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= month_start)
        .order_by(Receipt.amount.desc())
        .first()
    )

    top_category_percentage = 0
    if category_totals and monthly_expenses > 0:
        top_category_percentage = (category_totals[0][1] / monthly_expenses) * 100

    high_value_receipts = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= month_start)
        .filter(Receipt.amount >= 50)
        .order_by(Receipt.amount.desc())
        .limit(5)
        .all()
    )

    top_category = category_totals[0][0] if category_totals else None

    return render_template(
        "insights/insights.html",
        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        balance=balance,
        savings_rate=savings_rate,
        category_totals=category_totals,
        recent_receipts=recent_receipts,
        top_category=top_category,
        receipt_count=receipt_count,
        average_daily_spend=average_daily_spend,
        largest_expense=largest_expense,
        top_category_percentage=top_category_percentage,
        high_value_receipts=high_value_receipts
    )