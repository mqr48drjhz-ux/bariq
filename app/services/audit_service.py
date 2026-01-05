"""
Audit Service - Full Implementation
"""
from datetime import datetime
from app import db
from app.models.audit_log import AuditLog


class AuditService:
    """Audit service with full database implementation"""

    @staticmethod
    def get_audit_logs(actor_type=None, action=None, from_date=None, page=1, per_page=20):
        """Get audit logs with filters"""
        try:
            query = AuditLog.query

            if actor_type:
                query = query.filter(AuditLog.actor_type == actor_type)

            if action:
                query = query.filter(AuditLog.action == action)

            if from_date:
                if isinstance(from_date, str):
                    from_date = datetime.strptime(from_date, '%Y-%m-%d')
                query = query.filter(AuditLog.created_at >= from_date)

            query = query.order_by(AuditLog.created_at.desc())
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)

            return {
                'success': True,
                'data': {
                    'logs': [log.to_dict() for log in pagination.items],
                    'pagination': {
                        'page': page,
                        'per_page': per_page,
                        'total': pagination.total,
                        'pages': pagination.pages
                    }
                }
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def log_action(actor_type, actor_id, action, entity_type=None, entity_id=None,
                   old_values=None, new_values=None, metadata=None, details=None):
        """Log an action to the audit trail"""
        try:
            log = AuditLog(
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                old_values=old_values,
                new_values=new_values,
                extra_data=details or metadata
            )
            db.session.add(log)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Audit log error: {e}")
            return False
