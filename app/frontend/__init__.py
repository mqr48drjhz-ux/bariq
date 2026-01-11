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


@frontend_bp.route('/privacy-policy')
def privacy_policy():
    """Privacy policy page"""
    return render_template('privacy-policy.html')


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

@frontend_bp.route('/payment/complete', methods=['GET', 'POST'])
def payment_complete():
    """Payment completion redirect page"""
    from flask import request

    # PayTabs can redirect here with query params (GET) or form data (POST)
    if request.method == 'POST':
        tran_ref = request.form.get('tranRef') or request.form.get('tran_ref')
        cart_id = request.form.get('cartId') or request.form.get('cart_id')
        status = request.form.get('respStatus') or request.form.get('payment_result', {}).get('response_status') if isinstance(request.form.get('payment_result'), dict) else request.form.get('respStatus')
        message = request.form.get('respMessage') or request.form.get('payment_result', {}).get('response_message') if isinstance(request.form.get('payment_result'), dict) else request.form.get('respMessage')
    else:
        tran_ref = request.args.get('tranRef') or request.args.get('tran_ref')
        cart_id = request.args.get('cartId') or request.args.get('cart_id')
        status = request.args.get('respStatus')
        message = request.args.get('respMessage')

    return render_template(
        'payment/complete.html',
        tran_ref=tran_ref,
        cart_id=cart_id,
        status=status,
        message=message
    )


# ==================== Admin Pages (at /panel) ====================

@frontend_bp.route('/panel/login')
def admin_login():
    """Admin login page"""
    return render_template('admin/login.html')


@frontend_bp.route('/panel')
def admin_dashboard():
    """Admin dashboard"""
    return render_template('admin/dashboard.html', active_page='dashboard')


@frontend_bp.route('/panel/customers')
def admin_customers():
    """Admin customers management page"""
    return render_template('admin/customers.html', active_page='customers')


@frontend_bp.route('/panel/merchants')
def admin_merchants():
    """Admin merchants management page"""
    return render_template('admin/merchants.html', active_page='merchants')


@frontend_bp.route('/panel/transactions')
def admin_transactions():
    """Admin transactions monitoring page"""
    return render_template('admin/transactions.html', active_page='transactions')


@frontend_bp.route('/panel/payments')
def admin_payments():
    """Admin payments management page"""
    return render_template('admin/payments.html', active_page='payments')


@frontend_bp.route('/panel/settlements')
def admin_settlements():
    """Admin settlements management page"""
    return render_template('admin/settlements.html', active_page='settlements')


@frontend_bp.route('/panel/reports')
def admin_reports():
    """Admin reports and analytics page"""
    return render_template('admin/reports.html', active_page='reports')


@frontend_bp.route('/panel/staff')
def admin_staff():
    """Admin staff management page"""
    return render_template('admin/staff.html', active_page='staff')


@frontend_bp.route('/panel/audit-logs')
def admin_audit_logs():
    """Admin audit logs page"""
    return render_template('admin/audit-logs.html', active_page='audit-logs')


@frontend_bp.route('/panel/settings')
def admin_settings():
    """Admin system settings page"""
    return render_template('admin/settings.html', active_page='settings')
