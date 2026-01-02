"""Add PayTabs gateway fields to payments table

Revision ID: 003_add_paytabs_fields
Revises: 7e2dde3a3c1a
Create Date: 2025-01-02
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003_add_paytabs_fields'
down_revision = '7e2dde3a3c1a'
branch_labels = None
depends_on = None


def upgrade():
    # Add PayTabs gateway fields to payments table
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('gateway_reference', sa.String(100), nullable=True))
        batch_op.add_column(sa.Column('gateway_response', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('refunded_amount', sa.Numeric(10, 2), server_default='0'))
        batch_op.create_index('ix_payments_gateway_reference', ['gateway_reference'], unique=False)


def downgrade():
    with op.batch_alter_table('payments', schema=None) as batch_op:
        batch_op.drop_index('ix_payments_gateway_reference')
        batch_op.drop_column('refunded_amount')
        batch_op.drop_column('gateway_response')
        batch_op.drop_column('gateway_reference')
