"""
Device Models - Store FCM tokens for push notifications
"""
from app.extensions import db
from app.models.mixins import TimestampMixin
import uuid


class CustomerDevice(db.Model, TimestampMixin):
    """Customer device for push notifications"""

    __tablename__ = 'customer_devices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False, index=True)

    # Device info
    fcm_token = db.Column(db.String(500), nullable=False, index=True)
    device_type = db.Column(db.String(20), nullable=False)  # ios, android
    device_name = db.Column(db.String(100), nullable=True)
    device_id = db.Column(db.String(100), nullable=True)  # Unique device identifier

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Relationship
    customer = db.relationship('Customer', backref=db.backref('devices', lazy='dynamic'))

    # Unique constraint: one FCM token per customer
    __table_args__ = (
        db.UniqueConstraint('customer_id', 'fcm_token', name='uq_customer_device_token'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'device_type': self.device_type,
            'device_name': self.device_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }


class MerchantUserDevice(db.Model, TimestampMixin):
    """Merchant staff device for push notifications"""

    __tablename__ = 'merchant_user_devices'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_user_id = db.Column(db.String(36), db.ForeignKey('merchant_users.id'), nullable=False, index=True)

    # Device info
    fcm_token = db.Column(db.String(500), nullable=False, index=True)
    device_type = db.Column(db.String(20), nullable=False)  # ios, android
    device_name = db.Column(db.String(100), nullable=True)
    device_id = db.Column(db.String(100), nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_used_at = db.Column(db.DateTime, nullable=True)

    # Relationship
    merchant_user = db.relationship('MerchantUser', backref=db.backref('devices', lazy='dynamic'))

    # Unique constraint
    __table_args__ = (
        db.UniqueConstraint('merchant_user_id', 'fcm_token', name='uq_merchant_user_device_token'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'device_type': self.device_type,
            'device_name': self.device_name,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
        }
