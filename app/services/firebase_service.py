"""
Firebase Cloud Messaging (FCM) Service for Push Notifications
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# Firebase Admin SDK - optional import
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("firebase-admin not installed. Push notifications will be logged only.")


class FirebaseService:
    """Firebase Cloud Messaging service for push notifications"""

    _initialized = False
    _app = None

    # Hardcoded Firebase credentials
    FIREBASE_CREDENTIALS = {
        "type": "service_account",
        "project_id": "bariq-al-yusr",
        "private_key_id": "947d7f14659d087712fd15e20a2dc424e675a4d6",
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCiK8Rqz2KsjkM+\nNEhoh//NrySz0TpmpqzkHEyoCMAIXEME2f3jgb4OpoZoZbOJf9b9NlzNMH2+OE75\n3/ZiOQ86LZwLQby6djAAcjmcdvlcabC6ej1sr+ybdyYkcoy8YeO79j9Ui253Bm1n\nKZ7MWzglwY2mNLn34Nv1WQQ/2bRlTlOuNvkB55p/bhikoncua+PSItCYf7fOjw+u\n2o+o03auNQuD5rJRmWpZFZw47dqPmLxGNMV+Y0ZLQHRnbwT6Gjd6oOuXP/MmfS+i\nizyqQKYH0ehX7+gu+21gUVGgAI5bQXDexWCjNHIiW33cTUSK5l/GFIbJ7HyYIExH\n9V2XAjeNAgMBAAECggEAAnJR8/xxbGyepx0PNHjA5l29/TxPwq57YMu95Rrlx7t6\niVvptfaTzdzPArB1+dVi60DgFPaDVS/bWI4alvAv1BAIDuw0fr0qDZbxYjJoY/dq\nlwAKK5Xid7PX0WxfOmoXd/vg9L4wnKPW3YKj+eu8BNP7mWBrn/B+NtbEJ3Le1J5n\npelgxwj9p1QFrxJF0JHxcvQya6DwI6ZQt9EpCB4k6jHZQmd5cUNOH4MtsuZDbW/m\n9g0OAzJ0T4qTLg8Cy0dSGORgpPvO9ZnCZlk9vjG/qyndGowTugKt/R3M/Z5oOXX8\nA9koIMJAbehyAEPXinzUpZ1JTDmdk+wjzd91E8o1EwKBgQDc79ihGZMfxf7Ktml9\noH1v7tZmqShGLZ0kyepS8LuAP6cGSf6CE+ijEFs0szXj92txJNnkiSrv1VAFqhAJ\nm8ofi4W8w5IqPv6ga9UPOkE54ROZWXzjwVkRzS/Xm3kBap8hlsQGauR3AThmOoCe\n5Dvm/JFFvTuwzkh17Yl4FONdRwKBgQC76GXAju6kfDeA4fllSI5ID/zU4Dw0C47w\n++N1rUN3CFhwcOcgMmsQSOWvFh/3LJRuDcdX0xMMA4JgVb6kF2ewBwIV3XGcneJS\nsSdFiLQXgqEJOcAuDo0tYOI3gtbwbYyjFQgQJ5aRMVEgKkjSwm1q4+KbgzykTP5t\nwcUTr33eiwKBgAL66T0jDyz6irlJRJsBMy/zVMkFtxlbPCdm4dZEkQLl2Obo0JoI\nkrbAXbqUQEHW8IgSKy49+2pIwk+RP64hf9R1GVS2fp47Q0v+qF0QOBkDxDPpVRnt\nXbozvlV2L2epfIQDeJltj69bQNuAJoP+KCCxf3QlXUzBO5D7p0MLZRW5AoGBAKqJ\nEb+eeKrDKURI0aTAIpD4IYe5MioxyzqeACMOakofQtRZQwmPeGdBIWKze7NBvDvd\nOWtVXtXqYWq4ptoZe7rfwV7CqJdxGrPdnzyWAovLvAa5aNbj0fC7GtMyZYuygI6J\nSdYPd7Cxx2Sfu5O7bL4zr7dfdavPTKGj2A4zmNJdAoGBAJWv32WiyGMR1kn9VISb\np9Ua9rBmnqbNIm1P0s0zBNcOkhkBUYE1GnLgOi0yS7gh0JbI2uC8ffmXqXz5+I/q\ncpAfMo2f+/xlvTv88PvbyAQv3SYst/XyTURCBWO5LHZeb8VXxwC4WfEoVPtwqe9L\nQBqHSv5LJdYonG+uH/lhvfUe\n-----END PRIVATE KEY-----\n",
        "client_email": "firebase-adminsdk-fbsvc@bariq-al-yusr.iam.gserviceaccount.com",
        "client_id": "106654875332820506645",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40bariq-al-yusr.iam.gserviceaccount.com",
        "universe_domain": "googleapis.com"
    }

    @classmethod
    def initialize(cls):
        """Initialize Firebase Admin SDK"""
        if cls._initialized:
            return True

        if not FIREBASE_AVAILABLE:
            logger.warning("Firebase Admin SDK not available")
            return False

        try:
            # Use hardcoded credentials first, then fall back to environment variables
            cred = None

            # Try hardcoded credentials first
            try:
                cred = credentials.Certificate(cls.FIREBASE_CREDENTIALS)
                logger.info("Firebase credentials loaded from hardcoded config")
            except Exception as e:
                logger.warning(f"Failed to load hardcoded credentials: {e}")

            # If hardcoded credentials failed, credentials are not available
            if not cred:
                logger.warning("No Firebase credentials available. Push notifications disabled.")
                return False

            cls._app = firebase_admin.initialize_app(cred)
            cls._initialized = True
            logger.info("Firebase Admin SDK initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            return False

    @classmethod
    def send_notification(
        cls,
        token: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None,
        badge_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a single device

        Args:
            token: FCM device token
            title: Notification title
            body: Notification body
            data: Additional data payload (all values must be strings)
            image_url: Optional image URL for rich notifications
            badge_count: iOS badge count

        Returns:
            dict with success status and message_id or error
        """
        if not cls._initialized:
            cls.initialize()

        if not FIREBASE_AVAILABLE or not cls._initialized:
            # Log the notification for debugging
            logger.info(f"[MOCK FCM] Send to {token[:20]}...: {title} - {body}")
            return {
                'success': True,
                'mock': True,
                'message': 'Notification logged (Firebase not configured)'
            }

        try:
            # Build notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )

            # Build Android config
            android_config = messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    click_action='FLUTTER_NOTIFICATION_CLICK'
                )
            )

            # Build iOS config
            apns_config = messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=badge_count
                    )
                )
            )

            # Build message
            message = messaging.Message(
                notification=notification,
                data=data or {},
                token=token,
                android=android_config,
                apns=apns_config
            )

            # Send message
            response = messaging.send(message)
            logger.info(f"FCM message sent successfully: {response}")

            return {
                'success': True,
                'message_id': response
            }

        except messaging.UnregisteredError:
            logger.warning(f"FCM token unregistered: {token[:20]}...")
            return {
                'success': False,
                'error': 'token_unregistered',
                'message': 'Device token is no longer valid'
            }
        except messaging.SenderIdMismatchError:
            logger.error(f"FCM sender ID mismatch for token: {token[:20]}...")
            return {
                'success': False,
                'error': 'sender_mismatch',
                'message': 'Sender ID mismatch'
            }
        except Exception as e:
            logger.error(f"FCM send error: {str(e)}")
            return {
                'success': False,
                'error': 'send_failed',
                'message': str(e)
            }

    @classmethod
    def send_multicast(
        cls,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None,
        image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to multiple devices (using individual sends for FCM v1 API)

        Args:
            tokens: List of FCM device tokens
            title: Notification title
            body: Notification body
            data: Additional data payload
            image_url: Optional image URL

        Returns:
            dict with success count, failure count, and failed tokens
        """
        if not tokens:
            return {
                'success': True,
                'success_count': 0,
                'failure_count': 0,
                'failed_tokens': []
            }

        if not cls._initialized:
            cls.initialize()

        if not FIREBASE_AVAILABLE or not cls._initialized:
            logger.info(f"[MOCK FCM] Multicast to {len(tokens)} devices: {title}")
            return {
                'success': True,
                'mock': True,
                'success_count': len(tokens),
                'failure_count': 0,
                'failed_tokens': []
            }

        success_count = 0
        failure_count = 0
        failed_tokens = []

        # Send to each device individually (FCM v1 API compatible)
        for token in tokens:
            result = cls.send_notification(
                token=token,
                title=title,
                body=body,
                data=data,
                image_url=image_url
            )

            if result.get('success') and not result.get('mock'):
                success_count += 1
                logger.info(f"FCM sent to {token[:30]}...")
            else:
                failure_count += 1
                failed_tokens.append({
                    'token': token,
                    'error': result.get('message', 'Unknown error')
                })
                logger.warning(f"FCM failed for {token[:30]}...: {result.get('message')}")

        logger.info(f"FCM send complete: {success_count} success, {failure_count} failed")

        return {
            'success': True,
            'success_count': success_count,
            'failure_count': failure_count,
            'failed_tokens': failed_tokens
        }

    @classmethod
    def send_to_topic(
        cls,
        topic: str,
        title: str,
        body: str,
        data: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a topic

        Args:
            topic: Topic name (e.g., 'promotions', 'merchant_123')
            title: Notification title
            body: Notification body
            data: Additional data payload

        Returns:
            dict with success status
        """
        if not cls._initialized:
            cls.initialize()

        if not FIREBASE_AVAILABLE or not cls._initialized:
            logger.info(f"[MOCK FCM] Topic '{topic}': {title}")
            return {
                'success': True,
                'mock': True,
                'message': f'Topic notification logged for {topic}'
            }

        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                topic=topic
            )

            response = messaging.send(message)
            logger.info(f"FCM topic message sent: {response}")

            return {
                'success': True,
                'message_id': response
            }

        except Exception as e:
            logger.error(f"FCM topic send error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    @classmethod
    def subscribe_to_topic(cls, tokens: List[str], topic: str) -> Dict[str, Any]:
        """Subscribe devices to a topic"""
        if not cls._initialized:
            cls.initialize()

        if not FIREBASE_AVAILABLE or not cls._initialized:
            logger.info(f"[MOCK FCM] Subscribe {len(tokens)} tokens to topic '{topic}'")
            return {'success': True, 'mock': True}

        try:
            response = messaging.subscribe_to_topic(tokens, topic)
            return {
                'success': True,
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }
        except Exception as e:
            logger.error(f"FCM subscribe error: {str(e)}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def unsubscribe_from_topic(cls, tokens: List[str], topic: str) -> Dict[str, Any]:
        """Unsubscribe devices from a topic"""
        if not cls._initialized:
            cls.initialize()

        if not FIREBASE_AVAILABLE or not cls._initialized:
            logger.info(f"[MOCK FCM] Unsubscribe {len(tokens)} tokens from topic '{topic}'")
            return {'success': True, 'mock': True}

        try:
            response = messaging.unsubscribe_from_topic(tokens, topic)
            return {
                'success': True,
                'success_count': response.success_count,
                'failure_count': response.failure_count
            }
        except Exception as e:
            logger.error(f"FCM unsubscribe error: {str(e)}")
            return {'success': False, 'error': str(e)}


class PushNotificationManager:
    """
    High-level manager for sending push notifications to customers and merchants
    Integrates with device models and notification service
    """

    def __init__(self):
        from app.extensions import db
        from app.models.device import CustomerDevice, MerchantUserDevice
        self.db = db
        self.CustomerDevice = CustomerDevice
        self.MerchantUserDevice = MerchantUserDevice

    def get_customer_tokens(self, customer_id: str) -> List[str]:
        """Get all active FCM tokens for a customer"""
        devices = self.CustomerDevice.query.filter_by(
            customer_id=customer_id,
            is_active=True
        ).all()
        return [d.fcm_token for d in devices]

    def get_merchant_user_tokens(self, merchant_user_id: str) -> List[str]:
        """Get all active FCM tokens for a merchant user"""
        devices = self.MerchantUserDevice.query.filter_by(
            merchant_user_id=merchant_user_id,
            is_active=True
        ).all()
        return [d.fcm_token for d in devices]

    def get_merchant_all_staff_tokens(self, merchant_id: str) -> List[str]:
        """Get FCM tokens for all active staff of a merchant"""
        from app.models.merchant_user import MerchantUser

        # Get all merchant users
        staff = MerchantUser.query.filter_by(
            merchant_id=merchant_id,
            is_active=True
        ).all()

        tokens = []
        for s in staff:
            tokens.extend(self.get_merchant_user_tokens(s.id))
        return tokens

    def send_to_customer(
        self,
        customer_id: str,
        title_ar: str,
        body_ar: str,
        title_en: str = None,
        body_en: str = None,
        data: Dict[str, str] = None,
        notification_type: str = None,
        related_entity_type: str = None,
        related_entity_id: str = None
    ) -> Dict[str, Any]:
        """
        Send push notification to all customer devices
        Also creates an in-app notification record
        """
        from app.services.notification_service import NotificationService

        # Create in-app notification
        NotificationService.create_notification(
            customer_id=customer_id,
            title_ar=title_ar,
            body_ar=body_ar,
            notification_type=notification_type or 'push',
            title_en=title_en,
            body_en=body_en,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )

        # Get customer devices
        tokens = self.get_customer_tokens(customer_id)

        if not tokens:
            return {
                'success': True,
                'message': 'In-app notification created (no devices registered)',
                'push_sent': False
            }

        # Add notification type to data
        push_data = data or {}
        if notification_type:
            push_data['notification_type'] = notification_type
        if related_entity_type:
            push_data['entity_type'] = related_entity_type
        if related_entity_id:
            push_data['entity_id'] = related_entity_id

        # Send push (use Arabic as default)
        result = FirebaseService.send_multicast(
            tokens=tokens,
            title=title_ar,
            body=body_ar,
            data=push_data
        )

        # Handle failed tokens (mark as inactive)
        if result.get('failed_tokens'):
            self._handle_failed_tokens(result['failed_tokens'], 'customer')

        return {
            'success': True,
            'message': 'Notification sent',
            'push_sent': True,
            'devices_reached': result.get('success_count', 0),
            'devices_failed': result.get('failure_count', 0)
        }

    def send_to_merchant_user(
        self,
        merchant_user_id: str,
        title_ar: str,
        body_ar: str,
        title_en: str = None,
        body_en: str = None,
        data: Dict[str, str] = None,
        notification_type: str = None,
        related_entity_type: str = None,
        related_entity_id: str = None
    ) -> Dict[str, Any]:
        """
        Send push notification to a merchant staff member
        Also creates an in-app notification record
        """
        from app.services.notification_service import NotificationService

        # Create in-app notification
        NotificationService.create_staff_notification(
            staff_id=merchant_user_id,
            title_ar=title_ar,
            body_ar=body_ar,
            notification_type=notification_type or 'push',
            title_en=title_en,
            body_en=body_en,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id
        )

        # Get merchant user devices
        tokens = self.get_merchant_user_tokens(merchant_user_id)

        if not tokens:
            return {
                'success': True,
                'message': 'In-app notification created (no devices registered)',
                'push_sent': False
            }

        # Add notification type to data
        push_data = data or {}
        if notification_type:
            push_data['notification_type'] = notification_type
        if related_entity_type:
            push_data['entity_type'] = related_entity_type
        if related_entity_id:
            push_data['entity_id'] = related_entity_id

        # Send push
        result = FirebaseService.send_multicast(
            tokens=tokens,
            title=title_ar,
            body=body_ar,
            data=push_data
        )

        # Handle failed tokens
        if result.get('failed_tokens'):
            self._handle_failed_tokens(result['failed_tokens'], 'merchant')

        return {
            'success': True,
            'message': 'Notification sent',
            'push_sent': True,
            'devices_reached': result.get('success_count', 0),
            'devices_failed': result.get('failure_count', 0)
        }

    def send_to_merchant_all_staff(
        self,
        merchant_id: str,
        title_ar: str,
        body_ar: str,
        title_en: str = None,
        body_en: str = None,
        data: Dict[str, str] = None,
        notification_type: str = None
    ) -> Dict[str, Any]:
        """Send push notification to all staff of a merchant"""
        from app.models.merchant_user import MerchantUser
        from app.services.notification_service import NotificationService

        # Get all staff
        staff = MerchantUser.query.filter_by(
            merchant_id=merchant_id,
            is_active=True
        ).all()

        # Create in-app notifications for all staff
        for s in staff:
            NotificationService.create_staff_notification(
                staff_id=s.id,
                title_ar=title_ar,
                body_ar=body_ar,
                notification_type=notification_type or 'push',
                title_en=title_en,
                body_en=body_en
            )

        # Get all tokens
        tokens = self.get_merchant_all_staff_tokens(merchant_id)

        if not tokens:
            return {
                'success': True,
                'message': f'In-app notifications created for {len(staff)} staff (no devices)',
                'push_sent': False
            }

        # Send push
        push_data = data or {}
        if notification_type:
            push_data['notification_type'] = notification_type

        result = FirebaseService.send_multicast(
            tokens=tokens,
            title=title_ar,
            body=body_ar,
            data=push_data
        )

        if result.get('failed_tokens'):
            self._handle_failed_tokens(result['failed_tokens'], 'merchant')

        return {
            'success': True,
            'message': f'Notification sent to {len(staff)} staff',
            'push_sent': True,
            'devices_reached': result.get('success_count', 0),
            'devices_failed': result.get('failure_count', 0)
        }

    def _handle_failed_tokens(self, failed_tokens: List, device_type: str):
        """Mark failed tokens as inactive"""
        try:
            for failed in failed_tokens:
                token = failed.get('token') if isinstance(failed, dict) else failed
                error = failed.get('error', '') if isinstance(failed, dict) else ''

                # Only deactivate for unregistered tokens
                if 'Unregistered' in str(error) or 'NotRegistered' in str(error):
                    if device_type == 'customer':
                        self.CustomerDevice.query.filter_by(
                            fcm_token=token
                        ).update({'is_active': False})
                    else:
                        self.MerchantUserDevice.query.filter_by(
                            fcm_token=token
                        ).update({'is_active': False})

            self.db.session.commit()
        except Exception as e:
            logger.error(f"Error handling failed tokens: {str(e)}")
            self.db.session.rollback()


# Global instance
push_manager = PushNotificationManager()
