"""
Notification Model
"""
from app.extensions import db
from app.models.mixins import TimestampMixin
import uuid


class Notification(db.Model, TimestampMixin):
    """Notification model"""

    __tablename__ = 'notifications'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=True, index=True)
    merchant_user_id = db.Column(db.String(36), db.ForeignKey('merchant_users.id'), nullable=True)
    admin_user_id = db.Column(db.String(36), db.ForeignKey('admin_users.id'), nullable=True)

    title_ar = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=True)
    body_ar = db.Column(db.Text, nullable=False)
    body_en = db.Column(db.Text, nullable=True)

    type = db.Column(db.String(50), nullable=False)
    related_entity_type = db.Column(db.String(50), nullable=True)
    related_entity_id = db.Column(db.String(36), nullable=True)

    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    sent_via = db.Column(db.JSON, default=['in_app'], nullable=True)

    # Relationships
    customer = db.relationship('Customer', back_populates='notifications')

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title_ar,  # Default to Arabic for mobile app
            'body': self.body_ar,    # Default to Arabic for mobile app
            'title_ar': self.title_ar,
            'title_en': self.title_en,
            'body_ar': self.body_ar,
            'body_en': self.body_en,
            'type': self.type,
            'is_read': self.is_read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
