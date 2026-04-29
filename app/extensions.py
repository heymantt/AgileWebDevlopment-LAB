from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect


# Create extension objects here.
# They are initialized inside the app factory in __init__.py.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Flask-Login configuration
login_manager.login_view = "auth.login"
login_manager.login_message_category = "warning"
login_manager.login_message = "Please log in to access that page."