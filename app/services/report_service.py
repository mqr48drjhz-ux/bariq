"""
Report Service - Full Implementation
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app import db
from app.models.customer import Customer
from app.models.merchant import Merchant
from app.models.transaction import Transaction
from app.models.payment import Payment
from app.models.settlement import Settlement


class ReportService:
    """Report service with full database implementation"""

    @staticmethod
    def get_merchant_summary(merchant_id, branch_id=None, from_date=None, to_date=None):
        """Get merchant summary report"""
        try:
            query = Transaction.query.filter_by(merchant_id=merchant_id)

            if branch_id:
                query = query.filter_by(branch_id=branch_id)

            if from_date:
                query = query.filter(Transaction.created_at >= from_date)
            if to_date:
                query = query.filter(Transaction.created_at <= to_date)

            transactions = query.all()

            total_amount = sum(float(t.total_amount or 0) for t in transactions)
            paid_amount = sum(float(t.paid_amount or 0) for t in transactions)
            cancelled = [t for t in transactions if t.status == 'cancelled']
            returns_amount = sum(float(t.total_amount or 0) for t in cancelled)

            return {
                'success': True,
                'data': {
                    'total_transactions': len(transactions),
                    'total_amount': total_amount,
                    'paid_amount': paid_amount,
                    'total_returns': len(cancelled),
                    'returns_amount': returns_amount,
                    'net_amount': total_amount - returns_amount,
                }
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def get_transaction_report(merchant_id, branch_id=None, from_date=None, to_date=None, group_by='day'):
        """Get transaction report grouped by period"""
        try:
            query = Transaction.query.filter_by(merchant_id=merchant_id)

            if branch_id:
                query = query.filter_by(branch_id=branch_id)

            if from_date:
                query = query.filter(Transaction.created_at >= from_date)
            if to_date:
                query = query.filter(Transaction.created_at <= to_date)

            transactions = query.order_by(Transaction.created_at).all()

            # Group by date
            grouped = {}
            for t in transactions:
                if group_by == 'day':
                    key = t.created_at.strftime('%Y-%m-%d')
                elif group_by == 'week':
                    key = t.created_at.strftime('%Y-W%W')
                elif group_by == 'month':
                    key = t.created_at.strftime('%Y-%m')
                else:
                    key = t.created_at.strftime('%Y-%m-%d')

                if key not in grouped:
                    grouped[key] = {'date': key, 'count': 0, 'amount': 0, 'paid': 0}
                grouped[key]['count'] += 1
                grouped[key]['amount'] += float(t.total_amount or 0)
                grouped[key]['paid'] += float(t.paid_amount or 0)

            return {
                'success': True,
                'data': {
                    'data': list(grouped.values())
                }
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def get_admin_overview(from_date=None, to_date=None, report_type='overview'):
        """Get admin overview report"""
        try:
            # Parse dates
            if from_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d') if isinstance(from_date, str) else from_date
            else:
                from_date = datetime.utcnow() - timedelta(days=30)

            if to_date:
                to_date = datetime.strptime(to_date, '%Y-%m-%d') if isinstance(to_date, str) else to_date
            else:
                to_date = datetime.utcnow()

            # Query transactions in range
            transactions = Transaction.query.filter(
                Transaction.created_at >= from_date,
                Transaction.created_at <= to_date
            ).all()

            # Query payments in range
            payments = Payment.query.filter(
                Payment.created_at >= from_date,
                Payment.created_at <= to_date
            ).all()

            # Build report based on type
            if report_type == 'transactions':
                return ReportService._build_transactions_report(transactions, from_date, to_date)
            elif report_type == 'customers':
                return ReportService._build_customers_report(from_date, to_date)
            elif report_type == 'merchants':
                return ReportService._build_merchants_report(from_date, to_date)
            else:
                return ReportService._build_overview_report(transactions, payments, from_date, to_date)
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @staticmethod
    def _build_overview_report(transactions, payments, from_date, to_date):
        """Build general overview report"""
        total_transactions = len(transactions)
        total_revenue = sum(float(t.total_amount or 0) for t in transactions)
        total_payments = sum(float(p.amount or 0) for p in payments if p.status == 'completed')

        # Status breakdown
        status_counts = {}
        for t in transactions:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1

        return {
            'success': True,
            'data': {
                'total_transactions': total_transactions,
                'total_revenue': total_revenue,
                'total_payments': total_payments,
                'paid_transactions': status_counts.get('paid', 0),
                'pending_transactions': status_counts.get('pending', 0) + status_counts.get('confirmed', 0),
                'overdue_transactions': status_counts.get('overdue', 0),
                'cancelled_transactions': status_counts.get('cancelled', 0)
            }
        }

    @staticmethod
    def _build_transactions_report(transactions, from_date, to_date):
        """Build transactions report"""
        # Status breakdown
        status_counts = {}
        overdue_amount = 0
        max_transaction = 0
        total_amount = 0

        for t in transactions:
            status_counts[t.status] = status_counts.get(t.status, 0) + 1
            amount = float(t.total_amount or 0)
            total_amount += amount
            if amount > max_transaction:
                max_transaction = amount
            if t.status == 'overdue':
                overdue_amount += float(t.remaining_amount or 0)

        avg_transaction = total_amount / len(transactions) if transactions else 0

        # Daily breakdown
        daily = {}
        for t in transactions:
            day = t.created_at.strftime('%Y-%m-%d')
            if day not in daily:
                daily[day] = {'date': day, 'count': 0, 'amount': 0}
            daily[day]['count'] += 1
            daily[day]['amount'] += float(t.total_amount or 0)

        return {
            'success': True,
            'data': {
                'total_transactions': len(transactions),
                'paid_transactions': status_counts.get('paid', 0),
                'pending_transactions': status_counts.get('pending', 0) + status_counts.get('confirmed', 0),
                'overdue_transactions': status_counts.get('overdue', 0),
                'cancelled_transactions': status_counts.get('cancelled', 0),
                'overdue_amount': overdue_amount,
                'max_transaction': max_transaction,
                'avg_transaction_value': avg_transaction,
                'daily_transactions': sorted(daily.values(), key=lambda x: x['date'])
            }
        }

    @staticmethod
    def _build_customers_report(from_date, to_date):
        """Build customers report"""
        # Total customers
        total_customers = Customer.query.count()
        active_customers = Customer.query.filter_by(status='active').count()
        pending_customers = Customer.query.filter_by(status='pending').count()
        suspended_customers = Customer.query.filter_by(status='suspended').count()

        # New customers in range
        new_customers = Customer.query.filter(
            Customer.created_at >= from_date,
            Customer.created_at <= to_date
        ).count()

        # Credit utilization
        total_credit = db.session.query(func.sum(Customer.credit_limit)).scalar() or 0
        total_debt = Transaction.query.filter(
            Transaction.status.in_(['confirmed', 'pending', 'overdue'])
        ).with_entities(func.sum(Transaction.total_amount - Transaction.paid_amount - Transaction.returned_amount)).scalar() or 0
        credit_utilization = (float(total_debt) / float(total_credit) * 100) if total_credit > 0 else 0

        # Top customers
        top_customers = db.session.query(
            Customer,
            func.count(Transaction.id).label('transactions_count'),
            func.sum(Transaction.total_amount).label('total_amount'),
            func.sum(Transaction.paid_amount).label('paid_amount')
        ).join(Transaction, Customer.id == Transaction.customer_id)\
         .filter(Transaction.created_at >= from_date)\
         .group_by(Customer.id)\
         .order_by(func.sum(Transaction.total_amount).desc())\
         .limit(10).all()

        top_customers_data = []
        for c, count, total, paid in top_customers:
            payment_rate = (float(paid or 0) / float(total or 1)) * 100
            top_customers_data.append({
                'bariq_id': c.bariq_id,
                'full_name_ar': c.full_name_ar,
                'transactions_count': count,
                'total_amount': float(total or 0),
                'payment_rate': payment_rate
            })

        # Customer growth
        growth = {}
        new_custs = Customer.query.filter(
            Customer.created_at >= from_date,
            Customer.created_at <= to_date
        ).all()
        for c in new_custs:
            day = c.created_at.strftime('%Y-%m-%d')
            if day not in growth:
                growth[day] = {'date': day, 'count': 0}
            growth[day]['count'] += 1

        return {
            'success': True,
            'data': {
                'total_customers': total_customers,
                'active_customers': active_customers,
                'pending_customers': pending_customers,
                'suspended_customers': suspended_customers,
                'new_customers': new_customers,
                'credit_utilization': credit_utilization,
                'top_customers': top_customers_data,
                'customer_growth': sorted(growth.values(), key=lambda x: x['date'])
            }
        }

    @staticmethod
    def _build_merchants_report(from_date, to_date):
        """Build merchants report"""
        # Total merchants
        total_merchants = Merchant.query.count()
        active_merchants = Merchant.query.filter_by(status='active').count()
        pending_merchants = Merchant.query.filter_by(status='pending').count()

        # Total branches
        from app.models.branch import Branch
        total_branches = Branch.query.count()

        # Top merchants
        top_merchants = db.session.query(
            Merchant,
            func.count(Transaction.id).label('transactions_count'),
            func.sum(Transaction.total_amount).label('total_sales')
        ).join(Transaction, Merchant.id == Transaction.merchant_id)\
         .filter(Transaction.created_at >= from_date)\
         .group_by(Merchant.id)\
         .order_by(func.sum(Transaction.total_amount).desc())\
         .limit(10).all()

        top_merchants_data = []
        for m, count, sales in top_merchants:
            commission = float(sales or 0) * float(m.commission_rate or 2.5) / 100
            top_merchants_data.append({
                'name_ar': m.name_ar,
                'business_type': m.business_type,
                'transactions_count': count,
                'total_sales': float(sales or 0),
                'total_commission': commission
            })

        # Business type distribution
        business_types = db.session.query(
            Merchant.business_type,
            func.count(Merchant.id)
        ).group_by(Merchant.business_type).all()
        business_types_dict = {bt or 'Other': count for bt, count in business_types}

        return {
            'success': True,
            'data': {
                'total_merchants': total_merchants,
                'active_merchants': active_merchants,
                'pending_merchants': pending_merchants,
                'total_branches': total_branches,
                'top_merchants': top_merchants_data,
                'business_types': business_types_dict
            }
        }

    @staticmethod
    def get_financial_report(from_date=None, to_date=None):
        """Get financial report"""
        try:
            # Parse dates
            if from_date:
                from_date = datetime.strptime(from_date, '%Y-%m-%d') if isinstance(from_date, str) else from_date
            else:
                from_date = datetime.utcnow() - timedelta(days=30)

            if to_date:
                to_date = datetime.strptime(to_date, '%Y-%m-%d') if isinstance(to_date, str) else to_date
            else:
                to_date = datetime.utcnow()

            # Query transactions
            transactions = Transaction.query.filter(
                Transaction.created_at >= from_date,
                Transaction.created_at <= to_date
            ).all()

            # Query completed payments
            payments = Payment.query.filter(
                Payment.created_at >= from_date,
                Payment.created_at <= to_date,
                Payment.status == 'completed'
            ).all()

            # Calculate totals
            total_revenue = sum(float(t.total_amount or 0) for t in transactions)
            total_paid = sum(float(p.amount or 0) for p in payments)

            # Calculate commission
            commission_by_merchant = {}
            for t in transactions:
                if t.merchant_id not in commission_by_merchant:
                    merchant = Merchant.query.get(t.merchant_id)
                    rate = float(merchant.commission_rate or 2.5) if merchant else 2.5
                    commission_by_merchant[t.merchant_id] = rate
                rate = commission_by_merchant[t.merchant_id]
                # Commission is calculated on paid amount

            total_commission = sum(float(t.paid_amount or 0) * 0.025 for t in transactions)  # Simplified

            # Outstanding debt
            outstanding = Transaction.query.filter(
                Transaction.status.in_(['confirmed', 'pending', 'overdue'])
            ).with_entities(func.sum(Transaction.total_amount - Transaction.paid_amount - Transaction.returned_amount)).scalar() or 0

            collection_rate = (total_paid / total_revenue * 100) if total_revenue > 0 else 0

            # Daily breakdown
            daily = {}
            for t in transactions:
                day = t.created_at.strftime('%Y-%m-%d')
                if day not in daily:
                    daily[day] = {'date': day, 'transactions_count': 0, 'revenue': 0, 'payments': 0, 'commission': 0}
                daily[day]['transactions_count'] += 1
                daily[day]['revenue'] += float(t.total_amount or 0)
                daily[day]['commission'] += float(t.paid_amount or 0) * 0.025

            for p in payments:
                day = p.created_at.strftime('%Y-%m-%d')
                if day in daily:
                    daily[day]['payments'] += float(p.amount or 0)

            # Payment method breakdown
            payment_methods = {}
            for p in payments:
                method = p.payment_method or 'other'
                payment_methods[method] = payment_methods.get(method, 0) + float(p.amount or 0)

            return {
                'success': True,
                'data': {
                    'total_revenue': total_revenue,
                    'total_commission': total_commission,
                    'outstanding_debt': float(outstanding),
                    'collection_rate': collection_rate,
                    'daily_breakdown': sorted(daily.values(), key=lambda x: x['date']),
                    'payment_methods': payment_methods
                }
            }
        except Exception as e:
            return {'success': False, 'message': str(e)}
