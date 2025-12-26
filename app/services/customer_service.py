"""
Customer Service - Full Implementation
"""
from datetime import datetime
from flask import current_app
from app.extensions import db
from app.models.customer import Customer
from app.models.credit_limit_request import CreditLimitRequest
from app.models.transaction import Transaction
from app.models.notification import Notification


class CustomerService:
    """Customer service for all customer-related operations"""

    # ==================== Profile ====================

    @staticmethod
    def get_customer_profile(customer_id):
        """Get customer profile by ID"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        return {
            'success': True,
            'data': {
                'customer': customer.to_dict(include_sensitive=True)
            }
        }

    @staticmethod
    def get_customer_by_national_id(national_id):
        """Get customer by national ID"""
        customer = Customer.query.filter_by(national_id=national_id).first()

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        return {
            'success': True,
            'data': {
                'customer': customer.to_dict()
            }
        }

    @staticmethod
    def update_customer_profile(customer_id, data):
        """Update customer profile"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Allowed fields to update
        allowed_fields = ['full_name_ar', 'full_name_en', 'email', 'phone', 'city', 'district', 'address_line', 'language', 'notifications_enabled']

        for field in allowed_fields:
            if field in data:
                setattr(customer, field, data[field])

        customer.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Profile updated successfully',
                'data': {
                    'customer': customer.to_dict(include_sensitive=True)
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update profile: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def update_notification_preferences(customer_id, data):
        """Update notification preferences"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        if 'notifications_enabled' in data:
            customer.notifications_enabled = data['notifications_enabled']

        customer.updated_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Notification preferences updated',
                'data': {
                    'notifications_enabled': customer.notifications_enabled
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update preferences: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Credit ====================

    @staticmethod
    def get_credit_details(customer_id):
        """Get customer credit details"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Get pending transactions count
        pending_transactions = Transaction.query.filter_by(
            customer_id=customer_id,
            status='confirmed'
        ).count()

        # Get pending amount
        pending_amount = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.total_amount - Transaction.paid_amount - Transaction.returned_amount), 0)
        ).filter(
            Transaction.customer_id == customer_id,
            Transaction.status == 'confirmed'
        ).scalar()

        # Get next payment info (earliest due transaction)
        next_payment_txn = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'overdue'])
        ).order_by(Transaction.due_date.asc()).first()

        next_payment_date = None
        next_payment_amount = 0

        if next_payment_txn:
            next_payment_date = next_payment_txn.due_date.isoformat() if next_payment_txn.due_date else None
            next_payment_amount = next_payment_txn.remaining_amount

        return {
            'success': True,
            'data': {
                'credit_limit': float(customer.credit_limit),
                'available_credit': float(customer.available_credit),
                'used_credit': float(customer.used_credit),
                'next_payment_date': next_payment_date,
                'next_payment_amount': float(next_payment_amount) if next_payment_amount else 0,
                'pending_transactions': pending_transactions,
                'pending_amount': float(pending_amount) if pending_amount else 0
            }
        }

    @staticmethod
    def get_credit_health(customer_id):
        """Get customer credit health score for mobile app"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Calculate payment history score (0-100)
        total_paid = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status == 'paid'
        ).count()

        on_time_paid = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status == 'paid',
            Transaction.paid_at <= Transaction.due_date
        ).count()

        if total_paid > 0:
            payment_history_score = int((on_time_paid / total_paid) * 100)
        else:
            payment_history_score = 100  # New customer gets full score

        # Calculate credit utilization score (0-100)
        # Lower utilization = higher score
        if customer.credit_limit > 0:
            utilization = float(customer.used_credit) / float(customer.credit_limit)
            if utilization <= 0.3:
                utilization_score = 100
            elif utilization <= 0.5:
                utilization_score = 80
            elif utilization <= 0.7:
                utilization_score = 60
            elif utilization <= 0.9:
                utilization_score = 40
            else:
                utilization_score = 20
        else:
            utilization_score = 100

        # Calculate account age score (0-100)
        if customer.created_at:
            from datetime import datetime
            days_active = (datetime.utcnow() - customer.created_at).days
            if days_active >= 365:
                account_age_score = 100
            elif days_active >= 180:
                account_age_score = 80
            elif days_active >= 90:
                account_age_score = 60
            elif days_active >= 30:
                account_age_score = 40
            else:
                account_age_score = 20
        else:
            account_age_score = 20

        # Check for overdue transactions
        overdue_count = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status == 'overdue'
        ).count()

        # Penalty for overdue transactions
        overdue_penalty = min(overdue_count * 10, 30)

        # Calculate overall score (weighted average)
        overall_score = int(
            (payment_history_score * 0.5) +
            (utilization_score * 0.3) +
            (account_age_score * 0.2) -
            overdue_penalty
        )
        overall_score = max(0, min(100, overall_score))

        # Determine rating
        if overall_score >= 80:
            rating = 'excellent'
            rating_ar = 'ممتاز'
            stars = 5
        elif overall_score >= 60:
            rating = 'good'
            rating_ar = 'جيد'
            stars = 4
        elif overall_score >= 40:
            rating = 'fair'
            rating_ar = 'متوسط'
            stars = 3
        else:
            rating = 'poor'
            rating_ar = 'ضعيف'
            stars = 2

        return {
            'success': True,
            'data': {
                'score': overall_score,
                'rating': rating,
                'rating_ar': rating_ar,
                'stars': stars,
                'factors': {
                    'payment_history': payment_history_score,
                    'credit_utilization': utilization_score,
                    'account_age': account_age_score
                },
                'tips': CustomerService._get_credit_health_tips(
                    payment_history_score,
                    utilization_score,
                    overdue_count
                )
            }
        }

    @staticmethod
    def _get_credit_health_tips(payment_history, utilization, overdue_count):
        """Generate tips to improve credit health"""
        tips = []

        if overdue_count > 0:
            tips.append({
                'ar': f'لديك {overdue_count} معاملة متأخرة. قم بسدادها لتحسين تقييمك',
                'en': f'You have {overdue_count} overdue transaction(s). Pay them to improve your score'
            })

        if payment_history < 80:
            tips.append({
                'ar': 'حاول سداد مستحقاتك في موعدها لتحسين سجل الدفعات',
                'en': 'Try to pay your dues on time to improve your payment history'
            })

        if utilization < 60:
            tips.append({
                'ar': 'حافظ على نسبة استخدام منخفضة لرصيدك الائتماني',
                'en': 'Keep your credit utilization low for a better score'
            })

        if not tips:
            tips.append({
                'ar': 'أداء ممتاز! حافظ على سجلك الجيد',
                'en': 'Excellent performance! Keep up the good work'
            })

        return tips

    @staticmethod
    def request_credit_increase(customer_id, requested_amount, reason=None):
        """Request credit limit increase"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        if customer.status != 'active':
            return {
                'success': False,
                'message': 'Only active customers can request credit increase',
                'error_code': 'CUST_003'
            }

        # Check max credit limit
        max_limit = current_app.config.get('MAX_CREDIT_LIMIT', 5000)
        if requested_amount > max_limit:
            return {
                'success': False,
                'message': f'Requested amount exceeds maximum limit of {max_limit} SAR',
                'error_code': 'VAL_001'
            }

        # Check if there's already a pending request
        pending_request = CreditLimitRequest.query.filter_by(
            customer_id=customer_id,
            status='pending'
        ).first()

        if pending_request:
            return {
                'success': False,
                'message': 'You already have a pending credit increase request',
                'error_code': 'VAL_001'
            }

        # Create the request
        credit_request = CreditLimitRequest(
            customer_id=customer_id,
            current_limit=customer.credit_limit,
            requested_limit=requested_amount,
            reason=reason
        )

        try:
            db.session.add(credit_request)
            db.session.commit()

            return {
                'success': True,
                'message': 'Credit increase request submitted successfully',
                'data': {
                    'request_id': credit_request.id,
                    'status': credit_request.status,
                    'requested_limit': float(credit_request.requested_limit)
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to submit request: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def get_credit_requests(customer_id, page=1, per_page=20):
        """Get customer's credit increase requests"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        pagination = CreditLimitRequest.query.filter_by(
            customer_id=customer_id
        ).order_by(
            CreditLimitRequest.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)

        return {
            'success': True,
            'data': {
                'requests': [r.to_dict() for r in pagination.items]
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    # ==================== Statistics ====================

    @staticmethod
    def get_customer_statistics(customer_id):
        """Get customer statistics for admin view"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Total transactions
        total_transactions = Transaction.query.filter_by(customer_id=customer_id).count()

        # Total spent (confirmed + paid transactions)
        total_spent = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.total_amount), 0)
        ).filter(
            Transaction.customer_id == customer_id,
            Transaction.status.in_(['confirmed', 'paid'])
        ).scalar()

        # Total paid
        total_paid = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.paid_amount), 0)
        ).filter(
            Transaction.customer_id == customer_id
        ).scalar()

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

        # On-time payments
        on_time_payments = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status == 'paid',
            Transaction.paid_at <= Transaction.due_date
        ).count()

        # Late payments
        late_payments = Transaction.query.filter(
            Transaction.customer_id == customer_id,
            Transaction.status == 'paid',
            Transaction.paid_at > Transaction.due_date
        ).count()

        return {
            'success': True,
            'data': {
                'customer': customer.to_dict(include_sensitive=True),
                'statistics': {
                    'total_transactions': total_transactions,
                    'total_spent': float(total_spent) if total_spent else 0,
                    'total_paid': float(total_paid) if total_paid else 0,
                    'outstanding': float(outstanding) if outstanding else 0,
                    'on_time_payments': on_time_payments,
                    'late_payments': late_payments
                }
            }
        }

    # ==================== Account Management ====================

    @staticmethod
    def update_customer_status(customer_id, status, reason=None, admin_id=None):
        """Update customer account status (admin only)"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        valid_statuses = ['pending', 'active', 'suspended', 'blocked']
        if status not in valid_statuses:
            return {
                'success': False,
                'message': f'Invalid status. Must be one of: {valid_statuses}',
                'error_code': 'VAL_001'
            }

        old_status = customer.status
        customer.status = status
        customer.status_reason = reason
        customer.updated_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='customer.status_updated',
                entity_type='customer',
                entity_id=customer_id,
                old_values={'status': old_status},
                new_values={'status': status, 'reason': reason}
            )

            return {
                'success': True,
                'message': f'Customer status updated to {status}',
                'data': {
                    'customer': customer.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update status: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def update_credit_limit(customer_id, new_limit, reason=None, admin_id=None):
        """Update customer credit limit (admin only)"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        max_limit = current_app.config.get('MAX_CREDIT_LIMIT', 5000)
        if new_limit > max_limit:
            return {
                'success': False,
                'message': f'Credit limit cannot exceed {max_limit} SAR',
                'error_code': 'VAL_001'
            }

        if new_limit < 0:
            return {
                'success': False,
                'message': 'Credit limit cannot be negative',
                'error_code': 'VAL_001'
            }

        old_limit = float(customer.credit_limit)
        old_available = float(customer.available_credit)

        # Calculate new available credit
        # new_available = new_limit - used_credit
        customer.credit_limit = new_limit
        customer.available_credit = new_limit - float(customer.used_credit)
        customer.updated_at = datetime.utcnow()

        try:
            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='customer.credit_limit_updated',
                entity_type='customer',
                entity_id=customer_id,
                old_values={'credit_limit': old_limit, 'available_credit': old_available},
                new_values={'credit_limit': new_limit, 'available_credit': float(customer.available_credit), 'reason': reason}
            )

            # Send notification to customer
            CustomerService._send_credit_limit_notification(customer, old_limit, new_limit)

            return {
                'success': True,
                'message': 'Credit limit updated successfully',
                'data': {
                    'customer': customer.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update credit limit: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def _send_credit_limit_notification(customer, old_limit, new_limit):
        """Send notification about credit limit change"""
        try:
            if new_limit > old_limit:
                title_ar = 'تم زيادة حد الشراء'
                body_ar = f'تم زيادة حد الشراء الخاص بك من {old_limit} إلى {new_limit} ريال'
            else:
                title_ar = 'تم تعديل حد الشراء'
                body_ar = f'تم تعديل حد الشراء الخاص بك من {old_limit} إلى {new_limit} ريال'

            notification = Notification(
                customer_id=customer.id,
                title_ar=title_ar,
                title_en='Credit Limit Updated',
                body_ar=body_ar,
                body_en=f'Your credit limit has been updated from {old_limit} to {new_limit} SAR',
                type='account_update'
            )
            db.session.add(notification)
            db.session.commit()
        except Exception:
            pass  # Don't fail the main operation if notification fails

    # ==================== Password Management ====================

    @staticmethod
    def change_password(customer_id, current_password, new_password):
        """Change customer password"""
        customer = Customer.query.get(customer_id)

        if not customer:
            return {
                'success': False,
                'message': 'Customer not found',
                'error_code': 'CUST_001'
            }

        # Verify current password
        if not customer.check_password(current_password):
            return {
                'success': False,
                'message': 'Current password is incorrect',
                'error_code': 'AUTH_003'
            }

        # Validate new password
        if len(new_password) < 8:
            return {
                'success': False,
                'message': 'New password must be at least 8 characters',
                'error_code': 'VAL_001'
            }

        try:
            customer.set_password(new_password)
            customer.updated_at = datetime.utcnow()
            db.session.commit()

            return {
                'success': True,
                'message': 'Password changed successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to change password: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Search & List ====================

    @staticmethod
    def search_customers(status=None, search=None, city=None, page=1, per_page=20):
        """Search customers (admin only)"""
        query = Customer.query

        if status:
            query = query.filter(Customer.status == status)

        if city:
            query = query.filter(Customer.city == city)

        if search:
            search_term = f'%{search}%'
            query = query.filter(
                db.or_(
                    Customer.full_name_ar.ilike(search_term),
                    Customer.full_name_en.ilike(search_term),
                    Customer.phone.ilike(search_term),
                    Customer.national_id.ilike(search_term),
                    Customer.email.ilike(search_term)
                )
            )

        query = query.order_by(Customer.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'success': True,
            'data': {
                'customers': [c.to_dict() for c in pagination.items]
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }
