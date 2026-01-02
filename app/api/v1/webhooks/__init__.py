"""
Webhook Routes - Handle external service callbacks
"""
from flask import Blueprint, jsonify, request, current_app
import json

webhooks_bp = Blueprint('webhooks', __name__)


@webhooks_bp.route('/paytabs', methods=['POST'])
def paytabs_callback():
    """
    PayTabs payment callback webhook

    This endpoint receives payment status updates from PayTabs.
    It processes the payment and updates transaction/customer records.
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

        # Log webhook (for debugging)
        current_app.logger.info(f"PayTabs webhook received: {json.dumps(payload)}")

        # Optional: Verify signature if provided
        signature = request.headers.get('X-PayTabs-Signature')
        if signature:
            if not PayTabsService.verify_signature(payload, signature):
                current_app.logger.warning("PayTabs webhook signature verification failed")
                return jsonify({
                    'success': False,
                    'message': 'Invalid signature'
                }), 401

        # Process the webhook
        result = PayTabsService.handle_webhook(payload)

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
