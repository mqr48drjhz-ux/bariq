"""
Public Routes (No authentication required)
"""
from flask import Blueprint, jsonify
import random
import string
from datetime import datetime

public_bp = Blueprint('public', __name__)


@public_bp.route('/cities', methods=['GET'])
def get_cities():
    """Get list of Saudi cities"""
    cities = [
        {'key': 'riyadh', 'name_ar': 'الرياض', 'name_en': 'Riyadh'},
        {'key': 'jeddah', 'name_ar': 'جدة', 'name_en': 'Jeddah'},
        {'key': 'makkah', 'name_ar': 'مكة المكرمة', 'name_en': 'Makkah'},
        {'key': 'madinah', 'name_ar': 'المدينة المنورة', 'name_en': 'Madinah'},
        {'key': 'dammam', 'name_ar': 'الدمام', 'name_en': 'Dammam'},
        {'key': 'khobar', 'name_ar': 'الخبر', 'name_en': 'Khobar'},
        {'key': 'dhahran', 'name_ar': 'الظهران', 'name_en': 'Dhahran'},
        {'key': 'taif', 'name_ar': 'الطائف', 'name_en': 'Taif'},
        {'key': 'tabuk', 'name_ar': 'تبوك', 'name_en': 'Tabuk'},
        {'key': 'buraidah', 'name_ar': 'بريدة', 'name_en': 'Buraidah'},
        {'key': 'khamis_mushait', 'name_ar': 'خميس مشيط', 'name_en': 'Khamis Mushait'},
        {'key': 'abha', 'name_ar': 'أبها', 'name_en': 'Abha'},
        {'key': 'najran', 'name_ar': 'نجران', 'name_en': 'Najran'},
        {'key': 'hail', 'name_ar': 'حائل', 'name_en': 'Hail'},
        {'key': 'jazan', 'name_ar': 'جازان', 'name_en': 'Jazan'},
        {'key': 'yanbu', 'name_ar': 'ينبع', 'name_en': 'Yanbu'},
        {'key': 'al_ahsa', 'name_ar': 'الأحساء', 'name_en': 'Al Ahsa'},
        {'key': 'qatif', 'name_ar': 'القطيف', 'name_en': 'Qatif'},
        {'key': 'jubail', 'name_ar': 'الجبيل', 'name_en': 'Jubail'},
    ]

    return jsonify({
        'success': True,
        'data': {
            'cities': cities
        }
    })


@public_bp.route('/business-types', methods=['GET'])
def get_business_types():
    """Get merchant business types"""
    types = [
        {'key': 'supermarket', 'name_ar': 'سوبرماركت', 'name_en': 'Supermarket'},
        {'key': 'hypermarket', 'name_ar': 'هايبرماركت', 'name_en': 'Hypermarket'},
        {'key': 'grocery', 'name_ar': 'بقالة', 'name_en': 'Grocery'},
        {'key': 'pharmacy', 'name_ar': 'صيدلية', 'name_en': 'Pharmacy'},
        {'key': 'bakery', 'name_ar': 'مخبز', 'name_en': 'Bakery'},
        {'key': 'butcher', 'name_ar': 'ملحمة', 'name_en': 'Butcher'},
        {'key': 'vegetables', 'name_ar': 'خضار وفواكه', 'name_en': 'Vegetables & Fruits'},
        {'key': 'dairy', 'name_ar': 'ألبان', 'name_en': 'Dairy'},
        {'key': 'general_store', 'name_ar': 'متجر عام', 'name_en': 'General Store'},
    ]

    return jsonify({
        'success': True,
        'data': {
            'types': types
        }
    })


@public_bp.route('/return-reasons', methods=['GET'])
def get_return_reasons():
    """Get valid return reasons"""
    reasons = [
        {'key': 'damaged', 'name_ar': 'المنتج تالف', 'name_en': 'Damaged'},
        {'key': 'wrong_item', 'name_ar': 'منتج خاطئ', 'name_en': 'Wrong Item'},
        {'key': 'defective', 'name_ar': 'منتج معيب', 'name_en': 'Defective'},
        {'key': 'customer_changed_mind', 'name_ar': 'تغير رأي العميل', 'name_en': 'Customer Changed Mind'},
        {'key': 'expired', 'name_ar': 'منتج منتهي الصلاحية', 'name_en': 'Expired'},
        {'key': 'other', 'name_ar': 'سبب آخر', 'name_en': 'Other'},
    ]

    return jsonify({
        'success': True,
        'data': {
            'reasons': reasons
        }
    })


@public_bp.route('/ticket-categories', methods=['GET'])
def get_ticket_categories():
    """Get support ticket categories"""
    categories = [
        {'key': 'payment_issue', 'name_ar': 'مشكلة في الدفع', 'name_en': 'Payment Issue'},
        {'key': 'transaction_issue', 'name_ar': 'مشكلة في العملية', 'name_en': 'Transaction Issue'},
        {'key': 'account_issue', 'name_ar': 'مشكلة في الحساب', 'name_en': 'Account Issue'},
        {'key': 'technical', 'name_ar': 'مشكلة تقنية', 'name_en': 'Technical Issue'},
        {'key': 'complaint', 'name_ar': 'شكوى', 'name_en': 'Complaint'},
        {'key': 'inquiry', 'name_ar': 'استفسار', 'name_en': 'Inquiry'},
        {'key': 'suggestion', 'name_ar': 'اقتراح', 'name_en': 'Suggestion'},
        {'key': 'other', 'name_ar': 'أخرى', 'name_en': 'Other'},
    ]

    return jsonify({
        'success': True,
        'data': {
            'categories': categories
        }
    })


@public_bp.route('/add_customer/<username>/<password>', methods=['GET', 'POST'])
def add_customer(username, password):
    """Create a new customer with the given username and password"""
    from app.extensions import db
    from app.models import Customer

    # Check if username already exists
    existing = Customer.query.filter_by(username=username).first()
    if existing:
        return jsonify({
            'success': False,
            'message': 'Username already exists',
            'data': existing.to_dict(include_sensitive=True)
        }), 400

    # Generate unique national_id and phone
    national_id = ''.join(random.choices(string.digits, k=10))
    while Customer.query.filter_by(national_id=national_id).first():
        national_id = ''.join(random.choices(string.digits, k=10))

    phone = '05' + ''.join(random.choices(string.digits, k=8))
    while Customer.query.filter_by(phone=phone).first():
        phone = '05' + ''.join(random.choices(string.digits, k=8))

    # Generate bariq_id
    bariq_id = Customer.generate_bariq_id()
    while Customer.query.filter_by(bariq_id=bariq_id).first():
        bariq_id = Customer.generate_bariq_id()

    # Create customer
    customer = Customer(
        username=username,
        national_id=national_id,
        bariq_id=bariq_id,
        full_name_ar=f'مستخدم {username}',
        full_name_en=f'User {username}',
        phone=phone,
        email=f'{username}@test.com',
        city='riyadh',
        status='active',
        credit_limit=500,
        available_credit=500,
        used_credit=0,
        verified_at=datetime.utcnow()
    )
    customer.set_password(password)

    db.session.add(customer)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Customer created successfully',
        'data': {
            **customer.to_dict(include_sensitive=True),
            'password': password  # Return password for reference
        }
    })


@public_bp.route('/add_merchant/<username>/<password>', methods=['GET', 'POST'])
def add_merchant(username, password):
    """Create a new merchant user with the given username (as email) and password"""
    from app.extensions import db
    from app.models import MerchantUser, Merchant

    email = f'{username}@merchant.com'

    # Check if email already exists
    existing = MerchantUser.query.filter_by(email=email).first()
    if existing:
        return jsonify({
            'success': False,
            'message': 'Email already exists',
            'data': existing.to_dict()
        }), 400

    # Get the first merchant to attach the user to
    merchant = Merchant.query.first()
    if not merchant:
        return jsonify({
            'success': False,
            'message': 'No merchant found. Please create a merchant first.'
        }), 400

    # Create merchant user
    merchant_user = MerchantUser(
        merchant_id=merchant.id,
        email=email,
        full_name=f'Merchant User {username}',
        phone='05' + ''.join(random.choices(string.digits, k=8)),
        role='cashier',
        is_active=True
    )
    merchant_user.set_password(password)

    db.session.add(merchant_user)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Merchant user created successfully',
        'data': {
            **merchant_user.to_dict(),
            'password': password,  # Return password for reference
            'merchant_name': merchant.name_en or merchant.name_ar
        }
    })
