"""
Application Configuration
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/bariq'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'

    # Rate Limiting
    RATELIMIT_DEFAULT = "100 per minute"
    RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'memory://')

    # Business Rules
    DEFAULT_CREDIT_LIMIT = 500  # SAR
    MAX_CREDIT_LIMIT = 5000  # SAR
    REPAYMENT_DAYS = 10
    DEFAULT_COMMISSION_RATE = 2.5  # Percentage
    MIN_TRANSACTION_AMOUNT = 10  # SAR
    MAX_TRANSACTION_AMOUNT = 2000  # SAR

    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100

    # PayTabs Configuration
    PAYTABS_PROFILE_ID = os.environ.get('PAYTABS_PROFILE_ID', '')
    PAYTABS_SERVER_KEY = os.environ.get('PAYTABS_SERVER_KEY', '')
    PAYTABS_CLIENT_KEY = os.environ.get('PAYTABS_CLIENT_KEY', '')
    PAYTABS_CURRENCY = os.environ.get('PAYTABS_CURRENCY', 'SAR')
    PAYTABS_REGION = os.environ.get('PAYTABS_REGION', 'egypt')  # egypt, saudi, uae, etc.
    PAYTABS_SANDBOX = os.environ.get('PAYTABS_SANDBOX', 'true').lower() == 'true'

    # PayTabs URLs (auto-set based on region)
    @property
    def PAYTABS_BASE_URL(self):
        region = self.PAYTABS_REGION.lower()
        region_urls = {
            'egypt': 'https://secure-egypt.paytabs.com',
            'saudi': 'https://secure.paytabs.sa',
            'uae': 'https://secure.paytabs.com',
            'global': 'https://secure-global.paytabs.com'
        }
        return region_urls.get(region, region_urls['egypt'])

    # Payment Settings
    PAYMENT_RETURN_URL = os.environ.get('PAYMENT_RETURN_URL', 'http://localhost:5001/payment/complete')
    PAYMENT_CALLBACK_URL = os.environ.get('PAYMENT_CALLBACK_URL', 'http://localhost:5001/api/v1/webhooks/paytabs')
    PAYMENT_EXPIRY_MINUTES = int(os.environ.get('PAYMENT_EXPIRY_MINUTES', '30'))
    MIN_PAYMENT_AMOUNT = float(os.environ.get('MIN_PAYMENT_AMOUNT', '10'))

    # Firebase Configuration
    FIREBASE_CREDENTIALS_PATH = os.environ.get('FIREBASE_CREDENTIALS_PATH', '')
    FIREBASE_CREDENTIALS_JSON = os.environ.get('FIREBASE_CREDENTIALS_JSON', '')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL',
        'sqlite:///bariq_dev.db'
    )


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=5)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False

    # Override with stronger settings
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
