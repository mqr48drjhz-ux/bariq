"""
Payment Service - Full Implementation
"""
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.payment import Payment
from app.models.transaction import Transaction
from app.models.customer import Customer
from app.models.notification import Notification


class PaymentService:
    """Payment service for all payment-related operations"""

    # ==================== Customer Debt Overview ====================

    @staticmethod
    def get_customer_debt(customer_id):
        """Get customer's outstanding debt summary"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Get outstanding transactions (confirmed and overdue)
        outstanding_transactions = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'overdue'])
        ).order_by(Transaction.due_date.asc()).all()

        # Calculate totals
        total_debt = 0
        overdue_amount = 0
        transactions_data = []

        for txn in outstanding_transactions:
            remaining = txn.remaining_amount
            total_debt += remaining

            if txn.status == 'overdue':
                overdue_amount += remaining

            transactions_data.append({
                'id': txn.id,
                'reference_number': txn.reference_number,
                'merchant_name': txn.merchant.name_ar,
                'total_amount': float(txn.total_amount),
                'paid_amount': float(txn.paid_amount),
                'returned_amount': float(txn.returned_amount),
                'remaining_amount': remaining,
                'due_date': txn.due_date.isoformat() if txn.due_date else None,
                'status': txn.status,
                'is_overdue': txn.is_overdue
            })

        return {
            'success': True,
            'data': {
                'total_debt': total_debt,
                'overdue_amount': overdue_amount,
                'transaction_count': len(transactions_data),
                'transactions': transactions_data
            }
        }

    # ==================== Payment History ====================

    @staticmethod
    def get_customer_payments(customer_id, page=1, per_page=20):
        """Get customer's payment history"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        query = Payment.query.filter_by(customer_id=customer_id)
        query = query.order_by(Payment.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        payments_data = []
        for payment in pagination.items:
            payment_dict = payment.to_dict()
            payment_dict['transaction'] = {
                'id': payment.transaction.id,
                'reference_number': payment.transaction.reference_number,
                'merchant_name': payment.transaction.merchant.name_ar
            }
            payments_data.append(payment_dict)

        return {
            'success': True,
            'data': {
                'payments': payments_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    # ==================== Make Payment ====================

    @staticmethod
    def make_payment(customer_id, transaction_id, amount, payment_method='cash'):
        """Process a payment for a transaction"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        transaction = Transaction.query.filter_by(
            id=transaction_id,
            customer_id=customer_id
        ).first()

        if not transaction:
            return {
                'success': False,
                'message': 'Transaction not found',
                'error_code': 'TXN_001'
            }

        if transaction.status not in ['confirmed', 'overdue']:
            return {
                'success': False,
                'message': f'Cannot make payment for transaction with status: {transaction.status}',
                'error_code': 'TXN_002'
            }

        amount = float(amount)
        remaining = transaction.remaining_amount

        if amount <= 0:
            return {
                'success': False,
                'message': 'Payment amount must be positive',
                'error_code': 'VAL_001'
            }

        if amount > remaining:
            return {
                'success': False,
                'message': f'Payment amount cannot exceed remaining balance of {remaining} SAR',
                'error_code': 'VAL_001'
            }

        # Valid payment methods
        valid_methods = ['cash', 'bank_transfer', 'card', 'mada', 'apple_pay', 'stc_pay']
        if payment_method not in valid_methods:
            payment_method = 'cash'

        try:
            # Create payment record
            payment = Payment(
                transaction_id=transaction_id,
                customer_id=customer_id,
                amount=amount,
                payment_method=payment_method,
                status='completed',
                completed_at=datetime.utcnow()
            )

            db.session.add(payment)

            # Update transaction
            transaction.paid_amount = float(transaction.paid_amount) + amount
            transaction.updated_at = datetime.utcnow()

            # Check if fully paid
            if transaction.remaining_amount <= 0:
                transaction.status = 'paid'
                transaction.paid_at = datetime.utcnow()

            # Update customer credit
            customer.available_credit = float(customer.available_credit) + amount
            customer.used_credit = float(customer.used_credit) - amount
            customer.updated_at = datetime.utcnow()

            db.session.commit()

            # Send notification
            PaymentService._notify_payment_received(customer, transaction, payment)

            return {
                'success': True,
                'message': 'Payment processed successfully',
                'data': {
                    'payment': payment.to_dict(),
                    'transaction': {
                        'id': transaction.id,
                        'reference_number': transaction.reference_number,
                        'status': transaction.status,
                        'paid_amount': float(transaction.paid_amount),
                        'remaining_amount': transaction.remaining_amount
                    },
                    'credit': {
                        'available_credit': float(customer.available_credit),
                        'used_credit': float(customer.used_credit)
                    }
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to process payment: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Pay Multiple Transactions ====================

    @staticmethod
    def make_multi_transaction_payment(customer_id, transaction_ids, total_amount, payment_method='card'):
        """Pay for specific transactions (by IDs)"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        if not transaction_ids or len(transaction_ids) == 0:
            return {
                'success': False,
                'message': 'At least one transaction_id is required',
                'error_code': 'VAL_001'
            }

        total_amount = float(total_amount) if total_amount else 0

        if total_amount <= 0:
            return {
                'success': False,
                'message': 'Payment amount must be positive',
                'error_code': 'VAL_001'
            }

        # Get specified transactions
        transactions = Transaction.query.filter(
            Transaction.id.in_(transaction_ids),
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'overdue'])
        ).order_by(Transaction.due_date.asc()).all()

        if not transactions:
            return {
                'success': False,
                'message': 'No valid transactions found',
                'error_code': 'TXN_001'
            }

        # Calculate total remaining for selected transactions
        total_remaining = sum(t.remaining_amount for t in transactions)

        if total_amount > total_remaining:
            return {
                'success': False,
                'message': f'Payment amount exceeds total remaining of {total_remaining} SAR',
                'error_code': 'VAL_001'
            }

        # Valid payment methods
        valid_methods = ['cash', 'bank_transfer', 'card', 'mada', 'apple_pay', 'stc_pay']
        if payment_method not in valid_methods:
            payment_method = 'card'

        try:
            remaining_payment = total_amount
            payments_made = []
            main_payment_ref = None

            for txn in transactions:
                if remaining_payment <= 0:
                    break

                txn_remaining = txn.remaining_amount
                payment_for_txn = min(remaining_payment, txn_remaining)

                # Create payment
                payment = Payment(
                    transaction_id=txn.id,
                    customer_id=customer_id,
                    amount=payment_for_txn,
                    payment_method=payment_method,
                    status='completed',
                    completed_at=datetime.utcnow()
                )
                db.session.add(payment)

                if not main_payment_ref:
                    main_payment_ref = payment.reference_number

                # Update transaction
                txn.paid_amount = float(txn.paid_amount) + payment_for_txn
                txn.updated_at = datetime.utcnow()

                if txn.remaining_amount <= 0:
                    txn.status = 'paid'
                    txn.paid_at = datetime.utcnow()

                payments_made.append({
                    'payment_id': payment.id,
                    'transaction_id': txn.id,
                    'reference_number': txn.reference_number,
                    'amount': payment_for_txn,
                    'transaction_status': txn.status
                })

                remaining_payment -= payment_for_txn

            # Update customer credit
            customer.available_credit = float(customer.available_credit) + total_amount
            customer.used_credit = float(customer.used_credit) - total_amount
            customer.updated_at = datetime.utcnow()

            db.session.commit()

            return {
                'success': True,
                'message': 'Payment processed successfully',
                'data': {
                    'id': payments_made[0]['payment_id'] if payments_made else None,
                    'reference_number': main_payment_ref,
                    'amount': total_amount,
                    'status': 'completed',
                    'payments': payments_made,
                    'credit': {
                        'available_credit': float(customer.available_credit),
                        'used_credit': float(customer.used_credit)
                    }
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to process payment: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def make_bulk_payment(customer_id, total_amount, payment_method='cash'):
        """Pay multiple transactions at once (oldest first)"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        total_amount = float(total_amount)

        if total_amount <= 0:
            return {
                'success': False,
                'message': 'Payment amount must be positive',
                'error_code': 'VAL_001'
            }

        # Get outstanding transactions ordered by due date (oldest first)
        outstanding = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'overdue'])
        ).order_by(Transaction.due_date.asc()).all()

        if not outstanding:
            return {
                'success': False,
                'message': 'No outstanding transactions to pay',
                'error_code': 'TXN_001'
            }

        # Calculate total outstanding
        total_outstanding = sum(t.remaining_amount for t in outstanding)

        if total_amount > total_outstanding:
            return {
                'success': False,
                'message': f'Payment amount exceeds total outstanding of {total_outstanding} SAR',
                'error_code': 'VAL_001'
            }

        try:
            remaining_payment = total_amount
            payments_made = []

            for txn in outstanding:
                if remaining_payment <= 0:
                    break

                txn_remaining = txn.remaining_amount

                # Determine how much to pay for this transaction
                payment_for_txn = min(remaining_payment, txn_remaining)

                # Create payment
                payment = Payment(
                    transaction_id=txn.id,
                    customer_id=customer_id,
                    amount=payment_for_txn,
                    payment_method=payment_method,
                    status='completed',
                    completed_at=datetime.utcnow()
                )
                db.session.add(payment)

                # Update transaction
                txn.paid_amount = float(txn.paid_amount) + payment_for_txn
                txn.updated_at = datetime.utcnow()

                if txn.remaining_amount <= 0:
                    txn.status = 'paid'
                    txn.paid_at = datetime.utcnow()

                payments_made.append({
                    'payment_id': payment.id,
                    'transaction_id': txn.id,
                    'reference_number': txn.reference_number,
                    'amount': payment_for_txn,
                    'transaction_status': txn.status
                })

                remaining_payment -= payment_for_txn

            # Update customer credit
            customer.available_credit = float(customer.available_credit) + total_amount
            customer.used_credit = float(customer.used_credit) - total_amount
            customer.updated_at = datetime.utcnow()

            db.session.commit()

            return {
                'success': True,
                'message': f'Successfully paid {total_amount} SAR across {len(payments_made)} transactions',
                'data': {
                    'total_paid': total_amount,
                    'payments': payments_made,
                    'credit': {
                        'available_credit': float(customer.available_credit),
                        'used_credit': float(customer.used_credit)
                    }
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to process payment: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Payment Reminders ====================

    @staticmethod
    def send_payment_reminders():
        """Send payment reminders for due transactions (called by scheduler)"""
        from datetime import timedelta

        today = datetime.utcnow().date()
        reminder_days = current_app.config.get('PAYMENT_REMINDER_DAYS', [3, 1, 0])

        count = 0
        for days in reminder_days:
            due_date = today + timedelta(days=days)

            transactions = Transaction.query.filter(
                Transaction.status == 'confirmed',
                Transaction.due_date == due_date
            ).all()

            for txn in transactions:
                PaymentService._send_reminder(txn.customer, txn, days)
                count += 1

        return {
            'success': True,
            'message': f'Sent {count} payment reminders'
        }

    # ==================== Admin/Report Functions ====================

    @staticmethod
    def get_payment_statistics(from_date=None, to_date=None):
        """Get payment statistics for admin dashboard"""
        query = Payment.query.filter_by(status='completed')

        if from_date:
            query = query.filter(Payment.completed_at >= from_date)

        if to_date:
            query = query.filter(Payment.completed_at <= to_date)

        total_count = query.count()
        total_amount = db.session.query(
            db.func.coalesce(db.func.sum(Payment.amount), 0)
        ).filter(Payment.status == 'completed')

        if from_date:
            total_amount = total_amount.filter(Payment.completed_at >= from_date)
        if to_date:
            total_amount = total_amount.filter(Payment.completed_at <= to_date)

        total_amount = total_amount.scalar()

        # By payment method
        by_method = db.session.query(
            Payment.payment_method,
            db.func.count(Payment.id).label('count'),
            db.func.sum(Payment.amount).label('amount')
        ).filter(Payment.status == 'completed')

        if from_date:
            by_method = by_method.filter(Payment.completed_at >= from_date)
        if to_date:
            by_method = by_method.filter(Payment.completed_at <= to_date)

        by_method = by_method.group_by(Payment.payment_method).all()

        return {
            'success': True,
            'data': {
                'total_count': total_count,
                'total_amount': float(total_amount) if total_amount else 0,
                'by_method': [
                    {
                        'method': m[0] or 'unknown',
                        'count': m[1],
                        'amount': float(m[2]) if m[2] else 0
                    }
                    for m in by_method
                ]
            }
        }

    @staticmethod
    def get_all_payments(status=None, from_date=None, to_date=None, page=1, per_page=20):
        """Get all payments for admin"""
        query = Payment.query

        if status:
            query = query.filter_by(status=status)

        if from_date:
            query = query.filter(Payment.created_at >= from_date)

        if to_date:
            query = query.filter(Payment.created_at <= to_date)

        query = query.order_by(Payment.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        payments_data = []
        for payment in pagination.items:
            payment_dict = payment.to_dict()
            payment_dict['customer'] = {
                'id': payment.customer.id,
                'name_ar': payment.customer.full_name_ar,
                'phone': payment.customer.phone
            }
            payment_dict['transaction'] = {
                'id': payment.transaction.id,
                'reference_number': payment.transaction.reference_number
            }
            payments_data.append(payment_dict)

        return {
            'success': True,
            'data': {
                'payments': payments_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    # ==================== Notifications ====================

    @staticmethod
    def _notify_payment_received(customer, transaction, payment):
        """Send notification for payment received"""
        try:
            notification = Notification(
                customer_id=customer.id,
                title_ar='تم استلام الدفعة',
                title_en='Payment Received',
                body_ar=f'تم استلام {payment.amount} ريال للمعاملة رقم {transaction.reference_number}',
                body_en=f'Received {payment.amount} SAR for transaction {transaction.reference_number}',
                type='payment',
                reference_id=payment.id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass

    @staticmethod
    def _send_reminder(customer, transaction, days_until_due):
        """Send payment reminder notification"""
        try:
            if days_until_due == 0:
                title_ar = 'تذكير: موعد السداد اليوم'
                title_en = 'Reminder: Payment Due Today'
                body_ar = f'موعد سداد المعاملة رقم {transaction.reference_number} اليوم. المبلغ المتبقي: {transaction.remaining_amount} ريال'
                body_en = f'Payment for transaction {transaction.reference_number} is due today. Remaining: {transaction.remaining_amount} SAR'
            else:
                title_ar = f'تذكير: موعد السداد بعد {days_until_due} أيام'
                title_en = f'Reminder: Payment Due in {days_until_due} Days'
                body_ar = f'موعد سداد المعاملة رقم {transaction.reference_number} بعد {days_until_due} أيام. المبلغ المتبقي: {transaction.remaining_amount} ريال'
                body_en = f'Payment for transaction {transaction.reference_number} is due in {days_until_due} days. Remaining: {transaction.remaining_amount} SAR'

            notification = Notification(
                customer_id=customer.id,
                title_ar=title_ar,
                title_en=title_en,
                body_ar=body_ar,
                body_en=body_en,
                type='payment_reminder',
                reference_id=transaction.id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass
