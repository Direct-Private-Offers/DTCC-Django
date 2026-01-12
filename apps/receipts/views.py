from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiResponse
from django.http import FileResponse
from django.contrib.auth.models import User

from apps.core.responses import ok, bad_request, not_found
from apps.core.permissions import IsAuthenticated
from .models import Receipt
from .serializers import ReceiptSerializer, ReceiptCreateSerializer
from .services import create_receipt

logger = __import__('logging').getLogger(__name__)


class ReceiptView(APIView):
    """Receipt management endpoints"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Generate receipt",
        description="Generate a receipt for a transaction",
        request=ReceiptCreateSerializer,
        responses={200: ReceiptSerializer}
    )
    def post(self, request):
        """Generate receipt for transaction"""
        serializer = ReceiptCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return bad_request(serializer.errors)
        
        data = serializer.validated_data
        
        # Create receipt
        receipt = create_receipt(
            receipt_type=data['receipt_type'],
            investor=request.user,
            transaction_id=str(data['transaction_id']),
            isin=data.get('isin'),
            quantity=data.get('quantity'),
            amount=data.get('amount'),
            currency=data.get('currency', 'USD'),
            metadata=data.get('metadata', {})
        )
        
        return ok(ReceiptSerializer(receipt, context={'request': request}).data)
    
    @extend_schema(
        summary="List receipts",
        description="List receipts for authenticated user",
        responses={200: ReceiptSerializer(many=True)}
    )
    def get(self, request):
        """List user receipts"""
        receipt_type = request.query_params.get('type')
        transaction_id = request.query_params.get('transaction_id')
        
        queryset = Receipt.objects.filter(investor=request.user)
        
        if receipt_type:
            queryset = queryset.filter(receipt_type=receipt_type)
        if transaction_id:
            queryset = queryset.filter(transaction_id=transaction_id)
        
        queryset = queryset.order_by('-created_at')
        
        serializer = ReceiptSerializer(queryset, many=True, context={'request': request})
        return ok(serializer.data)


class ReceiptDetailView(APIView):
    """Receipt detail and download"""
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        summary="Get receipt details",
        responses={200: ReceiptSerializer}
    )
    def get(self, request, receipt_id):
        """Get receipt details"""
        try:
            receipt = Receipt.objects.get(id=receipt_id, investor=request.user)
            serializer = ReceiptSerializer(receipt, context={'request': request})
            return ok(serializer.data)
        except Receipt.DoesNotExist:
            return not_found("Receipt not found")
    
    @extend_schema(
        summary="Download receipt PDF",
        responses={200: OpenApiResponse(description="PDF file")}
    )
    def post(self, request, receipt_id):
        """Download receipt PDF"""
        try:
            receipt = Receipt.objects.get(id=receipt_id, investor=request.user)
            
            if not receipt.pdf_file:
                return bad_request("Receipt PDF not available")
            
            return FileResponse(
                receipt.pdf_file.open('rb'),
                content_type='application/pdf',
                filename=f"{receipt.receipt_id}.pdf"
            )
        except Receipt.DoesNotExist:
            return not_found("Receipt not found")
