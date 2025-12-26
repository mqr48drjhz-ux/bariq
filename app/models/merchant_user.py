"""
Merchant User Model
"""
from app.extensions import db
from app.models.mixins import TimestampMixin
import uuid
import bcrypt


# Role hierarchy (higher number = more permissions)
ROLE_HIERARCHY = {
    'owner': 5,
    'executive_manager': 5,  # Same level as owner
    'region_manager': 3,
    'branch_manager': 2,
    'cashier': 1
}

# Role display names in Arabic
ROLE_NAMES_AR = {
    'owner': 'المالك',
    'executive_manager': 'المدير التنفيذي',
    'region_manager': 'مدير المنطقة',
    'branch_manager': 'مدير الفرع',
    'cashier': 'كاشير'
}

# Role display names in English
ROLE_NAMES_EN = {
    'owner': 'Owner',
    'executive_manager': 'Executive Manager',
    'region_manager': 'Region Manager',
    'branch_manager': 'Branch Manager',
    'cashier': 'Cashier'
}


class MerchantUser(db.Model, TimestampMixin):
    """Merchant User model - Staff members"""

    __tablename__ = 'merchant_users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    merchant_id = db.Column(db.String(36), db.ForeignKey('merchants.id'), nullable=False, index=True)
    branch_id = db.Column(db.String(36), db.ForeignKey('branches.id'), nullable=True, index=True)
    region_id = db.Column(db.String(36), db.ForeignKey('regions.id'), nullable=True)

    # Auth
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)

    # Personal Info
    full_name = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20), nullable=True)
    national_id = db.Column(db.String(10), nullable=True)

    # Role
    role = db.Column(db.String(30), nullable=False, index=True)
    # owner, executive_manager, region_manager, branch_manager, cashier

    # Permissions (JSON array)
    permissions = db.Column(db.JSON, default=[], nullable=True)

    # Status
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    merchant = db.relationship('Merchant', back_populates='users')
    branch = db.relationship('Branch', back_populates='users')
    region = db.relationship('Region', back_populates='users')

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """Check password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'merchant_id': self.merchant_id,
            'branch_id': self.branch_id,
            'region_id': self.region_id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'role_ar': ROLE_NAMES_AR.get(self.role, self.role),
            'role_en': ROLE_NAMES_EN.get(self.role, self.role),
            'permissions': self.permissions or [],
            'is_active': self.is_active,
            'role_level': ROLE_HIERARCHY.get(self.role, 0),
        }

    def get_role_level(self):
        """Get numeric role level for comparison"""
        return ROLE_HIERARCHY.get(self.role, 0)

    def can_manage(self, other_user):
        """Check if this user can manage another user"""
        return self.get_role_level() > other_user.get_role_level()

    def is_top_level(self):
        """Check if user is owner or executive manager"""
        return self.role in ['owner', 'executive_manager']

    def can_see_all_regions(self):
        """Check if user can see all regions"""
        return self.role in ['owner', 'executive_manager']

    def can_see_all_branches(self):
        """Check if user can see all branches"""
        return self.role in ['owner', 'executive_manager']

    def can_manage_staff(self):
        """Check if user can manage staff"""
        return self.role in ['owner', 'executive_manager', 'region_manager', 'branch_manager']

    def can_create_transactions(self):
        """Check if user can create transactions"""
        return self.role in ['cashier', 'branch_manager', 'region_manager', 'executive_manager', 'owner']

    def get_accessible_branch_ids(self):
        """Get list of branch IDs this user can access"""
        if self.can_see_all_branches():
            from app.models.branch import Branch
            branches = Branch.query.filter_by(merchant_id=self.merchant_id, is_active=True).all()
            return [b.id for b in branches]
        elif self.role == 'region_manager' and self.region_id:
            from app.models.branch import Branch
            branches = Branch.query.filter_by(region_id=self.region_id, is_active=True).all()
            return [b.id for b in branches]
        elif self.branch_id:
            return [self.branch_id]
        return []

    def get_accessible_region_ids(self):
        """Get list of region IDs this user can access"""
        if self.can_see_all_regions():
            from app.models.region import Region
            regions = Region.query.filter_by(merchant_id=self.merchant_id, is_active=True).all()
            return [r.id for r in regions]
        elif self.region_id:
            return [self.region_id]
        return []

    def get_subordinates(self):
        """Get all users this user can manage"""
        my_level = self.get_role_level()
        query = MerchantUser.query.filter(
            MerchantUser.merchant_id == self.merchant_id,
            MerchantUser.id != self.id,
            MerchantUser.is_active == True
        )

        if self.role == 'region_manager' and self.region_id:
            # Region manager sees branch managers and cashiers in their region
            query = query.filter(MerchantUser.region_id == self.region_id)
        elif self.role == 'branch_manager' and self.branch_id:
            # Branch manager sees only cashiers in their branch
            query = query.filter(MerchantUser.branch_id == self.branch_id)

        subordinates = query.all()
        return [u for u in subordinates if u.get_role_level() < my_level]
