"""
Brilliant Directories Form Webhook Handler
Receives issuer onboarding form submissions and triggers document generation
"""

import json
import hashlib
import hmac
from typing import Dict, Any

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from rest_framework import status

from .models import Issuer, SECFormType, SECDocumentTemplate
from .serializers import IssuerCreateSerializer
from .document_generator import generator


def verify_bd_signature(payload: str, signature: str) -> bool:
    """
    Verify webhook signature from Brilliant Directories
    
    Args:
        payload: Raw request body
        signature: X-BD-Signature header value
    
    Returns:
        True if signature is valid
    """
    secret = getattr(settings, 'BD_WEBHOOK_SECRET', None)
    
    if not secret:
        # Development mode - skip verification
        return True
    
    # Calculate expected signature
    expected_signature = hmac.new(
        secret.encode('utf-8'),
        payload.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)


def map_bd_to_issuer(bd_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map Brilliant Directories form fields to Issuer model fields
    
    Reference: BD_FORM_JSON_MAPPING.md
    """
    
    # Basic company info
    issuer_data = {
        'company_name': bd_data.get('company_name') or bd_data.get('business_name'),
        'security_name': bd_data.get('security_name') or bd_data.get('token_name'),
        'isin': bd_data.get('isin'),
        'price_per_token': bd_data.get('price_per_token') or bd_data.get('token_price'),
        'total_offering': bd_data.get('total_offering') or bd_data.get('offering_amount'),
        'min_investment': bd_data.get('min_investment') or bd_data.get('minimum_investment'),
        'description': bd_data.get('description') or bd_data.get('company_description'),
    }
    
    # URLs
    issuer_data['logo'] = bd_data.get('logo_url')
    issuer_data['website'] = bd_data.get('website')
    issuer_data['linkedin'] = bd_data.get('linkedin_url')
    issuer_data['twitter'] = bd_data.get('twitter_url')
    issuer_data['youtube'] = bd_data.get('youtube_url')
    issuer_data['facebook'] = bd_data.get('facebook_url')
    issuer_data['instagram'] = bd_data.get('instagram_url')
    
    # Payment rails
    issuer_data['paypal_account'] = bd_data.get('paypal_email')
    
    # Wire transfer details (nested in BD form)
    wire_data = bd_data.get('wire_transfer', {})
    if wire_data:
        issuer_data['wire_bank_name'] = wire_data.get('bank_name')
        issuer_data['wire_account_number'] = wire_data.get('account_number')
        issuer_data['wire_routing_number'] = wire_data.get('routing_number')
        issuer_data['wire_swift_code'] = wire_data.get('swift_code')
    
    issuer_data['crypto_merchant_id'] = bd_data.get('crypto_merchant_id')
    
    # Document URLs
    issuer_data['doc_prospectus'] = bd_data.get('prospectus_url')
    issuer_data['doc_terms'] = bd_data.get('terms_url')
    issuer_data['doc_risks'] = bd_data.get('risk_disclosures_url')
    issuer_data['doc_subscription'] = bd_data.get('subscription_agreement_url')
    
    # SEC form data (additional structured data)
    sec_form_data = {}
    
    if 'cik' in bd_data:
        sec_form_data['cik'] = bd_data['cik']
    
    if 'industry' in bd_data:
        sec_form_data['industry_group'] = bd_data['industry']
    
    if 'revenue_range' in bd_data:
        sec_form_data['revenue_range'] = bd_data['revenue_range']
    
    # Related persons (directors, officers)
    if 'officers' in bd_data:
        sec_form_data['officers'] = bd_data['officers']
    
    if 'related_persons' in bd_data:
        sec_form_data['related_persons'] = bd_data['related_persons']
    
    # Use of proceeds
    if 'use_of_proceeds' in bd_data:
        sec_form_data['use_of_proceeds'] = bd_data['use_of_proceeds']
    
    if sec_form_data:
        issuer_data['sec_form_data'] = sec_form_data
    
    return issuer_data


@csrf_exempt
@require_http_methods(["POST"])
def bd_form_submission(request):
    """
    Webhook endpoint for Brilliant Directories form submissions
    
    POST /api/webhooks/bd-form-submission/
    
    Headers:
        X-BD-Signature: HMAC-SHA256 signature
    
    Body: JSON with BD form data
    
    Returns:
        201: Issuer created successfully
        400: Invalid data
        401: Invalid signature
        500: Server error
    """
    
    try:
        # Verify signature
        signature = request.headers.get('X-BD-Signature', '')
        if not verify_bd_signature(request.body.decode('utf-8'), signature):
            return JsonResponse({
                'error': 'Invalid signature',
                'status': 'error'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Parse JSON payload
        try:
            bd_data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Invalid JSON',
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Map BD fields to Issuer model
        issuer_data = map_bd_to_issuer(bd_data)
        
        # Validate with serializer
        serializer = IssuerCreateSerializer(data=issuer_data)
        if not serializer.is_valid():
            return JsonResponse({
                'error': 'Validation failed',
                'errors': serializer.errors,
                'status': 'error'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create issuer
        issuer = serializer.save()
        
        # Generate documents based on form type
        form_type = bd_data.get('form_type', 'FORM_D')
        auto_generate = bd_data.get('auto_generate_documents', True)
        
        generated_docs = []
        
        if auto_generate:
            try:
                if form_type == 'FORM_D':
                    pdf_bytes = generator.generate_form_d(issuer, save=True)
                    generated_docs.append('Form D')
                    
                elif form_type == 'FORM_C':
                    pdf_bytes = generator.generate_form_c(issuer, save=True)
                    generated_docs.append('Form C')
                
                # Upload to Adobe Cloud if configured
                adobe_enabled = bd_data.get('upload_to_adobe', False)
                if adobe_enabled and generated_docs:
                    adobe_url = generator.upload_to_adobe(
                        pdf_bytes,
                        f"{form_type.lower()}-{issuer.slug}.pdf",
                        issuer
                    )
                    if adobe_url:
                        generated_docs.append(f'Uploaded to Adobe: {adobe_url}')
                
            except Exception as e:
                print(f"⚠️  Document generation failed: {e}")
                # Continue - issuer created successfully even if docs failed
        
        # Send confirmation email via Omnisend (if configured)
        omnisend_enabled = getattr(settings, 'OMNISEND_API_KEY', None)
        if omnisend_enabled:
            try:
                send_onboarding_confirmation_email(issuer, bd_data.get('contact_email'))
            except Exception as e:
                print(f"⚠️  Email notification failed: {e}")
        
        # Success response
        return JsonResponse({
            'status': 'success',
            'issuer': {
                'id': issuer.id,
                'slug': issuer.slug,
                'company_name': issuer.company_name,
                'isin': issuer.isin,
                'offering_page_url': issuer.offering_page_url,
            },
            'generated_documents': generated_docs,
            'message': 'Issuer created successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def send_onboarding_confirmation_email(issuer: Issuer, email: str):
    """
    Send confirmation email via Omnisend
    
    TODO: Implement Omnisend API integration
    """
    import requests
    
    api_key = getattr(settings, 'OMNISEND_API_KEY', None)
    if not api_key:
        return
    
    url = 'https://api.omnisend.com/v3/emails'
    
    headers = {
        'X-API-Key': api_key,
        'Content-Type': 'application/json'
    }
    
    payload = {
        'to': email,
        'from': {
            'email': 'noreply@dpoecosystem.com',
            'name': 'DPO Ecosystem'
        },
        'subject': f'Welcome to DPO Ecosystem - {issuer.company_name}',
        'body': f"""
        <html>
        <body>
            <h2>Welcome to DPO Ecosystem!</h2>
            <p>Your issuer profile has been created successfully.</p>
            
            <h3>Company Details:</h3>
            <ul>
                <li><strong>Company:</strong> {issuer.company_name}</li>
                <li><strong>ISIN:</strong> {issuer.isin}</li>
                <li><strong>Offering Amount:</strong> ${issuer.total_offering:,.2f}</li>
            </ul>
            
            <h3>Next Steps:</h3>
            <ol>
                <li>Review your offering page: <a href="{issuer.offering_page_url}">{issuer.offering_page_url}</a></li>
                <li>Review and sign your SEC documents</li>
                <li>Configure payment rails</li>
                <li>Launch your offering!</li>
            </ol>
            
            <p>Questions? Contact support@dpoecosystem.com</p>
        </body>
        </html>
        """
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print(f"✅ Confirmation email sent to {email}")
    else:
        print(f"❌ Email failed: {response.status_code}")
