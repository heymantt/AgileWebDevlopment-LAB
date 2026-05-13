from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from datetime import datetime, date

income_bp = Blueprint("income", __name__)

# Import Income model - will be created if needed
try:
    from app.models import Income
except ImportError:
    Income = None


@income_bp.route("/")
@login_required
def income_home():
    """Display income tracking page with all user's income records."""
    if Income is None:
        return render_template("income/index.html", page_title="Income", income_records=[], total_income=0)
    
    income_records = Income.query.filter_by(user_id=current_user.id).order_by(Income.income_date.desc()).all()
    total_income = sum(record.amount for record in income_records)
    return render_template("income/index.html", page_title="Income", income_records=income_records, total_income=total_income)


@income_bp.route("/add", methods=["POST"])
@login_required
def add_income():
    """Add new income record."""
    if Income is None:
        return jsonify({'success': False, 'message': 'Income feature not configured'}), 500
    
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('amount') or not data.get('source'):
            return jsonify({'success': False, 'message': 'Amount and source are required'}), 400
        
        try:
            amount = float(data.get('amount'))
            if amount <= 0:
                return jsonify({'success': False, 'message': 'Amount must be greater than 0'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'message': 'Invalid amount'}), 400
        
        income_date = data.get('income_date')
        if income_date:
            try:
                income_date = datetime.strptime(income_date, '%Y-%m-%d').date()
            except ValueError:
                income_date = date.today()
        else:
            income_date = date.today()
        
        # Create new income record
        new_income = Income(
            user_id=current_user.id,
            amount=amount,
            source=data.get('source'),
            description=data.get('description', ''),
            income_date=income_date
        )
        
        db.session.add(new_income)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Income added successfully', 'id': new_income.id}), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@income_bp.route("/<int:income_id>/delete", methods=["POST"])
@login_required
def delete_income(income_id):
    """Delete an income record."""
    if Income is None:
        return jsonify({'success': False, 'message': 'Income feature not configured'}), 500
    
    try:
        income = Income.query.filter_by(id=income_id, user_id=current_user.id).first()
        
        if not income:
            return jsonify({'success': False, 'message': 'Income record not found'}), 404
        
        db.session.delete(income)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Income deleted successfully'}), 200
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500