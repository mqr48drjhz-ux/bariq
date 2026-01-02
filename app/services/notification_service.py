"""
Notification Service - Full Implementation for Mobile App
"""
from datetime import datetime
from app.extensions import db
from app.models.notification import Notification
from app.models.device import CustomerDevice, MerchantUserDevice


class NotificationService:
    """Notification service for customer notifications"""

    @staticmethod
    def get_customer_notifications(customer_id, unread_only=False, page=1, per_page=20):
        """Get customer notifications"""
        query = Notification.query.filter_by(customer_id=customer_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        query = query.order_by(Notification.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Get unread count
        unread_count = Notification.query.filter_by(
            customer_id=customer_id,
            is_read=False
        ).count()

        return {
            'success': True,
            'data': {
                'notifications': [n.to_dict() for n in pagination.items],
                'unread_count': unread_count
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def mark_as_read(customer_id, notification_id):
        """Mark a notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            customer_id=customer_id
        ).first()

        if not notification:
            return {
                'success': False,
                'message': 'Notification not found',
                'error_code': 'NOTIF_001'
            }

        notification.is_read = True
        notification.read_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Notification marked as read'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to mark notification: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def mark_all_as_read(customer_id):
        """Mark all notifications as read"""
        try:
            Notification.query.filter_by(
                customer_id=customer_id,
                is_read=False
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })

            db.session.commit()
            return {
                'success': True,
                'message': 'All notifications marked as read'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to mark notifications: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def create_notification(customer_id, title_ar, body_ar, notification_type,
                           title_en=None, body_en=None, related_entity_type=None,
                           related_entity_id=None):
        """Create a new notification"""
        try:
            notification = Notification(
                customer_id=customer_id,
                title_ar=title_ar,
                title_en=title_en,
                body_ar=body_ar,
                body_en=body_en,
                type=notification_type,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id
            )

            db.session.add(notification)
            db.session.commit()

            return {
                'success': True,
                'data': {
                    'notification': notification.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create notification: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Device Registration for Push Notifications ====================

    @staticmethod
    def register_device(customer_id, fcm_token, device_type, device_name=None, device_id=None):
        """Register device for push notifications (FCM)"""
        if not fcm_token:
            return {
                'success': False,
                'message': 'FCM token is required',
                'error_code': 'VAL_001'
            }

        if device_type not in ['ios', 'android']:
            return {
                'success': False,
                'message': 'Device type must be ios or android',
                'error_code': 'VAL_001'
            }

        try:
            # Check if device already exists (by token)
            existing = CustomerDevice.query.filter_by(
                customer_id=customer_id,
                fcm_token=fcm_token
            ).first()

            if existing:
                # Update existing device
                existing.device_type = device_type
                existing.device_name = device_name
                existing.device_id = device_id
                existing.is_active = True
                existing.last_used_at = datetime.utcnow()
                db.session.commit()
                return {
                    'success': True,
                    'message': 'Device updated successfully',
                    'data': existing.to_dict()
                }

            # Create new device
            device = CustomerDevice(
                customer_id=customer_id,
                fcm_token=fcm_token,
                device_type=device_type,
                device_name=device_name,
                device_id=device_id,
                is_active=True,
                last_used_at=datetime.utcnow()
            )
            db.session.add(device)
            db.session.commit()

            return {
                'success': True,
                'message': 'Device registered successfully',
                'data': device.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to register device: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def unregister_device(customer_id, device_id):
        """Unregister device from push notifications"""
        try:
            device = CustomerDevice.query.filter_by(
                id=device_id,
                customer_id=customer_id
            ).first()

            if not device:
                return {
                    'success': False,
                    'message': 'Device not found',
                    'error_code': 'DEV_001'
                }

            db.session.delete(device)
            db.session.commit()

            return {
                'success': True,
                'message': 'Device unregistered successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to unregister device: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def get_customer_devices(customer_id):
        """Get all devices for a customer"""
        devices = CustomerDevice.query.filter_by(
            customer_id=customer_id,
            is_active=True
        ).all()

        return {
            'success': True,
            'data': {
                'devices': [d.to_dict() for d in devices]
            }
        }

    # ==================== Send Push Notification ====================

    @staticmethod
    def send_push_notification(customer_id, title, body, data=None, notification_type='push',
                               related_entity_type=None, related_entity_id=None):
        """Send push notification to customer's devices via Firebase FCM"""
        from app.services.firebase_service import push_manager

        return push_manager.send_to_customer(
            customer_id=customer_id,
            title_ar=title,
            body_ar=body,
            title_en=title,
            body_en=body,
            data=data,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )

    # ==================== Notification Templates ====================

    @staticmethod
    def notify_new_transaction(customer_id, transaction):
        """Notify customer about new transaction pending confirmation"""
        return NotificationService.create_notification(
            customer_id=customer_id,
            title_ar='معاملة جديدة',
            title_en='New Transaction',
            body_ar=f'لديك معاملة جديدة بقيمة {transaction.total_amount} ريال تحتاج للتأكيد',
            body_en=f'You have a new transaction of {transaction.total_amount} SAR pending confirmation',
            notification_type='transaction_pending',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

    @staticmethod
    def notify_payment_reminder(customer_id, transaction, days_until_due):
        """Notify customer about upcoming payment"""
        if days_until_due == 0:
            title_ar = 'دفعة مستحقة اليوم'
            body_ar = f'لديك دفعة بقيمة {transaction.total_amount - transaction.paid_amount} ريال مستحقة اليوم'
        else:
            title_ar = 'تذكير بالدفع'
            body_ar = f'لديك دفعة بقيمة {transaction.total_amount - transaction.paid_amount} ريال مستحقة خلال {days_until_due} أيام'

        return NotificationService.create_notification(
            customer_id=customer_id,
            title_ar=title_ar,
            title_en='Payment Reminder',
            body_ar=body_ar,
            body_en=f'You have a payment of {transaction.total_amount - transaction.paid_amount} SAR due in {days_until_due} days',
            notification_type='payment_reminder',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

    @staticmethod
    def notify_payment_success(customer_id, payment):
        """Notify customer about successful payment"""
        return NotificationService.create_notification(
            customer_id=customer_id,
            title_ar='تم الدفع بنجاح',
            title_en='Payment Successful',
            body_ar=f'تم استلام دفعتك بقيمة {payment.amount} ريال بنجاح',
            body_en=f'Your payment of {payment.amount} SAR has been received successfully',
            notification_type='payment_success',
            related_entity_type='payment',
            related_entity_id=payment.id
        )

    @staticmethod
    def notify_credit_alert(customer_id, alert_type, details):
        """Notify customer about credit alerts"""
        if alert_type == 'low_credit':
            title_ar = 'تنبيه الرصيد'
            body_ar = f'رصيدك المتاح منخفض: {details["available"]} ريال'
        elif alert_type == 'limit_increased':
            title_ar = 'زيادة حد الشراء'
            body_ar = f'تم زيادة حد الشراء الخاص بك إلى {details["new_limit"]} ريال'
        else:
            title_ar = 'تحديث الائتمان'
            body_ar = 'تم تحديث معلومات الائتمان الخاصة بك'

        return NotificationService.create_notification(
            customer_id=customer_id,
            title_ar=title_ar,
            title_en='Credit Alert',
            body_ar=body_ar,
            body_en='Your credit information has been updated',
            notification_type='credit_alert'
        )

    # ==================== Merchant Staff Notifications ====================

    @staticmethod
    def get_merchant_staff_notifications(staff_id, unread_only=False, page=1, per_page=20):
        """Get notifications for merchant staff member"""
        query = Notification.query.filter_by(merchant_user_id=staff_id)

        if unread_only:
            query = query.filter_by(is_read=False)

        query = query.order_by(Notification.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Get unread count
        unread_count = Notification.query.filter_by(
            merchant_user_id=staff_id,
            is_read=False
        ).count()

        return {
            'success': True,
            'data': {
                'notifications': [n.to_dict() for n in pagination.items],
                'unread_count': unread_count
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def mark_staff_notification_read(staff_id, notification_id):
        """Mark a staff notification as read"""
        notification = Notification.query.filter_by(
            id=notification_id,
            merchant_user_id=staff_id
        ).first()

        if not notification:
            return {
                'success': False,
                'message': 'Notification not found',
                'error_code': 'NOTIF_001'
            }

        notification.is_read = True
        notification.read_at = datetime.utcnow()

        try:
            db.session.commit()
            return {
                'success': True,
                'message': 'Notification marked as read'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to mark notification: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def mark_all_staff_notifications_read(staff_id):
        """Mark all staff notifications as read"""
        try:
            Notification.query.filter_by(
                merchant_user_id=staff_id,
                is_read=False
            ).update({
                'is_read': True,
                'read_at': datetime.utcnow()
            })

            db.session.commit()
            return {
                'success': True,
                'message': 'All notifications marked as read'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to mark notifications: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def create_staff_notification(staff_id, title_ar, body_ar, notification_type,
                                  title_en=None, body_en=None, related_entity_type=None,
                                  related_entity_id=None):
        """Create a notification for merchant staff"""
        try:
            notification = Notification(
                merchant_user_id=staff_id,
                title_ar=title_ar,
                title_en=title_en,
                body_ar=body_ar,
                body_en=body_en,
                type=notification_type,
                related_entity_type=related_entity_type,
                related_entity_id=related_entity_id
            )

            db.session.add(notification)
            db.session.commit()

            return {
                'success': True,
                'data': {
                    'notification': notification.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create notification: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Merchant Device Registration ====================

    @staticmethod
    def register_merchant_device(staff_id, fcm_token, device_type, device_name=None, device_id=None):
        """Register merchant staff device for push notifications"""
        if not fcm_token:
            return {
                'success': False,
                'message': 'FCM token is required',
                'error_code': 'VAL_001'
            }

        if device_type not in ['ios', 'android']:
            return {
                'success': False,
                'message': 'Device type must be ios or android',
                'error_code': 'VAL_001'
            }

        try:
            # Check if device already exists
            existing = MerchantUserDevice.query.filter_by(
                merchant_user_id=staff_id,
                fcm_token=fcm_token
            ).first()

            if existing:
                existing.device_type = device_type
                existing.device_name = device_name
                existing.device_id = device_id
                existing.is_active = True
                existing.last_used_at = datetime.utcnow()
                db.session.commit()
                return {
                    'success': True,
                    'message': 'Device updated successfully',
                    'data': existing.to_dict()
                }

            # Create new device
            device = MerchantUserDevice(
                merchant_user_id=staff_id,
                fcm_token=fcm_token,
                device_type=device_type,
                device_name=device_name,
                device_id=device_id,
                is_active=True,
                last_used_at=datetime.utcnow()
            )
            db.session.add(device)
            db.session.commit()

            return {
                'success': True,
                'message': 'Device registered successfully',
                'data': device.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to register device: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def unregister_merchant_device(staff_id, device_id):
        """Unregister merchant staff device from push notifications"""
        try:
            device = MerchantUserDevice.query.filter_by(
                id=device_id,
                merchant_user_id=staff_id
            ).first()

            if not device:
                return {
                    'success': False,
                    'message': 'Device not found',
                    'error_code': 'DEV_001'
                }

            db.session.delete(device)
            db.session.commit()

            return {
                'success': True,
                'message': 'Device unregistered successfully'
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to unregister device: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def get_merchant_devices(staff_id):
        """Get all devices for a merchant staff"""
        devices = MerchantUserDevice.query.filter_by(
            merchant_user_id=staff_id,
            is_active=True
        ).all()

        return {
            'success': True,
            'data': {
                'devices': [d.to_dict() for d in devices]
            }
        }

    @staticmethod
    def send_merchant_push_notification(staff_id, title, body, data=None, notification_type='push',
                                        related_entity_type=None, related_entity_id=None):
        """Send push notification to merchant staff's devices via Firebase FCM"""
        from app.services.firebase_service import push_manager

        return push_manager.send_to_merchant_user(
            merchant_user_id=staff_id,
            title_ar=title,
            body_ar=body,
            title_en=title,
            body_en=body,
            data=data,
            notification_type=notification_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )

    # ==================== Merchant Staff Notification Templates ====================

    @staticmethod
    def notify_staff_transaction_confirmed(staff_id, transaction):
        """Notify staff when customer confirms transaction"""
        return NotificationService.create_staff_notification(
            staff_id=staff_id,
            title_ar='تأكيد معاملة',
            title_en='Transaction Confirmed',
            body_ar=f'تم تأكيد المعاملة رقم {transaction.reference_number} بقيمة {transaction.total_amount} ريال',
            body_en=f'Transaction {transaction.reference_number} for {transaction.total_amount} SAR has been confirmed',
            notification_type='transaction_confirmed',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

    @staticmethod
    def notify_staff_transaction_rejected(staff_id, transaction, reason=None):
        """Notify staff when customer rejects transaction"""
        body_ar = f'تم رفض المعاملة رقم {transaction.reference_number}'
        if reason:
            body_ar += f' - السبب: {reason}'

        return NotificationService.create_staff_notification(
            staff_id=staff_id,
            title_ar='رفض معاملة',
            title_en='Transaction Rejected',
            body_ar=body_ar,
            body_en=f'Transaction {transaction.reference_number} has been rejected',
            notification_type='transaction_rejected',
            related_entity_type='transaction',
            related_entity_id=transaction.id
        )

    @staticmethod
    def notify_staff_payment_received(staff_id, payment):
        """Notify staff when payment is received"""
        return NotificationService.create_staff_notification(
            staff_id=staff_id,
            title_ar='دفعة جديدة',
            title_en='Payment Received',
            body_ar=f'تم استلام دفعة بقيمة {payment.amount} ريال',
            body_en=f'Payment of {payment.amount} SAR has been received',
            notification_type='payment_received',
            related_entity_type='payment',
            related_entity_id=payment.id
        )

    @staticmethod
    def notify_staff_settlement_ready(staff_id, settlement):
        """Notify staff when settlement is ready"""
        return NotificationService.create_staff_notification(
            staff_id=staff_id,
            title_ar='تسوية جاهزة',
            title_en='Settlement Ready',
            body_ar=f'تسوية بقيمة {settlement.amount} ريال جاهزة للصرف',
            body_en=f'Settlement of {settlement.amount} SAR is ready for payout',
            notification_type='settlement_ready',
            related_entity_type='settlement',
            related_entity_id=settlement.id
        )
