"""Add group expenses support with splits

Revision ID: add_group_expenses
Revises: recurring_income_001
Create Date: 2026-05-16 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_group_expenses'
down_revision = 'recurring_income_001'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Only add group_id if it doesn't already exist (handles partial previous run)
    existing_columns = [col['name'] for col in inspector.get_columns('receipts')]
    if 'group_id' not in existing_columns:
        op.add_column('receipts', sa.Column('group_id', sa.Integer(), nullable=True))
    # SQLite does not support ADD CONSTRAINT via ALTER TABLE — FK enforced by ORM only

    # Create expense_splits table only if it doesn't already exist
    existing_tables = inspector.get_table_names()
    if 'expense_splits' not in existing_tables:
        op.create_table(
            'expense_splits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('expense_id', sa.Integer(), nullable=False),
            sa.Column('member_id', sa.Integer(), nullable=False),
            sa.Column('amount', sa.Float(), nullable=False),
            sa.Column('paid', sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_expense_splits_expense_id', 'expense_splits', ['expense_id'], unique=False)
        op.create_index('ix_expense_splits_member_id', 'expense_splits', ['member_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if 'expense_splits' in inspector.get_table_names():
        op.drop_index('ix_expense_splits_member_id', table_name='expense_splits')
        op.drop_index('ix_expense_splits_expense_id', table_name='expense_splits')
        op.drop_table('expense_splits')

    if 'group_id' in [col['name'] for col in inspector.get_columns('receipts')]:
        op.drop_column('receipts', 'group_id')