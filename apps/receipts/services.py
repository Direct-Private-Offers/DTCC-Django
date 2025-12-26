import os
from io import BytesIO
from decimal import Decimal
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from apps.notifications.services import create_notification

from .models import Receipt


class ReceiptGenerator:
    """Generate PDF receipts for token distribution events"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        self.styles.add(ParagraphStyle(
            name='ReceiptTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a1a1a'),
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReceiptHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            alignment=TA_LEFT
        ))
        
        self.styles.add(ParagraphStyle(
            name='ReceiptBody',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.HexColor('#666666'),
            spaceAfter=8,
            alignment=TA_LEFT
        ))
    
    def generate_issuance_receipt(self, receipt: Receipt, investor_name: str, issuer_name: str) -> BytesIO:
        """Generate PDF receipt for token issuance"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Title
        story.append(Paragraph("TOKEN ISSUANCE RECEIPT", self.styles['ReceiptTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt ID and Date
        receipt_data = [
            ['Receipt ID:', receipt.receipt_id],
            ['Date:', receipt.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')],
        ]
        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(receipt_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Investor Information
        story.append(Paragraph("Investor Information", self.styles['ReceiptHeader']))
        investor_data = [
            ['Name:', investor_name],
            ['User ID:', str(receipt.investor.id)],
        ]
        investor_table = Table(investor_data, colWidths=[2*inch, 4*inch])
        investor_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(investor_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Transaction Details
        story.append(Paragraph("Transaction Details", self.styles['ReceiptHeader']))
        transaction_data = [
            ['Transaction ID:', str(receipt.transaction_id)],
            ['ISIN:', receipt.isin or 'N/A'],
            ['Quantity:', f"{receipt.quantity:,.18f}" if receipt.quantity else 'N/A'],
            ['Amount:', f"{receipt.amount:,.2f} {receipt.currency}" if receipt.amount else 'N/A'],
            ['Issuer:', issuer_name],
        ]
        transaction_table = Table(transaction_data, colWidths=[2*inch, 4*inch])
        transaction_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(transaction_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"This is an automated receipt generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}. " \
                      f"For questions, please contact support."
        story.append(Paragraph(footer_text, self.styles['ReceiptBody']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_transfer_receipt(self, receipt: Receipt, from_name: str, to_name: str) -> BytesIO:
        """Generate PDF receipt for token transfer"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Title
        story.append(Paragraph("TOKEN TRANSFER RECEIPT", self.styles['ReceiptTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt ID and Date
        receipt_data = [
            ['Receipt ID:', receipt.receipt_id],
            ['Date:', receipt.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')],
        ]
        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(receipt_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Transfer Details
        story.append(Paragraph("Transfer Details", self.styles['ReceiptHeader']))
        transfer_data = [
            ['Transaction ID:', str(receipt.transaction_id)],
            ['From:', from_name],
            ['To:', to_name],
            ['ISIN:', receipt.isin or 'N/A'],
            ['Quantity:', f"{receipt.quantity:,.18f}" if receipt.quantity else 'N/A'],
        ]
        transfer_table = Table(transfer_data, colWidths=[2*inch, 4*inch])
        transfer_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(transfer_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"This is an automated receipt generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}."
        story.append(Paragraph(footer_text, self.styles['ReceiptBody']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_settlement_receipt(self, receipt: Receipt, buyer_name: str, seller_name: str) -> BytesIO:
        """Generate PDF receipt for settlement"""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.5*inch, bottomMargin=0.5*inch)
        story = []
        
        # Title
        story.append(Paragraph("SETTLEMENT RECEIPT", self.styles['ReceiptTitle']))
        story.append(Spacer(1, 0.2*inch))
        
        # Receipt ID and Date
        receipt_data = [
            ['Receipt ID:', receipt.receipt_id],
            ['Date:', receipt.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')],
        ]
        receipt_table = Table(receipt_data, colWidths=[2*inch, 4*inch])
        receipt_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        story.append(receipt_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Settlement Details
        story.append(Paragraph("Settlement Details", self.styles['ReceiptHeader']))
        settlement_data = [
            ['Transaction ID:', str(receipt.transaction_id)],
            ['Buyer:', buyer_name],
            ['Seller:', seller_name],
            ['ISIN:', receipt.isin or 'N/A'],
            ['Quantity:', f"{receipt.quantity:,.18f}" if receipt.quantity else 'N/A'],
            ['Amount:', f"{receipt.amount:,.2f} {receipt.currency}" if receipt.amount else 'N/A'],
        ]
        settlement_table = Table(settlement_data, colWidths=[2*inch, 4*inch])
        settlement_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        story.append(settlement_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Footer
        story.append(Spacer(1, 0.5*inch))
        footer_text = f"This is an automated settlement receipt generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')}."
        story.append(Paragraph(footer_text, self.styles['ReceiptBody']))
        
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def generate_receipt(self, receipt: Receipt, **kwargs) -> BytesIO:
        """Generate receipt based on type"""
        if receipt.receipt_type == 'ISSUANCE':
            return self.generate_issuance_receipt(
                receipt,
                investor_name=kwargs.get('investor_name', receipt.investor.username),
                issuer_name=kwargs.get('issuer_name', 'Issuer')
            )
        elif receipt.receipt_type == 'TRANSFER':
            return self.generate_transfer_receipt(
                receipt,
                from_name=kwargs.get('from_name', 'Sender'),
                to_name=kwargs.get('to_name', 'Recipient')
            )
        elif receipt.receipt_type == 'SETTLEMENT':
            return self.generate_settlement_receipt(
                receipt,
                buyer_name=kwargs.get('buyer_name', 'Buyer'),
                seller_name=kwargs.get('seller_name', 'Seller')
            )
        else:
            raise ValueError(f"Unknown receipt type: {receipt.receipt_type}")


def create_receipt(
    receipt_type: str,
    investor: 'User',
    transaction_id: str,
    isin: str = None,
    quantity: Decimal = None,
    amount: Decimal = None,
    currency: str = 'USD',
    metadata: dict = None
) -> Receipt:
    """Create and generate receipt for a transaction"""
    import uuid as uuid_lib
    
    receipt_id = f"RCPT-{receipt_type[:3]}-{uuid_lib.uuid4().hex[:12].upper()}"
    
    receipt = Receipt.objects.create(
        receipt_id=receipt_id,
        receipt_type=receipt_type,
        investor=investor,
        transaction_id=uuid_lib.UUID(transaction_id),
        isin=isin,
        quantity=quantity,
        amount=amount,
        currency=currency,
        metadata=metadata or {}
    )
    
    # Generate PDF
    generator = ReceiptGenerator()
    pdf_buffer = generator.generate_receipt(receipt, **metadata or {})
    
    # Save PDF file
    filename = f"{receipt_id}.pdf"
    receipt.pdf_file.save(filename, ContentFile(pdf_buffer.read()), save=True)
    
    # Send email notification with receipt
    try:
        create_notification(
            user=investor,
            event_type=f'RECEIPT_{receipt_type}',
            notification_type='EMAIL',
            context={
                'receipt_id': receipt_id,
                'receipt_type': receipt_type,
                'transaction_id': str(transaction_id),
                'isin': isin or 'N/A',
                'quantity': str(quantity) if quantity else 'N/A',
                'amount': str(amount) if amount else 'N/A',
                'currency': currency,
            },
        )
    except Exception as email_error:
        # Log but don't fail receipt creation if email fails
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to send receipt email notification: {str(email_error)}")
    
    return receipt
