"""
Test Field Mapping System
Demonstrates SEC form document generation system
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.issuers.models import (
    DataSource, FieldDefinition, SECFormType,
    SECDocumentTemplate, FieldMappingRule, MappingPreset,
    Issuer
)

print("=" * 70)
print("🧪 FIELD MAPPING SYSTEM TEST")
print("=" * 70)
print()

# 1. Create Issuer Model Data Source
print("1️⃣  Creating Issuer Model Data Source...")
issuer_source, created = DataSource.objects.get_or_create(
    source_name="Issuer Model",
    defaults={
        'source_type': 'MODEL',
        'model_name': 'Issuer',
        'model_path': 'apps.issuers.models.Issuer',
        'description': 'Main issuer data from Brilliant Directories form'
    }
)
print(f"   ✅ {issuer_source} ({'created' if created else 'exists'})")
print()

# 2. Create Field Definitions for Issuer fields
print("2️⃣  Creating Field Definitions...")
fields_to_create = [
    {
        'field_name': 'company_name',
        'display_name': 'Company Name',
        'field_path': 'issuer.company_name',
        'data_type': 'STRING',
        'is_required': True,
        'description': 'Legal entity name',
        'example_value': 'ACME Corporation'
    },
    {
        'field_name': 'isin',
        'display_name': 'ISIN',
        'field_path': 'issuer.isin',
        'data_type': 'STRING',
        'is_required': True,
        'validation_regex': r'^[A-Z]{2}[A-Z0-9]{10}$',
        'description': 'International Securities Identification Number',
        'example_value': 'US0123456789'
    },
    {
        'field_name': 'total_offering',
        'display_name': 'Total Offering Amount',
        'field_path': 'issuer.total_offering',
        'data_type': 'CURRENCY',
        'is_required': True,
        'format_template': '${:,.2f}',
        'description': 'Total amount being offered',
        'example_value': '50000000.00'
    },
    {
        'field_name': 'price_per_token',
        'display_name': 'Price Per Token',
        'field_path': 'issuer.price_per_token',
        'data_type': 'CURRENCY',
        'is_required': True,
        'format_template': '${:,.2f}',
        'description': 'Price per security token',
        'example_value': '100.00'
    },
]

for field_data in fields_to_create:
    field, created = FieldDefinition.objects.get_or_create(
        data_source=issuer_source,
        field_name=field_data['field_name'],
        defaults=field_data
    )
    print(f"   {'✅' if created else '♻️ '} {field.display_name}")

print()

# 3. Create SEC Form Type
print("3️⃣  Creating SEC Form Types...")
form_d, created = SECFormType.objects.get_or_create(
    form_type='FORM_D',
    defaults={
        'display_name': 'SEC Form D (Regulation D)',
        'description': 'Notice of Exempt Offering of Securities'
    }
)
print(f"   ✅ {form_d} ({'created' if created else 'exists'})")
print()

# 4. Create Document Template
print("4️⃣  Creating Form D Template...")
template_content = """
SEC FORM D
NOTICE OF EXEMPT OFFERING OF SECURITIES

Issuer Information:
- Company Name: {{ company_name }}
- ISIN: {{ isin }}

Offering Information:
- Total Offering Amount: {{ total_offering_formatted }}
- Price Per Token: {{ price_per_token_formatted }}

This notice is filed pursuant to Rule 503 of Regulation D under the Securities Act of 1933.
"""

template, created = SECDocumentTemplate.objects.get_or_create(
    name="Form D Template v1.0",
    form_type=form_d,
    defaults={
        'template_content': template_content,
        'version': '1.0',
        'is_default': True
    }
)
print(f"   ✅ {template} ({'created' if created else 'exists'})")
print()

# 5. Create Field Mapping Rules
print("5️⃣  Creating Field Mapping Rules...")
mappings = [
    ('company_name', 'company_name', 'DIRECT'),
    ('isin', 'isin', 'DIRECT'),
    ('total_offering', 'total_offering_formatted', 'DIRECT'),
    ('price_per_token', 'price_per_token_formatted', 'DIRECT'),
]

for source_field_name, template_var, transform_type in mappings:
    source_field = FieldDefinition.objects.get(
        data_source=issuer_source,
        field_name=source_field_name
    )
    
    rule, created = FieldMappingRule.objects.get_or_create(
        template=template,
        template_variable=template_var,
        defaults={
            'source_field': source_field,
            'transformation_type': transform_type,
            'priority': 100
        }
    )
    print(f"   {'✅' if created else '♻️ '} {template_var} ← {source_field_name}")

print()

# 6. Create Mapping Preset
print("6️⃣  Creating Mapping Preset...")
preset, created = MappingPreset.objects.get_or_create(
    name="Standard Reg D Mapping",
    defaults={
        'description': 'Standard field mapping for Regulation D offerings',
        'offering_types_json': ['REG_D'],
        'mapping_config': {
            'company_name': {'source': 'issuer.company_name', 'transformation': 'DIRECT'},
            'isin': {'source': 'issuer.isin', 'transformation': 'DIRECT'},
            'total_offering': {'source': 'issuer.total_offering', 'transformation': 'CURRENCY'},
            'price_per_token': {'source': 'issuer.price_per_token', 'transformation': 'CURRENCY'}
        },
        'is_default': True
    }
)
if created:
    preset.form_types.add(form_d)
print(f"   ✅ {preset} ({'created' if created else 'exists'})")
print()

# 7. Summary
print("=" * 70)
print("📊 SUMMARY")
print("=" * 70)
print(f"Data Sources: {DataSource.objects.count()}")
print(f"Field Definitions: {FieldDefinition.objects.count()}")
print(f"SEC Form Types: {SECFormType.objects.count()}")
print(f"Document Templates: {SECDocumentTemplate.objects.count()}")
print(f"Mapping Rules: {FieldMappingRule.objects.count()}")
print(f"Mapping Presets: {MappingPreset.objects.count()}")
print()

# 8. Test with existing issuer (if any)
issuers = Issuer.objects.all()
if issuers.exists():
    issuer = issuers.first()
    print("🎯 Testing with existing issuer...")
    print(f"   Company: {issuer.company_name}")
    print(f"   ISIN: {issuer.isin}")
    print(f"   Offering: ${issuer.total_offering:,.2f}")
    print(f"   Price: ${issuer.price_per_token:,.2f}")
    print()
    
    # Simulate template rendering (we'd use Jinja2 in production)
    print("📄 Simulated Form D Output:")
    print("-" * 70)
    print(template_content.replace('{{ company_name }}', issuer.company_name)
                          .replace('{{ isin }}', issuer.isin)
                          .replace('{{ total_offering_formatted }}', f'${issuer.total_offering:,.2f}')
                          .replace('{{ price_per_token_formatted }}', f'${issuer.price_per_token:,.2f}'))
    print("-" * 70)
else:
    print("ℹ️  No issuers in database yet. Create one to test document generation.")

print()
print("✅ Field Mapping System is READY!")
print("=" * 70)
