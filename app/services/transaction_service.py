"""
Transaction Service - Full Implementation
"""
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models.transaction import Transaction
from app.models.transaction_return import TransactionReturn
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.branch import Branch
from app.models.merchant_user import MerchantUser
from app.models.notification import Notification


class TransactionService:
    """Transaction service for all transaction-related operations"""

    # ==================== Create Transaction ====================

    @staticmethod
    def create_transaction(merchant_id, branch_id, cashier_id, customer_bariq_id, items, discount=0, notes=None, payment_term_days=None):
        """Create a new transaction (initiated by merchant/cashier)"""
        # Validate merchant
        merchant = Merchant.query.get(merchant_id)
        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        if merchant.status != 'active':
            return {
                'success': False,
                'message': 'Merchant is not active',
                'error_code': 'MERCH_004'
            }

        # Validate branch
        branch = Branch.query.filter_by(id=branch_id, merchant_id=merchant_id).first()
        if not branch:
            return {
                'success': False,
                'message': 'Branch not found',
                'error_code': 'MERCH_005'
            }

        if not branch.is_active:
            return {
                'success': False,
                'message': 'Branch is not active',
                'error_code': 'MERCH_005'
            }

        # Find customer by Bariq ID
        customer = Customer.query.filter_by(bariq_id=customer_bariq_id).first()
        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        if customer.status != 'active':
            return {
                'success': False,
                'message': 'Customer account is not active',
                'error_code': 'CUST_003'
            }

        # Calculate amounts
        if not items or len(items) == 0:
            return {
                'success': False,
                'message': 'At least one item is required',
                'error_code': 'VAL_001'
            }

        # Support both 'price' and 'unit_price' field names
        subtotal = sum(
            float(item.get('unit_price') or item.get('price') or 0) * int(item.get('quantity', 1))
            for item in items
        )
        discount = float(discount) if discount else 0

        if discount < 0:
            return {
                'success': False,
                'message': 'Discount cannot be negative',
                'error_code': 'VAL_001'
            }

        if discount > subtotal:
            return {
                'success': False,
                'message': 'Discount cannot exceed subtotal',
                'error_code': 'VAL_001'
            }

        total_amount = subtotal - discount

        # Check customer credit limit
        if total_amount > float(customer.available_credit):
            return {
                'success': False,
                'message': f'Insufficient credit. Available: {customer.available_credit} SAR, Required: {total_amount} SAR',
                'error_code': 'CUST_004'
            }

        # Check minimum and maximum transaction amounts
        min_amount = current_app.config.get('MIN_TRANSACTION_AMOUNT', 10)
        max_amount = current_app.config.get('MAX_TRANSACTION_AMOUNT', 5000)

        if total_amount < min_amount:
            return {
                'success': False,
                'message': f'Transaction amount must be at least {min_amount} SAR',
                'error_code': 'VAL_001'
            }

        if total_amount > max_amount:
            return {
                'success': False,
                'message': f'Transaction amount cannot exceed {max_amount} SAR',
                'error_code': 'VAL_001'
            }

        # Calculate due date based on payment terms
        if payment_term_days:
            repayment_days = int(payment_term_days)
        else:
            repayment_days = current_app.config.get('REPAYMENT_DAYS', 30)
        due_date = (datetime.utcnow() + timedelta(days=repayment_days)).date()

        try:
            # Create transaction
            transaction = Transaction(
                customer_id=customer.id,
                merchant_id=merchant_id,
                branch_id=branch_id,
                cashier_id=cashier_id,
                subtotal=subtotal,
                discount=discount,
                total_amount=total_amount,
                items=items,
                due_date=due_date,
                status='pending',  # Requires customer confirmation
                notes=notes
            )

            db.session.add(transaction)
            db.session.commit()

            # Send notification to customer
            TransactionService._notify_customer_new_transaction(customer, transaction, merchant, branch)

            return {
                'success': True,
                'message': 'Transaction created. Awaiting customer confirmation.',
                'data': {
                    'transaction': transaction.to_dict(),
                    'customer': {
                        'id': customer.id,
                        'name': customer.full_name_ar,
                        'available_credit': float(customer.available_credit)
                    }
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create transaction: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Customer Transaction Views ====================

    @staticmethod
    def get_customer_transactions(customer_id, status=None, page=1, per_page=20):
        """Get customer's transactions"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        query = Transaction.query.filter_by(customer_id=customer_id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Transaction.transaction_date.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        transactions_data = []
        for txn in pagination.items:
            txn_dict = txn.to_dict()
            txn_dict['merchant'] = {
                'id': txn.merchant.id,
                'name_ar': txn.merchant.name_ar,
                'name_en': txn.merchant.name_en
            }
            txn_dict['branch'] = {
                'id': txn.branch.id,
                'name_ar': txn.branch.name_ar,
                'city': txn.branch.city
            }
            transactions_data.append(txn_dict)

        return {
            'success': True,
            'data': {
                'transactions': transactions_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def get_transaction_for_customer(customer_id, transaction_id):
        """Get single transaction details for customer"""
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

        txn_dict = transaction.to_dict()
        txn_dict['merchant'] = {
            'id': transaction.merchant.id,
            'name_ar': transaction.merchant.name_ar,
            'name_en': transaction.merchant.name_en,
            'phone': transaction.merchant.phone
        }
        txn_dict['branch'] = {
            'id': transaction.branch.id,
            'name_ar': transaction.branch.name_ar,
            'name_en': transaction.branch.name_en,
            'city': transaction.branch.city,
            'district': transaction.branch.district,
            'address_line': transaction.branch.address_line,
            'phone': transaction.branch.phone
        }

        # Include payments history
        payments = [p.to_dict() for p in transaction.payments.order_by(db.desc('created_at')).all()]
        txn_dict['payments'] = payments

        # Include returns if any
        returns = [r.to_dict() for r in transaction.returns.all()]
        txn_dict['returns'] = returns

        return {
            'success': True,
            'data': {
                'transaction': txn_dict
            }
        }

    # ==================== Confirm/Reject Transaction ====================

    @staticmethod
    def reject_transaction(customer_id, transaction_id, reason=None):
        """Customer rejects a pending transaction"""
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

        if transaction.status != 'pending':
            return {
                'success': False,
                'message': f'Cannot reject transaction with status: {transaction.status}',
                'error_code': 'TXN_002'
            }

        try:
            # Update transaction status to rejected
            transaction.status = 'rejected'
            transaction.cancellation_reason = reason or 'Rejected by customer'
            transaction.updated_at = datetime.utcnow()

            db.session.commit()

            # Notify merchant about rejection
            TransactionService._notify_merchant_rejected(transaction, reason)

            return {
                'success': True,
                'message': 'Transaction rejected successfully',
                'data': {
                    'transaction': transaction.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to reject transaction: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def _notify_merchant_rejected(transaction, reason):
        """Send notification to merchant about rejected transaction"""
        try:
            # Create notification for merchant (would need a merchant notification system)
            # For now, we just log it
            pass
        except Exception:
            pass

    @staticmethod
    def confirm_transaction(customer_id, transaction_id):
        """Customer confirms a pending transaction"""
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

        if transaction.status != 'pending':
            return {
                'success': False,
                'message': f'Cannot confirm transaction with status: {transaction.status}',
                'error_code': 'TXN_002'
            }

        customer = Customer.query.get(customer_id)

        # Re-check credit availability
        if float(transaction.total_amount) > float(customer.available_credit):
            return {
                'success': False,
                'message': 'Insufficient credit to confirm this transaction',
                'error_code': 'CUST_004'
            }

        try:
            # Update transaction status
            transaction.status = 'confirmed'
            transaction.updated_at = datetime.utcnow()

            # Deduct from customer's available credit
            customer.available_credit = float(customer.available_credit) - float(transaction.total_amount)
            customer.used_credit = float(customer.used_credit) + float(transaction.total_amount)
            customer.updated_at = datetime.utcnow()

            db.session.commit()

            return {
                'success': True,
                'message': 'Transaction confirmed successfully',
                'data': {
                    'transaction': transaction.to_dict(),
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
                'message': f'Failed to confirm transaction: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Merchant Transaction Views ====================

    @staticmethod
    def get_merchant_transactions(merchant_id, branch_id=None, status=None, from_date=None, to_date=None, page=1, per_page=20):
        """Get merchant's transactions"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        query = Transaction.query.filter_by(merchant_id=merchant_id)

        if branch_id:
            query = query.filter_by(branch_id=branch_id)

        if status:
            query = query.filter_by(status=status)

        if from_date:
            query = query.filter(Transaction.transaction_date >= from_date)

        if to_date:
            query = query.filter(Transaction.transaction_date <= to_date)

        query = query.order_by(Transaction.transaction_date.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        transactions_data = []
        for txn in pagination.items:
            txn_dict = txn.to_dict()
            txn_dict['customer'] = {
                'id': txn.customer.id,
                'name_ar': txn.customer.full_name_ar,
                'phone': txn.customer.phone
            }
            txn_dict['branch'] = {
                'id': txn.branch.id,
                'name_ar': txn.branch.name_ar
            }
            if txn.cashier:
                txn_dict['cashier'] = {
                    'id': txn.cashier.id,
                    'name': txn.cashier.full_name
                }
            transactions_data.append(txn_dict)

        return {
            'success': True,
            'data': {
                'transactions': transactions_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def get_transaction_for_merchant(merchant_id, transaction_id):
        """Get single transaction details for merchant"""
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            merchant_id=merchant_id
        ).first()

        if not transaction:
            return {
                'success': False,
                'message': 'Transaction not found',
                'error_code': 'TXN_001'
            }

        txn_dict = transaction.to_dict()
        txn_dict['customer'] = {
            'id': transaction.customer.id,
            'name_ar': transaction.customer.full_name_ar,
            'phone': transaction.customer.phone,
            'national_id': transaction.customer.national_id[-4:] + '******'  # Masked
        }
        txn_dict['branch'] = transaction.branch.to_dict()
        if transaction.cashier:
            txn_dict['cashier'] = transaction.cashier.to_dict()

        # Include returns
        returns = [r.to_dict() for r in transaction.returns.all()]
        txn_dict['returns'] = returns

        return {
            'success': True,
            'data': {
                'transaction': txn_dict
            }
        }

    # ==================== Cancel Transaction ====================

    @staticmethod
    def cancel_transaction(merchant_id, transaction_id, reason, cancelled_by=None):
        """Cancel a pending transaction (before customer confirms)"""
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            merchant_id=merchant_id
        ).first()

        if not transaction:
            return {
                'success': False,
                'message': 'Transaction not found',
                'error_code': 'TXN_001'
            }

        if transaction.status != 'pending':
            return {
                'success': False,
                'message': 'Only pending transactions can be cancelled',
                'error_code': 'TXN_002'
            }

        try:
            transaction.status = 'cancelled'
            transaction.cancellation_reason = reason
            transaction.updated_at = datetime.utcnow()

            db.session.commit()

            # Notify customer
            TransactionService._notify_customer_cancelled(transaction.customer, transaction, reason)

            return {
                'success': True,
                'message': 'Transaction cancelled successfully',
                'data': {
                    'transaction': transaction.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to cancel transaction: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Process Return ====================

    @staticmethod
    def process_return(merchant_id, transaction_id, return_amount, reason, reason_details=None, returned_items=None, processed_by=None):
        """Process a return for a transaction"""
        transaction = Transaction.query.filter_by(
            id=transaction_id,
            merchant_id=merchant_id
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
                'message': 'Returns can only be processed for confirmed or overdue transactions',
                'error_code': 'TXN_002'
            }

        return_amount = float(return_amount)

        # Validate return amount
        max_returnable = float(transaction.total_amount) - float(transaction.returned_amount)
        if return_amount <= 0:
            return {
                'success': False,
                'message': 'Return amount must be positive',
                'error_code': 'VAL_001'
            }

        if return_amount > max_returnable:
            return {
                'success': False,
                'message': f'Return amount cannot exceed {max_returnable} SAR (remaining amount)',
                'error_code': 'VAL_001'
            }

        customer = transaction.customer

        try:
            # Create return record
            transaction_return = TransactionReturn(
                transaction_id=transaction_id,
                return_amount=return_amount,
                reason=reason,
                reason_details=reason_details,
                returned_items=returned_items or [],
                processed_by=processed_by,
                status='completed',
                processed_at=datetime.utcnow()
            )

            db.session.add(transaction_return)

            # Update transaction
            transaction.returned_amount = float(transaction.returned_amount) + return_amount
            transaction.updated_at = datetime.utcnow()

            # Restore customer credit
            customer.available_credit = float(customer.available_credit) + return_amount
            customer.used_credit = float(customer.used_credit) - return_amount
            customer.updated_at = datetime.utcnow()

            # Check if fully refunded
            if transaction.remaining_amount <= 0:
                transaction.status = 'refunded'

            db.session.commit()

            # Notify customer
            TransactionService._notify_customer_return(customer, transaction, return_amount)

            return {
                'success': True,
                'message': 'Return processed successfully',
                'data': {
                    'return': transaction_return.to_dict(),
                    'transaction': transaction.to_dict(),
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
                'message': f'Failed to process return: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def get_merchant_returns(merchant_id, branch_id=None, from_date=None, to_date=None, page=1, per_page=20):
        """Get merchant's returns"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        query = TransactionReturn.query.join(Transaction).filter(
            Transaction.merchant_id == merchant_id
        )

        if branch_id:
            query = query.filter(Transaction.branch_id == branch_id)

        if from_date:
            query = query.filter(TransactionReturn.created_at >= from_date)

        if to_date:
            query = query.filter(TransactionReturn.created_at <= to_date)

        query = query.order_by(TransactionReturn.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        returns_data = []
        for ret in pagination.items:
            ret_dict = ret.to_dict()
            ret_dict['transaction'] = {
                'id': ret.transaction.id,
                'reference_number': ret.transaction.reference_number,
                'total_amount': float(ret.transaction.total_amount)
            }
            ret_dict['customer'] = {
                'id': ret.transaction.customer.id,
                'name_ar': ret.transaction.customer.full_name_ar
            }
            returns_data.append(ret_dict)

        return {
            'success': True,
            'data': {
                'returns': returns_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    # ==================== Overdue Processing ====================

    @staticmethod
    def mark_overdue_transactions():
        """Mark transactions as overdue (called by scheduler)"""
        today = datetime.utcnow().date()

        overdue_transactions = Transaction.query.filter(
            Transaction.status == 'confirmed',
            Transaction.due_date < today
        ).all()

        count = 0
        for txn in overdue_transactions:
            txn.status = 'overdue'
            txn.updated_at = datetime.utcnow()
            count += 1

            # Notify customer
            TransactionService._notify_customer_overdue(txn.customer, txn)

        try:
            db.session.commit()
            return {
                'success': True,
                'message': f'{count} transactions marked as overdue'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update overdue transactions: {str(e)}'
            }

    # ==================== Statistics ====================

    @staticmethod
    def get_customer_transaction_stats(customer_id):
        """Get transaction statistics for a customer"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Total transactions
        total = Transaction.query.filter_by(customer_id=customer_id).count()

        # By status
        pending = Transaction.query.filter_by(customer_id=customer_id, status='pending').count()
        confirmed = Transaction.query.filter_by(customer_id=customer_id, status='confirmed').count()
        paid = Transaction.query.filter_by(customer_id=customer_id, status='paid').count()
        overdue = Transaction.query.filter_by(customer_id=customer_id, status='overdue').count()

        # Outstanding amount
        outstanding = db.session.query(
            db.func.coalesce(
                db.func.sum(Transaction.total_amount - Transaction.paid_amount - Transaction.returned_amount),
                0
            )
        ).filter(
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'overdue'])
        ).scalar()

        return {
            'success': True,
            'data': {
                'statistics': {
                    'total_transactions': total,
                    'pending': pending,
                    'confirmed': confirmed,
                    'paid': paid,
                    'overdue': overdue,
                    'outstanding_amount': float(outstanding) if outstanding else 0
                }
            }
        }

    # ==================== Notifications ====================

    @staticmethod
    def _notify_customer_new_transaction(customer, transaction, merchant, branch):
        """Send notification for new transaction"""
        try:
            notification = Notification(
                customer_id=customer.id,
                title_ar='معاملة جديدة',
                title_en='New Transaction',
                body_ar=f'لديك معاملة جديدة من {merchant.name_ar} بمبلغ {transaction.total_amount} ريال. الرجاء التأكيد.',
                body_en=f'New transaction from {merchant.name_en or merchant.name_ar} for {transaction.total_amount} SAR. Please confirm.',
                type='transaction',
                reference_id=transaction.id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass

    @staticmethod
    def _notify_customer_cancelled(customer, transaction, reason):
        """Send notification for cancelled transaction"""
        try:
            notification = Notification(
                customer_id=customer.id,
                title_ar='تم إلغاء المعاملة',
                title_en='Transaction Cancelled',
                body_ar=f'تم إلغاء المعاملة رقم {transaction.reference_number}',
                body_en=f'Transaction {transaction.reference_number} has been cancelled',
                type='transaction',
                reference_id=transaction.id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass

    @staticmethod
    def _notify_customer_return(customer, transaction, return_amount):
        """Send notification for processed return"""
        try:
            notification = Notification(
                customer_id=customer.id,
                title_ar='تم استرداد مبلغ',
                title_en='Refund Processed',
                body_ar=f'تم استرداد {return_amount} ريال من المعاملة رقم {transaction.reference_number}',
                body_en=f'{return_amount} SAR refunded from transaction {transaction.reference_number}',
                type='transaction',
                reference_id=transaction.id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass

    @staticmethod
    def _notify_customer_overdue(customer, transaction):
        """Send notification for overdue transaction"""
        try:
            notification = Notification(
                customer_id=customer.id,
                title_ar='معاملة متأخرة',
                title_en='Overdue Transaction',
                body_ar=f'المعاملة رقم {transaction.reference_number} متأخرة عن موعد السداد. الرجاء السداد في أقرب وقت.',
                body_en=f'Transaction {transaction.reference_number} is overdue. Please pay as soon as possible.',
                type='payment_reminder',
                reference_id=transaction.id
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass
