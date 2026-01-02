"""
Database Models Package

Import all models here so they are registered with SQLAlchemy
"""
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.region import Region
from app.models.branch import Branch
from app.models.merchant_user import MerchantUser
from app.models.admin_user import AdminUser
from app.models.transaction import Transaction
from app.models.transaction_return import TransactionReturn
from app.models.payment import Payment
from app.models.settlement import Settlement
from app.models.credit_limit_request import CreditLimitRequest
from app.models.support_ticket import SupportTicket, SupportTicketMessage
from app.models.notification import Notification
from app.models.audit_log import AuditLog
from app.models.system_setting import SystemSetting
from app.models.promotion import Promotion
from app.models.customer_rating import CustomerRating
from app.models.device import CustomerDevice, MerchantUserDevice

__all__ = [
    'Customer',
    'Merchant',
    'Region',
    'Branch',
    'MerchantUser',
    'AdminUser',
    'Transaction',
    'TransactionReturn',
    'Payment',
    'Settlement',
    'CreditLimitRequest',
    'SupportTicket',
    'SupportTicketMessage',
    'Notification',
    'AuditLog',
    'SystemSetting',
    'Promotion',
    'CustomerRating',
    'CustomerDevice',
    'MerchantUserDevice',
]
