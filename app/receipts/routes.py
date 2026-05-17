import os
from datetime import datetime, date, timedelta
from uuid import uuid4

from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import Receipt, ExpenseSplit, GroupMember

receipts_bp = Blueprint("receipts", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "pdf"}


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@receipts_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """Unified expenses page - displays expenses list with integrated add form."""
    
    # Handle POST requests (new expense submission)
    if request.method == "POST":
        merchant = request.form.get("merchant", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date_raw = request.form.get("expense_date", "").strip()
        notes = request.form.get("notes", "").strip()
        frequency = request.form.get("frequency", "one-time").strip()
        frequency_interval = request.form.get("frequency_interval", "").strip()
        frequency_details = request.form.get("frequency_details", "").strip()
        file = request.files.get("receipt_image")

        errors = []

        if not merchant:
            errors.append("Merchant is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not category:
            errors.append("Category is required.")
        if not expense_date_raw:
            errors.append("Date is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = 0

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date must be valid.")
            expense_date = date.today()

        image_filename = None
        save_path = None
        if file and file.filename:
            if not allowed_file(file.filename):
                errors.append("Only PNG, JPG, JPEG, WEBP, and PDF files are allowed.")
            else:
                original_name = secure_filename(file.filename)
                unique_name = f"{uuid4().hex}_{original_name}"
                image_filename = unique_name
                save_path = os.path.join(
                    current_app.config["RECEIPT_UPLOAD_FOLDER"],
                    unique_name
                )

        if errors:
            for error in errors:
                flash(error, "error")
            # Re-render the page with the form visible
            q = request.args.get("q", "").strip()
            category_filter = request.args.get("category", "").strip()
            frequency_filter = request.args.get("frequency", "").strip()
            query = Receipt.query.filter_by(user_id=current_user.id)
            
            if q:
                like_term = f"%{q}%"
                query = query.filter(Receipt.merchant.ilike(like_term))
            
            if category_filter:
                query = query.filter(Receipt.category == category_filter)
            
            if frequency_filter:
                query = query.filter(Receipt.frequency_type == frequency_filter)
            
            expenses = query.order_by(Receipt.expense_date.desc(), Receipt.created_at.desc()).all()

            member_map = {}
            group_receipt_ids = [e.id for e in expenses if e.group_id]
            if group_receipt_ids:
                user_members = GroupMember.query.filter_by(user_id=current_user.id).all()
                member_ids = [m.id for m in user_members]
                if member_ids:
                    splits = ExpenseSplit.query.filter(
                        ExpenseSplit.expense_id.in_(group_receipt_ids),
                        ExpenseSplit.member_id.in_(member_ids)
                    ).all()
                    for s in splits:
                        member_map[s.expense_id] = s.amount
            for e in expenses:
                if e.group_id and e.id in member_map:
                    e.display_amount = member_map[e.id]
                    e.is_group_split = True
                else:
                    e.display_amount = e.amount
                    e.is_group_split = False
            
            categories = (
                db.session.query(Receipt.category)
                .filter_by(user_id=current_user.id)
                .distinct()
                .order_by(Receipt.category.asc())
                .all()
            )
            categories = [c[0] for c in categories]
            
            return render_template(
                "receipts/index.html",
                page_title="Expenses",
                expenses=expenses,
                categories=categories,
                selected_category=category_filter,
                search_query=q,
                selected_frequency=frequency_filter
            )

        # Create and save the receipt
        receipt = Receipt(
            user_id=current_user.id,
            merchant=merchant,
            amount=amount,
            category=category,
            expense_date=expense_date,
            notes=notes if notes else None,
            frequency_type=frequency,
            frequency_interval=frequency_interval if frequency == "recurring" else None,
            frequency_details=frequency_details if frequency == "recurring" else None,
            image_filename=image_filename
        )

        if file and file.filename and image_filename and save_path:
            file.save(save_path)

        db.session.add(receipt)
        
        today = date.today()

        # Award points for tracking an expense
        current_user.total_points += 10

        # Update streak only once per day
        if current_user.last_upload_date is None:
            current_user.current_streak = 1
        elif current_user.last_upload_date == today:
            pass
        elif current_user.last_upload_date == today - timedelta(days=1):
            current_user.current_streak += 1
        else:
            current_user.current_streak = 1

        current_user.last_upload_date = today
        
        db.session.commit()

        flash("Expense added successfully.", "success")
        # Redirect to the expense detail page after successful submission
        return redirect(url_for("receipts.receipt_detail", receipt_id=receipt.id))

    # Handle GET requests (display the page with list and form)
    q = request.args.get("q", "").strip()
    category_filter = request.args.get("category", "").strip()
    frequency_filter = request.args.get("frequency", "").strip()

    query = Receipt.query.filter_by(user_id=current_user.id)

    if q:
        like_term = f"%{q}%"
        query = query.filter(Receipt.merchant.ilike(like_term))

    if category_filter:
        query = query.filter(Receipt.category == category_filter)

    if frequency_filter:
        query = query.filter(Receipt.frequency_type == frequency_filter)

    personal_expenses = query.order_by(Receipt.expense_date.desc(), Receipt.created_at.desc()).all()

    # Also fetch group expenses the user is a member of (but didn't create)
    user_members = GroupMember.query.filter_by(user_id=current_user.id).all()
    member_group_ids = [m.group_id for m in user_members]
    member_receipt_ids = {e.id for e in personal_expenses if e.group_id}

    group_expenses_query = Receipt.query.filter(
        Receipt.group_id.in_(member_group_ids),
        Receipt.id.notin_(member_receipt_ids)
    ) if member_group_ids else Receipt.query.filter(db.false())

    if q:
        group_expenses_query = group_expenses_query.filter(Receipt.merchant.ilike(f"%{q}%"))
    if category_filter:
        group_expenses_query = group_expenses_query.filter(Receipt.category == category_filter)

    group_only_expenses = group_expenses_query.order_by(Receipt.expense_date.desc(), Receipt.created_at.desc()).all()

    expenses = personal_expenses + group_only_expenses
    expenses.sort(key=lambda e: (e.expense_date, e.created_at), reverse=True)

    # For group expenses, show the current user's split amount instead of full amount
    member_map = {}
    group_receipt_ids = [e.id for e in expenses if e.group_id]
    if group_receipt_ids and user_members:
        member_ids = [m.id for m in user_members]
        if member_ids:
            splits = ExpenseSplit.query.filter(
                ExpenseSplit.expense_id.in_(group_receipt_ids),
                ExpenseSplit.member_id.in_(member_ids)
            ).all()
            for s in splits:
                member_map[s.expense_id] = s.amount

    for e in expenses:
        if e.group_id and e.id in member_map:
            e.display_amount = member_map[e.id]
            e.is_group_split = True
        else:
            e.display_amount = e.amount
            e.is_group_split = False

    categories = (
        db.session.query(Receipt.category)
        .filter_by(user_id=current_user.id)
        .distinct()
        .order_by(Receipt.category.asc())
        .all()
    )
    categories = [c[0] for c in categories]

    return render_template(
        "receipts/index.html",
        page_title="Expenses",
        expenses=expenses,
        categories=categories,
        selected_category=category_filter,
        search_query=q,
        selected_frequency=frequency_filter
    )


@receipts_bp.route("/upload", methods=["GET"])
@login_required
def upload_receipt():
    """Redirect to the unified expenses page."""
    return redirect(url_for("receipts.index"))


@receipts_bp.route("/archive", methods=["GET"])
@login_required
def archive():
    """Redirect to the unified expenses page."""
    # Preserve query parameters for continuity
    q = request.args.get("q", "")
    category = request.args.get("category", "")
    
    if q or category:
        return redirect(url_for("receipts.index", q=q, category=category))
    return redirect(url_for("receipts.index"))


@receipts_bp.route("/<int:receipt_id>")
@login_required
def receipt_detail(receipt_id):
    from flask import abort
    # Allow viewing if user owns it, or is a member of the group it belongs to
    receipt = Receipt.query.filter_by(id=receipt_id, user_id=current_user.id).first()
    if receipt is None:
        receipt = Receipt.query.filter_by(id=receipt_id).first_or_404()
        is_member = GroupMember.query.filter_by(
            group_id=receipt.group_id, user_id=current_user.id
        ).first() if receipt.group_id else None
        if not is_member:
            abort(403)
    return render_template(
        "receipts/detail.html",
        page_title="Receipt Detail",
        receipt=receipt
    )


@receipts_bp.route("/<int:receipt_id>/edit", methods=["GET", "POST"])
@login_required
def edit_receipt(receipt_id):
    receipt = Receipt.query.filter_by(id=receipt_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        merchant = request.form.get("merchant", "").strip()
        amount_raw = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        expense_date_raw = request.form.get("expense_date", "").strip()
        notes = request.form.get("notes", "").strip()
        frequency = request.form.get("frequency", "one-time").strip()
        frequency_interval = request.form.get("frequency_interval", "").strip()
        frequency_details = request.form.get("frequency_details", "").strip()

        errors = []

        if not merchant:
            errors.append("Merchant is required.")
        if not amount_raw:
            errors.append("Amount is required.")
        if not category:
            errors.append("Category is required.")
        if not expense_date_raw:
            errors.append("Date is required.")

        try:
            amount = float(amount_raw)
            if amount <= 0:
                errors.append("Amount must be greater than 0.")
        except ValueError:
            errors.append("Amount must be a valid number.")
            amount = receipt.amount

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date must be valid.")
            expense_date = receipt.expense_date

        if errors:
            for error in errors:
                flash(error, "error")
            return render_template(
                "receipts/edit.html",
                page_title="Edit Receipt",
                receipt=receipt
            )

        receipt.merchant = merchant
        receipt.amount = amount
        receipt.category = category
        receipt.expense_date = expense_date
        receipt.notes = notes if notes else None
        receipt.frequency_type = frequency
        receipt.frequency_interval = frequency_interval if frequency == "recurring" else None
        receipt.frequency_details = frequency_details if frequency == "recurring" else None

        db.session.commit()

        flash("Receipt updated successfully.", "success")
        return redirect(url_for("receipts.receipt_detail", receipt_id=receipt.id))

    return render_template(
        "receipts/edit.html",
        page_title="Edit Receipt",
        receipt=receipt
    )


@receipts_bp.route("/<int:receipt_id>/delete", methods=["POST"])
@login_required
def delete_receipt(receipt_id):
    """Delete an expense record."""
    receipt = Receipt.query.filter_by(id=receipt_id, user_id=current_user.id).first_or_404()
    
    # Delete receipt image if it exists
    if receipt.image_filename:
        image_path = os.path.join(current_app.config["RECEIPT_UPLOAD_FOLDER"], receipt.image_filename)
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                current_app.logger.error(f"Error deleting image file: {e}")
    
    db.session.delete(receipt)
    db.session.commit()
    
    flash("Expense deleted successfully.", "success")
    return redirect(url_for("receipts.index"))