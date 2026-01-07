"""
SEC Document Generator Service
Generates Form D, Form C, PPM, and other SEC documents from Issuer data
"""

import os
import io
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

from django.conf import settings
from django.template.loader import get_template
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Try WeasyPrint first, fall back to reportlab
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    PDF_ENGINE = 'weasyprint'
except (ImportError, OSError):
    # WeasyPrint not available or missing GTK on Windows
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_LEFT, TA_CENTER
    from xhtml2pdf import pisa
    PDF_ENGINE = 'reportlab'

from .models import (
    Issuer, IssuerDocument, SECDocumentTemplate,
    FieldMappingRule, FieldDefinition
)


class DocumentGenerator:
    """Generates SEC compliance documents from templates"""
    
    def __init__(self):
        self.template_dir = Path(settings.BASE_DIR) / 'templates' / 'sec_forms'
        self.template_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup Jinja2 environment
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=select_autoescape(['html', 'xml']),
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # PDF engine configuration
        if PDF_ENGINE == 'weasyprint':
            self.font_config = FontConfiguration()
            print("✅ Using WeasyPrint for PDF generation")
        else:
            print("✅ Using xhtml2pdf (pisa) for PDF generation")
    
    def get_template_context(self, issuer: Issuer, template: SECDocumentTemplate) -> Dict[str, Any]:
        """
        Build template context from issuer data using field mapping rules
        """
        context = {}
        
        # Get all mapping rules for this template
        rules = FieldMappingRule.objects.filter(
            template=template,
            is_active=True
        ).select_related('source_field').order_by('-priority')
        
        for rule in rules:
            try:
                value = self._resolve_field_value(issuer, rule)
                context[rule.template_variable] = value
            except Exception as e:
                print(f"Warning: Failed to resolve {rule.template_variable}: {e}")
                context[rule.template_variable] = rule.fallback_value or ''
        
        # Add standard context variables
        context.update({
            'issuer': issuer,
            'generated_date': datetime.now().strftime('%B %d, %Y'),
            'generated_datetime': datetime.now(),
        })
        
        return context
    
    def _resolve_field_value(self, issuer: Issuer, rule: FieldMappingRule) -> Any:
        """Resolve a field value based on mapping rule"""
        
        if rule.transformation_type == 'DIRECT':
            # Direct field access
            if rule.source_field:
                field_path = rule.source_field.field_path
                parts = field_path.split('.')
                
                value = issuer
                for part in parts[1:]:  # Skip 'issuer' prefix
                    value = getattr(value, part)
                
                # Apply formatting if needed
                if rule.apply_formatting and rule.source_field.format_template:
                    return self._format_value(value, rule.source_field)
                
                return value
        
        elif rule.transformation_type == 'CONCATENATE':
            # Concatenate multiple fields
            source_fields = rule.source_fields.all()
            values = []
            for field in source_fields:
                field_path = field.field_path
                parts = field_path.split('.')
                value = issuer
                for part in parts[1:]:
                    value = getattr(value, part, '')
                if value:
                    values.append(str(value))
            return ' '.join(values)
        
        elif rule.transformation_type == 'CONDITIONAL':
            # Conditional logic
            if rule.conditions:
                # Simple conditional support
                condition_field = rule.conditions.get('field')
                condition_value = rule.conditions.get('value')
                then_value = rule.conditions.get('then')
                else_value = rule.conditions.get('else')
                
                if condition_field:
                    actual_value = getattr(issuer, condition_field, None)
                    if actual_value == condition_value:
                        return then_value
                    else:
                        return else_value
        
        return rule.fallback_value or ''
    
    def _format_value(self, value: Any, field_def: FieldDefinition) -> str:
        """Format a value according to field definition"""
        
        if field_def.data_type == 'CURRENCY':
            if isinstance(value, (int, float)):
                return f'${value:,.2f}'
        
        elif field_def.data_type == 'PERCENTAGE':
            if isinstance(value, (int, float)):
                return f'{value:.2f}%'
        
        elif field_def.data_type == 'DATE':
            if hasattr(value, 'strftime'):
                return value.strftime('%B %d, %Y')
        
        return str(value)
    
    def generate_html(self, issuer: Issuer, template: SECDocumentTemplate) -> str:
        """Generate HTML document from template"""
        
        # Get template context
        context = self.get_template_context(issuer, template)
        
        # Load and render template
        if template.template_file_path and os.path.exists(template.template_file_path):
            # Load from file
            jinja_template = self.jinja_env.get_template(os.path.basename(template.template_file_path))
        else:
            # Render from database content
            jinja_template = self.jinja_env.from_string(template.template_content)
        
        html_content = jinja_template.render(**context)
        return html_content
    
    def generate_pdf(
        self, 
        issuer: Issuer, 
        template: SECDocumentTemplate,
        save_to_disk: bool = True
    ) -> bytes:
        """
        Generate PDF document from template
        
        Returns PDF bytes and optionally saves to disk
        """
        
        # Generate HTML first
        html_content = self.generate_html(issuer, template)
        
        # Convert to PDF based on available engine
        if PDF_ENGINE == 'weasyprint':
            html = HTML(string=html_content)
            pdf_bytes = html.write_pdf(font_config=self.font_config)
        else:
            # Use xhtml2pdf (pisa)
            result_file = io.BytesIO()
            pisa_status = pisa.CreatePDF(
                io.BytesIO(html_content.encode('utf-8')),
                dest=result_file
            )
            
            if pisa_status.err:
                raise Exception(f"PDF generation failed: {pisa_status.err}")
            
            pdf_bytes = result_file.getvalue()
        
        if save_to_disk:
            # Save to media directory
            media_dir = Path(settings.MEDIA_ROOT) / 'sec_documents' / issuer.slug
            media_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            doc_type = template.form_type.form_type.lower().replace('_', '-')
            timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            filename = f"{doc_type}-{timestamp}.pdf"
            filepath = media_dir / filename
            
            # Write PDF
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            
            # Calculate file hash
            file_hash = hashlib.sha256(pdf_bytes).hexdigest()
            
            # Prepare generation data (exclude non-serializable objects)
            generation_context = self.get_template_context(issuer, template)
            
            # Remove issuer object and convert datetime to strings
            generation_data = {}
            for k, v in generation_context.items():
                if k == 'issuer' or callable(v):
                    continue
                elif hasattr(v, 'isoformat'):  # datetime objects
                    generation_data[k] = v.isoformat()
                else:
                    generation_data[k] = v
            
            # Create IssuerDocument record
            document = IssuerDocument.objects.create(
                issuer=issuer,
                document_type=template.form_type.form_type,
                file_url=str(filepath.relative_to(settings.MEDIA_ROOT)),
                file_hash=file_hash,
                generation_data=generation_data,
                is_current=True
            )
            
            print(f"✅ Generated {document.document_type}: {filepath}")
        
        return pdf_bytes
    
    def generate_form_d(self, issuer: Issuer, save: bool = True) -> bytes:
        """Generate SEC Form D"""
        
        from .models import SECFormType
        
        # Get Form D template
        form_type = SECFormType.objects.get(form_type='FORM_D')
        template = form_type.templates.filter(is_default=True).first()
        
        if not template:
            raise ValueError("No default Form D template found")
        
        return self.generate_pdf(issuer, template, save_to_disk=save)
    
    def generate_form_c(self, issuer: Issuer, save: bool = True) -> bytes:
        """Generate SEC Form C"""
        
        from .models import SECFormType
        
        # Get Form C template
        form_type = SECFormType.objects.get(form_type='FORM_C')
        template = form_type.templates.filter(is_default=True).first()
        
        if not template:
            raise ValueError("No default Form C template found")
        
        return self.generate_pdf(issuer, template, save_to_disk=save)
    
    def upload_to_adobe(
        self, 
        pdf_bytes: bytes, 
        filename: str,
        issuer: Issuer
    ) -> Optional[str]:
        """
        Upload PDF to Adobe Document Cloud
        
        Returns: Document URL or None if failed
        """
        
        # TODO: Implement Adobe API integration
        # This is a placeholder for Adobe Document Cloud API
        
        try:
            import requests
            
            adobe_api_key = getattr(settings, 'ADOBE_API_KEY', None)
            adobe_client_id = getattr(settings, 'ADOBE_CLIENT_ID', None)
            
            if not adobe_api_key or not adobe_client_id:
                print("⚠️  Adobe credentials not configured")
                return None
            
            # Adobe API endpoint (placeholder - actual endpoint depends on service)
            url = 'https://pdf-services.adobe.io/assets'
            
            headers = {
                'Authorization': f'Bearer {adobe_api_key}',
                'X-API-Key': adobe_client_id,
                'Content-Type': 'application/pdf'
            }
            
            # Upload PDF
            response = requests.post(
                url,
                headers=headers,
                data=pdf_bytes,
                params={'filename': filename}
            )
            
            if response.status_code == 201:
                data = response.json()
                document_url = data.get('downloadUri')
                print(f"✅ Uploaded to Adobe: {document_url}")
                return document_url
            else:
                print(f"❌ Adobe upload failed: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Adobe upload error: {e}")
            return None


# Singleton instance
generator = DocumentGenerator()
