from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models import Group, GroupMember, User, Receipt, ExpenseSplit

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/")
@login_required
def groups_home():
    """Display all groups created by the current user."""
    groups = Group.query.filter_by(creator_id=current_user.id).all()
    return render_template("groups/index.html", page_title="Groups", groups=groups)


@groups_bp.route("/create", methods=["POST"])
@login_required
def create_group():
    """Create a new group with optional members."""
    try:
        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        member_identifiers = data.get('members', [])
        if isinstance(member_identifiers, str):
            member_identifiers = [m.strip() for m in member_identifiers.split(',') if m.strip()]

        if not name:
            return jsonify({'success': False, 'message': 'Group name is required'}), 400

        if len(name) < 2:
            return jsonify({'success': False, 'message': 'Group name must be at least 2 characters long'}), 400

        if len(name) > 100:
            return jsonify({'success': False, 'message': 'Group name must be less than 100 characters'}), 400

        new_group = Group(
            creator_id=current_user.id,
            name=name,
            description=description if description else None
        )
        db.session.add(new_group)
        db.session.flush()

        for identifier in member_identifiers:
            identifier = identifier.strip()
            if not identifier:
                continue
            matched_user = User.query.filter(
                (User.username == identifier) | (User.email == identifier)
            ).first()
            member = GroupMember(
                group_id=new_group.id,
                user_id=matched_user.id if matched_user else None,
                identifier=identifier
            )
            db.session.add(member)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Group created successfully', 'id': new_group.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/edit", methods=["POST"])
@login_required
def edit_group(group_id):
    """Edit group name, description, and members."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        member_identifiers = data.get('members', [])
        if isinstance(member_identifiers, str):
            member_identifiers = [m.strip() for m in member_identifiers.split(',') if m.strip()]

        if not name or len(name) < 2:
            return jsonify({'success': False, 'message': 'Group name must be at least 2 characters long'}), 400

        if len(name) > 100:
            return jsonify({'success': False, 'message': 'Group name must be less than 100 characters'}), 400

        group.name = name
        group.description = description if description else None

        GroupMember.query.filter_by(group_id=group.id).delete()
        for identifier in member_identifiers:
            identifier = identifier.strip()
            if not identifier:
                continue
            matched_user = User.query.filter(
                (User.username == identifier) | (User.email == identifier)
            ).first()
            member = GroupMember(
                group_id=group.id,
                user_id=matched_user.id if matched_user else None,
                identifier=identifier
            )
            db.session.add(member)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Group updated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/delete", methods=["POST"])
@login_required
def delete_group(group_id):
    """Delete a group (creator only)."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        db.session.delete(group)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Group deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>")
@login_required
def group_detail(group_id):
    group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
    if not group:
        return render_template(
            "groups/detail.html",
            page_title="Group Detail",
            heading="Group not found",
            group=None
        )
    return render_template(
        "groups/detail.html",
        page_title="Group Detail",
        heading=group.name,
        group=group
    )


@groups_bp.route("/<int:group_id>/add-expense", methods=["POST"])
@login_required
def add_group_expense(group_id):
    """Add an expense to a group and split it among members."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form

        merchant = str(data.get('merchant', '') or '').strip()
        amount_raw = data.get('amount', '')
        category = str(data.get('category', '') or '').strip()
        expense_date_raw = str(data.get('expense_date', '') or '').strip()
        notes = str(data.get('notes', '') or '').strip()
        split_type = str(data.get('split_type', 'equal') or 'equal').strip()

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
        except (ValueError, TypeError):
            errors.append("Amount must be a valid number.")
            amount = 0

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            errors.append("Date must be valid.")
            expense_date = None

        if errors:
            return jsonify({'success': False, 'message': ' '.join(errors)}), 400

        if not group.members:
            return jsonify({'success': False, 'message': 'Group must have at least one member to add expenses'}), 400

        # Create the receipt
        receipt = Receipt(
            user_id=current_user.id,
            group_id=group.id,
            merchant=merchant,
            amount=amount,
            category=category,
            expense_date=expense_date,
            notes=notes if notes else None,
            frequency_type="one-time"
        )
        db.session.add(receipt)
        db.session.flush()

        # Create splits
        if split_type == 'equal':
            split_amount = round(amount / len(group.members), 2)
            for member in group.members:
                split = ExpenseSplit(
                    expense_id=receipt.id,
                    member_id=member.id,
                    amount=split_amount,
                    paid=False
                )
                db.session.add(split)
        else:
            # Custom split - expects member_splits in format: member_id:amount
            member_splits = data.get('member_splits', {})
            if isinstance(member_splits, str):
                # Parse from string if needed
                member_splits = {}
            
            for member in group.members:
                member_id_str = str(member.id)
                split_amount = float(member_splits.get(member_id_str, 0)) if member_id_str in member_splits else 0
                if split_amount > 0:
                    split = ExpenseSplit(
                        expense_id=receipt.id,
                        member_id=member.id,
                        amount=split_amount,
                        paid=False
                    )
                    db.session.add(split)

        db.session.commit()
        return jsonify({'success': True, 'message': 'Expense added successfully', 'id': receipt.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/expenses")
@login_required
def group_expenses(group_id):
    """Get all expenses for a group."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        expenses = Receipt.query.filter_by(group_id=group.id).order_by(Receipt.expense_date.desc()).all()
        
        expenses_data = []
        for expense in expenses:
            splits_data = []
            for split in expense.splits:
                splits_data.append({
                    'id': split.id,
                    'member_name': split.member.identifier,
                    'amount': split.amount,
                    'paid': split.paid
                })
            
            expenses_data.append({
                'id': expense.id,
                'merchant': expense.merchant,
                'amount': expense.amount,
                'category': expense.category,
                'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
                'notes': expense.notes,
                'splits': splits_data
            })

        return jsonify({'success': True, 'expenses': expenses_data}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/mark-paid/<int:split_id>", methods=["POST"])
@login_required
def mark_split_paid(group_id, split_id):
    """Mark an expense split as paid."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        split = ExpenseSplit.query.filter_by(id=split_id).first()
        if not split or split.expense.group_id != group.id:
            return jsonify({'success': False, 'message': 'Split not found'}), 404

        split.paid = not split.paid
        db.session.commit()

        return jsonify({'success': True, 'message': 'Split updated', 'paid': split.paid}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500