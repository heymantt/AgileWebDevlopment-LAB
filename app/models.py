from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    total_points = db.Column(db.Integer, default=0, nullable=False)
    current_streak = db.Column(db.Integer, default=0, nullable=False)
    last_upload_date = db.Column(db.Date, nullable=True)

    receipts = db.relationship(
        "Receipt",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True
    )
    incomes = db.relationship(
        "Income",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy=True
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def __repr__(self) -> str:
        return f"<User {self.username}>"

class Group(db.Model):
    __tablename__ = "groups"

    id = db.Column(db.Integer, primary_key=True)
    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    creator = db.relationship("User", backref="groups")
    members = db.relationship(
        "GroupMember",
        backref="group",
        cascade="all, delete-orphan",
        lazy=True
    )

    def __repr__(self):
        return f"<Group {self.name}>"


class GroupMember(db.Model):
    __tablename__ = "group_members"

    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey("groups.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    identifier = db.Column(db.String(120), nullable=False)
    added_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", foreign_keys=[user_id])
    splits = db.relationship("ExpenseSplit", backref="member", cascade="all, delete-orphan", lazy=True)

    def __repr__(self):
        return f"<GroupMember {self.identifier}>"

class Receipt(db.Model):
    __tablename__ = "receipts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    group_id = db.Column(db.Integer, db.ForeignKey("groups.id"), nullable=True)

    merchant = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    expense_date = db.Column(db.Date, nullable=False)
    notes = db.Column(db.Text, nullable=True)

    # Frequency fields for recurring expenses
    frequency_type = db.Column(db.String(20), default="one-time", nullable=False)  # "one-time" or "recurring"
    frequency_interval = db.Column(db.String(20), nullable=True)  # "daily", "weekly", "monthly"
    frequency_details = db.Column(db.String(255), nullable=True)  # "Monday", "15th", etc.

    image_filename = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    user = db.relationship("User", back_populates="receipts")
    splits = db.relationship("ExpenseSplit", backref="expense", cascade="all, delete-orphan", lazy=True)

    def __repr__(self) -> str:
        return f"<Receipt {self.merchant} - {self.amount}>"


class ExpenseSplit(db.Model):
    __tablename__ = "expense_splits"

    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey("receipts.id"), nullable=False, index=True)
    member_id = db.Column(db.Integer, db.ForeignKey("group_members.id"), nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    paid = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<ExpenseSplit expense={self.expense_id} member={self.member_id} amount={self.amount}>"


class Income(db.Model):
    __tablename__ = "income"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    source = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    income_date = db.Column(db.Date, nullable=False)
    income_type = db.Column(db.String(80), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    
    # New fields for recurring income
    frequency = db.Column(db.String(20), default="one-time", nullable=False)  # one-time, daily, weekly, monthly, yearly
    category = db.Column(db.String(80), nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    user = db.relationship("User", back_populates="incomes")

    def __repr__(self) -> str:
        return f"<Income {self.source} - {self.amount}>"
