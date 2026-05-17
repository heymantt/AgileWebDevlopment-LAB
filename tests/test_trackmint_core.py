from datetime import date, timedelta

from app.extensions import db
from app.models import Group, GroupMember, Receipt, User
from conftest import create_user, login


def test_signup_creates_user(client, app):
    response = client.post(
        "/auth/signup",
        data={
            "username": "alice",
            "email": "alice@example.com",
            "password": "Password123",
            "confirm_password": "Password123",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        assert user is not None
        assert user.username == "alice"
        assert user.check_password("Password123")


def test_login_rejects_wrong_password(client, app):
    with app.app_context():
        create_user("alice", "alice@example.com")

    response = client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "WrongPassword"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Invalid email or password" in response.data


def test_create_group_with_registered_user_succeeds(client, app):
    with app.app_context():
        alice = create_user("alice", "alice@example.com")
        bob = create_user("bob", "bob@example.com")
        alice_id = alice.id
        bob_id = bob.id

    login(client, "alice@example.com")

    response = client.post(
        "/groups/create",
        json={
            "name": "Housemates",
            "description": "Shared household expenses",
            "members": ["bob@example.com"],
        },
    )

    assert response.status_code == 201
    assert response.get_json()["success"] is True

    with app.app_context():
        group = Group.query.filter_by(name="Housemates").first()
        assert group is not None

        member_user_ids = {
            member.user_id for member in GroupMember.query.filter_by(group_id=group.id).all()
        }
        assert alice_id in member_user_ids
        assert bob_id in member_user_ids


def test_creator_can_delete_group(client, app):
    with app.app_context():
        alice = create_user("alice", "alice@example.com")
        group = Group(creator_id=alice.id, name="Creator Group")
        db.session.add(group)
        db.session.flush()
        db.session.add(GroupMember(group_id=group.id, user_id=alice.id, identifier="alice"))
        db.session.commit()
        group_id = group.id

    login(client, "alice@example.com")

    response = client.post(f"/groups/{group_id}/delete")

    assert response.status_code == 200
    assert response.get_json()["success"] is True

    with app.app_context():
        assert db.session.get(Group, group_id) is None


def test_add_expense_updates_leaderboard_points_and_streak(client, app):
    with app.app_context():
        create_user("alice", "alice@example.com")

    login(client, "alice@example.com")

    response = client.post(
        "/receipts/",
        data={
            "merchant": "Coles",
            "amount": "25.50",
            "category": "Groceries",
            "expense_date": date.today().strftime("%Y-%m-%d"),
            "notes": "Weekly groceries",
            "frequency": "one-time",
        },
        follow_redirects=False,
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        receipt = Receipt.query.filter_by(user_id=user.id, merchant="Coles").first()

        assert receipt is not None
        assert user.total_points == 10
        assert user.current_streak == 1
        assert user.last_upload_date == date.today()


def test_same_day_expense_adds_points_but_does_not_increase_streak(client, app):
    with app.app_context():
        user = create_user("alice", "alice@example.com")
        user.total_points = 10
        user.current_streak = 1
        user.last_upload_date = date.today()
        db.session.commit()

    login(client, "alice@example.com")

    response = client.post(
        "/receipts/",
        data={
            "merchant": "Woolworths",
            "amount": "12.00",
            "category": "Food",
            "expense_date": date.today().strftime("%Y-%m-%d"),
            "frequency": "one-time",
        },
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        assert user.total_points == 20
        assert user.current_streak == 1


def test_consecutive_day_expense_increases_streak(client, app):
    with app.app_context():
        user = create_user("alice", "alice@example.com")
        user.total_points = 10
        user.current_streak = 1
        user.last_upload_date = date.today() - timedelta(days=1)
        db.session.commit()

    login(client, "alice@example.com")

    response = client.post(
        "/receipts/",
        data={
            "merchant": "Bus Fare",
            "amount": "4.50",
            "category": "Transport",
            "expense_date": date.today().strftime("%Y-%m-%d"),
            "frequency": "one-time",
        },
    )

    assert response.status_code in (302, 303)

    with app.app_context():
        user = User.query.filter_by(email="alice@example.com").first()
        assert user.total_points == 20
        assert user.current_streak == 2


def test_invalid_expense_amount_is_not_saved(client, app):
    with app.app_context():
        create_user("alice", "alice@example.com")

    login(client, "alice@example.com")

    response = client.post(
        "/receipts/",
        data={
            "merchant": "Invalid Expense",
            "amount": "-10",
            "category": "Food",
            "expense_date": date.today().strftime("%Y-%m-%d"),
            "frequency": "one-time",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Amount must be greater than 0" in response.data

    with app.app_context():
        assert Receipt.query.filter_by(merchant="Invalid Expense").first() is None


def test_search_users_excludes_current_user(client, app):
    with app.app_context():
        create_user("alice", "alice@example.com")
        create_user("alex", "alex@example.com")

    login(client, "alice@example.com")

    response = client.get("/groups/search-users?q=al")

    assert response.status_code == 200
    data = response.get_json()
    usernames = {user["username"] for user in data}

    assert "alex" in usernames
    assert "alice" not in usernames
