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
    # Add group_id to receipts table
    op.add_column('receipts', sa.Column('group_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_receipts_group_id', 'receipts', 'groups', ['group_id'], ['id'])

    # Create expense_splits table
    op.create_table('expense_splits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('expense_id', sa.Integer(), nullable=False),
        sa.Column('member_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('paid', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['expense_id'], ['receipts.id'], name='fk_expense_splits_expense_id'),
        sa.ForeignKeyConstraint(['member_id'], ['group_members.id'], name='fk_expense_splits_member_id'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_expense_splits_expense_id'), 'expense_splits', ['expense_id'], unique=False)
    op.create_index(op.f('ix_expense_splits_member_id'), 'expense_splits', ['member_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_expense_splits_member_id'), table_name='expense_splits')
    op.drop_index(op.f('ix_expense_splits_expense_id'), table_name='expense_splits')
    op.drop_table('expense_splits')
    op.drop_constraint('fk_receipts_group_id', 'receipts', type_='foreignkey')
    op.drop_column('receipts', 'group_id')
