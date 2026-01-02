"""
PayTabs Payment Gateway Service
Handles all payment gateway operations with PayTabs
"""
import requests
import hashlib
import hmac
import json
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.notification import Notification


class PayTabsService:
    """PayTabs payment gateway integration service"""

    # Payment status mapping from PayTabs to internal status
    STATUS_MAPPING = {
        'A': 'completed',      # Authorized/Approved
        'H': 'pending',        # Hold
        'P': 'pending',        # Pending
        'V': 'voided',         # Voided
        'E': 'failed',         # Error
        'D': 'declined',       # Declined
    }

    # ==================== Configuration ====================

    @staticmethod
    def get_config():
        """Get PayTabs configuration"""
        config = current_app.config
        return {
            'profile_id': config.get('PAYTABS_PROFILE_ID'),
            'server_key': config.get('PAYTABS_SERVER_KEY'),
            'client_key': config.get('PAYTABS_CLIENT_KEY'),
            'currency': config.get('PAYTABS_CURRENCY', 'SAR'),
            'region': config.get('PAYTABS_REGION', 'egypt'),
            'sandbox': config.get('PAYTABS_SANDBOX', True),
            'return_url': config.get('PAYMENT_RETURN_URL'),
            'callback_url': config.get('PAYMENT_CALLBACK_URL'),
            'expiry_minutes': config.get('PAYMENT_EXPIRY_MINUTES', 30),
            'min_amount': config.get('MIN_PAYMENT_AMOUNT', 10),
        }

    @staticmethod
    def get_base_url():
        """Get PayTabs API base URL based on region"""
        config = PayTabsService.get_config()
        region = config['region'].lower()

        region_urls = {
            'egypt': 'https://secure-egypt.paytabs.com',
            'saudi': 'https://secure.paytabs.sa',
            'uae': 'https://secure.paytabs.com',
            'global': 'https://secure-global.paytabs.com'
        }
        return region_urls.get(region, region_urls['egypt'])

    @staticmethod
    def get_headers():
        """Get API request headers"""
        config = PayTabsService.get_config()
        return {
            'Authorization': config['server_key'],
            'Content-Type': 'application/json'
        }

    # ==================== Create Payment Page ====================

    @staticmethod
    def create_payment_page(
        customer_id,
        transaction_ids,
        amount,
        payment_methods='all',
        description=None
    ):
        """
        Create a PayTabs hosted payment page

        Args:
            customer_id: Customer ID
            transaction_ids: List of transaction IDs to pay for
            amount: Payment amount in SAR
            payment_methods: 'all', 'creditcard', 'mada', 'stcpay', 'applepay', etc.
            description: Optional payment description

        Returns:
            dict with payment page URL and reference
        """
        config = PayTabsService.get_config()

        # Validate amount
        if amount < config['min_amount']:
            return {
                'success': False,
                'message': f"Minimum payment amount is {config['min_amount']} SAR",
                'error_code': 'PAY_001'
            }

        # Get customer
        customer = Customer.query.get(customer_id)
        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Validate transactions
        transactions = Transaction.query.filter(
            Transaction.id.in_(transaction_ids),
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'overdue'])
        ).all()

        if not transactions:
            return {
                'success': False,
                'message': 'No valid transactions found',
                'error_code': 'TXN_001'
            }

        # Calculate total remaining
        total_remaining = sum(t.remaining_amount for t in transactions)
        if amount > total_remaining:
            return {
                'success': False,
                'message': f'Amount exceeds total remaining balance of {total_remaining} SAR',
                'error_code': 'PAY_002'
            }

        # Generate unique cart ID
        cart_id = f"BARIQ-{customer.bariq_id}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # Build transaction IDs string for reference
        txn_refs = ','.join([str(t.id) for t in transactions])

        # Default description
        if not description:
            if len(transactions) == 1:
                description = f"Payment for transaction {transactions[0].reference_number}"
            else:
                description = f"Payment for {len(transactions)} transactions"

        # Build payment request
        payload = {
            'profile_id': config['profile_id'],
            'tran_type': 'sale',
            'tran_class': 'ecom',
            'cart_id': cart_id,
            'cart_description': description,
            'cart_currency': config['currency'],
            'cart_amount': float(amount),
            'callback': config['callback_url'],
            'return': config['return_url'],
            'customer_details': {
                'name': customer.full_name_en or customer.full_name_ar,
                'email': customer.email or f"{customer.bariq_id}@bariq.sa",
                'phone': customer.phone or '',
                'street1': customer.address_line or 'Saudi Arabia',
                'city': customer.city or 'Riyadh',
                'state': customer.city or 'Riyadh',
                'country': 'SA',
                'zip': '00000'
            },
            'hide_shipping': True,
            'user_defined': {
                'udf1': str(customer_id),          # Customer ID
                'udf2': txn_refs,                   # Transaction IDs
                'udf3': str(amount),                # Original amount
                'udf4': 'bariq_payment',            # Payment type identifier
                'udf5': datetime.utcnow().isoformat()  # Timestamp
            }
        }

        # Add payment methods filter if not 'all'
        if payment_methods and payment_methods != 'all':
            # PayTabs expects payment methods as string like "creditcard,mada"
            payload['payment_methods'] = payment_methods.split(',') if isinstance(payment_methods, str) else payment_methods

        try:
            # Make API request
            base_url = PayTabsService.get_base_url()
            response = requests.post(
                f"{base_url}/payment/request",
                headers=PayTabsService.get_headers(),
                json=payload,
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200 and 'redirect_url' in response_data:
                # Create pending payment record
                payment = Payment(
                    customer_id=customer_id,
                    transaction_id=transactions[0].id,  # Primary transaction
                    amount=amount,
                    payment_method='paytabs',
                    status='pending',
                    gateway_reference=response_data.get('tran_ref'),
                    gateway_response=json.dumps({
                        'cart_id': cart_id,
                        'transaction_ids': [t.id for t in transactions],
                        'redirect_url': response_data.get('redirect_url')
                    })
                )
                db.session.add(payment)
                db.session.commit()

                return {
                    'success': True,
                    'message': 'Payment page created successfully',
                    'data': {
                        'payment_id': payment.id,
                        'payment_url': response_data.get('redirect_url'),
                        'tran_ref': response_data.get('tran_ref'),
                        'cart_id': cart_id,
                        'amount': float(amount),
                        'currency': config['currency'],
                        'expires_in_minutes': config['expiry_minutes']
                    }
                }
            else:
                error_message = response_data.get('message', 'Failed to create payment page')
                return {
                    'success': False,
                    'message': error_message,
                    'error_code': 'PAY_003',
                    'gateway_response': response_data
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'message': 'Payment gateway timeout. Please try again.',
                'error_code': 'PAY_004'
            }
        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'message': f'Payment gateway error: {str(e)}',
                'error_code': 'PAY_005'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Webhook Handler ====================

    @staticmethod
    def handle_webhook(payload):
        """
        Handle PayTabs webhook callback

        Args:
            payload: Webhook payload from PayTabs

        Returns:
            dict with processing result
        """
        try:
            tran_ref = payload.get('tran_ref')
            tran_type = payload.get('tran_type')
            cart_id = payload.get('cart_id')
            cart_amount = float(payload.get('cart_amount', 0))
            cart_currency = payload.get('cart_currency')
            response_status = payload.get('payment_result', {}).get('response_status', '')
            response_code = payload.get('payment_result', {}).get('response_code', '')
            response_message = payload.get('payment_result', {}).get('response_message', '')
            payment_method = payload.get('payment_info', {}).get('payment_method', '')

            # Get user defined fields
            customer_id = payload.get('user_defined', {}).get('udf1')
            transaction_ids_str = payload.get('user_defined', {}).get('udf2', '')
            original_amount = payload.get('user_defined', {}).get('udf3')

            # Find the pending payment
            payment = Payment.query.filter_by(gateway_reference=tran_ref).first()

            if not payment:
                return {
                    'success': False,
                    'message': 'Payment record not found',
                    'error_code': 'PAY_006'
                }

            # Already processed
            if payment.status in ['completed', 'failed', 'declined']:
                return {
                    'success': True,
                    'message': 'Payment already processed',
                    'data': {'status': payment.status}
                }

            # Map status
            internal_status = PayTabsService.STATUS_MAPPING.get(response_status, 'failed')

            # Update payment record
            payment.status = internal_status
            payment.payment_method = payment_method or 'paytabs'
            payment.gateway_response = json.dumps(payload)
            payment.updated_at = datetime.utcnow()

            if internal_status == 'completed':
                payment.completed_at = datetime.utcnow()

                # Process the actual payment - update transactions
                result = PayTabsService._process_successful_payment(
                    payment=payment,
                    customer_id=int(customer_id) if customer_id else payment.customer_id,
                    transaction_ids_str=transaction_ids_str,
                    amount=cart_amount
                )

                if not result['success']:
                    # Rollback payment status if transaction update fails
                    payment.status = 'pending'
                    payment.gateway_response = json.dumps({
                        **payload,
                        'processing_error': result['message']
                    })
                    db.session.commit()
                    return result

            db.session.commit()

            return {
                'success': True,
                'message': f'Payment {internal_status}',
                'data': {
                    'payment_id': payment.id,
                    'status': internal_status,
                    'tran_ref': tran_ref,
                    'amount': cart_amount,
                    'response_code': response_code,
                    'response_message': response_message
                }
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Webhook processing error: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Process Successful Payment ====================

    @staticmethod
    def _process_successful_payment(payment, customer_id, transaction_ids_str, amount):
        """Process a successful payment - update transactions and credit"""
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return {
                    'success': False,
                    'message': 'Customer not found',
                    'error_code': 'CUST_001'
                }

            # Parse transaction IDs
            transaction_ids = [int(tid) for tid in transaction_ids_str.split(',') if tid]

            if not transaction_ids:
                transaction_ids = [payment.transaction_id]

            # Get transactions
            transactions = Transaction.query.filter(
                Transaction.id.in_(transaction_ids),
                Transaction.customer_id == customer_id
            ).order_by(Transaction.due_date.asc()).all()

            if not transactions:
                return {
                    'success': False,
                    'message': 'Transactions not found',
                    'error_code': 'TXN_001'
                }

            # Distribute payment across transactions
            remaining_payment = float(amount)
            payments_made = []

            for txn in transactions:
                if remaining_payment <= 0:
                    break

                if txn.status not in ['confirmed', 'overdue']:
                    continue

                txn_remaining = txn.remaining_amount
                payment_for_txn = min(remaining_payment, txn_remaining)

                # Update transaction
                txn.paid_amount = float(txn.paid_amount) + payment_for_txn
                txn.updated_at = datetime.utcnow()

                if txn.remaining_amount <= 0:
                    txn.status = 'paid'
                    txn.paid_at = datetime.utcnow()

                payments_made.append({
                    'transaction_id': txn.id,
                    'reference_number': txn.reference_number,
                    'amount': payment_for_txn,
                    'new_status': txn.status
                })

                remaining_payment -= payment_for_txn

            # Update customer credit
            total_paid = float(amount) - remaining_payment
            customer.available_credit = float(customer.available_credit) + total_paid
            customer.used_credit = float(customer.used_credit) - total_paid
            customer.updated_at = datetime.utcnow()

            # Send notification
            PayTabsService._notify_payment_success(customer, payment, payments_made)

            db.session.commit()

            return {
                'success': True,
                'message': 'Payment processed successfully',
                'data': {
                    'total_paid': total_paid,
                    'payments': payments_made,
                    'credit': {
                        'available_credit': float(customer.available_credit),
                        'used_credit': float(customer.used_credit)
                    }
                }
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'Payment processing error: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Query Payment Status ====================

    @staticmethod
    def query_payment_status(tran_ref):
        """Query payment status from PayTabs"""
        config = PayTabsService.get_config()

        payload = {
            'profile_id': config['profile_id'],
            'tran_ref': tran_ref
        }

        try:
            base_url = PayTabsService.get_base_url()
            response = requests.post(
                f"{base_url}/payment/query",
                headers=PayTabsService.get_headers(),
                json=payload,
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200:
                payment_status = response_data.get('payment_result', {}).get('response_status', '')
                internal_status = PayTabsService.STATUS_MAPPING.get(payment_status, 'unknown')

                return {
                    'success': True,
                    'data': {
                        'tran_ref': tran_ref,
                        'status': internal_status,
                        'gateway_status': payment_status,
                        'amount': response_data.get('cart_amount'),
                        'currency': response_data.get('cart_currency'),
                        'payment_method': response_data.get('payment_info', {}).get('payment_method'),
                        'response_message': response_data.get('payment_result', {}).get('response_message')
                    }
                }
            else:
                return {
                    'success': False,
                    'message': response_data.get('message', 'Failed to query payment'),
                    'error_code': 'PAY_007'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Query error: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Refund Payment ====================

    @staticmethod
    def refund_payment(tran_ref, amount, reason=None):
        """Refund a payment (partial or full)"""
        config = PayTabsService.get_config()

        # Find the original payment
        payment = Payment.query.filter_by(gateway_reference=tran_ref).first()

        if not payment:
            return {
                'success': False,
                'message': 'Original payment not found',
                'error_code': 'PAY_006'
            }

        if payment.status != 'completed':
            return {
                'success': False,
                'message': 'Can only refund completed payments',
                'error_code': 'PAY_008'
            }

        if amount > float(payment.amount):
            return {
                'success': False,
                'message': 'Refund amount exceeds original payment',
                'error_code': 'PAY_009'
            }

        payload = {
            'profile_id': config['profile_id'],
            'tran_type': 'refund',
            'tran_class': 'ecom',
            'cart_id': f"REFUND-{tran_ref}",
            'cart_currency': config['currency'],
            'cart_amount': float(amount),
            'cart_description': reason or 'Refund',
            'tran_ref': tran_ref
        }

        try:
            base_url = PayTabsService.get_base_url()
            response = requests.post(
                f"{base_url}/payment/request",
                headers=PayTabsService.get_headers(),
                json=payload,
                timeout=30
            )

            response_data = response.json()

            if response.status_code == 200:
                payment_result = response_data.get('payment_result', {})
                if payment_result.get('response_status') == 'A':
                    # Update original payment
                    payment.refunded_amount = float(payment.refunded_amount or 0) + amount
                    payment.updated_at = datetime.utcnow()

                    if payment.refunded_amount >= float(payment.amount):
                        payment.status = 'refunded'

                    db.session.commit()

                    return {
                        'success': True,
                        'message': 'Refund processed successfully',
                        'data': {
                            'refund_ref': response_data.get('tran_ref'),
                            'amount': amount,
                            'original_payment_id': payment.id
                        }
                    }
                else:
                    return {
                        'success': False,
                        'message': payment_result.get('response_message', 'Refund failed'),
                        'error_code': 'PAY_010'
                    }
            else:
                return {
                    'success': False,
                    'message': response_data.get('message', 'Refund request failed'),
                    'error_code': 'PAY_010'
                }

        except Exception as e:
            return {
                'success': False,
                'message': f'Refund error: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Verify Webhook Signature ====================

    @staticmethod
    def verify_signature(payload, signature):
        """Verify PayTabs webhook signature"""
        config = PayTabsService.get_config()
        server_key = config['server_key']

        # PayTabs uses HMAC-SHA256 for signature
        computed_signature = hmac.new(
            server_key.encode('utf-8'),
            json.dumps(payload, separators=(',', ':')).encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(computed_signature, signature)

    # ==================== Notifications ====================

    @staticmethod
    def _notify_payment_success(customer, payment, payments_made):
        """Send notification for successful payment"""
        try:
            total_amount = sum(p['amount'] for p in payments_made)
            txn_count = len(payments_made)

            if txn_count == 1:
                body_ar = f'تم استلام دفعة بمبلغ {total_amount} ريال للمعاملة رقم {payments_made[0]["reference_number"]}'
                body_en = f'Payment of {total_amount} SAR received for transaction {payments_made[0]["reference_number"]}'
            else:
                body_ar = f'تم استلام دفعة بمبلغ {total_amount} ريال لعدد {txn_count} معاملات'
                body_en = f'Payment of {total_amount} SAR received for {txn_count} transactions'

            notification = Notification(
                customer_id=customer.id,
                title_ar='تم استلام الدفعة بنجاح',
                title_en='Payment Received Successfully',
                body_ar=body_ar,
                body_en=body_en,
                type='payment',
                reference_id=payment.id
            )
            db.session.add(notification)
        except Exception:
            pass  # Don't fail the payment if notification fails

    # ==================== Get Payment Methods ====================

    @staticmethod
    def get_available_payment_methods():
        """Get list of available payment methods"""
        return {
            'success': True,
            'data': {
                'methods': [
                    {
                        'code': 'all',
                        'name_ar': 'جميع الطرق',
                        'name_en': 'All Methods',
                        'description_ar': 'عرض جميع طرق الدفع المتاحة',
                        'description_en': 'Show all available payment methods'
                    },
                    {
                        'code': 'creditcard',
                        'name_ar': 'بطاقة ائتمان',
                        'name_en': 'Credit Card',
                        'description_ar': 'فيزا أو ماستركارد',
                        'description_en': 'Visa or Mastercard'
                    },
                    {
                        'code': 'mada',
                        'name_ar': 'مدى',
                        'name_en': 'mada',
                        'description_ar': 'بطاقة مدى السعودية',
                        'description_en': 'Saudi mada debit card'
                    },
                    {
                        'code': 'stcpay',
                        'name_ar': 'STC Pay',
                        'name_en': 'STC Pay',
                        'description_ar': 'محفظة STC Pay',
                        'description_en': 'STC Pay wallet'
                    },
                    {
                        'code': 'applepay',
                        'name_ar': 'Apple Pay',
                        'name_en': 'Apple Pay',
                        'description_ar': 'الدفع عبر Apple Pay',
                        'description_en': 'Pay with Apple Pay'
                    }
                ]
            }
        }
