"""
Customer Model
"""
from app.extensions import db
from app.models.mixins import TimestampMixin
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import random


class Customer(db.Model, TimestampMixin):
    """Customer model - End users who buy from stores"""

    __tablename__ = 'customers'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Bariq ID - Unique customer identifier for merchants
    bariq_id = db.Column(db.String(10), unique=True, nullable=True, index=True)

    # Login credentials (after Nafath registration)
    username = db.Column(db.String(50), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(256), nullable=True)

    # Nafath Data (for initial registration only)
    national_id = db.Column(db.String(10), unique=True, nullable=False, index=True)
    nafath_id = db.Column(db.String(100), unique=True, nullable=True)

    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        """Verify password"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    @staticmethod
    def generate_bariq_id():
        """Generate unique Bariq ID (6 digits)"""
        return str(random.randint(100000, 999999))

    # Personal Info
    full_name_ar = db.Column(db.String(200), nullable=False)
    full_name_en = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(255), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=False, index=True)
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)  # male, female

    # Address
    city = db.Column(db.String(100), nullable=True)
    district = db.Column(db.String(100), nullable=True)
    address_line = db.Column(db.Text, nullable=True)

    # Account Status
    status = db.Column(db.String(20), default='pending', nullable=False, index=True)
    # pending, active, suspended, blocked
    status_reason = db.Column(db.Text, nullable=True)

    # Credit Info
    credit_limit = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    available_credit = db.Column(db.Numeric(10, 2), default=0, nullable=False)
    used_credit = db.Column(db.Numeric(10, 2), default=0, nullable=False)

    # Settings
    language = db.Column(db.String(5), default='ar', nullable=False)
    notifications_enabled = db.Column(db.Boolean, default=True, nullable=False)

    # Timestamps
    last_login_at = db.Column(db.DateTime, nullable=True)
    verified_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    transactions = db.relationship('Transaction', back_populates='customer', lazy='dynamic')
    payments = db.relationship('Payment', back_populates='customer', lazy='dynamic')
    credit_requests = db.relationship('CreditLimitRequest', back_populates='customer', lazy='dynamic')
    notifications = db.relationship('Notification', back_populates='customer', lazy='dynamic')
    ratings = db.relationship('CustomerRating', back_populates='customer', lazy='dynamic')

    def __repr__(self):
        return f'<Customer {self.national_id}>'

    def to_dict(self, include_sensitive=False):
        """Convert to dictionary"""
        data = {
            'id': self.id,
            'bariq_id': self.bariq_id,
            'username': self.username,
            'full_name_ar': self.full_name_ar,
            'full_name_en': self.full_name_en,
            'phone': self.phone,
            'email': self.email,
            'city': self.city,
            'district': self.district,
            'status': self.status,
            'credit_limit': float(self.credit_limit) if self.credit_limit else 0,
            'available_credit': float(self.available_credit) if self.available_credit else 0,
            'used_credit': float(self.used_credit) if self.used_credit else 0,
            'language': self.language,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

        if include_sensitive:
            data['national_id'] = self.national_id
            data['date_of_birth'] = self.date_of_birth.isoformat() if self.date_of_birth else None
            data['gender'] = self.gender

        return data

    def update_credit_usage(self, amount, operation='use'):
        """Update credit usage"""
        if operation == 'use':
            self.used_credit = float(self.used_credit) + amount
            self.available_credit = float(self.credit_limit) - float(self.used_credit)
        elif operation == 'release':
            self.used_credit = max(0, float(self.used_credit) - amount)
            self.available_credit = float(self.credit_limit) - float(self.used_credit)

    def can_purchase(self, amount):
        """Check if customer can make a purchase"""
        if self.status != 'active':
            return False, 'Account is not active'
        if float(self.available_credit) < amount:
            return False, 'Insufficient credit'
        return True, None
