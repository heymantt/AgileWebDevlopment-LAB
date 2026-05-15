from flask import Blueprint, render_template, request, redirect, url_for, flash

from flask_login import current_user, login_user, logout_user

from app.extensions import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    print("SIGNUP ROUTE HIT")

    if current_user.is_authenticated:
        print("USER ALREADY AUTHENTICATED")
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        print("POST RECEIVED")
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        print("FORM DATA:", username, email)

        errors = []

        if not username:
            errors.append("Username is required.")
        if not email:
            errors.append("Email is required.")
        if not password:
            errors.append("Password is required.")
        if password != confirm_password:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long.")

        existing_username = User.query.filter_by(username=username).first()
        if existing_username:
            errors.append("That username is already taken.")

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            errors.append("That email is already registered.")

        print("ERRORS:", errors)

        if errors:
            for error in errors:
                flash(error, "error")
            print("RETURNING SIGNUP PAGE AGAIN")
            return render_template("auth/signup.html", page_title="Sign Up")

        user = User(username=username, email=email)
        user.set_password(password)

        print("ADDING USER TO DB")
        db.session.add(user)
        db.session.commit()
        print("USER CREATED:", user.id, user.username, user.email)

        flash("Account created successfully. Please log in.", "success")
        print("REDIRECTING TO LOGIN")
        return redirect(url_for("auth.login"))

    return render_template("auth/signup.html", page_title="Sign Up")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html", page_title="Login")

        login_user(user)
        flash("Logged in successfully.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html", page_title="Login")

@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "success")
    return redirect(url_for("main.landing"))


@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    """Handle forgot password requests."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        
        if user:
            # In production, generate a secure token and send email
            # For now, we'll show a success message
            pass
        
        # Always show success message for security
        flash("If an account exists with that email, you will receive password reset instructions.", "success")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/forgot_password.html", page_title="Forgot Password")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    """Handle password reset via token."""
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    
    if request.method == "POST":
        new_password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        
        errors = []
        if not new_password:
            errors.append("Password is required.")
        if new_password != confirm_password:
            errors.append("Passwords do not match.")
        if len(new_password) < 6:
            errors.append("Password must be at least 6 characters long.")
        
        if errors:
            for error in errors:
                flash(error, "error")
            return render_template("auth/reset_password.html", token=token, page_title="Reset Password")
        
        # In production, verify token and reset password
        flash("Password reset would be processed here. Feature coming soon.", "info")
        return redirect(url_for("auth.login"))
    
    return render_template("auth/reset_password.html", token=token, page_title="Reset Password")