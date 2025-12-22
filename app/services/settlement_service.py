"""
Settlement Service - Full Implementation
"""
from datetime import datetime, timedelta
from flask import current_app
from app.extensions import db
from app.models.settlement import Settlement
from app.models.transaction import Transaction
from app.models.transaction_return import TransactionReturn
from app.models.merchant import Merchant
from app.models.branch import Branch


class SettlementService:
    """Settlement service for merchant payment cycles"""

    # ==================== Merchant Views ====================

    @staticmethod
    def get_merchant_settlements(merchant_id, branch_id=None, status=None, page=1, per_page=20):
        """Get settlements for a merchant"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        query = Settlement.query.filter_by(merchant_id=merchant_id)

        if branch_id:
            query = query.filter_by(branch_id=branch_id)

        if status:
            query = query.filter_by(status=status)

        query = query.order_by(Settlement.period_end.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        settlements_data = []
        for settlement in pagination.items:
            settlement_dict = settlement.to_dict()
            settlement_dict['branch'] = {
                'id': settlement.branch.id,
                'name_ar': settlement.branch.name_ar,
                'city': settlement.branch.city
            }
            settlements_data.append(settlement_dict)

        return {
            'success': True,
            'data': {
                'settlements': settlements_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def get_settlement_details(merchant_id, settlement_id):
        """Get settlement details for merchant"""
        settlement = Settlement.query.filter_by(
            id=settlement_id,
            merchant_id=merchant_id
        ).first()

        if not settlement:
            return {
                'success': False,
                'message': 'Settlement not found',
                'error_code': 'STL_001'
            }

        settlement_dict = settlement.to_dict()
        settlement_dict['branch'] = settlement.branch.to_dict()
        settlement_dict['merchant'] = {
            'id': settlement.merchant.id,
            'name_ar': settlement.merchant.name_ar,
            'commission_rate': float(settlement.merchant.commission_rate)
        }

        # Get transactions in this settlement
        transactions = Transaction.query.filter_by(settlement_id=settlement_id).all()
        settlement_dict['transactions'] = [
            {
                'id': t.id,
                'reference_number': t.reference_number,
                'total_amount': float(t.total_amount),
                'returned_amount': float(t.returned_amount),
                'transaction_date': t.transaction_date.isoformat() if t.transaction_date else None,
                'status': t.status
            }
            for t in transactions
        ]

        return {
            'success': True,
            'data': {
                'settlement': settlement_dict
            }
        }

    @staticmethod
    def get_pending_settlement_amount(merchant_id, branch_id=None):
        """Get pending settlement amount for merchant/branch"""
        query = Transaction.query.filter(
            Transaction.merchant_id == merchant_id,
            Transaction.settlement_id == None,
            Transaction.status.in_(['paid', 'confirmed', 'overdue'])
        )

        if branch_id:
            query = query.filter_by(branch_id=branch_id)

        # Calculate gross amount (confirmed transactions)
        gross_amount = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.total_amount), 0)
        ).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.settlement_id == None,
            Transaction.status.in_(['paid', 'confirmed', 'overdue'])
        )

        if branch_id:
            gross_amount = gross_amount.filter(Transaction.branch_id == branch_id)

        gross_amount = gross_amount.scalar()

        # Calculate returns
        returns_amount = db.session.query(
            db.func.coalesce(db.func.sum(Transaction.returned_amount), 0)
        ).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.settlement_id == None,
            Transaction.status.in_(['paid', 'confirmed', 'overdue'])
        )

        if branch_id:
            returns_amount = returns_amount.filter(Transaction.branch_id == branch_id)

        returns_amount = returns_amount.scalar()

        # Get commission rate
        merchant = Merchant.query.get(merchant_id)
        commission_rate = float(merchant.commission_rate) if merchant else 2.5

        net_amount = float(gross_amount) - float(returns_amount)
        commission = net_amount * (commission_rate / 100)
        final_amount = net_amount - commission

        transaction_count = query.count()

        return {
            'success': True,
            'data': {
                'gross_amount': float(gross_amount) if gross_amount else 0,
                'returns_amount': float(returns_amount) if returns_amount else 0,
                'commission_rate': commission_rate,
                'commission_amount': commission,
                'net_amount': final_amount,
                'transaction_count': transaction_count
            }
        }

    # ==================== Admin Views ====================

    @staticmethod
    def get_all_settlements(status=None, merchant_id=None, page=1, per_page=20):
        """Get all settlements for admin"""
        query = Settlement.query

        if status:
            query = query.filter_by(status=status)

        if merchant_id:
            query = query.filter_by(merchant_id=merchant_id)

        query = query.order_by(Settlement.created_at.desc())
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        settlements_data = []
        for settlement in pagination.items:
            settlement_dict = settlement.to_dict()
            settlement_dict['merchant'] = {
                'id': settlement.merchant.id,
                'name_ar': settlement.merchant.name_ar
            }
            settlement_dict['branch'] = {
                'id': settlement.branch.id,
                'name_ar': settlement.branch.name_ar
            }
            settlements_data.append(settlement_dict)

        return {
            'success': True,
            'data': {
                'settlements': settlements_data
            },
            'meta': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'total_pages': pagination.pages
            }
        }

    @staticmethod
    def get_settlement_details_admin(settlement_id):
        """Get settlement details for admin"""
        settlement = Settlement.query.get(settlement_id)

        if not settlement:
            return {
                'success': False,
                'message': 'Settlement not found',
                'error_code': 'STL_001'
            }

        settlement_dict = settlement.to_dict()
        settlement_dict['merchant'] = settlement.merchant.to_dict()
        settlement_dict['branch'] = settlement.branch.to_dict()

        # Get bank info
        settlement_dict['bank_info'] = {
            'bank_name': settlement.merchant.bank_name,
            'iban': settlement.merchant.iban,
            'account_holder_name': settlement.merchant.account_holder_name
        }

        # Get transactions
        transactions = Transaction.query.filter_by(settlement_id=settlement_id).all()
        settlement_dict['transactions'] = [
            {
                'id': t.id,
                'reference_number': t.reference_number,
                'total_amount': float(t.total_amount),
                'returned_amount': float(t.returned_amount),
                'transaction_date': t.transaction_date.isoformat() if t.transaction_date else None,
                'customer': {
                    'id': t.customer.id,
                    'name_ar': t.customer.full_name_ar
                }
            }
            for t in transactions
        ]

        return {
            'success': True,
            'data': {
                'settlement': settlement_dict
            }
        }

    # ==================== Settlement Processing ====================

    @staticmethod
    def create_settlement(merchant_id, branch_id, period_start, period_end):
        """Create a new settlement for a branch"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        branch = Branch.query.filter_by(id=branch_id, merchant_id=merchant_id).first()

        if not branch:
            return {
                'success': False,
                'message': 'Branch not found',
                'error_code': 'MERCH_005'
            }

        # Get unsettled transactions for this period
        transactions = Transaction.query.filter(
            Transaction.merchant_id == merchant_id,
            Transaction.branch_id == branch_id,
            Transaction.settlement_id == None,
            Transaction.status.in_(['paid', 'confirmed', 'overdue']),
            Transaction.transaction_date >= period_start,
            Transaction.transaction_date <= period_end
        ).all()

        if not transactions:
            return {
                'success': False,
                'message': 'No transactions found for this period',
                'error_code': 'STL_002'
            }

        # Calculate amounts
        gross_amount = sum(float(t.total_amount) for t in transactions)
        returns_amount = sum(float(t.returned_amount) for t in transactions)
        net_before_commission = gross_amount - returns_amount

        commission_rate = float(merchant.commission_rate)
        commission_amount = net_before_commission * (commission_rate / 100)
        net_amount = net_before_commission - commission_amount

        # Count returns
        return_count = TransactionReturn.query.join(Transaction).filter(
            Transaction.merchant_id == merchant_id,
            Transaction.branch_id == branch_id,
            TransactionReturn.created_at >= period_start,
            TransactionReturn.created_at <= period_end
        ).count()

        try:
            # Create settlement
            settlement = Settlement(
                merchant_id=merchant_id,
                branch_id=branch_id,
                period_start=period_start,
                period_end=period_end,
                gross_amount=gross_amount,
                returns_amount=returns_amount,
                commission_amount=commission_amount,
                net_amount=net_amount,
                transaction_count=len(transactions),
                return_count=return_count,
                status='pending'
            )

            db.session.add(settlement)
            db.session.flush()

            # Link transactions to settlement
            for txn in transactions:
                txn.settlement_id = settlement.id
                txn.updated_at = datetime.utcnow()

            db.session.commit()

            return {
                'success': True,
                'message': 'Settlement created successfully',
                'data': {
                    'settlement': settlement.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to create settlement: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def generate_weekly_settlements():
        """Generate weekly settlements for all branches (called by scheduler)"""
        today = datetime.utcnow().date()
        week_start = today - timedelta(days=today.weekday() + 7)  # Last week Monday
        week_end = week_start + timedelta(days=6)  # Last week Sunday

        # Get all active branches with weekly settlement cycle
        branches = Branch.query.filter_by(
            is_active=True,
            settlement_cycle='weekly'
        ).all()

        created_count = 0
        for branch in branches:
            result = SettlementService.create_settlement(
                merchant_id=branch.merchant_id,
                branch_id=branch.id,
                period_start=week_start,
                period_end=week_end
            )
            if result.get('success'):
                created_count += 1

        return {
            'success': True,
            'message': f'Created {created_count} settlements for period {week_start} to {week_end}'
        }

    # ==================== Settlement Approval ====================

    @staticmethod
    def approve_settlement(settlement_id, admin_id):
        """Approve a settlement for transfer"""
        settlement = Settlement.query.get(settlement_id)

        if not settlement:
            return {
                'success': False,
                'message': 'Settlement not found',
                'error_code': 'STL_001'
            }

        if settlement.status != 'pending':
            return {
                'success': False,
                'message': f'Cannot approve settlement with status: {settlement.status}',
                'error_code': 'STL_003'
            }

        try:
            settlement.status = 'approved'
            settlement.approved_by = admin_id
            settlement.approved_at = datetime.utcnow()
            settlement.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='settlement.approved',
                entity_type='settlement',
                entity_id=settlement_id,
                old_values={'status': 'pending'},
                new_values={'status': 'approved'}
            )

            return {
                'success': True,
                'message': 'Settlement approved successfully',
                'data': {
                    'settlement': settlement.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to approve settlement: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def mark_as_transferred(settlement_id, transfer_reference, admin_id):
        """Mark settlement as transferred"""
        settlement = Settlement.query.get(settlement_id)

        if not settlement:
            return {
                'success': False,
                'message': 'Settlement not found',
                'error_code': 'STL_001'
            }

        if settlement.status != 'approved':
            return {
                'success': False,
                'message': f'Cannot mark as transferred. Current status: {settlement.status}',
                'error_code': 'STL_003'
            }

        try:
            settlement.status = 'transferred'
            settlement.transfer_reference = transfer_reference
            settlement.transferred_at = datetime.utcnow()
            settlement.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='settlement.transferred',
                entity_type='settlement',
                entity_id=settlement_id,
                old_values={'status': 'approved'},
                new_values={'status': 'transferred', 'transfer_reference': transfer_reference}
            )

            return {
                'success': True,
                'message': 'Settlement marked as transferred',
                'data': {
                    'settlement': settlement.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to update settlement: {str(e)}',
                'error_code': 'SYS_001'
            }

    @staticmethod
    def reject_settlement(settlement_id, reason, admin_id):
        """Reject a settlement"""
        settlement = Settlement.query.get(settlement_id)

        if not settlement:
            return {
                'success': False,
                'message': 'Settlement not found',
                'error_code': 'STL_001'
            }

        if settlement.status not in ['pending', 'approved']:
            return {
                'success': False,
                'message': f'Cannot reject settlement with status: {settlement.status}',
                'error_code': 'STL_003'
            }

        old_status = settlement.status

        try:
            settlement.status = 'rejected'
            settlement.updated_at = datetime.utcnow()

            # Unlink transactions from this settlement
            transactions = Transaction.query.filter_by(settlement_id=settlement_id).all()
            for txn in transactions:
                txn.settlement_id = None
                txn.updated_at = datetime.utcnow()

            db.session.commit()

            # Log the action
            from app.services.audit_service import AuditService
            AuditService.log_action(
                actor_type='admin_user',
                actor_id=admin_id,
                action='settlement.rejected',
                entity_type='settlement',
                entity_id=settlement_id,
                old_values={'status': old_status},
                new_values={'status': 'rejected', 'reason': reason}
            )

            return {
                'success': True,
                'message': 'Settlement rejected',
                'data': {
                    'settlement': settlement.to_dict()
                }
            }
        except Exception as e:
            db.session.rollback()
            return {
                'success': False,
                'message': f'Failed to reject settlement: {str(e)}',
                'error_code': 'SYS_001'
            }

    # ==================== Statistics ====================

    @staticmethod
    def get_settlement_statistics(from_date=None, to_date=None):
        """Get settlement statistics for admin dashboard"""
        query = Settlement.query

        if from_date:
            query = query.filter(Settlement.created_at >= from_date)

        if to_date:
            query = query.filter(Settlement.created_at <= to_date)

        # Total settlements
        total_count = query.count()

        # By status
        pending_count = query.filter_by(status='pending').count()
        approved_count = query.filter_by(status='approved').count()
        transferred_count = query.filter_by(status='transferred').count()

        # Total amounts
        total_gross = db.session.query(
            db.func.coalesce(db.func.sum(Settlement.gross_amount), 0)
        ).filter(Settlement.status == 'transferred')
        if from_date:
            total_gross = total_gross.filter(Settlement.created_at >= from_date)
        if to_date:
            total_gross = total_gross.filter(Settlement.created_at <= to_date)
        total_gross = total_gross.scalar()

        total_commission = db.session.query(
            db.func.coalesce(db.func.sum(Settlement.commission_amount), 0)
        ).filter(Settlement.status == 'transferred')
        if from_date:
            total_commission = total_commission.filter(Settlement.created_at >= from_date)
        if to_date:
            total_commission = total_commission.filter(Settlement.created_at <= to_date)
        total_commission = total_commission.scalar()

        total_transferred = db.session.query(
            db.func.coalesce(db.func.sum(Settlement.net_amount), 0)
        ).filter(Settlement.status == 'transferred')
        if from_date:
            total_transferred = total_transferred.filter(Settlement.created_at >= from_date)
        if to_date:
            total_transferred = total_transferred.filter(Settlement.created_at <= to_date)
        total_transferred = total_transferred.scalar()

        # Pending amount
        pending_amount = db.session.query(
            db.func.coalesce(db.func.sum(Settlement.net_amount), 0)
        ).filter(Settlement.status.in_(['pending', 'approved']))
        if from_date:
            pending_amount = pending_amount.filter(Settlement.created_at >= from_date)
        if to_date:
            pending_amount = pending_amount.filter(Settlement.created_at <= to_date)
        pending_amount = pending_amount.scalar()

        return {
            'success': True,
            'data': {
                'total_settlements': total_count,
                'by_status': {
                    'pending': pending_count,
                    'approved': approved_count,
                    'transferred': transferred_count
                },
                'amounts': {
                    'total_gross': float(total_gross) if total_gross else 0,
                    'total_commission': float(total_commission) if total_commission else 0,
                    'total_transferred': float(total_transferred) if total_transferred else 0,
                    'pending_amount': float(pending_amount) if pending_amount else 0
                }
            }
        }

    @staticmethod
    def get_merchant_settlement_summary(merchant_id):
        """Get settlement summary for a merchant"""
        merchant = Merchant.query.get(merchant_id)

        if not merchant:
            return {
                'success': False,
                'message': 'Merchant not found',
                'error_code': 'MERCH_001'
            }

        # Total transferred
        total_transferred = db.session.query(
            db.func.coalesce(db.func.sum(Settlement.net_amount), 0)
        ).filter(
            Settlement.merchant_id == merchant_id,
            Settlement.status == 'transferred'
        ).scalar()

        # Pending settlements
        pending_settlements = Settlement.query.filter(
            Settlement.merchant_id == merchant_id,
            Settlement.status.in_(['pending', 'approved'])
        ).all()

        pending_amount = sum(float(s.net_amount) for s in pending_settlements)

        # Latest settlement
        latest_settlement = Settlement.query.filter_by(
            merchant_id=merchant_id
        ).order_by(Settlement.created_at.desc()).first()

        return {
            'success': True,
            'data': {
                'total_transferred': float(total_transferred) if total_transferred else 0,
                'pending_amount': pending_amount,
                'pending_count': len(pending_settlements),
                'latest_settlement': latest_settlement.to_dict() if latest_settlement else None
            }
        }
