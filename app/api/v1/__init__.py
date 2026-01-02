"""
API v1 Blueprint
"""
from flask import Blueprint, jsonify

api_v1_bp = Blueprint('api_v1', __name__)


# Health check endpoint
@api_v1_bp.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'success': True,
        'message': 'Bariq Al-Yusr API is running',
        'version': '1.0.0'
    })


# Import and register route modules
from app.api.v1.auth import auth_bp
from app.api.v1.customers import customers_bp
from app.api.v1.merchants import merchants_bp
from app.api.v1.admin import admin_bp
from app.api.v1.public import public_bp
from app.api.v1.webhooks import webhooks_bp

api_v1_bp.register_blueprint(auth_bp, url_prefix='/auth')
api_v1_bp.register_blueprint(customers_bp, url_prefix='/customers')
api_v1_bp.register_blueprint(merchants_bp, url_prefix='/merchants')
api_v1_bp.register_blueprint(admin_bp, url_prefix='/admin')
api_v1_bp.register_blueprint(public_bp, url_prefix='/public')
api_v1_bp.register_blueprint(webhooks_bp, url_prefix='/webhooks')
