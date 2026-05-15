"""Add frequency fields to receipts table

Revision ID: add_frequency_fields
Revises: ed25e18663a1
Create Date: 2026-05-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_frequency_fields'
down_revision = 'ed25e18663a1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('receipts', sa.Column('frequency_type', sa.String(20), server_default='one-time', nullable=False))
    op.add_column('receipts', sa.Column('frequency_interval', sa.String(20), nullable=True))
    op.add_column('receipts', sa.Column('frequency_details', sa.String(255), nullable=True))


def downgrade():
    op.drop_column('receipts', 'frequency_details')
    op.drop_column('receipts', 'frequency_interval')
    op.drop_column('receipts', 'frequency_type')
