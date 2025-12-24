"""
Reporting and analytics endpoints.
"""
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from apps.core.responses import ok, bad_request
from apps.core.permissions import IsInGroup
from apps.dex.models import Order, Trade, Swap
from apps.settlement.models import Settlement
from apps.issuance.models import IssuanceEvent
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse
from apps.core.schemas import ERROR_401, ERROR_403
import logging

logger = logging.getLogger(__name__)


class TradingReportView(APIView):
    """Trading activity reports."""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=["Reports"],
        summary="Get trading report",
        description="Get trading activity report with volume and statistics.",
        parameters=[
            OpenApiParameter(name="start_date", location=OpenApiParameter.QUERY, type=str, required=False),
            OpenApiParameter(name="end_date", location=OpenApiParameter.QUERY, type=str, required=False),
            OpenApiParameter(name="isin", location=OpenApiParameter.QUERY, type=str, required=False),
        ],
        responses={200: OpenApiResponse(description="Trading report")}
    )
    def get(self, request: Request):
        """Get trading report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        isin = request.query_params.get('isin')
        
        # Default to last 30 days
        if not end_date:
            end_date = timezone.now()
        else:
            end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        trades = Trade.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        orders = Order.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        
        if isin:
            trades = trades.filter(isin=isin)
            orders = orders.filter(isin=isin)
        
        total_volume = trades.aggregate(total=Sum('total_value'))['total'] or 0
        total_trades = trades.count()
        total_orders = orders.count()
        
        return ok({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'statistics': {
                'total_trades': total_trades,
                'total_orders': total_orders,
                'total_volume': str(total_volume),
                'average_trade_value': str(total_volume / total_trades) if total_trades > 0 else '0',
            },
            'isin': isin,
        })


class SettlementReportView(APIView):
    """Settlement activity reports."""
    permission_classes = [IsAuthenticated, IsInGroup.with_names(["ops", "issuer"])]
    
    @extend_schema(
        tags=["Reports"],
        summary="Get settlement report",
        description="Get settlement activity report. Requires 'ops' or 'issuer' group.",
        parameters=[
            OpenApiParameter(name="start_date", location=OpenApiParameter.QUERY, type=str, required=False),
            OpenApiParameter(name="end_date", location=OpenApiParameter.QUERY, type=str, required=False),
            OpenApiParameter(name="status", location=OpenApiParameter.QUERY, type=str, required=False),
        ],
        responses={200: OpenApiResponse(description="Settlement report")}
    )
    def get(self, request: Request):
        """Get settlement report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        status_filter = request.query_params.get('status')
        
        if not end_date:
            end_date = timezone.now()
        else:
            end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        settlements = Settlement.objects.filter(created_at__gte=start_date, created_at__lte=end_date)
        
        if status_filter:
            settlements = settlements.filter(status=status_filter)
        
        total_quantity = settlements.aggregate(total=Sum('quantity'))['total'] or 0
        by_status = settlements.values('status').annotate(count=Count('id'))
        
        return ok({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'statistics': {
                'total_settlements': settlements.count(),
                'total_quantity': str(total_quantity),
                'by_status': {item['status']: item['count'] for item in by_status},
            },
        })


class IssuanceReportView(APIView):
    """Token issuance reports."""
    permission_classes = [IsAuthenticated, IsInGroup.with_names(["ops", "issuer"])]
    
    @extend_schema(
        tags=["Reports"],
        summary="Get issuance report",
        description="Get token issuance activity report. Requires 'ops' or 'issuer' group.",
        parameters=[
            OpenApiParameter(name="start_date", location=OpenApiParameter.QUERY, type=str, required=False),
            OpenApiParameter(name="end_date", location=OpenApiParameter.QUERY, type=str, required=False),
            OpenApiParameter(name="isin", location=OpenApiParameter.QUERY, type=str, required=False),
        ],
        responses={200: OpenApiResponse(description="Issuance report")}
    )
    def get(self, request: Request):
        """Get issuance report."""
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        isin = request.query_params.get('isin')
        
        if not end_date:
            end_date = timezone.now()
        else:
            end_date = timezone.datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        if not start_date:
            start_date = end_date - timedelta(days=30)
        else:
            start_date = timezone.datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        
        events = IssuanceEvent.objects.filter(
            created_at__gte=start_date,
            created_at__lte=end_date,
            processed=True
        )
        
        if isin:
            events = events.filter(isin=isin)
        
        total_amount = events.aggregate(total=Sum('amount'))['total'] or 0
        unique_investors = events.values('investor_address').distinct().count()
        
        return ok({
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
            },
            'statistics': {
                'total_issuances': events.count(),
                'total_amount': str(total_amount),
                'unique_investors': unique_investors,
            },
            'isin': isin,
        })

