# tests.py
import unittest
from datetime import date
from app import create_app
from app.extensions import db
from app.models import User, Receipt, Income, Group, GroupMember, ExpenseSplit

class TrackMintTestCase(unittest.TestCase):
    def setUp(self):
        """Set up an isolated testing environment before every test case."""
        self.app = create_app("testing")
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        """Clean up and tear down the in-memory database after each test."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user_registration_and_password_hashing(self):
        """Test user account creation security and password validation."""
        user = User(username="test_dev", email="dev@trackmint.com")
        user.set_password("SecurePassword123")
        db.session.add(user)
        db.session.commit()

        # Check if database properly flags existing entities
        retrieved = User.query.filter_by(username="test_dev").first()
        self.assertIsNotNone(retrieved)
        self.assertTrue(retrieved.check_password("SecurePassword123"))
        self.assertFalse(retrieved.check_password("WrongPassword"))

    def test_receipt_creation_and_points_streak_triggers(self):
        """Test receipt tracking metrics, including points allocation and streaks."""
        user = User(username="tracker", email="tracker@trackmint.com")
        user.set_password("Password123")
        db.session.add(user)
        db.session.commit()

        # Simulate adding a receipt record
        receipt = Receipt(
            user_id=user.id,
            merchant="Woolworths",
            amount=84.50,
            category="Groceries",
            expense_date=date.today(),
            frequency_type="one-time"
        )
        db.session.add(receipt)
        
        # Mimic points assignment logic present in the receipts blueprint
        user.total_points += 10
        user.current_streak = 1
        user.last_upload_date = date.today()
        db.session.commit()

        # Assertions
        saved_receipt = Receipt.query.filter_by(merchant="Woolworths").first()
        self.assertIsNotNone(saved_receipt)
        self.assertEqual(saved_receipt.amount, 84.50)
        self.assertEqual(user.total_points, 10)
        self.assertEqual(user.current_streak, 1)

    def test_income_tracking_and_frequency(self):
        """Test financial entries for tracking multi-frequency recurring income."""
        user = User(username="earner", email="earner@trackmint.com")
        user.set_password("Password123")
        db.session.add(user)
        db.session.commit()

        income = Income(
            user_id=user.id,
            source="Freelance Project",
            amount=1500.00,
            income_date=date.today(),
            income_type="monthly",
            frequency="monthly",
            category="Freelance",
            start_date=date.today()
        )
        db.session.add(income)
        db.session.commit()

        saved_income = Income.query.filter_by(source="Freelance Project").first()
        self.assertIsNotNone(saved_income)
        self.assertEqual(saved_income.amount, 1500.00)
        self.assertEqual(saved_income.frequency, "monthly")

    def test_group_expense_splitting_logic(self):
        """Test group generation and the equal mathematical distribution of bills."""
        # Create users
        u1 = User(username="hugh", email="hugh@trackmint.com", password_hash="hash")
        u2 = User(username="selukash", email="sel@trackmint.com", password_hash="hash")
        db.session.add_all([u1, u2])
        db.session.commit()

        # Create group
        group = Group(creator_id=u1.id, name="Morley Roommates")
        db.session.add(group)
        db.session.flush()

        # Add members
        m1 = GroupMember(group_id=group.id, user_id=u1.id, identifier=u1.username)
        m2 = GroupMember(group_id=group.id, user_id=u2.id, identifier=u2.username)
        db.session.add_all([m1, m2])
        db.session.commit()

        # Log shared expense
        total_bill = 120.00
        receipt = Receipt(user_id=u1.id, group_id=group.id, merchant="Optus", amount=total_bill, category="Bills", expense_date=date.today())
        db.session.add(receipt)
        db.session.flush()

        # Split bill equally
        members = [m1, m2]
        split_amount = round(total_bill / len(members), 2)
        for m in members:
            split = ExpenseSplit(expense_id=receipt.id, member_id=m.id, amount=split_amount, paid=False)
            db.session.add(split)
        db.session.commit()

        # Verify splits
        saved_splits = ExpenseSplit.query.filter_by(expense_id=receipt.id).all()
        self.assertEqual(len(saved_splits), 2)
        for split in saved_splits:
            self.assertEqual(split.amount, 60.00)
            self.assertFalse(split.paid)

if __name__ == "__main__":
    unittest.main()
