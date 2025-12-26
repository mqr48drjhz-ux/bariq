"""
Seed Data Script - Initialize database with sample data
"""
from datetime import datetime, timedelta
from app.extensions import db
from app.models.admin_user import AdminUser
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.region import Region
from app.models.branch import Branch
from app.models.merchant_user import MerchantUser
from app.models.system_setting import SystemSetting


def seed_admin_users():
    """Create default admin users"""
    print("Seeding admin users...")

    # Check if admin already exists
    if AdminUser.query.filter_by(email='admin@bariq.sa').first():
        print("  Admin user already exists, skipping...")
        return

    admin = AdminUser(
        email='admin@bariq.sa',
        full_name='System Administrator',
        phone='0500000000',
        role='super_admin',
        department='IT',
        permissions=['all'],
        is_active=True
    )
    admin.set_password('Admin@123')

    db.session.add(admin)
    db.session.commit()
    print("  Created admin user: admin@bariq.sa / Admin@123")


def seed_system_settings():
    """Create default system settings"""
    print("Seeding system settings...")

    settings = [
        {
            'key': 'default_credit_limit',
            'value': {'amount': 500, 'currency': 'SAR'},
            'description': 'Default credit limit for new customers',
            'editable_by': 'super_admin'
        },
        {
            'key': 'max_credit_limit',
            'value': {'amount': 5000, 'currency': 'SAR'},
            'description': 'Maximum allowed credit limit',
            'editable_by': 'super_admin'
        },
        {
            'key': 'repayment_days',
            'value': {'days': 10},
            'description': 'Number of days to repay',
            'editable_by': 'super_admin'
        },
        {
            'key': 'default_commission_rate',
            'value': {'rate': 2.5},
            'description': 'Default merchant commission rate (%)',
            'editable_by': 'super_admin'
        },
        {
            'key': 'min_transaction_amount',
            'value': {'amount': 10, 'currency': 'SAR'},
            'description': 'Minimum transaction amount',
            'editable_by': 'super_admin'
        },
        {
            'key': 'max_transaction_amount',
            'value': {'amount': 2000, 'currency': 'SAR'},
            'description': 'Maximum transaction amount',
            'editable_by': 'super_admin'
        },
        {
            'key': 'payment_reminder_days',
            'value': {'days': [3, 1, 0]},
            'description': 'Days before due date to send reminders',
            'editable_by': 'admin'
        }
    ]

    for setting_data in settings:
        if not SystemSetting.query.filter_by(key=setting_data['key']).first():
            setting = SystemSetting(**setting_data)
            db.session.add(setting)

    db.session.commit()
    print(f"  Created {len(settings)} system settings")


def seed_sample_customer():
    """Create a sample customer for testing"""
    print("Seeding sample customer...")

    existing = Customer.query.filter_by(national_id='1234567890').first()
    if existing:
        # Update existing customer with new fields
        existing.bariq_id = '123456'
        existing.username = 'ahmed_ali'
        existing.set_password('Customer@123')
        existing.credit_limit = 2500
        existing.available_credit = 2500
        existing.used_credit = 0
        existing.status = 'active'
        existing.verified_at = datetime.utcnow()
        db.session.commit()
        print("  Updated sample customer: 1234567890")
        print("    Bariq ID: 123456")
        print("    Username: ahmed_ali / Customer@123")
        return

    customer = Customer(
        national_id='1234567890',
        nafath_id='NAFATH123456',
        bariq_id='123456',  # Unique Bariq ID for merchant lookup
        username='ahmed_ali',  # Username for login
        full_name_ar='أحمد محمد العلي',
        full_name_en='Ahmed Mohammed Al-Ali',
        email='ahmed@test.com',
        phone='0551234567',
        date_of_birth=datetime(1990, 5, 15).date(),
        gender='male',
        city='Riyadh',
        district='Al Olaya',
        address_line='Building 123, Street 456',
        status='active',
        credit_limit=2500,  # 2500 SAR credit limit
        available_credit=2500,
        used_credit=0,
        language='ar',
        notifications_enabled=True,
        verified_at=datetime.utcnow()
    )
    customer.set_password('Customer@123')

    db.session.add(customer)
    db.session.commit()
    print("  Created sample customer:")
    print("    National ID: 1234567890")
    print("    Bariq ID: 123456")
    print("    Username: ahmed_ali / Customer@123")
    print("    Credit: 2,500 SAR")


def seed_sample_merchant():
    """Create a sample merchant with branches and full staff hierarchy for testing"""
    print("Seeding sample merchant...")

    if Merchant.query.filter_by(commercial_registration='1234567890').first():
        print("  Sample merchant already exists, skipping...")
        return

    # Create merchant
    merchant = Merchant(
        name_ar='سوبرماركت البركة',
        name_en='Al Baraka Supermarket',
        commercial_registration='1234567890',
        tax_number='300012345678901',
        business_type='supermarket',
        email='merchant@test.com',
        phone='0112345678',
        website='https://albaraka.sa',
        city='Riyadh',
        district='Al Malaz',
        address_line='King Fahd Road, Building 100',
        bank_name='Al Rajhi Bank',
        iban='SA0380000000608010167519',
        account_holder_name='Al Baraka Trading Est.',
        commission_rate=2.50,
        status='active',
        plan_type='basic',
        approved_at=datetime.utcnow()
    )

    db.session.add(merchant)
    db.session.flush()

    # Create regions
    region_riyadh = Region(
        merchant_id=merchant.id,
        name_ar='منطقة الرياض',
        name_en='Riyadh Region',
        city='Riyadh',
        area_description='المنطقة الوسطى - الرياض وضواحيها',
        is_active=True
    )
    db.session.add(region_riyadh)

    region_jeddah = Region(
        merchant_id=merchant.id,
        name_ar='منطقة جدة',
        name_en='Jeddah Region',
        city='Jeddah',
        area_description='المنطقة الغربية - جدة ومكة المكرمة',
        is_active=True
    )
    db.session.add(region_jeddah)

    db.session.flush()

    # Create branches for Riyadh region
    branch_olaya = Branch(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        name_ar='فرع العليا',
        name_en='Olaya Branch',
        code='RYD001',
        city='Riyadh',
        district='Al Olaya',
        address_line='Olaya Street, Building 50',
        phone='0112345001',
        latitude=24.7136,
        longitude=46.6753,
        settlement_cycle='weekly',
        is_active=True
    )
    db.session.add(branch_olaya)

    branch_malaz = Branch(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        name_ar='فرع الملز',
        name_en='Malaz Branch',
        code='RYD002',
        city='Riyadh',
        district='Al Malaz',
        address_line='King Fahd Road, Building 75',
        phone='0112345002',
        latitude=24.6748,
        longitude=46.7148,
        settlement_cycle='weekly',
        is_active=True
    )
    db.session.add(branch_malaz)

    # Create branches for Jeddah region
    branch_tahlia = Branch(
        merchant_id=merchant.id,
        region_id=region_jeddah.id,
        name_ar='فرع التحلية',
        name_en='Tahlia Branch',
        code='JED001',
        city='Jeddah',
        district='Al Tahlia',
        address_line='Tahlia Street, Building 20',
        phone='0122345001',
        latitude=21.5433,
        longitude=39.1728,
        settlement_cycle='weekly',
        is_active=True
    )
    db.session.add(branch_tahlia)

    db.session.flush()

    # ==================== Create Staff Hierarchy ====================

    # 1. Owner
    owner = MerchantUser(
        merchant_id=merchant.id,
        email='owner@albaraka.sa',
        full_name='محمد البركة',
        phone='0551234567',
        role='owner',
        permissions=['all'],
        is_active=True
    )
    owner.set_password('Owner@123')
    db.session.add(owner)

    # 2. Executive Manager
    exec_manager = MerchantUser(
        merchant_id=merchant.id,
        email='exec@albaraka.sa',
        full_name='عبدالله السعيد',
        phone='0551234568',
        role='executive_manager',
        permissions=['all'],
        is_active=True
    )
    exec_manager.set_password('Exec@123')
    db.session.add(exec_manager)

    # 3. Region Managers
    region_mgr_riyadh = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        email='region.riyadh@albaraka.sa',
        full_name='سعد الرياض',
        phone='0551234569',
        role='region_manager',
        permissions=['manage_branches', 'manage_staff', 'view_reports'],
        is_active=True
    )
    region_mgr_riyadh.set_password('Region@123')
    db.session.add(region_mgr_riyadh)

    region_mgr_jeddah = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_jeddah.id,
        email='region.jeddah@albaraka.sa',
        full_name='خالد جدة',
        phone='0551234570',
        role='region_manager',
        permissions=['manage_branches', 'manage_staff', 'view_reports'],
        is_active=True
    )
    region_mgr_jeddah.set_password('Region@123')
    db.session.add(region_mgr_jeddah)

    # 4. Branch Managers
    branch_mgr_olaya = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        branch_id=branch_olaya.id,
        email='branch.olaya@albaraka.sa',
        full_name='فهد العليا',
        phone='0551234571',
        role='branch_manager',
        permissions=['manage_staff', 'create_transaction', 'view_reports'],
        is_active=True
    )
    branch_mgr_olaya.set_password('Branch@123')
    db.session.add(branch_mgr_olaya)

    branch_mgr_malaz = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        branch_id=branch_malaz.id,
        email='branch.malaz@albaraka.sa',
        full_name='ماجد الملز',
        phone='0551234572',
        role='branch_manager',
        permissions=['manage_staff', 'create_transaction', 'view_reports'],
        is_active=True
    )
    branch_mgr_malaz.set_password('Branch@123')
    db.session.add(branch_mgr_malaz)

    branch_mgr_tahlia = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_jeddah.id,
        branch_id=branch_tahlia.id,
        email='branch.tahlia@albaraka.sa',
        full_name='عمر التحلية',
        phone='0551234573',
        role='branch_manager',
        permissions=['manage_staff', 'create_transaction', 'view_reports'],
        is_active=True
    )
    branch_mgr_tahlia.set_password('Branch@123')
    db.session.add(branch_mgr_tahlia)

    # 5. Cashiers
    cashier_olaya1 = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        branch_id=branch_olaya.id,
        email='cashier@albaraka.sa',
        full_name='علي حسن',
        phone='0559876543',
        role='cashier',
        permissions=['create_transaction', 'view_transactions'],
        is_active=True
    )
    cashier_olaya1.set_password('Cashier@123')
    db.session.add(cashier_olaya1)

    cashier_olaya2 = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        branch_id=branch_olaya.id,
        email='cashier2@albaraka.sa',
        full_name='أحمد محمود',
        phone='0559876544',
        role='cashier',
        permissions=['create_transaction', 'view_transactions'],
        is_active=True
    )
    cashier_olaya2.set_password('Cashier@123')
    db.session.add(cashier_olaya2)

    cashier_malaz = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_riyadh.id,
        branch_id=branch_malaz.id,
        email='cashier.malaz@albaraka.sa',
        full_name='يوسف سالم',
        phone='0559876545',
        role='cashier',
        permissions=['create_transaction', 'view_transactions'],
        is_active=True
    )
    cashier_malaz.set_password('Cashier@123')
    db.session.add(cashier_malaz)

    cashier_tahlia = MerchantUser(
        merchant_id=merchant.id,
        region_id=region_jeddah.id,
        branch_id=branch_tahlia.id,
        email='cashier.tahlia@albaraka.sa',
        full_name='زياد عمر',
        phone='0559876546',
        role='cashier',
        permissions=['create_transaction', 'view_transactions'],
        is_active=True
    )
    cashier_tahlia.set_password('Cashier@123')
    db.session.add(cashier_tahlia)

    db.session.commit()

    print("  Created sample merchant: Al Baraka Supermarket")
    print("  Regions: 2 (Riyadh, Jeddah)")
    print("  Branches: 3 (Olaya, Malaz, Tahlia)")
    print("\n  Staff Hierarchy:")
    print("    Owner: owner@albaraka.sa / Owner@123")
    print("    Executive Manager: exec@albaraka.sa / Exec@123")
    print("    Region Manager (Riyadh): region.riyadh@albaraka.sa / Region@123")
    print("    Region Manager (Jeddah): region.jeddah@albaraka.sa / Region@123")
    print("    Branch Manager (Olaya): branch.olaya@albaraka.sa / Branch@123")
    print("    Branch Manager (Malaz): branch.malaz@albaraka.sa / Branch@123")
    print("    Branch Manager (Tahlia): branch.tahlia@albaraka.sa / Branch@123")
    print("    Cashier: cashier@albaraka.sa / Cashier@123")


def seed_all():
    """Run all seed functions"""
    print("\n" + "=" * 50)
    print("Starting database seeding...")
    print("=" * 50 + "\n")

    seed_admin_users()
    seed_system_settings()
    seed_sample_customer()
    seed_sample_merchant()

    print("\n" + "=" * 60)
    print("Database seeding completed!")
    print("=" * 60)
    print("\nTest Accounts:")
    print("-" * 60)
    print("Admin:              admin@bariq.sa / Admin@123")
    print("Customer:           ahmed_ali / Customer@123 (Bariq ID: 123456)")
    print("-" * 60)
    print("\nMerchant Staff Hierarchy:")
    print("-" * 60)
    print("Owner:              owner@albaraka.sa / Owner@123")
    print("Executive Manager:  exec@albaraka.sa / Exec@123")
    print("Region Mgr Riyadh:  region.riyadh@albaraka.sa / Region@123")
    print("Region Mgr Jeddah:  region.jeddah@albaraka.sa / Region@123")
    print("Branch Mgr Olaya:   branch.olaya@albaraka.sa / Branch@123")
    print("Branch Mgr Malaz:   branch.malaz@albaraka.sa / Branch@123")
    print("Branch Mgr Tahlia:  branch.tahlia@albaraka.sa / Branch@123")
    print("Cashier (Olaya):    cashier@albaraka.sa / Cashier@123")
    print("-" * 60 + "\n")


if __name__ == '__main__':
    from app import create_app
    app = create_app()
    with app.app_context():
        seed_all()
