"""
Frontend Routes - Serve HTML Templates
"""
from flask import Blueprint, render_template

frontend_bp = Blueprint('frontend', __name__)


# ==================== Public Pages ====================

@frontend_bp.route('/')
def index():
    """Landing page"""
    return render_template('index.html')


@frontend_bp.route('/login')
def login():
    """Login page"""
    return render_template('login.html')


# ==================== Customer Pages ====================

@frontend_bp.route('/customer')
def customer_dashboard():
    """Customer dashboard"""
    return render_template('customer/dashboard.html', active_page='dashboard')


@frontend_bp.route('/customer/transactions')
def customer_transactions():
    """Customer transactions page"""
    return render_template('customer/transactions.html', active_page='transactions')


@frontend_bp.route('/customer/payments')
def customer_payments():
    """Customer payments page"""
    return render_template('customer/payments.html', active_page='payments')


@frontend_bp.route('/customer/credit')
def customer_credit():
    """Customer credit page"""
    return render_template('customer/credit.html', active_page='credit')


@frontend_bp.route('/customer/profile')
def customer_profile():
    """Customer profile page"""
    return render_template('customer/profile.html', active_page='profile')


@frontend_bp.route('/customer/pay')
def customer_pay():
    """Customer payment page"""
    return render_template('customer/pay.html', active_page='payments')


# ==================== Merchant Pages ====================

@frontend_bp.route('/merchant')
def merchant_dashboard():
    """Merchant dashboard"""
    return render_template('merchant/dashboard.html', active_page='dashboard')


@frontend_bp.route('/merchant/transactions')
def merchant_transactions():
    """Merchant transactions page"""
    return render_template('merchant/transactions.html', active_page='transactions')


@frontend_bp.route('/merchant/new-transaction')
def merchant_new_transaction():
    """Merchant new transaction page"""
    return render_template('merchant/new_transaction.html', active_page='new-transaction')


@frontend_bp.route('/merchant/staff')
def merchant_staff():
    """Merchant staff page"""
    return render_template('merchant/staff.html', active_page='staff')


@frontend_bp.route('/merchant/branches')
def merchant_branches():
    """Merchant branches page"""
    return render_template('merchant/branches.html', active_page='branches')


@frontend_bp.route('/merchant/settlements')
def merchant_settlements():
    """Merchant settlements page"""
    return render_template('merchant/settlements.html', active_page='settlements')


@frontend_bp.route('/merchant/reports')
def merchant_reports():
    """Merchant reports page"""
    return render_template('merchant/reports.html', active_page='reports')


@frontend_bp.route('/merchant/team')
def merchant_team():
    """Merchant team/staff hierarchy page"""
    return render_template('merchant/team.html', active_page='team')


@frontend_bp.route('/merchant/regions')
def merchant_regions():
    """Merchant regions page"""
    return render_template('merchant/regions.html', active_page='regions')


# ==================== Payment Gateway Pages ====================

@frontend_bp.route('/payment/complete')
def payment_complete():
    """Payment completion redirect page"""
    from flask import request

    # PayTabs will redirect here with query params
    tran_ref = request.args.get('tranRef')
    cart_id = request.args.get('cartId')
    status = request.args.get('respStatus')
    message = request.args.get('respMessage')

    return render_template(
        'payment/complete.html',
        tran_ref=tran_ref,
        cart_id=cart_id,
        status=status,
        message=message
    )
