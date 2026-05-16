from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
from app.extensions import db
from app.models import Group, GroupMember, User, Receipt, ExpenseSplit, SettlementComment

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/")
@login_required
def groups_home():
    """Display all groups the current user is part of (created or member)."""
    # Groups created by the user
    created_groups = Group.query.filter_by(creator_id=current_user.id).all()
    created_ids = {g.id for g in created_groups}

    # Groups where the user is a member but not the creator
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
    """Edit group name, description, and members."""
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
        group = Group.query.filter_by(id=group_id).first()
        _is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not _is_member):
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
    # Allow access if user is creator OR a member
    group = Group.query.filter_by(id=group_id).first()
    if not group:
        return render_template("groups/detail.html", page_title="Group Detail", group=None)

    is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
    if group.creator_id != current_user.id and not is_member:
        return render_template("groups/detail.html", page_title="Group Detail", group=None)

    return render_template("groups/detail.html", page_title="Group Detail", heading=group.name, group=group)


@groups_bp.route("/<int:group_id>/add-expense", methods=["POST"])
@login_required
def add_group_expense(group_id):
    """Add an expense to a group and split it among members."""
    try:
        group = Group.query.filter_by(id=group_id).first()
        is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not is_member):
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
        group = Group.query.filter_by(id=group_id).first()
        _is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not _is_member):
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        expenses = Receipt.query.filter_by(group_id=group.id).order_by(Receipt.expense_date.desc()).all()
        
        expenses_data = []
        for expense in expenses:
            splits_data = []
            for split in expense.splits:
                comments_data = [{
                    'id': c.id,
                    'author': c.author.username,
                    'text': c.comment,
                    'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
                } for c in split.comments]
                splits_data.append({
                    'id': split.id,
                    'member_id': split.member_id,
                    'member_name': split.member.identifier,
                    'amount': split.amount,
                    'paid': split.paid,
                    'settled_at': split.settled_at.strftime('%Y-%m-%d %H:%M') if split.settled_at else None,
                    'comments': comments_data
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
        group = Group.query.filter_by(id=group_id).first()
        _is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not _is_member):
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


@groups_bp.route("/<int:group_id>/splits/<int:split_id>/settle", methods=["POST"])
@login_required
def settle_split(group_id, split_id):
    """Mark a split as settled and optionally add a comment."""
    try:
        group = Group.query.filter_by(id=group_id).first()
        _is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not _is_member):
            return jsonify({'success': False, 'message': 'Group not found or access denied'}), 404

        split = ExpenseSplit.query.filter_by(id=split_id).first()
        if not split or split.expense.group_id != group.id:
            return jsonify({'success': False, 'message': 'Split not found'}), 404

        data = request.get_json(silent=True) or {}
        comment_text = str(data.get('comment', '') or '').strip()

        split.paid = True
        split.settled_at = datetime.utcnow()

        if comment_text:
            comment = SettlementComment(
                split_id=split.id,
                user_id=current_user.id,
                comment=comment_text
            )
            db.session.add(comment)

        db.session.commit()
        return jsonify({'success': True, 'paid': True, 'settled_at': split.settled_at.strftime('%Y-%m-%d %H:%M')}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/splits/<int:split_id>/comment", methods=["POST"])
@login_required
def add_comment(group_id, split_id):
    """Add a comment to a split without settling it."""
    try:
        group = Group.query.filter_by(id=group_id).first()
        _is_member = GroupMember.query.filter_by(group_id=group_id, user_id=current_user.id).first()
        if not group or (group.creator_id != current_user.id and not _is_member):
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
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@groups_bp.route("/<int:group_id>/splits/<int:split_id>/comments")
@login_required
def get_comments(group_id, split_id):
    """Get all comments for a split."""
    try:
        split = ExpenseSplit.query.filter_by(id=split_id).first()
        if not split:
            return jsonify({'success': False, 'message': 'Split not found'}), 404
        comments = [{
            'id': c.id,
            'author': c.author.username,
            'text': c.comment,
            'created_at': c.created_at.strftime('%Y-%m-%d %H:%M')
        } for c in split.comments]
        return jsonify({'success': True, 'comments': comments}), 200
    except Exception as e:
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
        merchant = str(data.get('merchant', '') or '').strip()
        category = str(data.get('category', '') or '').strip()
        notes = str(data.get('notes', '') or '').strip()
        expense_date_raw = str(data.get('expense_date', '') or '').strip()

        if not merchant or not category or not expense_date_raw:
            return jsonify({'success': False, 'message': 'Merchant, category and date are required'}), 400

        try:
            expense_date = datetime.strptime(expense_date_raw, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({'success': False, 'message': 'Invalid date format'}), 400

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
