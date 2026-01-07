"""
Issuer API Views
Handles issuer onboarding, offering page generation, and data retrieval.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Issuer, IssuerDocument
from .serializers import (
    IssuerCreateSerializer,
    IssuerResponseSerializer,
    IssuerListSerializer,
    IssuerDocumentSerializer,
)


class IssuerViewSet(viewsets.ModelViewSet):
    """
    API endpoints for issuer management.
    
    POST /api/issuers/ - Create new issuer from BD form data
    GET /api/issuers/ - List all issuers
    GET /api/issuers/{slug}/ - Get issuer details by slug
    PATCH /api/issuers/{slug}/ - Update issuer
    DELETE /api/issuers/{slug}/ - Delete issuer
    """
    
    queryset = Issuer.objects.all()
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return IssuerCreateSerializer
        elif self.action == 'list':
            return IssuerListSerializer
        return IssuerResponseSerializer
    
    def get_permissions(self):
        """
        Allow public read access to offering pages (for embedding).
        Require auth for create/update/delete.
        """
        if self.action in ['retrieve', 'offering_data']:
            return [AllowAny()]
        return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        """
        Create new issuer from BD form submission.
        
        Request body matches BD_FORM_JSON_MAPPING.md structure.
        Returns issuer ID, slug, and offering_page_url.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        issuer = serializer.save()
        
        # Return response with offering page URL
        response_serializer = IssuerResponseSerializer(issuer)
        
        return Response(
            {
                'success': True,
                'message': f'Issuer "{issuer.company_name}" created successfully',
                'data': response_serializer.data,
            },
            status=status.HTTP_201_CREATED
        )
    
    def retrieve(self, request, *args, **kwargs):
        """
        Get issuer details by slug.
        Public endpoint - returns data formatted for offering template.
        """
        issuer = self.get_object()
        serializer = IssuerResponseSerializer(issuer)
        
        return Response(serializer.data)
    
    def update(self, request, *args, **kwargs):
        """Update issuer (PATCH /api/issuers/{slug}/)"""
        partial = kwargs.pop('partial', True)
        issuer = self.get_object()
        
        serializer = IssuerCreateSerializer(issuer, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        response_serializer = IssuerResponseSerializer(issuer)
        
        return Response({
            'success': True,
            'message': f'Issuer "{issuer.company_name}" updated successfully',
            'data': response_serializer.data,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def publish(self, request, slug=None):
        """
        Publish issuer offering (make it live).
        POST /api/issuers/{slug}/publish/
        """
        issuer = self.get_object()
        
        if issuer.status == 'active':
            return Response({
                'success': False,
                'message': 'Offering is already published',
            }, status=status.HTTP_400_BAD_REQUEST)
        
        issuer.status = 'active'
        issuer.published_at = timezone.now()
        issuer.save()
        
        return Response({
            'success': True,
            'message': f'Offering for "{issuer.company_name}" is now live',
            'offering_page_url': issuer.offering_page_url,
        })
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def pause(self, request, slug=None):
        """
        Pause issuer offering.
        POST /api/issuers/{slug}/pause/
        """
        issuer = self.get_object()
        issuer.status = 'paused'
        issuer.save()
        
        return Response({
            'success': True,
            'message': f'Offering for "{issuer.company_name}" has been paused',
        })
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def offering_data(self, request, slug=None):
        """
        Get offering data in exact format expected by ISSUER_OFFERING_TEMPLATE.html
        GET /api/issuers/{slug}/offering_data/
        
        This endpoint is called by the JavaScript in the offering template.
        """
        issuer = self.get_object()
        
        # Format data to match template's expected structure
        data = {
            'companyName': issuer.company_name,
            'logo': issuer.logo or 'https://via.placeholder.com/200x80?text=Company+Logo',
            'securityName': issuer.security_name,
            'isin': issuer.isin,
            'pricePerToken': float(issuer.price_per_token),
            'totalOffering': float(issuer.total_offering),
            'minInvestment': float(issuer.min_investment),
            'website': issuer.website,
            'linkedin': issuer.linkedin,
            'twitter': issuer.twitter,
            'youtube': issuer.youtube,
            'facebook': issuer.facebook,
            'instagram': issuer.instagram,
            'paypalAccount': issuer.paypal_account,
            'wireAccount': issuer.wire_account_details,
            'cryptoMerchantId': issuer.crypto_merchant_id,
            'docs': issuer.documents,
            'description': issuer.description,
        }
        
        return Response(data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated])
    def documents(self, request, slug=None):
        """
        List all generated documents for an issuer.
        GET /api/issuers/{slug}/documents/
        """
        issuer = self.get_object()
        documents = issuer.documents.all()
        serializer = IssuerDocumentSerializer(documents, many=True)
        
        return Response({
            'success': True,
            'count': documents.count(),
            'data': serializer.data,
        })


class IssuerDocumentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoints for generated issuer documents.
    
    GET /api/documents/ - List all documents
    GET /api/documents/{id}/ - Get document details
    """
    
    queryset = IssuerDocument.objects.all()
    serializer_class = IssuerDocumentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by issuer if provided"""
        queryset = super().get_queryset()
        issuer_slug = self.request.query_params.get('issuer', None)
        
        if issuer_slug:
            queryset = queryset.filter(issuer__slug=issuer_slug)
        
        return queryset
