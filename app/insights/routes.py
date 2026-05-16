from flask import redirect, url_for
from flask_login import login_required

from . import insights_bp


@insights_bp.route("/")
@login_required
def insights_home():
    """Redirect to the merged Dashboard + Insights page.

    The /insights/ URL is kept alive so bookmarks and url_for('insights.insights_home')
    calls still resolve without a 404.  All rendering logic now lives in
    app/main/routes.py :: dashboard().
    """
    return redirect(url_for("main.dashboard"))
