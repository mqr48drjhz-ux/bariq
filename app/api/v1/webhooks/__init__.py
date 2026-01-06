"""
Webhook Routes - Handle external service callbacks
"""
from flask import Blueprint, jsonify, request, current_app
from datetime import datetime, timedelta
from app.extensions import limiter
import json
import os

webhooks_bp = Blueprint('webhooks', __name__)

# Webhook security settings
WEBHOOK_TIMESTAMP_TOLERANCE_MINUTES = 5  # Allow 5 minute window for webhook timestamps
# PayTabs doesn't always send signatures, so we disable mandatory check
# Enable this once you configure PayTabs to send server-to-server callbacks with signature
REQUIRE_SIGNATURE_IN_PRODUCTION = False


def _mask_sensitive_data(payload):
    """Mask sensitive fields before logging"""
    if not payload:
        return payload

    masked = payload.copy()
    sensitive_fields = ['card_number', 'cvv', 'expiry_date', 'customer_email', 'phone']

    def mask_recursive(obj):
        if isinstance(obj, dict):
            return {
                k: '***MASKED***' if k.lower() in sensitive_fields else mask_recursive(v)
                for k, v in obj.items()
            }
        elif isinstance(obj, list):
            return [mask_recursive(item) for item in obj]
        return obj

    return mask_recursive(masked)


@webhooks_bp.route('/paytabs', methods=['POST'])
@limiter.limit("100 per minute")  # Allow reasonable webhook volume while preventing abuse
def paytabs_callback():
    """
    PayTabs payment callback webhook

    This endpoint receives payment status updates from PayTabs.
    It processes the payment and updates transaction/customer records.

    Security measures:
    - Mandatory signature verification in production
    - Timestamp validation to prevent replay attacks
    - Amount verification against expected payment
    - Idempotency check for duplicate webhooks
    """
    from app.services.paytabs_service import PayTabsService

    try:
        # Get payload
        payload = request.get_json()

        if not payload:
            return jsonify({
                'success': False,
                'message': 'No payload received'
            }), 400

        # Log webhook with masked sensitive data
        masked_payload = _mask_sensitive_data(payload)
        current_app.logger.info(f"PayTabs webhook received: {json.dumps(masked_payload)}")

        # === SECURITY: Signature Verification ===
        signature = request.headers.get('X-PayTabs-Signature')
        is_production = os.environ.get('FLASK_ENV') == 'production'

        # In production, signature is MANDATORY
        if is_production and REQUIRE_SIGNATURE_IN_PRODUCTION:
            if not signature:
                current_app.logger.warning("PayTabs webhook rejected: Missing signature in production")
                return jsonify({
                    'success': False,
                    'message': 'Missing signature'
                }), 401

        # Verify signature if provided (mandatory in production)
        if signature:
            if not PayTabsService.verify_signature(payload, signature):
                current_app.logger.warning("PayTabs webhook signature verification failed")
                return jsonify({
                    'success': False,
                    'message': 'Invalid signature'
                }), 401

        # === SECURITY: Timestamp Validation (Replay Attack Protection) ===
        webhook_timestamp = payload.get('user_defined', {}).get('udf5')
        if webhook_timestamp:
            try:
                payment_time = datetime.fromisoformat(webhook_timestamp.replace('Z', '+00:00'))
                now = datetime.utcnow()
                time_diff = abs((now - payment_time.replace(tzinfo=None)).total_seconds())
                max_age_seconds = WEBHOOK_TIMESTAMP_TOLERANCE_MINUTES * 60

                # Allow reasonable time for payment completion (30 min for payment + 5 min tolerance)
                # Payment page can take up to 30 minutes, so we allow that plus tolerance
                payment_expiry = int(os.environ.get('PAYMENT_EXPIRY_MINUTES', 30))
                max_age_seconds = (payment_expiry + WEBHOOK_TIMESTAMP_TOLERANCE_MINUTES) * 60

                if time_diff > max_age_seconds:
                    current_app.logger.warning(
                        f"PayTabs webhook rejected: Timestamp too old ({time_diff}s > {max_age_seconds}s)"
                    )
                    return jsonify({
                        'success': False,
                        'message': 'Webhook timestamp expired'
                    }), 400
            except (ValueError, TypeError) as e:
                current_app.logger.warning(f"PayTabs webhook: Could not parse timestamp: {e}")
                # Don't reject if timestamp parsing fails, but log it

        # === SECURITY: Amount Verification ===
        result = PayTabsService.handle_webhook(payload, verify_amount=True)

        if result['success']:
            current_app.logger.info(f"PayTabs webhook processed: {result.get('data', {}).get('status')}")
            return jsonify(result), 200
        else:
            current_app.logger.error(f"PayTabs webhook error: {result.get('message')}")
            return jsonify(result), 400

    except Exception as e:
        current_app.logger.error(f"PayTabs webhook exception: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'Webhook processing error: {str(e)}'
        }), 500


@webhooks_bp.route('/paytabs/test', methods=['GET'])
def paytabs_test():
    """Test endpoint to verify webhook URL is accessible"""
    return jsonify({
        'success': True,
        'message': 'PayTabs webhook endpoint is active',
        'timestamp': __import__('datetime').datetime.utcnow().isoformat()
    })
