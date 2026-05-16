"""Add settlement comments and settled_at

Revision ID: add_settlement_comments
Revises: merge_all_heads
Create Date: 2026-05-16 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'add_settlement_comments'
down_revision = 'merge_all_heads'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    # Add settled_at to expense_splits if missing
    existing_cols = [c['name'] for c in inspector.get_columns('expense_splits')]
    if 'settled_at' not in existing_cols:
        op.add_column('expense_splits', sa.Column('settled_at', sa.DateTime(), nullable=True))

    # Create settlement_comments table if missing
    if 'settlement_comments' not in inspector.get_table_names():
        op.create_table(
            'settlement_comments',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('split_id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('comment', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_settlement_comments_split_id', 'settlement_comments', ['split_id'], unique=False)


def downgrade():
    bind = op.get_bind()
    inspector = inspect(bind)

    if 'settlement_comments' in inspector.get_table_names():
        op.drop_index('ix_settlement_comments_split_id', table_name='settlement_comments')
        op.drop_table('settlement_comments')

    if 'settled_at' in [c['name'] for c in inspector.get_columns('expense_splits')]:
        op.drop_column('expense_splits', 'settled_at')
