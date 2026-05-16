import os
import sys
from pathlib import Path

import pytest

# Make the project root importable when pytest is run from the project folder.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app
from app.extensions import db
from app.models import User


@pytest.fixture()
def app(tmp_path):
    """Create a fresh TrackMint app and in-memory database for each test."""
    app = create_app("testing")

    receipt_uploads = tmp_path / "receipts"
    profile_uploads = tmp_path / "profiles"
    receipt_uploads.mkdir(parents=True, exist_ok=True)
    profile_uploads.mkdir(parents=True, exist_ok=True)

    app.config.update(
        RECEIPT_UPLOAD_FOLDER=str(receipt_uploads),
        PROFILE_UPLOAD_FOLDER=str(profile_uploads),
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def runner(app):
    return app.test_cli_runner()


def create_user(username, email, password="Password123"):
    """Create and persist a user for tests."""
    user = User(username=username, email=email.lower())
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


def login(client, email, password="Password123"):
    """Log in through the real login route."""
    return client.post(
        "/auth/login",
        data={"email": email.lower(), "password": password},
        follow_redirects=True,
    )
