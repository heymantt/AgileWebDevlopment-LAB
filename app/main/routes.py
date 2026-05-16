from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from sqlalchemy import func
from datetime import date

from app.extensions import db
from app.models import User, Receipt, Income

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def landing():
    return render_template("landing.html", page_title="TrackMint")

@main_bp.route("/dashboard")
@login_required
def dashboard():
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

    from app.models import Group
    active_groups = Group.query.filter_by(creator_id=current_user.id).count()

    return render_template(
        "dashboard.html",
        page_title="Dashboard",
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
        active_groups=active_groups,
    )

@main_bp.route("/profile")
@login_required
def profile():
    return render_template("profile.html", page_title="Profile")


@main_bp.route("/profile/update", methods=["POST"])
@login_required
def update_profile():
    """Update user profile information."""
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        
        if not username:
            return jsonify({'success': False, 'message': 'Username is required'}), 400
        
        # Check if username is already taken
        existing_user = User.query.filter_by(username=username).first()
        if existing_user and existing_user.id != current_user.id:
            return jsonify({'success': False, 'message': 'Username already taken'}), 400
        
        current_user.username = username
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Profile updated successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route("/profile/change-password", methods=["POST"])
@login_required
def change_password():
    """Change user password."""
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        confirm_password = data.get('confirm_password', '')
        
        # Validate inputs
        if not old_password or not new_password or not confirm_password:
            return jsonify({'success': False, 'message': 'All fields are required'}), 400
        
        # Check old password
        if not current_user.check_password(old_password):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # Check passwords match
        if new_password != confirm_password:
            return jsonify({'success': False, 'message': 'New passwords do not match'}), 400
        
        # Check password length
        if len(new_password) < 6:
            return jsonify({'success': False, 'message': 'Password must be at least 6 characters long'}), 400
        
        # Update password
        current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@main_bp.route("/debug-auth")
def debug_auth():
    return f"""
    authenticated: {current_user.is_authenticated}<br>
    id: {getattr(current_user, 'id', None)}<br>
    username: {getattr(current_user, 'username', None)}
    """