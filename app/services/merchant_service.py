"""
Merchant Service - Full Implementation
"""
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.merchant import Merchant
from app.models.region import Region
from app.models.branch import Branch
from app.models.merchant_user import MerchantUser
from app.models.transaction import Transaction


class MerchantService:
    """Merchant service for all merchant-related operations"""

    # ==================== Registration ====================

    @staticmethod
    def register_merchant(data):
        """Register a new merchant"""
        # Check if commercial registration already exists
        existing = Merchant.query.filter_by(
            commercial_registration=data.get('commercial_registration')
        ).first()

        if existing:
            return {
                'success': False,
                'message': 'Commercial registration already registered',
                'error_code': 'MERCH_002'
            }

        # Check if email already exists
        if Merchant.query.filter_by(email=data.get('email')).first():
            return {
                'success': False,
                'message': 'Email already registered',
                'error_code': 'VAL_001'
            }

        try:
            # Create merchant
            merchant = Merchant(
                name_ar=data.get('name_ar'),
                name_en=data.get('name_en'),
                commercial_registration=data.get('commercial_registration'),
                tax_number=data.get('tax_number'),
                business_type=data.get('business_type'),
                email=data.get('email'),
                phone=data.get('phone'),
                website=data.get('website'),
                city=data.get('city'),
                district=data.get('district'),
                address_line=data.get('address_line'),
                bank_name=data.get('bank_name'),
                iban=data.get('iban'),
                account_holder_name=data.get('account_holder_name'),
                status='pending'
            )

            db.session.add(merchant)
            db.session.flush()  # Get merchant ID

            # Create owner user
            owner = MerchantUser(
                merchant_id=merchant.id,
                email=data.get('owner_email', data.get('email')),
                full_name=data.get('owner_name'),
                phone=data.get('owner_phone', data.get('phone')),
                role='owner',
                permissions=['all']
            )
            owner.set_password(data.get('password'))

            db.session.add(owner)
            db.session.commit()

            return {
                'success': True,
                'message': 'Merchant registered successfully. Pending approval.',
                'data': {
                    'merchant': merchant.to_dict(),
                    'owner': owner.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to register merchant: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Profile ====================

    @staticmethod
    def get_merchant_profile(merchant_id):
        """Get merchant profile by ID"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        # Get counts
        branch_count = Branch.query.filter_by(merchant_id=merchant_id, is_active=True).count()
        staff_count = MerchantUser.query.filter_by(merchant_id=merchant_id, is_active=True).count()
        region_count = Region.query.filter_by(merchant_id=merchant_id, is_active=True).count()

        return {
            'success': True,
            'data': {
                'merchant': merchant.to_dict(),
                'stats': {
                    'branch_count': branch_count,
                    'staff_count': staff_count,
                    'region_count': region_count
                }
            }
        }

    @staticmethod
    def update_merchant_profile(merchant_id, data):
        """Update merchant profile"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        # Allowed fields to update
        allowed_fields = [
            'name_ar', 'name_en', 'phone', 'website',
            'city', 'district', 'address_line',
            'bank_name', 'iban', 'account_holder_name'
        ]

        for field in allowed_fields:
            if field in data:
                setattr(merchant, field, data[field])

        merchant.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'data': {
                    'merchant': merchant.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update profile: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Regions ====================

    @staticmethod
    def get_regions(merchant_id):
        """Get all regions for a merchant"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        regions = Region.query.filter_by(merchant_id=merchant_id).order_by(Region.name_ar).all()

        regions_data = []
        for region in regions:
            region_dict = region.to_dict()
            region_dict['branch_count'] = Branch.query.filter_by(
                region_id=region.id, is_active=True
            ).count()
            regions_data.append(region_dict)

        return {
            'success': True,
            'data': {
                'regions': regions_data
            }
        }

    @staticmethod
    def create_region(merchant_id, data):
        """Create a new region"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        # Check if region name already exists for this merchant
        existing = Region.query.filter_by(
            merchant_id=merchant_id,
            name_ar=data.get('name_ar')
        ).first()

        if existing:
            return {
                'success': False,
                'message': 'Region with this name already exists',
                'error_code': 'VAL_001'
            }

        try:
            region = Region(
                merchant_id=merchant_id,
                name_ar=data.get('name_ar'),
                name_en=data.get('name_en'),
                city=data.get('city'),
                area_description=data.get('area_description'),
                is_active=data.get('is_active', True)
            )

            db.session.add(region)
            db.session.commit()

            return {
                'success': True,
                'message': 'Region created successfully',
                'data': {
                    'region': region.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create region: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def update_region(merchant_id, region_id, data):
        """Update a region"""
        region = Region.query.filter_by(id=region_id, merchant_id=merchant_id).first()

        if not region:
            return {
                'success': False,
                'message': 'Region not found',
                'error_code': 'MERCH_003'
            }

        # Check for duplicate name if changing
        if 'name_ar' in data and data['name_ar'] != region.name_ar:
            existing = Region.query.filter_by(
                merchant_id=merchant_id,
                name_ar=data['name_ar']
            ).first()

            if existing:
                return {
                    'success': False,
                    'message': 'Region with this name already exists',
                    'error_code': 'VAL_001'
                }

        allowed_fields = ['name_ar', 'name_en', 'city', 'area_description', 'is_active']

        for field in allowed_fields:
            if field in data:
                setattr(region, field, data[field])

        region.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Region updated successfully',
                'data': {
                    'region': region.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update region: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def delete_region(merchant_id, region_id):
        """Delete a region (soft delete by setting inactive)"""
        region = Region.query.filter_by(id=region_id, merchant_id=merchant_id).first()

        if not region:
            return {
                'success': False,
                'message': 'Region not found',
                'error_code': 'MERCH_003'
            }

        # Check if region has active branches
        active_branches = Branch.query.filter_by(region_id=region_id, is_active=True).count()
        if active_branches > 0:
            return {
                'success': False,
                'message': f'Cannot delete region with {active_branches} active branches',
                'error_code': 'VAL_001'
            }

        try:
            region.is_active = False
            region.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'message': 'Region deleted successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to delete region: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Branches ====================

    @staticmethod
    def get_branches(merchant_id, region_id=None, is_active=None):
        """Get branches for a merchant"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        query = Branch.query.filter_by(merchant_id=merchant_id)

        if region_id:
            query = query.filter_by(region_id=region_id)

        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        branches = query.order_by(Branch.name_ar).all()

        return {
            'success': True,
            'data': {
                'branches': [b.to_dict() for b in branches]
            }
        }

    @staticmethod
    def create_branch(merchant_id, data):
        """Create a new branch"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        if merchant.status != 'active':
            return {
                'success': False,
                'message': 'Only active merchants can create branches',
                'error_code': 'MERCH_004'
            }

        # Validate region if provided
        if data.get('region_id'):
            region = Region.query.filter_by(
                id=data['region_id'],
                merchant_id=merchant_id
            ).first()

            if not region:
                return {
                    'success': False,
                    'message': 'Region not found',
                    'error_code': 'MERCH_003'
                }

        # Check for duplicate code
        if data.get('code'):
            existing = Branch.query.filter_by(
                merchant_id=merchant_id,
                code=data['code']
            ).first()

            if existing:
                return {
                    'success': False,
                    'message': 'Branch code already exists',
                    'error_code': 'VAL_001'
                }

        try:
            branch = Branch(
                merchant_id=merchant_id,
                region_id=data.get('region_id'),
                name_ar=data.get('name_ar'),
                name_en=data.get('name_en'),
                code=data.get('code'),
                city=data.get('city'),
                district=data.get('district'),
                address_line=data.get('address_line'),
                latitude=data.get('latitude'),
                longitude=data.get('longitude'),
                phone=data.get('phone'),
                email=data.get('email'),
                operating_hours=data.get('operating_hours', {}),
                settlement_cycle=data.get('settlement_cycle', 'weekly'),
                is_active=data.get('is_active', True)
            )

            db.session.add(branch)
            db.session.commit()

            return {
                'success': True,
                'message': 'Branch created successfully',
                'data': {
                    'branch': branch.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create branch: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def get_branch(merchant_id, branch_id):
        """Get a specific branch"""
        branch = Branch.query.filter_by(id=branch_id, merchant_id=merchant_id).first()

        if not branch:
            return {
                'success': False,
                'message': 'Branch not found',
                'error_code': 'MERCH_005'
            }

        # Get staff count
        staff_count = MerchantUser.query.filter_by(branch_id=branch_id, is_active=True).count()

        branch_data = branch.to_dict()
        branch_data['staff_count'] = staff_count
        branch_data['region'] = branch.region.to_dict() if branch.region else None

        return {
            'success': True,
            'data': {
                'branch': branch_data
            }
        }

    @staticmethod
    def update_branch(merchant_id, branch_id, data):
        """Update a branch"""
        branch = Branch.query.filter_by(id=branch_id, merchant_id=merchant_id).first()

        if not branch:
            return {
                'success': False,
                'message': 'Branch not found',
                'error_code': 'MERCH_005'
            }

        # Validate region if changing
        if 'region_id' in data and data['region_id']:
            region = Region.query.filter_by(
                id=data['region_id'],
                merchant_id=merchant_id
            ).first()

            if not region:
                return {
                    'success': False,
                    'message': 'Region not found',
                    'error_code': 'MERCH_003'
                }

        # Check for duplicate code if changing
        if 'code' in data and data['code'] != branch.code:
            existing = Branch.query.filter_by(
                merchant_id=merchant_id,
                code=data['code']
            ).first()

            if existing:
                return {
                    'success': False,
                    'message': 'Branch code already exists',
                    'error_code': 'VAL_001'
                }

        allowed_fields = [
            'region_id', 'name_ar', 'name_en', 'code', 'city', 'district',
            'address_line', 'latitude', 'longitude', 'phone', 'email',
            'operating_hours', 'settlement_cycle', 'is_active'
        ]

        for field in allowed_fields:
            if field in data:
                setattr(branch, field, data[field])

        branch.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Branch updated successfully',
                'data': {
                    'branch': branch.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update branch: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Staff ====================

    @staticmethod
    def get_staff(merchant_id, role=None, branch_id=None, page=1, per_page=20):
        """Get staff members for a merchant"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        query = MerchantUser.query.filter_by(merchant_id=merchant_id)

        if role:
            query = query.filter_by(role=role)

        if branch_id:
            query = query.filter_by(branch_id=branch_id)

        pagination = query.order_by(MerchantUser.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )

        staff_data = []
        for user in pagination.items:
            user_dict = user.to_dict()
            user_dict['branch'] = user.branch.to_dict() if user.branch else None
            user_dict['region'] = user.region.to_dict() if user.region else None
            staff_data.append(user_dict)

        return {
            'success': True,
            'data': {
                'staff': staff_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def create_staff(merchant_id, data):
        """Create a new staff member"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        # Check if email already exists
        if MerchantUser.query.filter_by(email=data.get('email')).first():
            return {
                'success': False,
                'message': 'Email already registered',
                'error_code': 'VAL_001'
            }

        # Validate branch if provided
        if data.get('branch_id'):
            branch = Branch.query.filter_by(
                id=data['branch_id'],
                merchant_id=merchant_id
            ).first()

            if not branch:
                return {
                    'success': False,
                    'message': 'Branch not found',
                    'error_code': 'MERCH_005'
                }

        # Validate region if provided
        if data.get('region_id'):
            region = Region.query.filter_by(
                id=data['region_id'],
                merchant_id=merchant_id
            ).first()

            if not region:
                return {
                    'success': False,
                    'message': 'Region not found',
                    'error_code': 'MERCH_003'
                }

        # Validate role
        valid_roles = ['owner', 'general_manager', 'region_manager', 'branch_manager', 'cashier']
        role = data.get('role', 'cashier')
        if role not in valid_roles:
            return {
                'success': False,
                'message': f'Invalid role. Must be one of: {valid_roles}',
                'error_code': 'VAL_001'
            }

        try:
            user = MerchantUser(
                merchant_id=merchant_id,
                branch_id=data.get('branch_id'),
                region_id=data.get('region_id'),
                email=data.get('email'),
                full_name=data.get('full_name'),
                phone=data.get('phone'),
                national_id=data.get('national_id'),
                role=role,
                permissions=data.get('permissions', []),
                is_active=data.get('is_active', True)
            )
            user.set_password(data.get('password'))

            db.session.add(user)
            db.session.commit()

            return {
                'success': True,
                'message': 'Staff member created successfully',
                'data': {
                    'staff': user.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create staff member: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def update_staff(merchant_id, staff_id, data):
        """Update a staff member"""
        user = MerchantUser.query.filter_by(id=staff_id, merchant_id=merchant_id).first()

        if not user:
            return {
                'success': False,
                'message': 'Staff member not found',
                'error_code': 'MERCH_006'
            }

        # Validate branch if changing
        if 'branch_id' in data and data['branch_id']:
            branch = Branch.query.filter_by(
                id=data['branch_id'],
                merchant_id=merchant_id
            ).first()

            if not branch:
                return {
                    'success': False,
                    'message': 'Branch not found',
                    'error_code': 'MERCH_005'
                }

        # Validate region if changing
        if 'region_id' in data and data['region_id']:
            region = Region.query.filter_by(
                id=data['region_id'],
                merchant_id=merchant_id
            ).first()

            if not region:
                return {
                    'success': False,
                    'message': 'Region not found',
                    'error_code': 'MERCH_003'
                }

        # Validate role if changing
        if 'role' in data:
            valid_roles = ['owner', 'general_manager', 'region_manager', 'branch_manager', 'cashier']
            if data['role'] not in valid_roles:
                return {
                    'success': False,
                    'message': f'Invalid role. Must be one of: {valid_roles}',
                    'error_code': 'VAL_001'
                }

        allowed_fields = [
            'branch_id', 'region_id', 'full_name', 'phone',
            'role', 'permissions', 'is_active'
        ]

        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])

        # Handle password update separately
        if 'password' in data and data['password']:
            user.set_password(data['password'])

        user.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Staff member updated successfully',
                'data': {
                    'staff': user.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update staff member: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def delete_staff(merchant_id, staff_id):
        """Delete (deactivate) a staff member"""
        user = MerchantUser.query.filter_by(id=staff_id, merchant_id=merchant_id).first()

        if not user:
            return {
                'success': False,
                'message': 'Staff member not found',
                'error_code': 'MERCH_006'
            }

        # Cannot delete owner
        if user.role == 'owner':
            return {
                'success': False,
                'message': 'Cannot delete owner account',
                'error_code': 'VAL_001'
            }

        try:
            user.is_active = False
            user.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'message': 'Staff member deleted successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to delete staff member: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Statistics ====================

    @staticmethod
    def get_merchant_statistics(merchant_id):
        """Get merchant statistics for dashboard"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        # Total transactions
        total_transactions = Transaction.query.filter_by(merchant_id=merchant_id).count()

        # Total sales (confirmed + paid)
        total_sales = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.total_amount), 0)
        ).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.status.in_(['confirmed', 'paid'])
        ).scalar()

        # Pending settlement amount
        pending_settlement = db.session.query(
            db.func.coalesce(
                db.func.sum(Transaction.total_amount - Transaction.paid_amount),
                0
            )
        ).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.status == 'confirmed'
        ).scalar()

        # Active branches
        active_branches = Branch.query.filter_by(
            merchant_id=merchant_id, is_active=True
        ).count()

        # Active staff
        active_staff = MerchantUser.query.filter_by(
            merchant_id=merchant_id, is_active=True
        ).count()

        return {
            'success': True,
            'data': {
                'statistics': {
                    'total_transactions': total_transactions,
                    'total_sales': float(total_sales) if total_sales else 0,
                    'pending_settlement': float(pending_settlement) if pending_settlement else 0,
                    'active_branches': active_branches,
                    'active_staff': active_staff
                }
            }
        }

    # ==================== Public Store Listing ====================

    @staticmethod
    def get_stores_for_customer(city=None, search=None, page=1, per_page=20):
        """Get approved stores for customer browsing"""
        query = Merchant.query.filter_by(status='active')

        if city:
            # Filter by merchants with branches in this city
            merchant_ids = db.session.query(Branch.merchant_id).filter(
                Branch.city == city,
                Branch.is_active == True
            ).distinct()
            query = query.filter(Merchant.id.in_(merchant_ids))

        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Merchant.name_ar.ilike(search_term),
                    Merchant.name_en.ilike(search_term)
                )
            )

        pagination = query.order_by(Merchant.name_ar).paginate(
            page=page, per_page=per_page, error_out=False
        )

        merchants_data = []
        for merchant in pagination.items:
            merchant_dict = {
                'id': merchant.id,
                'name_ar': merchant.name_ar,
                'name_en': merchant.name_en,
                'business_type': merchant.business_type,
                'city': merchant.city,
                'branch_count': Branch.query.filter_by(
                    merchant_id=merchant.id, is_active=True
                ).count()
            }
            merchants_data.append(merchant_dict)

        return {
            'success': True,
            'data': {
                'merchants': merchants_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def get_store_details(merchant_id):
        """Get store details for customer view"""
        merchant = Merchant.query.filter_by(id=merchant_id, status='active').first()

        if not merchant:
            return {
                'success': False,
                'message': 'Store not found',
                'error_code': 'MERCH_001'
            }

        # Get active branches
        branches = Branch.query.filter_by(
            merchant_id=merchant_id, is_active=True
        ).all()

        return {
            'success': True,
            'data': {
                'merchant': {
                    'id': merchant.id,
                    'name_ar': merchant.name_ar,
                    'name_en': merchant.name_en,
                    'business_type': merchant.business_type,
                    'city': merchant.city,
                    'phone': merchant.phone,
                    'website': merchant.website
                },
                'branches': [
                    {
                        'id': b.id,
                        'name_ar': b.name_ar,
                        'name_en': b.name_en,
                        'city': b.city,
                        'district': b.district,
                        'address_line': b.address_line,
                        'phone': b.phone,
                        'latitude': float(b.latitude) if b.latitude else None,
                        'longitude': float(b.longitude) if b.longitude else None,
                        'operating_hours': b.operating_hours
                    }
                    for b in branches
                ]
            }
        }

    # ==================== Admin Functions ====================

    @staticmethod
    def search_merchants(status=None, search=None, city=None, page=1, per_page=20):
        """Search merchants (admin only)"""
        query = Merchant.query

        if status:
            query = query.filter(Merchant.status == status)

        if city:
            query = query.filter(Merchant.city == city)

        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Merchant.name_ar.ilike(search_term),
                    Merchant.name_en.ilike(search_term),
                    Merchant.commercial_registration.ilike(search_term),
                    Merchant.email.ilike(search_term)
                )
            )

        query = query.order_by(Merchant.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'success': True,
            'data': {
                'merchants': [m.to_dict() for m in pagination.items]
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def update_merchant_status(merchant_id, status, reason=None, admin_id=None):
        """Update merchant status (admin only)"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        valid_statuses = ['pending', 'active', 'suspended', 'rejected']
        if status not in valid_statuses:
            return {
                'success': False,
                'message': f'Invalid status. Must be one of: {valid_statuses}',
                'error_code': 'VAL_001'
            }

        old_status = merchant.status
        merchant.status = status
        merchant.status_reason = reason
        merchant.updated_at = datetime.utcnow()

        if status == 'active' and old_status == 'pending':
            merchant.approved_by = admin_id
            merchant.approved_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='merchant.status_updated',
                entity_type='merchant',
                entity_id=merchant_id,
                old_values={'status': old_status},
                new_values={'status': status, 'reason': reason}
            )

            return {
                'success': True,
                'message': f'Merchant status updated to {status}',
                'data': {
                    'merchant': merchant.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update status: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def update_merchant_commission(merchant_id, commission_rate, admin_id=None):
        """Update merchant commission rate (admin only)"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        if commission_rate < 0 or commission_rate > 100:
            return {
                'success': False,
                'message': 'Commission rate must be between 0 and 100',
                'error_code': 'VAL_001'
            }

        old_rate = float(merchant.commission_rate)
        merchant.commission_rate = commission_rate
        merchant.updated_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='merchant.commission_updated',
                entity_type='merchant',
                entity_id=merchant_id,
                old_values={'commission_rate': old_rate},
                new_values={'commission_rate': commission_rate}
            )

            return {
                'success': True,
                'message': 'Commission rate updated successfully',
                'data': {
                    'merchant': merchant.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update commission: {str(e)}',
                'error_code': 'SYS_001'
            }
