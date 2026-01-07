"""
Adobe Document Cloud Integration
Handles PDF uploads, e-signature workflows, and document management
"""

import requests
import base64
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from django.conf import settings


class AdobeCloudClient:
    """
    Adobe PDF Services API and Adobe Sign API client
    
    Features:
    - Upload PDF documents
    - Create signature agreements
    - Track signature status
    - Download signed documents
    """
    
    def __init__(self):
        self.client_id = getattr(settings, 'ADOBE_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'ADOBE_CLIENT_SECRET', None)
        self.api_key = getattr(settings, 'ADOBE_API_KEY', None)
        
        # API endpoints
        self.pdf_services_base = 'https://pdf-services.adobe.io'
        self.sign_base = 'https://api.na1.adobesign.com/api/rest/v6'
        
        self._access_token = None
        self._token_expires_at = None
    
    def authenticate(self) -> str:
        """
        Get OAuth2 access token for Adobe APIs
        
        Returns:
            Access token
        """
        
        # Check if we have a valid cached token
        if self._access_token and self._token_expires_at:
            if datetime.now() < self._token_expires_at:
                return self._access_token
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Adobe credentials not configured")
        
        # OAuth2 token endpoint
        url = 'https://ims-na1.adobelogin.com/ims/token/v3'
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'openid,AdobeID,read_organizations,additional_info.projectedProductContext'
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self._access_token = token_data['access_token']
        
        # Cache token (expires in 24 hours, refresh after 23)
        self._token_expires_at = datetime.now() + timedelta(hours=23)
        
        return self._access_token
    
    def upload_pdf(self, pdf_bytes: bytes, filename: str) -> str:
        """
        Upload PDF to Adobe Document Cloud
        
        Args:
            pdf_bytes: PDF file content
            filename: File name
        
        Returns:
            Document ID or upload URI
        """
        
        token = self.authenticate()
        
        # Step 1: Create upload session
        upload_url = f'{self.pdf_services_base}/assets'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json'
        }
        
        # Request upload URI
        upload_request = {
            'mediaType': 'application/pdf',
            'filename': filename
        }
        
        response = requests.post(upload_url, headers=headers, json=upload_request)
        response.raise_for_status()
        
        upload_data = response.json()
        asset_id = upload_data.get('assetID')
        upload_uri = upload_data.get('uploadUri')
        
        # Step 2: Upload PDF to the URI
        upload_headers = {
            'Content-Type': 'application/pdf'
        }
        
        response = requests.put(upload_uri, headers=upload_headers, data=pdf_bytes)
        response.raise_for_status()
        
        print(f"✅ Uploaded to Adobe: {asset_id}")
        
        return asset_id
    
    def create_agreement(
        self,
        pdf_bytes: bytes,
        filename: str,
        signer_email: str,
        signer_name: str,
        agreement_name: str,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create an Adobe Sign agreement (e-signature workflow)
        
        Args:
            pdf_bytes: PDF content
            filename: File name
            signer_email: Email of person who needs to sign
            signer_name: Full name of signer
            agreement_name: Name for the agreement
            message: Optional message to signer
        
        Returns:
            Agreement data with ID and signing URL
        """
        
        token = self.authenticate()
        
        # Step 1: Upload transient document
        transient_url = f'{self.sign_base}/transientDocuments'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-API-Key': self.api_key
        }
        
        files = {
            'File': (filename, pdf_bytes, 'application/pdf')
        }
        
        data = {
            'File-Name': filename
        }
        
        response = requests.post(transient_url, headers=headers, files=files, data=data)
        response.raise_for_status()
        
        transient_data = response.json()
        transient_doc_id = transient_data['transientDocumentId']
        
        # Step 2: Create agreement
        agreement_url = f'{self.sign_base}/agreements'
        
        headers['Content-Type'] = 'application/json'
        
        agreement_payload = {
            'fileInfos': [
                {
                    'transientDocumentId': transient_doc_id
                }
            ],
            'name': agreement_name,
            'participantSetsInfo': [
                {
                    'memberInfos': [
                        {
                            'email': signer_email,
                            'name': signer_name
                        }
                    ],
                    'order': 1,
                    'role': 'SIGNER'
                }
            ],
            'signatureType': 'ESIGN',
            'state': 'IN_PROCESS',
            'message': message or f'Please review and sign {agreement_name}'
        }
        
        response = requests.post(agreement_url, headers=headers, json=agreement_payload)
        response.raise_for_status()
        
        agreement_data = response.json()
        agreement_id = agreement_data['id']
        
        # Step 3: Get signing URL
        signing_url = self.get_signing_url(agreement_id, signer_email)
        
        print(f"✅ Created Adobe Sign agreement: {agreement_id}")
        
        return {
            'agreement_id': agreement_id,
            'signing_url': signing_url,
            'status': 'IN_PROCESS'
        }
    
    def get_signing_url(self, agreement_id: str, signer_email: str) -> str:
        """
        Get signing URL for a specific participant
        
        Args:
            agreement_id: Agreement ID
            signer_email: Email of signer
        
        Returns:
            Signing URL
        """
        
        token = self.authenticate()
        
        url = f'{self.sign_base}/agreements/{agreement_id}/signingUrls'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-API-Key': self.api_key
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        urls_data = response.json()
        signing_url_set = urls_data.get('signingUrlSetInfos', [])
        
        if signing_url_set:
            for url_info in signing_url_set:
                signing_urls = url_info.get('signingUrls', [])
                for signing_url_data in signing_urls:
                    if signing_url_data.get('email') == signer_email:
                        return signing_url_data.get('esignUrl')
        
        return None
    
    def get_agreement_status(self, agreement_id: str) -> Dict[str, Any]:
        """
        Check status of an agreement
        
        Args:
            agreement_id: Agreement ID
        
        Returns:
            Status information
        """
        
        token = self.authenticate()
        
        url = f'{self.sign_base}/agreements/{agreement_id}'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-API-Key': self.api_key
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        agreement_data = response.json()
        
        return {
            'agreement_id': agreement_id,
            'status': agreement_data.get('status'),
            'name': agreement_data.get('name'),
            'signed_date': agreement_data.get('signedDate'),
            'participants': agreement_data.get('participantSetsInfo', [])
        }
    
    def download_signed_document(self, agreement_id: str) -> bytes:
        """
        Download signed PDF
        
        Args:
            agreement_id: Agreement ID
        
        Returns:
            PDF bytes
        """
        
        token = self.authenticate()
        
        url = f'{self.sign_base}/agreements/{agreement_id}/combinedDocument'
        
        headers = {
            'Authorization': f'Bearer {token}',
            'X-API-Key': self.api_key
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        return response.content


# Singleton instance
adobe_client = AdobeCloudClient()


def upload_and_sign(
    pdf_bytes: bytes,
    filename: str,
    signer_email: str,
    signer_name: str,
    agreement_name: str
) -> Dict[str, Any]:
    """
    Convenience function to upload PDF and create signature agreement
    
    Returns:
        Agreement data with signing URL
    """
    
    try:
        agreement = adobe_client.create_agreement(
            pdf_bytes=pdf_bytes,
            filename=filename,
            signer_email=signer_email,
            signer_name=signer_name,
            agreement_name=agreement_name
        )
        
        return agreement
        
    except Exception as e:
        print(f"❌ Adobe Sign failed: {e}")
        return None
