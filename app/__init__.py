import os

from flask import Flask

from config import config_by_name
from app.extensions import db, migrate, login_manager, csrf


def create_app(config_name=None):
    """
    Application factory for TrackMint.

    This creates and configures the Flask app instance.
    """
    if config_name is None:
        config_name = os.getenv("FLASK_CONFIG", "development")

    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    initialize_extensions(app)
    register_blueprints(app)
    register_login_loader()
    create_upload_directories(app)

    return app


def initialize_extensions(app):
    """Attach Flask extensions to the app."""
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)


def register_blueprints(app):
    """
    Register all blueprint modules.

    These route files will be implemented in later steps.
    """
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.receipts.routes import receipts_bp
    from app.income.routes import income_bp
    from app.insights.routes import insights_bp
    from app.groups.routes import groups_bp
    from app.leaderboard.routes import leaderboard_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(receipts_bp, url_prefix="/receipts")
    app.register_blueprint(income_bp, url_prefix="/income")
    app.register_blueprint(insights_bp, url_prefix="/insights")
    app.register_blueprint(groups_bp, url_prefix="/groups")
    app.register_blueprint(leaderboard_bp, url_prefix="/leaderboard")


def register_login_loader():
    """
    Configure Flask-Login's user loader.

    Imported inside the function to avoid circular imports.
    """
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return db.session.get(User, int(user_id))


def create_upload_directories(app):
    """Ensure required upload folders exist."""
    os.makedirs(app.config["RECEIPT_UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(app.config["PROFILE_UPLOAD_FOLDER"], exist_ok=True)