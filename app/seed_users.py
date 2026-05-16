"""
Run this once to seed dummy users into the database.
Usage: python seed_users.py
"""
from app import create_app
from app.extensions import db
from app.models import User

DUMMY_USERS = [
    {"username": "alice",   "email": "alice@example.com",   "password": "Password1!"},
    {"username": "bob",     "email": "bob@example.com",     "password": "Password1!"},
    {"username": "charlie", "email": "charlie@example.com", "password": "Password1!"},
    {"username": "diana",   "email": "diana@example.com",   "password": "Password1!"},
    {"username": "evan",    "email": "evan@example.com",    "password": "Password1!"},
]

app = create_app()

with app.app_context():
    added = 0
    for u in DUMMY_USERS:
        exists = User.query.filter(
            (User.username == u["username"]) | (User.email == u["email"])
        ).first()
        if not exists:
            user = User(username=u["username"], email=u["email"])
            user.set_password(u["password"])
            db.session.add(user)
            added += 1
            print(f"  Added: {u['username']} ({u['email']})")
        else:
            print(f"  Skipped (already exists): {u['username']}")
    db.session.commit()
    print(f"\nDone. {added} new user(s) added.")
