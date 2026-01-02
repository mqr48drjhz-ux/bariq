"""
Payment Model
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, generate_reference
import uuid


class Payment(db.Model, TimestampMixin):
    """Payment model"""

    __tablename__ = 'payments'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    transaction_id = db.Column(db.String(36), db.ForeignKey('transactions.id'), nullable=False, index=True)
    customer_id = db.Column(db.String(36), db.ForeignKey('customers.id'), nullable=False, index=True)

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_method = db.Column(db.String(30), nullable=True)
    status = db.Column(db.String(20), default='pending', nullable=False)
    external_reference = db.Column(db.String(100), nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # PayTabs gateway fields
    gateway_reference = db.Column(db.String(100), nullable=True, index=True)  # PayTabs tran_ref
    gateway_response = db.Column(db.Text, nullable=True)  # Full gateway response JSON
    refunded_amount = db.Column(db.Numeric(10, 2), default=0)

    # Relationships
    transaction = db.relationship('Transaction', back_populates='payments')
    customer = db.relationship('Customer', back_populates='payments')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.reference_number:
            self.reference_number = generate_reference('PAY')

    def to_dict(self):
        return {
            'id': self.id,
            'reference_number': self.reference_number,
            'transaction_id': self.transaction_id,
            'amount': float(self.amount),
            'payment_method': self.payment_method,
            'status': self.status,
            'gateway_reference': self.gateway_reference,
            'refunded_amount': float(self.refunded_amount) if self.refunded_amount else 0,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
        }
