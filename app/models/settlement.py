"""
Settlement Model
"""
from app.extensions import db
from app.models.mixins import TimestampMixin, generate_reference
import uuid


class Settlement(db.Model, TimestampMixin):
    """Settlement model - Merchant payment cycles"""

    __tablename__ = 'settlements'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    reference_number = db.Column(db.String(20), unique=True, nullable=False, index=True)

    merchant_id = db.Column(db.String(36), db.ForeignKey('merchants.id'), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey('branches.id'), nullable=False, index=True)

    # Period
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)

    # Amounts
    gross_amount = db.Column(db.Numeric(12, 2), nullable=False)
    returns_amount = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    commission_amount = db.Column(db.Numeric(12, 2), nullable=False)
    net_amount = db.Column(db.Numeric(12, 2), nullable=False)

    # Counts
    transaction_count = db.Column(db.Integer, default=0, nullable=False)
    return_count = db.Column(db.Integer, default=0, nullable=False)

    # Status
    status = db.Column(db.String(20), default='open', nullable=False, index=True)

    # Transfer Info
    transfer_reference = db.Column(db.String(100), nullable=True)
    transferred_at = db.Column(db.DateTime, nullable=True)

    # Approval
    approved_by = db.Column(db.String(36), db.ForeignKey('admin_users.id'), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    merchant = db.relationship('Merchant', back_populates='settlements')
    branch = db.relationship('Branch', back_populates='settlements')
    transactions = db.relationship('Transaction', back_populates='settlement', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.reference_number:
            self.reference_number = generate_reference('STL')

    def to_dict(self):
        return {
            'id': self.id,
            'reference_number': self.reference_number,
            'merchant_id': self.merchant_id,
            'branch_id': self.branch_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'gross_amount': float(self.gross_amount),
            'total_amount': float(self.gross_amount),  # Alias for frontend
            'returns_amount': float(self.returns_amount),
            'commission_amount': float(self.commission_amount),
            'net_amount': float(self.net_amount),
            'transaction_count': self.transaction_count,
            'return_count': self.return_count,
            'status': self.status,
            'transfer_reference': self.transfer_reference,
            'transferred_at': self.transferred_at.isoformat() if self.transferred_at else None,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
        }
