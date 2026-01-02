"""
Merchant Routes
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user

merchants_bp = Blueprint('merchants', __name__)


# ==================== Public Endpoints ====================

@merchants_bp.route('/public', methods=['GET'])
def get_public_merchants():
    """Get list of active merchants (public endpoint for app)"""
    from app.services.merchant_service import MerchantService

    category = request.args.get('category')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = MerchantService.get_public_merchants(
        category=category,
        search=search,
        page=page,
        per_page=per_page
    )

    return jsonify(result)


# ==================== Registration & Profile ====================

@merchants_bp.route('/register', methods=['POST'])
def register_merchant():
    """Register new merchant"""
    from app.services.merchant_service import MerchantService

    data = request.get_json()
    result = MerchantService.register_merchant(data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me', methods=['GET'])
@jwt_required()
def get_merchant_profile():
    """Get merchant profile"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_merchant_profile(identity['merchant_id'])

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@merchants_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_merchant_profile():
    """Update merchant profile"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.update_merchant_profile(identity['merchant_id'], data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Regions ====================

@merchants_bp.route('/me/regions', methods=['GET'])
@jwt_required()
def get_regions():
    """Get all regions"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_regions(identity['merchant_id'])

    return jsonify(result)


@merchants_bp.route('/me/regions', methods=['POST'])
@jwt_required()
def create_region():
    """Create region"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.create_region(identity['merchant_id'], data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me/regions/<region_id>', methods=['PUT'])
@jwt_required()
def update_region(region_id):
    """Update region"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.update_region(identity['merchant_id'], region_id, data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


@merchants_bp.route('/me/regions/<region_id>', methods=['DELETE'])
@jwt_required()
def delete_region(region_id):
    """Delete region"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.delete_region(identity['merchant_id'], region_id)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Branches ====================

@merchants_bp.route('/me/branches', methods=['GET'])
@jwt_required()
def get_branches():
    """Get all branches"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    region_id = request.args.get('region_id')
    is_active = request.args.get('is_active')

    result = MerchantService.get_branches(
        identity['merchant_id'],
        region_id=region_id,
        is_active=is_active
    )

    return jsonify(result)


@merchants_bp.route('/me/branches', methods=['POST'])
@jwt_required()
def create_branch():
    """Create branch"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.create_branch(identity['merchant_id'], data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me/branches/<branch_id>', methods=['GET'])
@jwt_required()
def get_branch(branch_id):
    """Get branch details"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_branch(identity['merchant_id'], branch_id)

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@merchants_bp.route('/me/branches/<branch_id>', methods=['PUT'])
@jwt_required()
def update_branch(branch_id):
    """Update branch"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.update_branch(identity['merchant_id'], branch_id, data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Staff ====================

@merchants_bp.route('/me/staff', methods=['GET'])
@jwt_required()
def get_staff():
    """Get all staff"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    role = request.args.get('role')
    branch_id = request.args.get('branch_id')

    result = MerchantService.get_staff(
        identity['merchant_id'],
        role=role,
        branch_id=branch_id
    )

    return jsonify(result)


@merchants_bp.route('/me/staff', methods=['POST'])
@jwt_required()
def create_staff():
    """Add staff member"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.create_staff(identity['merchant_id'], data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me/staff/<staff_id>', methods=['GET'])
@jwt_required()
def get_staff_member(staff_id):
    """Get staff member details"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_staff_member(identity['merchant_id'], staff_id)

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@merchants_bp.route('/me/staff/<staff_id>', methods=['PUT'])
@jwt_required()
def update_staff(staff_id):
    """Update staff"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()
    result = MerchantService.update_staff(identity['merchant_id'], staff_id, data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Customer Lookup (by Bariq ID) ====================

@merchants_bp.route('/customers/lookup/<bariq_id>', methods=['GET'])
@jwt_required()
def lookup_customer(bariq_id):
    """Look up customer by Bariq ID for transaction"""
    from app.models.customer import Customer

    customer = Customer.query.filter_by(bariq_id=bariq_id).first()

    if not customer:
        return jsonify({
            'success': False,
            'message': 'Customer not found',
            'error_code': 'CUST_001'
        }), 404

    return jsonify({
        'success': True,
        'data': {
            'id': customer.id,
            'bariq_id': customer.bariq_id,
            'full_name_ar': customer.full_name_ar,
            'full_name_en': customer.full_name_en,
            'status': customer.status,
            'credit_limit': customer.credit_limit,
            'available_credit': customer.available_credit,
            'used_credit': customer.credit_limit - customer.available_credit if customer.credit_limit else 0
        }
    })


# ==================== Transactions ====================

@merchants_bp.route('/me/transactions', methods=['POST'])
@jwt_required()
def create_transaction():
    """Create new transaction/invoice"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    data = request.get_json()

    # Support both customer_bariq_id (new) and customer_national_id (legacy)
    customer_bariq_id = data.get('customer_bariq_id')

    result = TransactionService.create_transaction(
        merchant_id=identity['merchant_id'],
        branch_id=data.get('branch_id') or identity.get('branch_id'),
        cashier_id=identity['id'],
        customer_bariq_id=customer_bariq_id,
        items=data.get('items', []),
        discount=data.get('discount', 0),
        notes=data.get('notes'),
        payment_term_days=data.get('payment_term_days')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get transactions"""
    from app.services.transaction_service import TransactionService

    identity = current_user

    branch_id = request.args.get('branch_id')
    status = request.args.get('status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = TransactionService.get_merchant_transactions(
        merchant_id=identity['merchant_id'],
        branch_id=branch_id or identity.get('branch_id'),
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        per_page=per_page
    )

    return jsonify(result)


@merchants_bp.route('/me/transactions/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get transaction details"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    result = TransactionService.get_transaction_for_merchant(
        identity['merchant_id'],
        transaction_id
    )

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@merchants_bp.route('/me/transactions/<transaction_id>/cancel', methods=['POST'])
@jwt_required()
def cancel_transaction(transaction_id):
    """Cancel pending transaction"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    data = request.get_json()

    result = TransactionService.cancel_transaction(
        identity['merchant_id'],
        transaction_id,
        data.get('reason')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Returns ====================

@merchants_bp.route('/me/transactions/<transaction_id>/returns', methods=['POST'])
@jwt_required()
def create_return(transaction_id):
    """Process return"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    data = request.get_json()

    result = TransactionService.process_return(
        merchant_id=identity['merchant_id'],
        transaction_id=transaction_id,
        return_amount=data.get('return_amount'),
        reason=data.get('reason'),
        reason_details=data.get('reason_details'),
        returned_items=data.get('returned_items', []),
        processed_by=identity['id']
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me/returns', methods=['GET'])
@jwt_required()
def get_returns():
    """Get all returns"""
    from app.services.transaction_service import TransactionService

    identity = current_user

    branch_id = request.args.get('branch_id')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    result = TransactionService.get_merchant_returns(
        merchant_id=identity['merchant_id'],
        branch_id=branch_id,
        from_date=from_date,
        to_date=to_date
    )

    return jsonify(result)


# ==================== Reports ====================

@merchants_bp.route('/me/reports/summary', methods=['GET'])
@jwt_required()
def get_reports_summary():
    """Get summary dashboard"""
    from app.services.report_service import ReportService

    identity = current_user

    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    branch_id = request.args.get('branch_id')

    result = ReportService.get_merchant_summary(
        merchant_id=identity['merchant_id'],
        branch_id=branch_id,
        from_date=from_date,
        to_date=to_date
    )

    return jsonify(result)


@merchants_bp.route('/me/reports/transactions', methods=['GET'])
@jwt_required()
def get_reports_transactions():
    """Detailed transaction report"""
    from app.services.report_service import ReportService

    identity = current_user

    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    branch_id = request.args.get('branch_id')
    group_by = request.args.get('group_by', 'day')

    result = ReportService.get_transaction_report(
        merchant_id=identity['merchant_id'],
        branch_id=branch_id,
        from_date=from_date,
        to_date=to_date,
        group_by=group_by
    )

    return jsonify(result)


# ==================== Settlements ====================

@merchants_bp.route('/me/settlements', methods=['GET'])
@jwt_required()
def get_settlements():
    """Get settlements"""
    from app.services.settlement_service import SettlementService

    identity = current_user

    status = request.args.get('status')
    branch_id = request.args.get('branch_id')
    page = request.args.get('page', 1, type=int)

    result = SettlementService.get_merchant_settlements(
        merchant_id=identity['merchant_id'],
        branch_id=branch_id,
        status=status,
        page=page
    )

    return jsonify(result)


@merchants_bp.route('/me/settlements/<settlement_id>', methods=['GET'])
@jwt_required()
def get_settlement(settlement_id):
    """Get settlement details"""
    from app.services.settlement_service import SettlementService

    identity = current_user
    result = SettlementService.get_settlement_details(
        identity['merchant_id'],
        settlement_id
    )

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


# ==================== Mobile App Endpoints ====================

# -------- Staff Profile --------

@merchants_bp.route('/me/profile', methods=['GET'])
@jwt_required()
def get_staff_profile():
    """Get current staff member's profile (for mobile app)"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_staff_profile(identity['id'])

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@merchants_bp.route('/me/profile', methods=['PUT'])
@jwt_required()
def update_staff_profile():
    """Update current staff member's profile"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()

    result = MerchantService.update_staff_profile(identity['id'], data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


@merchants_bp.route('/me/profile/password', methods=['PUT'])
@jwt_required()
def change_staff_password():
    """Change staff password"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required',
            'error_code': 'VAL_001'
        }), 400

    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({
            'success': False,
            'message': 'Current password and new password are required',
            'error_code': 'VAL_001'
        }), 400

    result = MerchantService.change_staff_password(
        identity['id'],
        current_password,
        new_password
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# -------- Mobile Dashboard --------

@merchants_bp.route('/me/dashboard', methods=['GET'])
@jwt_required()
def get_mobile_dashboard():
    """Get role-based dashboard data for mobile app"""
    from app.services.merchant_service import MerchantService

    identity = current_user

    # Get optional filters
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')

    result = MerchantService.get_mobile_dashboard(
        staff_id=identity['id'],
        merchant_id=identity['merchant_id'],
        from_date=from_date,
        to_date=to_date
    )

    return jsonify(result)


@merchants_bp.route('/me/quick-stats', methods=['GET'])
@jwt_required()
def get_quick_stats():
    """Get quick stats based on role"""
    from app.services.merchant_service import MerchantService

    identity = current_user

    result = MerchantService.get_role_based_stats(
        staff_id=identity['id'],
        merchant_id=identity['merchant_id']
    )

    return jsonify(result)


# -------- Staff Notifications --------

@merchants_bp.route('/me/notifications', methods=['GET'])
@jwt_required()
def get_staff_notifications():
    """Get staff notifications"""
    from app.services.notification_service import NotificationService

    identity = current_user
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)

    result = NotificationService.get_merchant_staff_notifications(
        identity['id'],
        unread_only=unread_only,
        page=page
    )

    return jsonify(result)


@merchants_bp.route('/me/notifications/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_staff_notification_read(notification_id):
    """Mark notification as read"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.mark_staff_notification_read(
        identity['id'],
        notification_id
    )

    return jsonify(result)


@merchants_bp.route('/me/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_staff_notifications_read():
    """Mark all notifications as read"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.mark_all_staff_notifications_read(identity['id'])

    return jsonify(result)


# -------- Device Registration (FCM) --------

@merchants_bp.route('/me/devices', methods=['GET'])
@jwt_required()
def get_staff_devices():
    """Get registered devices"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.get_merchant_devices(identity['id'])

    return jsonify(result)


@merchants_bp.route('/me/devices', methods=['POST'])
@jwt_required()
def register_staff_device():
    """Register device for push notifications"""
    from app.services.notification_service import NotificationService

    identity = current_user
    data = request.get_json()

    result = NotificationService.register_merchant_device(
        staff_id=identity['id'],
        fcm_token=data.get('fcm_token'),
        device_type=data.get('device_type'),
        device_name=data.get('device_name'),
        device_id=data.get('device_id')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@merchants_bp.route('/me/devices/<device_id>', methods=['DELETE'])
@jwt_required()
def unregister_staff_device(device_id):
    """Unregister device from push notifications"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.unregister_merchant_device(identity['id'], device_id)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# -------- Role-Based Data Endpoints --------

@merchants_bp.route('/me/accessible-branches', methods=['GET'])
@jwt_required()
def get_accessible_branches():
    """Get branches accessible by current staff member"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_accessible_branches(identity['id'])

    return jsonify(result)


@merchants_bp.route('/me/accessible-regions', methods=['GET'])
@jwt_required()
def get_accessible_regions():
    """Get regions accessible by current staff member"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_accessible_regions(identity['id'])

    return jsonify(result)


@merchants_bp.route('/me/team', methods=['GET'])
@jwt_required()
def get_my_team():
    """Get staff members that current user can manage"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_subordinates(identity['id'])

    return jsonify(result)


# -------- Today's Activity (for Cashier/Branch Manager) --------

@merchants_bp.route('/me/today', methods=['GET'])
@jwt_required()
def get_today_activity():
    """Get today's activity summary"""
    from app.services.merchant_service import MerchantService

    identity = current_user
    result = MerchantService.get_today_activity(
        staff_id=identity['id'],
        merchant_id=identity['merchant_id']
    )

    return jsonify(result)


@merchants_bp.route('/me/my-transactions', methods=['GET'])
@jwt_required()
def get_my_transactions():
    """Get transactions created by current staff member"""
    from app.services.transaction_service import TransactionService

    identity = current_user

    status = request.args.get('status')
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = TransactionService.get_staff_transactions(
        staff_id=identity['id'],
        status=status,
        from_date=from_date,
        to_date=to_date,
        page=page,
        per_page=per_page
    )

    return jsonify(result)
