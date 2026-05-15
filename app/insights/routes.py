from flask import render_template
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date, timedelta

from app.models import Receipt, Income
from . import insights_bp


def get_month_range(year=None, month=None):
    """Get start and end dates for a given month"""
    if year is None and month is None:
        today = date.today()
    else:
        today = date(year, month, 1)
    
    month_start = today.replace(day=1)
    if month == 12:
        month_end = month_start.replace(year=month_start.year + 1, month=1) - timedelta(days=1)
    else:
        month_end = month_start.replace(month=month_start.month + 1) - timedelta(days=1)
    
    return month_start, month_end


@insights_bp.route("/")
@login_required
def insights_home():
    today = date.today()
    month_start = today.replace(day=1)
    
    # Previous month dates
    prev_month_date = today.replace(day=1) - timedelta(days=1)
    prev_month_start = prev_month_date.replace(day=1)
    prev_month_end = today.replace(day=1) - timedelta(days=1)

    # Current month calculations
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

    # Previous month calculations for comparison
    prev_monthly_income = (
        Income.query
        .filter(Income.user_id == current_user.id)
        .filter(Income.income_date >= prev_month_start)
        .filter(Income.income_date <= prev_month_end)
        .with_entities(func.coalesce(func.sum(Income.amount), 0))
        .scalar()
    )

    prev_monthly_expenses = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= prev_month_start)
        .filter(Receipt.expense_date <= prev_month_end)
        .with_entities(func.coalesce(func.sum(Receipt.amount), 0))
        .scalar()
    )

    # Calculate percentage changes
    expense_change_pct = 0
    if prev_monthly_expenses > 0:
        expense_change_pct = ((monthly_expenses - prev_monthly_expenses) / prev_monthly_expenses) * 100
    
    income_change_pct = 0
    if prev_monthly_income > 0:
        income_change_pct = ((monthly_income - prev_monthly_income) / prev_monthly_income) * 100

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

    # Calculate year-to-date statistics
    year_start = date(today.year, 1, 1)
    ytd_income = (
        Income.query
        .filter(Income.user_id == current_user.id)
        .filter(Income.income_date >= year_start)
        .with_entities(func.coalesce(func.sum(Income.amount), 0))
        .scalar()
    )

    ytd_expenses = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= year_start)
        .with_entities(func.coalesce(func.sum(Receipt.amount), 0))
        .scalar()
    )

    # Recurring expenses analysis
    recurring_monthly = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.frequency_type == "recurring")
        .filter(Receipt.frequency_interval == "monthly")
        .with_entities(func.coalesce(func.sum(Receipt.amount), 0))
        .scalar()
    )

    # Get all receipts for current month with dates to estimate daily/weekly patterns
    all_month_receipts = (
        Receipt.query
        .filter(Receipt.user_id == current_user.id)
        .filter(Receipt.expense_date >= month_start)
        .order_by(Receipt.expense_date.desc())
        .all()
    )

    # Calculate days remaining in month
    if today.month == 12:
        next_month = date(today.year + 1, 1, 1)
    else:
        next_month = date(today.year, today.month + 1, 1)
    days_in_month = (next_month - month_start).days
    days_remaining = (next_month - today).days

    # Projected month-end spending (if current pace continues)
    projected_end_spending = 0
    if today.day > 0:
        daily_average = monthly_expenses / today.day
        projected_end_spending = daily_average * days_in_month

    # Budget health score (0-100)
    budget_health = 100
    if monthly_income > 0:
        budget_utilization = (monthly_expenses / monthly_income) * 100
        if budget_utilization < 50:
            budget_health = 100
        elif budget_utilization < 80:
            budget_health = 80
        elif budget_utilization < 100:
            budget_health = 60
        else:
            budget_health = max(0, 100 - (budget_utilization - 100) * 2)

    return render_template(
        "insights/insights.html",
        # Current month data
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
        high_value_receipts=high_value_receipts,
        # Comparison data
        prev_monthly_income=prev_monthly_income,
        prev_monthly_expenses=prev_monthly_expenses,
        expense_change_pct=expense_change_pct,
        income_change_pct=income_change_pct,
        # YTD data
        ytd_income=ytd_income,
        ytd_expenses=ytd_expenses,
        # Recurring expenses
        recurring_monthly=recurring_monthly,
        # Projections and analysis
        projected_end_spending=projected_end_spending,
        days_remaining=days_remaining,
        days_in_month=days_in_month,
        budget_health=budget_health,
        current_day=today.day,
        current_month=today.month,
        current_year=today.year,
        today=today
    )