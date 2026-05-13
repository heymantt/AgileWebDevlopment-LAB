from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.extensions import db
from app.models import Group

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/")
@login_required
def groups_home():
    """Display all groups where user is a member."""
    groups = Group.query.filter_by(creator_id=current_user.id).all()
    return render_template("groups/index.html", page_title="Groups", groups=groups)


@groups_bp.route("/create", methods=["POST"])
@login_required
def create_group():
    """Create a new group."""
    try:
        data = request.get_json()
        
        # Validate input
        if not data.get('name'):
            return jsonify({'success': False, 'message': 'Group name is required'}), 400
        
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        
        if len(name) < 2:
            return jsonify({'success': False, 'message': 'Group name must be at least 2 characters long'}), 400
        
        if len(name) > 100:
            return jsonify({'success': False, 'message': 'Group name must be less than 100 characters'}), 400
        
        # Create new group
        new_group = Group(
            creator_id=current_user.id,
            name=name,
            description=description if description else None
        )
        
        db.session.add(new_group)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Group created successfully', 'id': new_group.id}), 201
    
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
            heading=f"Group not found",
            group=None
        )
    return render_template(
        "groups/detail.html",
        page_title="Group Detail",
        heading=group.name,
        group=group
    )