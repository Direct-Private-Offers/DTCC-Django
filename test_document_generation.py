"""
Test Document Generation Workflow
Demonstrates complete SEC document generation pipeline
"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.issuers.models import Issuer, SECFormType, SECDocumentTemplate, IssuerDocument
from apps.issuers.document_generator import generator


def test_form_d_generation():
    """Test Form D PDF generation"""
    
    print("\n" + "=" * 60)
    print("📄 TESTING FORM D GENERATION")
    print("=" * 60 + "\n")
    
    # Find or create test issuer
    issuer = Issuer.objects.filter(slug='test-corp').first()
    
    if not issuer:
        print("❌ Test issuer 'test-corp' not found")
        print("💡 Run: python test_field_mapping.py first to create test data")
        return
    
    print(f"✅ Found issuer: {issuer.company_name}")
    print(f"   ISIN: {issuer.isin}")
    print(f"   Offering: ${issuer.total_offering:,.2f}")
    print(f"   Price: ${issuer.price_per_token:.2f}\n")
    
    # Check if Form D template exists
    try:
        form_type = SECFormType.objects.get(form_type='FORM_D')
        template = form_type.templates.filter(is_default=True).first()
        
        if not template:
            print("❌ No Form D template found")
            return
        
        print(f"✅ Found template: {template.name} (v{template.version})\n")
        
        # Generate HTML first
        print("🔄 Generating HTML...")
        html_content = generator.generate_html(issuer, template)
        print(f"✅ HTML generated ({len(html_content)} bytes)\n")
        
        # Save HTML preview
        html_preview_path = f"form_d_preview_{issuer.slug}.html"
        with open(html_preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 HTML preview saved: {html_preview_path}\n")
        
        # Generate PDF
        print("🔄 Generating PDF with WeasyPrint...")
        pdf_bytes = generator.generate_pdf(issuer, template, save_to_disk=True)
        print(f"✅ PDF generated ({len(pdf_bytes)} bytes)\n")
        
        # Check database record
        latest_doc = IssuerDocument.objects.filter(
            issuer=issuer,
            document_type='FORM_D'
        ).order_by('-generated_at').first()
        
        if latest_doc:
            print("✅ IssuerDocument record created:")
            print(f"   Document Type: {latest_doc.document_type}")
            print(f"   File: {latest_doc.file_url}")
            print(f"   Hash: {latest_doc.file_hash[:16]}...")
            print(f"   Generated: {latest_doc.generated_at}")
        
        print("\n" + "=" * 60)
        print("✅ FORM D GENERATION SUCCESSFUL")
        print("=" * 60 + "\n")
        
    except SECFormType.DoesNotExist:
        print("❌ Form D type not found in database")
        print("💡 Run: python test_field_mapping.py to create SEC form types")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_form_c_generation():
    """Test Form C PDF generation"""
    
    print("\n" + "=" * 60)
    print("📄 TESTING FORM C GENERATION")
    print("=" * 60 + "\n")
    
    # Create Form C form type if it doesn't exist
    form_c_type, created = SECFormType.objects.get_or_create(
        form_type='FORM_C',
        defaults={
            'display_name': 'SEC Form C (Regulation Crowdfunding)',
            'description': 'Offering statement for Reg CF crowdfunding offerings'
        }
    )
    
    if created:
        print(f"✅ Created Form C type: {form_c_type.display_name}\n")
    
    # Create template if it doesn't exist
    template, created = SECDocumentTemplate.objects.get_or_create(
        form_type=form_c_type,
        name='Form C Template v1.0',
        defaults={
            'template_file_path': 'form_c.html',
            'version': '1.0',
            'is_active': True,
            'is_default': True
        }
    )
    
    if created:
        print(f"✅ Created template: {template.name}\n")
    
    # Find test issuer
    issuer = Issuer.objects.filter(slug='test-corp').first()
    
    if not issuer:
        print("❌ Test issuer not found")
        return
    
    print(f"✅ Found issuer: {issuer.company_name}\n")
    
    try:
        # Generate HTML
        print("🔄 Generating HTML...")
        html_content = generator.generate_html(issuer, template)
        print(f"✅ HTML generated ({len(html_content)} bytes)\n")
        
        # Save HTML preview
        html_preview_path = f"form_c_preview_{issuer.slug}.html"
        with open(html_preview_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"💾 HTML preview saved: {html_preview_path}\n")
        
        # Generate PDF
        print("🔄 Generating PDF...")
        pdf_bytes = generator.generate_pdf(issuer, template, save_to_disk=True)
        print(f"✅ PDF generated ({len(pdf_bytes)} bytes)\n")
        
        print("=" * 60)
        print("✅ FORM C GENERATION SUCCESSFUL")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def test_webhook_simulation():
    """Simulate BD webhook submission"""
    
    print("\n" + "=" * 60)
    print("🌐 TESTING WEBHOOK SIMULATION")
    print("=" * 60 + "\n")
    
    # Simulate BD form data
    bd_form_data = {
        'company_name': 'TechVentures Inc',
        'security_name': 'TechVentures Token',
        'isin': 'US9876543210',
        'price_per_token': 50.00,
        'total_offering': 500000.00,
        'min_investment': 1000.00,
        'description': 'AI-powered venture capital platform democratizing startup investing',
        'website': 'https://techventures.example.com',
        'linkedin_url': 'https://linkedin.com/company/techventures',
        'paypal_email': 'invest@techventures.example.com',
        'wire_transfer': {
            'bank_name': 'Silicon Valley Bank',
            'account_number': '1234567890',
            'routing_number': '121000248',
            'swift_code': 'SVBKUS6S'
        },
        'form_type': 'FORM_D',
        'auto_generate_documents': True,
        'contact_email': 'ceo@techventures.example.com'
    }
    
    # Import webhook handler
    from apps.issuers.webhooks import map_bd_to_issuer
    from apps.issuers.serializers import IssuerCreateSerializer
    
    print("🔄 Mapping BD form data to Issuer model...")
    issuer_data = map_bd_to_issuer(bd_form_data)
    
    print(f"✅ Mapped {len(issuer_data)} fields\n")
    
    # Validate with serializer
    print("🔄 Validating data...")
    serializer = IssuerCreateSerializer(data=issuer_data)
    
    if serializer.is_valid():
        print("✅ Data validation passed\n")
        
        # Create issuer
        print("🔄 Creating issuer...")
        issuer = serializer.save()
        print(f"✅ Created issuer: {issuer.company_name}")
        print(f"   Slug: {issuer.slug}")
        print(f"   URL: {issuer.offering_page_url}\n")
        
        # Generate Form D
        print("🔄 Auto-generating Form D...")
        try:
            pdf_bytes = generator.generate_form_d(issuer, save=True)
            print(f"✅ Form D generated ({len(pdf_bytes)} bytes)\n")
            
            print("=" * 60)
            print("✅ WEBHOOK SIMULATION SUCCESSFUL")
            print("=" * 60 + "\n")
            
        except Exception as e:
            print(f"⚠️  Document generation failed: {e}\n")
    else:
        print(f"❌ Validation failed: {serializer.errors}\n")


if __name__ == '__main__':
    print("\n🚀 DPO ECOSYSTEM - DOCUMENT GENERATION TEST SUITE\n")
    
    # Test 1: Form D
    test_form_d_generation()
    
    # Test 2: Form C
    test_form_c_generation()
    
    # Test 3: Webhook
    test_webhook_simulation()
    
    print("\n✅ ALL TESTS COMPLETE\n")
