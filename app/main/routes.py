from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import User

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def landing():
    return render_template("landing.html", page_title="TrackMint")

@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", page_title="Dashboard")

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