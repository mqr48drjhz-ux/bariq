"""
Customer Routes
"""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, current_user
from app.extensions import limiter

customers_bp = Blueprint('customers', __name__)

# Rate limit key function for customer-based limiting
def get_customer_id():
    """Get current customer ID for rate limiting"""
    try:
        from flask_jwt_extended import get_jwt_identity
        identity = get_jwt_identity()
        if identity:
            import json
            user_data = json.loads(identity)
            return user_data.get('id', 'anonymous')
    except:
        pass
    return 'anonymous'


# ==================== Profile ====================

@customers_bp.route('/me', methods=['GET'])
@jwt_required()
def get_profile():
    """Get current customer profile"""
    from app.services.customer_service import CustomerService

    identity = current_user
    result = CustomerService.get_customer_profile(identity['id'])

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@customers_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_profile():
    """Update customer profile"""
    from app.services.customer_service import CustomerService

    identity = current_user
    data = request.get_json()

    result = CustomerService.update_customer_profile(identity['id'], data)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


@customers_bp.route('/me/password', methods=['PUT'])
@jwt_required()
def change_password():
    """Change customer password"""
    from app.services.customer_service import CustomerService

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

    result = CustomerService.change_password(
        identity['id'],
        current_password,
        new_password
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Credit ====================

@customers_bp.route('/me/credit', methods=['GET'])
@jwt_required()
def get_credit():
    """Get customer credit details"""
    from app.services.customer_service import CustomerService

    identity = current_user
    result = CustomerService.get_credit_details(identity['id'])

    return jsonify(result)


@customers_bp.route('/me/credit/request-increase', methods=['POST'])
@jwt_required()
def request_credit_increase():
    """Request credit limit increase"""
    from app.services.customer_service import CustomerService

    identity = current_user
    data = request.get_json()

    result = CustomerService.request_credit_increase(
        identity['id'],
        data.get('requested_amount'),
        data.get('reason')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


# ==================== Transactions ====================

@customers_bp.route('/me/transactions', methods=['GET'])
@jwt_required()
def get_transactions():
    """Get customer transactions"""
    from app.services.transaction_service import TransactionService

    identity = current_user

    # Get query params
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = TransactionService.get_customer_transactions(
        identity['id'],
        status=status,
        page=page,
        per_page=per_page
    )

    return jsonify(result)


@customers_bp.route('/me/transactions/<transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    """Get single transaction details"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    result = TransactionService.get_transaction_for_customer(
        identity['id'],
        transaction_id
    )

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


@customers_bp.route('/me/transactions/<transaction_id>/confirm', methods=['POST'])
@jwt_required()
def confirm_transaction(transaction_id):
    """Confirm a pending transaction"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    result = TransactionService.confirm_transaction(
        identity['id'],
        transaction_id
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


@customers_bp.route('/me/transactions/<transaction_id>/reject', methods=['POST'])
@jwt_required()
def reject_transaction(transaction_id):
    """Reject a pending transaction"""
    from app.services.transaction_service import TransactionService

    identity = current_user
    data = request.get_json() or {}

    result = TransactionService.reject_transaction(
        identity['id'],
        transaction_id,
        reason=data.get('reason')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== Debt & Payments ====================

@customers_bp.route('/me/debt', methods=['GET'])
@jwt_required()
def get_debt():
    """Get current debt summary"""
    from app.services.payment_service import PaymentService

    identity = current_user
    result = PaymentService.get_customer_debt(identity['id'])

    return jsonify(result)


@customers_bp.route('/me/payments', methods=['GET'])
@jwt_required()
def get_payments():
    """Get payment history"""
    from app.services.payment_service import PaymentService

    identity = current_user
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = PaymentService.get_customer_payments(
        identity['id'],
        page=page,
        per_page=per_page
    )

    return jsonify(result)


@customers_bp.route('/me/payments', methods=['POST'])
@jwt_required()
def make_payment():
    """Make a payment for one or multiple transactions"""
    from app.services.payment_service import PaymentService

    identity = current_user
    data = request.get_json()

    # Support both single transaction_id and array of transaction_ids
    transaction_ids = data.get('transaction_ids')
    transaction_id = data.get('transaction_id')
    amount = data.get('amount')
    payment_method = data.get('payment_method', 'card')

    if transaction_ids and isinstance(transaction_ids, list):
        # Pay for multiple transactions
        result = PaymentService.make_multi_transaction_payment(
            identity['id'],
            transaction_ids,
            amount,
            payment_method
        )
    elif transaction_id:
        # Pay for single transaction (backward compatibility)
        result = PaymentService.make_payment(
            identity['id'],
            transaction_id,
            amount,
            payment_method
        )
    else:
        return jsonify({
            'success': False,
            'message': 'Either transaction_id or transaction_ids is required',
            'error_code': 'VAL_001'
        }), 400

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


# ==================== Stores ====================

@customers_bp.route('/stores', methods=['GET'])
@jwt_required()
def get_stores():
    """Get available stores"""
    from app.services.merchant_service import MerchantService

    city = request.args.get('city')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    result = MerchantService.get_stores_for_customer(
        city=city,
        search=search,
        page=page,
        per_page=per_page
    )

    return jsonify(result)


@customers_bp.route('/stores/<merchant_id>', methods=['GET'])
@jwt_required()
def get_store(merchant_id):
    """Get store details"""
    from app.services.merchant_service import MerchantService

    result = MerchantService.get_store_details(merchant_id)

    if not result['success']:
        return jsonify(result), 404

    return jsonify(result)


# ==================== Notifications ====================

@customers_bp.route('/me/notifications', methods=['GET'])
@jwt_required()
def get_notifications():
    """Get notifications"""
    from app.services.notification_service import NotificationService

    identity = current_user
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    page = request.args.get('page', 1, type=int)

    result = NotificationService.get_customer_notifications(
        identity['id'],
        unread_only=unread_only,
        page=page
    )

    return jsonify(result)


@customers_bp.route('/me/notifications/<notification_id>/read', methods=['PUT'])
@jwt_required()
def mark_notification_read(notification_id):
    """Mark notification as read"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.mark_as_read(identity['id'], notification_id)

    return jsonify(result)


@customers_bp.route('/me/notifications/read-all', methods=['POST'])
@jwt_required()
def mark_all_notifications_read():
    """Mark all notifications as read"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.mark_all_as_read(identity['id'])

    return jsonify(result)


# ==================== Credit Health ====================

@customers_bp.route('/me/credit/health', methods=['GET'])
@jwt_required()
def get_credit_health():
    """Get customer credit health score"""
    from app.services.customer_service import CustomerService

    identity = current_user
    result = CustomerService.get_credit_health(identity['id'])

    return jsonify(result)


# ==================== Device Registration (FCM) ====================

@customers_bp.route('/me/devices', methods=['GET'])
@jwt_required()
def get_devices():
    """Get registered devices"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.get_customer_devices(identity['id'])

    return jsonify(result)


@customers_bp.route('/me/devices', methods=['POST'])
@jwt_required()
def register_device():
    """Register device for push notifications"""
    from app.services.notification_service import NotificationService

    identity = current_user
    data = request.get_json()

    result = NotificationService.register_device(
        customer_id=identity['id'],
        fcm_token=data.get('fcm_token'),
        device_type=data.get('device_type'),
        device_name=data.get('device_name'),
        device_id=data.get('device_id')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@customers_bp.route('/me/devices/<device_id>', methods=['DELETE'])
@jwt_required()
def unregister_device(device_id):
    """Unregister device from push notifications"""
    from app.services.notification_service import NotificationService

    identity = current_user
    result = NotificationService.unregister_device(identity['id'], device_id)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


# ==================== PayTabs Payment Gateway ====================

@customers_bp.route('/me/payments/initiate', methods=['POST'])
@limiter.limit("10 per minute", key_func=get_customer_id)  # Prevent payment spam
@limiter.limit("50 per hour", key_func=get_customer_id)    # Hourly cap
@jwt_required()
def initiate_payment():
    """
    Initiate a payment via PayTabs

    Request body:
    {
        "transaction_ids": [1, 2, 3],  // or single "transaction_id": 1
        "amount": 100.00,
        "payment_method": "all"  // optional: all, creditcard, mada, stcpay, applepay
    }

    Returns payment page URL for redirect

    Rate limits:
    - 10 requests per minute per customer
    - 50 requests per hour per customer
    """
    from app.services.paytabs_service import PayTabsService

    identity = current_user
    data = request.get_json()

    if not data:
        return jsonify({
            'success': False,
            'message': 'Request body is required',
            'error_code': 'VAL_001'
        }), 400

    # Support both single and multiple transaction IDs
    transaction_ids = data.get('transaction_ids')
    if not transaction_ids:
        transaction_id = data.get('transaction_id')
        if transaction_id:
            transaction_ids = [transaction_id]

    if not transaction_ids:
        return jsonify({
            'success': False,
            'message': 'transaction_ids or transaction_id is required',
            'error_code': 'VAL_001'
        }), 400

    amount = data.get('amount')
    if not amount:
        return jsonify({
            'success': False,
            'message': 'amount is required',
            'error_code': 'VAL_001'
        }), 400

    payment_method = data.get('payment_method', 'all')

    result = PayTabsService.create_payment_page(
        customer_id=identity['id'],
        transaction_ids=transaction_ids,
        amount=float(amount),
        payment_methods=payment_method,
        description=data.get('description')
    )

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result), 201


@customers_bp.route('/me/payments/<payment_id>/status', methods=['GET'])
@jwt_required()
def get_payment_status(payment_id):
    """Get payment status by payment ID"""
    from app.models.payment import Payment

    identity = current_user

    payment = Payment.query.filter_by(
        id=payment_id,
        customer_id=identity['id']
    ).first()

    if not payment:
        return jsonify({
            'success': False,
            'message': 'Payment not found',
            'error_code': 'PAY_006'
        }), 404

    return jsonify({
        'success': True,
        'data': {
            'payment_id': payment.id,
            'status': payment.status,
            'amount': float(payment.amount),
            'payment_method': payment.payment_method,
            'gateway_reference': payment.gateway_reference,
            'created_at': payment.created_at.isoformat() if payment.created_at else None,
            'completed_at': payment.completed_at.isoformat() if payment.completed_at else None
        }
    })


@customers_bp.route('/me/payments/query/<tran_ref>', methods=['GET'])
@jwt_required()
def query_payment_gateway(tran_ref):
    """Query payment status directly from PayTabs"""
    from app.services.paytabs_service import PayTabsService
    from app.models.payment import Payment

    identity = current_user

    # Verify this payment belongs to the customer
    payment = Payment.query.filter_by(
        gateway_reference=tran_ref,
        customer_id=identity['id']
    ).first()

    if not payment:
        return jsonify({
            'success': False,
            'message': 'Payment not found',
            'error_code': 'PAY_006'
        }), 404

    result = PayTabsService.query_payment_status(tran_ref)

    if not result['success']:
        return jsonify(result), 400

    return jsonify(result)


@customers_bp.route('/me/payment-methods', methods=['GET'])
@jwt_required()
def get_payment_methods():
    """Get available payment methods"""
    from app.services.paytabs_service import PayTabsService

    result = PayTabsService.get_available_payment_methods()
    return jsonify(result)


@customers_bp.route('/me/payments/<payment_id>/verify', methods=['POST'])
@jwt_required()
def verify_payment(payment_id):
    """
    Manually verify and complete a pending payment by querying PayTabs.

    Use this endpoint after returning from PayTabs payment page to ensure
    payment status is updated (useful when webhooks are not received).
    """
    from app.services.paytabs_service import PayTabsService
    from app.models.payment import Payment

    identity = current_user

    # Find the payment
    payment = Payment.query.filter_by(
        id=payment_id,
        customer_id=identity['id']
    ).first()

    if not payment:
        return jsonify({
            'success': False,
            'message': 'Payment not found',
            'error_code': 'PAY_006'
        }), 404

    # If already completed, return success
    if payment.status == 'completed':
        return jsonify({
            'success': True,
            'message': 'Payment already completed',
            'data': {
                'payment_id': payment.id,
                'status': payment.status,
                'amount': float(payment.amount)
            }
        })

    # If no gateway reference, can't verify
    if not payment.gateway_reference:
        return jsonify({
            'success': False,
            'message': 'No gateway reference to verify',
            'error_code': 'PAY_007'
        }), 400

    # Query PayTabs for the actual status
    query_result = PayTabsService.query_payment_status(payment.gateway_reference)

    if not query_result['success']:
        # PayTabs query failed - provide helpful message
        return jsonify({
            'success': False,
            'message': 'لا يمكن التحقق من حالة الدفع حالياً. يرجى المحاولة لاحقاً أو الاتصال بالدعم.',
            'error_code': 'PAY_007',
            'details': query_result.get('message', 'Gateway query failed')
        }), 400

    gateway_status = query_result['data'].get('gateway_status', '')

    # If PayTabs says it's authorized, process the payment
    if gateway_status == 'A':  # Authorized/Approved
        # Build a webhook-like payload and process it
        import json
        gateway_response = json.loads(payment.gateway_response) if payment.gateway_response else {}

        webhook_payload = {
            'tran_ref': payment.gateway_reference,
            'cart_amount': float(payment.amount),
            'cart_currency': 'SAR',
            'payment_result': {
                'response_status': 'A',
                'response_code': '000',
                'response_message': 'Authorised'
            },
            'payment_info': {
                'payment_method': query_result['data'].get('payment_method', 'card')
            },
            'user_defined': {
                'udf1': identity['id'],
                'udf2': ','.join([str(tid) for tid in gateway_response.get('transaction_ids', [payment.transaction_id])]),
                'udf3': str(payment.amount)
            }
        }

        result = PayTabsService.handle_webhook(webhook_payload, verify_amount=False)

        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Payment verified and completed successfully',
                'data': result.get('data', {})
            })
        else:
            return jsonify(result), 400

    elif gateway_status in ['D', 'E']:  # Declined or Error
        payment.status = 'failed'
        from app.extensions import db
        db.session.commit()

        return jsonify({
            'success': False,
            'message': 'Payment was declined or failed',
            'error_code': 'PAY_001',
            'data': {
                'status': 'failed',
                'gateway_message': query_result['data'].get('response_message')
            }
        }), 400

    else:
        # Still pending or other status
        return jsonify({
            'success': True,
            'message': 'Payment is still being processed',
            'data': {
                'payment_id': payment.id,
                'status': payment.status,
                'gateway_status': gateway_status
            }
        })


@customers_bp.route('/me/test-notification', methods=['POST'])
@jwt_required()
def test_notification():
    """Send a test push notification to the customer's devices"""
    from app.services.firebase_service import push_manager

    customer_id = current_user.get('id')

    # Send notification (creates in-app + push)
    try:
        result = push_manager.send_to_customer(
            customer_id=customer_id,
            title_ar='إشعار تجريبي',
            body_ar='هذا إشعار تجريبي للتأكد من عمل الإشعارات',
            title_en='Test Notification',
            body_en='This is a test notification',
            notification_type='system'
        )
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e), 'error_code': 'PUSH_001'})
