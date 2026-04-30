from flask import Blueprint, render_template

groups_bp = Blueprint("groups", __name__)


@groups_bp.route("/")
def groups_home():
    return render_template("groups/index.html", page_title="Groups")


@groups_bp.route("/<int:group_id>")
def group_detail(group_id):
    return render_template(
        "groups/detail.html",
        page_title="Group Detail",
        heading=f"Group Detail #{group_id}"
    )