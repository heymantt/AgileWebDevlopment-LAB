from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models import Group, GroupMember, User, Receipt, ExpenseSplit, SettlementComment

groups_bp = Blueprint("groups", __name__)


def _get_group_or_403(group_id):
    """Return (group, is_member) or (None, None) if no access."""
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return None, None
    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if group.creator_id != current_user.id and not is_member:
        return None, None
    return group, is_member


def _compute_balances(group):
    """
    Compute net balance per member.
    Positive = they are owed money (others owe them).
    Negative = they owe money.
    """
    balances = {m.id: 0.0 for m in group.members}
    expenses = Receipt.query.filter_by(group_id=group.id).all()
    for expense in expenses:
        for split in expense.splits:
            if not split.paid:
                if split.member_id in balances:
                    balances[split.member_id] -= split.amount
    return balances


@groups_bp.route("/")
@login_required
def groups_home():
    """Display all groups the current user is part of (created or member)."""
    created_groups = Group.query.filter_by(creator_id=current_user.id).all()

    member_groups = Group.query.join(GroupMember).filter(
        GroupMember.user_id == current_user.id,
        Group.creator_id != current_user.id
    ).all()

    groups = created_groups + member_groups
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

        # Auto-add the creator as the first member
        creator_member = GroupMember(
            group_id=new_group.id,
            user_id=current_user.id,
            identifier=current_user.username
        )
        db.session.add(creator_member)

        for identifier in member_identifiers:
            identifier = identifier.strip()
            if not identifier:
                continue
            matched_user = User.query.filter(
                (User.username == identifier) | (User.email == identifier)
            ).first()
            # Skip if this is the creator — already added above
            if matched_user and matched_user.id == current_user.id:
                continue
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
    """Edit group name and description (creator only)."""
    try:
        group = Group.query.filter_by(id=group_id).first()
        _is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not _is_member):
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form

        name = data.get('name', '').strip()
        description = data.get('description', '').strip()

        if not name or len(name) < 2:
            return jsonify({'success': False, 'message': 'Group name must be at least 2 characters long'}), 400
        if len(name) > 100:
            return jsonify({'success': False, 'message': 'Group name must be less than 100 characters'}), 400

        group.name = name
        group.description = description if description else None
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
        group = Group.query.filter_by(id=group_id).first()
        if not group or group.creator_id != current_user.id:
            return jsonify({'success': False, 'message': 'Only the creator can delete a group'}), 403

        db.session.delete(group)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Group deleted successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>")
@login_required
def group_detail(group_id):
    """Show group detail page — passes members and balances to template."""
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return render_template("groups/detail.html", page_title="Group Detail", group=None,
                               members=[], balances={})

    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if group.creator_id != current_user.id and not is_member:
        return render_template("groups/detail.html", page_title="Group Detail", group=None,
                               members=[], balances={})

    members = GroupMember.query.filter_by(group_id=group_id).all()
    balances = _compute_balances(group)

    return render_template(
        "groups/detail.html",
        page_title="Group Detail",
        heading=group.name,
        group=group,
        members=members,
        balances=balances,
    )


@groups_bp.route("/<int:group_id>/add-expense", methods=["POST"])
@login_required
def add_group_expense(group_id):
    """Add an expense to a group and split it among members."""
    try:
        group, _ = _get_group_or_403(group_id)
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        if request.is_json:
            data = request.get_json(silent=True) or {}
        else:
            data = request.form

        # Accept both 'merchant' and 'title' from the frontend
        merchant = str(data.get('merchant') or data.get('title') or '').strip()
        amount_raw = data.get('amount', '')
        category = str(data.get('category', '') or '').strip()
        expense_date_raw = str(data.get('expense_date', '') or '').strip()
        notes = str(data.get('notes', '') or '').strip()
        split_type = str(data.get('split_type', 'equal') or 'equal').strip()

        errors = []
        if not merchant:
            errors.append("Description is required.")
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
            errors.append("Date must be in YYYY-MM-DD format.")
            expense_date = None

        if errors:
            return jsonify({'success': False, 'message': ' '.join(errors)}), 400

        members = GroupMember.query.filter_by(group_id=group.id).all()
        if not members:
            return jsonify({'success': False, 'message': 'Group must have at least one member to add expenses'}), 400

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

        if split_type == 'equal':
            split_amount = round(amount / len(members), 2)
            for member in members:
                db.session.add(ExpenseSplit(
                    expense_id=receipt.id,
                    member_id=member.id,
                    amount=split_amount,
                    paid=False
                ))
        else:
            member_splits = data.get('member_splits', {})
            if not isinstance(member_splits, dict):
                member_splits = {}
            for member in members:
                split_amount = float(member_splits.get(str(member.id), 0) or 0)
                if split_amount > 0:
                    db.session.add(ExpenseSplit(
                        expense_id=receipt.id,
                        member_id=member.id,
                        amount=split_amount,
                        paid=False
                    ))

        db.session.commit()
        return jsonify({'success': True, 'message': 'Expense added successfully', 'id': receipt.id}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/expenses")
@login_required
def group_expenses(group_id):
    """Get all expenses for a group as JSON."""
    try:
        group, _ = _get_group_or_403(group_id)
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        expenses = Receipt.query.filter_by(group_id=group.id).order_by(Receipt.expense_date.desc()).all()

        expenses_data = []
        for expense in expenses:
            # Identify who paid (the user who created the expense)
            paid_by_user = User.query.get(expense.user_id)
            paid_by_name = paid_by_user.username if paid_by_user else "Unknown"

            splits_data = []
            for split in expense.splits:
                comments_data = [{
                    'id': c.id,
                    'author': c.author.username,
                    'text': c.comment,
                    'created_at': c.created_at.strftime('%d %b %Y %H:%M')
                } for c in split.comments]

                splits_data.append({
                    'id': split.id,
                    'member_id': split.member_id,
                    'member_name': split.member.identifier,
                    'amount': split.amount,
                    'paid': split.paid,
                    'settled_at': split.settled_at.strftime('%d %b %Y %H:%M') if split.settled_at else None,
                    'comments': comments_data
                })

            expenses_data.append({
                'id': expense.id,
                # Use 'title' as alias for merchant so the JS template works
                'title': expense.merchant,
                'merchant': expense.merchant,
                'amount': expense.amount,
                'category': expense.category,
                'expense_date': expense.expense_date.strftime('%Y-%m-%d'),
                'notes': expense.notes,
                'paid_by': paid_by_name,
                'paid_by_id': expense.user_id,
                'splits': splits_data
            })

        return jsonify({'success': True, 'expenses': expenses_data}), 200

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/splits/<int:split_id>/settle", methods=["POST"])
@login_required
def settle_split(group_id, split_id):
    """Mark a split as settled and optionally add a comment."""
    try:
        group, _ = _get_group_or_403(group_id)
        if not group:
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        split = ExpenseSplit.query.filter_by(id=split_id).first()
        if not split or split.expense.group_id != group.id:
            return jsonify({'success': False, 'message': 'Split not found'}), 404

        data = request.get_json(silent=True) or {}
        comment_text = str(data.get('comment', '') or '').strip()

        split.paid = True
        split.settled_at = datetime.utcnow()

        if comment_text:
            db.session.add(SettlementComment(
                split_id=split.id,
                user_id=current_user.id,
                comment=comment_text
            ))

        db.session.commit()
        return jsonify({'success': True, 'paid': True,
                        'settled_at': split.settled_at.strftime('%d %b %Y %H:%M')}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/splits/<int:split_id>/comment", methods=["POST"])
@login_required
def add_comment(group_id, split_id):
    """Add a comment to a split without settling it."""
    try:
        group, _ = _get_group_or_403(group_id)
        if not group:
            return jsonify({'success': False, 'message': 'Access denied'}), 404

        split = ExpenseSplit.query.filter_by(id=split_id).first()
        if not split or split.expense.group_id != group.id:
            return jsonify({'success': False, 'message': 'Split not found'}), 404

        data = request.get_json(silent=True) or {}
        comment_text = str(data.get('comment', '') or '').strip()
        if not comment_text:
            return jsonify({'success': False, 'message': 'Comment cannot be empty'}), 400

        comment = SettlementComment(
            split_id=split.id,
            user_id=current_user.id,
            comment=comment_text
        )
        db.session.add(comment)
        db.session.commit()
        return jsonify({
            'success': True,
            'comment': {
                'id': comment.id,
                'author': comment.author.username,
                'text': comment.comment,
                'created_at': comment.created_at.strftime('%d %b %Y %H:%M')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/members/add", methods=["POST"])
@login_required
def add_member(group_id):
    """Add a member to a group by email (creator only)."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Only the group creator can add members'}), 403

        data = request.get_json(silent=True) or {}
        identifier = str(data.get('email', '') or '').strip()
        if not identifier:
            return jsonify({'success': False, 'message': 'Email or username is required'}), 400

        # Check not already a member (by identifier or user_id)
        matched_user = User.query.filter(
            (User.username == identifier) | (User.email == identifier)
        ).first()

        existing = None
        if matched_user:
            existing = GroupMember.query.filter_by(group_id=group_id, user_id=matched_user.id).first()
        if not existing:
            existing = GroupMember.query.filter_by(group_id=group_id, identifier=identifier).first()

        if existing:
            return jsonify({'success': False, 'message': 'This person is already a member'}), 400

        member = GroupMember(
            group_id=group.id,
            user_id=matched_user.id if matched_user else None,
            identifier=matched_user.username if matched_user else identifier
        )
        db.session.add(member)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Member added successfully'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/members/<int:member_id>/remove", methods=["POST"])
@login_required
def remove_member(group_id, member_id):
    """Remove a member from a group (creator only)."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Only the group creator can remove members'}), 403

        member = GroupMember.query.filter_by(id=member_id, group_id=group_id).first()
        if not member:
            return jsonify({'success': False, 'message': 'Member not found'}), 404

        if member.user_id == current_user.id:
            return jsonify({'success': False, 'message': 'You cannot remove yourself as the creator'}), 400

        db.session.delete(member)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Member removed'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/expenses/<int:expense_id>/edit", methods=["POST"])
@login_required
def edit_group_expense(group_id, expense_id):
    """Edit a group expense (creator only)."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Only the group creator can edit expenses'}), 403

        expense = Receipt.query.filter_by(id=expense_id, group_id=group_id).first()
        if not expense:
            return jsonify({'success': False, 'message': 'Expense not found'}), 404

        data = request.get_json(silent=True) or {}
        # Accept 'merchant' or 'title'
        merchant = str(data.get('merchant') or data.get('title') or '').strip()
        category = str(data.get('category', '') or '').strip()
        notes = str(data.get('notes', '') or '').strip()
        expense_date_raw = str(data.get('expense_date', '') or '').strip()
        amount_raw = data.get('amount')

        if not merchant or not category or not expense_date_raw:
            return jsonify({'success': False, 'message': 'Description, category and date are required'}), 400

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400

        # Update amount if provided
        if amount_raw is not None:
            try:
                amount = float(amount_raw)
                if amount < 0:
                    return jsonify({'success': False, 'message': 'Amount must be positive'}), 400
                expense.amount = amount
            except (ValueError, TypeError):
                return jsonify({'success': False, 'message': 'Invalid amount format'}), 400

        expense.merchant = merchant
        expense.category = category
        expense.notes = notes or None
        expense.expense_date = expense_date
        db.session.commit()
        return jsonify({'success': True, 'message': 'Expense updated'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete_group_expense(group_id, expense_id):
    """Delete a group expense (creator only)."""
    try:
        group = Group.query.filter_by(id=group_id, creator_id=current_user.id).first()
        if not group:
            return jsonify({'success': False, 'message': 'Only the group creator can delete expenses'}), 403

        expense = Receipt.query.filter_by(id=expense_id, group_id=group_id).first()
        if not expense:
            return jsonify({'success': False, 'message': 'Expense not found'}), 404

        db.session.delete(expense)
        db.session.commit()
        return jsonify({'success': True, 'message': 'Expense deleted'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/search-users")
@login_required
def search_users():
    """Search users by username or email for adding to a group."""
    q = request.args.get("q", "").strip()
    if len(q) < 2:
        return jsonify([])
    results = User.query.filter(
        (User.username.ilike(f"%{q}%")) | (User.email.ilike(f"%{q}%"))
    ).filter(User.id != current_user.id).limit(8).all()
    return jsonify([{"id": u.id, "username": u.username, "email": u.email} for u in results])