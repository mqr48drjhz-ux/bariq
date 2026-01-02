"""Add device models for FCM push notifications

Revision ID: 004_add_devices
Revises: 003_add_paytabs_fields
Create Date: 2026-01-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_devices'
down_revision = '003_add_paytabs_fields'
branch_labels = None
depends_on = None


def upgrade():
    # Create customer_devices table
    op.create_table('customer_devices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('customer_id', sa.String(36), sa.ForeignKey('customers.id'), nullable=False),
        sa.Column('fcm_token', sa.String(500), nullable=False),
        sa.Column('device_type', sa.String(20), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('customer_id', 'fcm_token', name='uq_customer_device_token')
    )
    op.create_index('ix_customer_devices_customer_id', 'customer_devices', ['customer_id'])
    op.create_index('ix_customer_devices_fcm_token', 'customer_devices', ['fcm_token'])

    # Create merchant_user_devices table
    op.create_table('merchant_user_devices',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('merchant_user_id', sa.String(36), sa.ForeignKey('merchant_users.id'), nullable=False),
        sa.Column('fcm_token', sa.String(500), nullable=False),
        sa.Column('device_type', sa.String(20), nullable=False),
        sa.Column('device_name', sa.String(100), nullable=True),
        sa.Column('device_id', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.UniqueConstraint('merchant_user_id', 'fcm_token', name='uq_merchant_user_device_token')
    )
    op.create_index('ix_merchant_user_devices_merchant_user_id', 'merchant_user_devices', ['merchant_user_id'])
    op.create_index('ix_merchant_user_devices_fcm_token', 'merchant_user_devices', ['fcm_token'])


def downgrade():
    op.drop_table('merchant_user_devices')
    op.drop_table('customer_devices')
