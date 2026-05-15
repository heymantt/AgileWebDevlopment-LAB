"""Merge all heads into one

Revision ID: merge_all_heads
Revises: add_frequency_fields, add_group_expenses, add_group_members_001
Create Date: 2026-05-16 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'merge_all_heads'
down_revision = ('add_frequency_fields', 'add_group_expenses', 'add_group_members_001')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
