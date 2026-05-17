from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import current_user, login_user, logout_user

from flask_mail import Message
from app.extensions import db, mail
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

@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            try:
                send_password_reset_email(user)
                flash("A password reset link has been sent to your email.", "success")
            except Exception as e:
                import traceback
                print("EMAIL ERROR TYPE:", type(e))
                print("EMAIL ERROR MESSAGE:", repr(e))
                traceback.print_exc()
                flash("Password reset email could not be sent. Please try again later.", "error")
        else:
            flash("If an account exists with that email, a reset link has been sent.", "info")

        return redirect(url_for("auth.login"))

    return render_template("auth/forgot_password.html", page_title="Forgot Password")


@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    user = User.verify_reset_token(token)

    if user is None:
        flash("The password reset link is invalid or has expired.", "error")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "error")
            return render_template("auth/reset_password.html", page_title="Reset Password")

        if new_password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template("auth/reset_password.html", page_title="Reset Password")

        user.set_password(new_password)
        db.session.commit()

        flash("Your password has been reset. Please log in with your new password.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", page_title="Reset Password")



@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("You have been logged out.", "success")
    return redirect(url_for("main.landing"))

def send_password_reset_email(user):
    token = user.get_reset_token()

    reset_url = url_for(
        "auth.reset_password",
        token=token,
        _external=True
    )

    print("PASSWORD RESET LINK:", reset_url)

    sender = (current_app.config.get("MAIL_DEFAULT_SENDER") or "").strip()
    recipient = (user.email or "").strip().lower()

    print("SENDER:", repr(sender))
    print("RECIPIENT:", repr(recipient))

    msg = Message(
        subject="TrackMint Password Reset",
        sender=sender,
        recipients=[recipient]
    )

    msg.body = f"""Hello {user.username},

A password reset was requested for your TrackMint account.

Click the link below to reset your password:

{reset_url}

This link will expire in 30 minutes.

If you did not request this password reset, you can ignore this email.

TrackMint Team
"""

    mail.send(msg)