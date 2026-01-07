"""
Issuer Models
Stores SEC form data collected from Brilliant Directories forms.
Maps to ISSUER_ONBOARDING_SCHEMA.json structure.

Includes Field Mapping System for SEC Form Generation (Python 3.13 compatible).
"""

from django.db import models
from django.utils.text import slugify
from django.core.validators import URLValidator, MinValueValidator
import uuid


class Issuer(models.Model):
    """
    Main issuer model - stores SEC form data and offering details.
    White-labeled for each issuer (zero DPO branding).
    """
    
    # Primary Key
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Basic Issuer Info (SEC Form Common Fields)
    company_name = models.CharField(max_length=255, db_index=True, help_text="Legal entity name")
    slug = models.SlugField(max_length=255, unique=True, db_index=True, help_text="URL-friendly identifier")
    logo = models.URLField(blank=True, null=True, help_text="Company logo URL")
    
    # Security Details
    security_name = models.CharField(max_length=255, help_text="Name of the security being offered")
    isin = models.CharField(max_length=12, unique=True, db_index=True, help_text="ISIN (International Securities Identification Number)")
    
    # Offering Details
    price_per_token = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0.01)])
    total_offering = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(1)])
    min_investment = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(1)])
    
    # Social Media Links
    website = models.URLField(blank=True, null=True, validators=[URLValidator()])
    linkedin = models.URLField(blank=True, null=True, validators=[URLValidator()])
    twitter = models.URLField(blank=True, null=True, validators=[URLValidator()])
    youtube = models.URLField(blank=True, null=True, validators=[URLValidator()])
    facebook = models.URLField(blank=True, null=True, validators=[URLValidator()])
    instagram = models.URLField(blank=True, null=True, validators=[URLValidator()])
    
    # Payment Rails
    paypal_account = models.CharField(max_length=255, blank=True, null=True, help_text="PayPal username or email")
    
    # Wire Transfer Details (stored as JSON)
    wire_bank_name = models.CharField(max_length=255, blank=True, null=True)
    wire_account_number = models.CharField(max_length=100, blank=True, null=True)
    wire_routing_number = models.CharField(max_length=100, blank=True, null=True)
    wire_swift = models.CharField(max_length=11, blank=True, null=True, help_text="SWIFT/BIC code")
    
    # Crypto Payment
    crypto_merchant_id = models.CharField(max_length=255, blank=True, null=True, help_text="BillBitcoins merchant ID")
    
    # Offering Documents (Adobe Cloud links)
    doc_prospectus = models.URLField(blank=True, null=True, validators=[URLValidator()])
    doc_terms = models.URLField(blank=True, null=True, validators=[URLValidator()])
    doc_risks = models.URLField(blank=True, null=True, validators=[URLValidator()])
    doc_subscription = models.URLField(blank=True, null=True, validators=[URLValidator()])
    
    # Business Description
    description = models.TextField(blank=True, null=True, help_text="Company/offering description")
    
    # SEC Form Data (stored as JSONB for flexibility)
    sec_form_data = models.JSONField(default=dict, blank=True, help_text="Complete SEC form data from BD")
    
    # Offering Status
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending_review', 'Pending Review'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft', db_index=True)
    
    # Offering Page URL (generated)
    offering_page_url = models.URLField(blank=True, null=True, help_text="Full URL to white-labeled offering page")
    
    # BD Integration
    bd_post_id = models.IntegerField(blank=True, null=True, help_text="Brilliant Directories post/listing ID")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(blank=True, null=True, help_text="When offering went live")
    
    # Metadata
    notes = models.TextField(blank=True, null=True, help_text="Internal admin notes")
    
    class Meta:
        db_table = 'issuers'
        ordering = ['-created_at']
        verbose_name = 'Issuer'
        verbose_name_plural = 'Issuers'
        indexes = [
            models.Index(fields=['company_name', 'status']),
            models.Index(fields=['isin', 'status']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.company_name} - {self.security_name}"
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from company name if not provided"""
        if not self.slug:
            base_slug = slugify(self.company_name)
            slug = base_slug
            counter = 1
            while Issuer.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        
        # Generate offering page URL
        if not self.offering_page_url:
            # In production, this would use your BD domain
            # Example: https://acme-corp.offerings.dpo-global.com
            self.offering_page_url = f"https://offerings.dpo-global.com/{self.slug}/"
        
        super().save(*args, **kwargs)
    
    @property
    def wire_account_details(self):
        """Return wire transfer details as dict for API serialization"""
        if not self.wire_account_number:
            return None
        return {
            'bankName': self.wire_bank_name,
            'accountNumber': self.wire_account_number,
            'routingNumber': self.wire_routing_number,
            'swift': self.wire_swift,
        }
    
    @property
    def documents(self):
        """Return all document URLs as dict"""
        return {
            'prospectus': self.doc_prospectus,
            'terms': self.doc_terms,
            'risks': self.doc_risks,
            'subscription': self.doc_subscription,
        }
    
    @property
    def social_links(self):
        """Return all social media links as dict"""
        return {
            'website': self.website,
            'linkedin': self.linkedin,
            'twitter': self.twitter,
            'youtube': self.youtube,
            'facebook': self.facebook,
            'instagram': self.instagram,
        }


class IssuerDocument(models.Model):
    """
    Generated documents for issuers (Form D, Form C, PPM, etc.)
    Uses Jinja templates populated with SEC form data.
    """
    
    DOCUMENT_TYPES = [
        ('form_d', 'SEC Form D'),
        ('form_c', 'SEC Form C'),
        ('form_1a', 'SEC Form 1-A'),
        ('form_10', 'SEC Form 10'),
        ('ppm', 'Private Placement Memorandum'),
        ('subscription', 'Subscription Agreement'),
        ('terms', 'Terms & Conditions'),
        ('risks', 'Risk Disclosures'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    issuer = models.ForeignKey(Issuer, on_delete=models.CASCADE, related_name='documents')
    
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    template_version = models.CharField(max_length=50, default='1.0')
    
    # Generated document storage
    file_url = models.URLField(help_text="Adobe Cloud or S3 URL to generated PDF")
    file_hash = models.CharField(max_length=64, help_text="SHA256 hash for integrity verification")
    
    # Generation metadata
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.CharField(max_length=255, default='system')
    generation_data = models.JSONField(default=dict, help_text="Data used to generate document")
    
    # Status
    is_current = models.BooleanField(default=True, help_text="Is this the current version?")
    
    class Meta:
        db_table = 'issuer_documents'
        ordering = ['-generated_at']
        verbose_name = 'Issuer Document'
        verbose_name_plural = 'Issuer Documents'
        indexes = [
            models.Index(fields=['issuer', 'document_type', 'is_current']),
        ]
    
    def __str__(self):
        return f"{self.issuer.company_name} - {self.get_document_type_display()}"

# ═══════════════════════════════════════════════════════════
# Field Mapping System for SEC Form Generation
# Python 3.13 Compatible (No PostgreSQL ArrayField)
# ═══════════════════════════════════════════════════════════


class DataSource(models.Model):
    """
    Defines available data sources for field mapping
    """
    SOURCE_TYPES = [
        ('MODEL', 'Django Model'),
        ('API', 'External API'),
        ('COMPUTED', 'Computed/Calculated'),
        ('USER_INPUT', 'User Input Required'),
        ('CONSTANT', 'Constant Value'),
    ]
    
    source_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    source_name = models.CharField(max_length=100, unique=True)
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    
    # For MODEL type
    model_name = models.CharField(max_length=100, blank=True, help_text="e.g., 'Issuer'")
    model_path = models.CharField(max_length=255, blank=True, help_text="e.g., 'apps.issuers.models.Issuer'")
    
    # For API type
    api_endpoint = models.URLField(blank=True)
    api_method = models.CharField(max_length=10, default='GET', blank=True)
    api_headers = models.JSONField(default=dict, blank=True)
    
    # For COMPUTED type
    computation_function = models.CharField(max_length=255, blank=True, help_text="Python function path")
    
    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sec_data_sources'
        verbose_name = 'Data Source'
        verbose_name_plural = 'Data Sources'
    
    def __str__(self):
        return f"{self.source_name} ({self.source_type})"


class FieldDefinition(models.Model):
    """
    Catalog of all available fields across data sources
    """
    DATA_TYPES = [
        ('STRING', 'String/Text'),
        ('INTEGER', 'Integer'),
        ('DECIMAL', 'Decimal/Float'),
        ('BOOLEAN', 'Boolean'),
        ('DATE', 'Date'),
        ('DATETIME', 'Date & Time'),
        ('CURRENCY', 'Currency'),
        ('PERCENTAGE', 'Percentage'),
        ('ADDRESS', 'Address'),
        ('EMAIL', 'Email'),
        ('PHONE', 'Phone Number'),
        ('URL', 'URL'),
        ('ARRAY', 'Array/List'),
        ('OBJECT', 'Object/Dictionary'),
    ]
    
    field_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Identification
    field_name = models.CharField(max_length=100)
    display_name = models.CharField(max_length=255)
    field_path = models.CharField(max_length=500)
    
    # Data source
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='fields')
    
    # Type and validation
    data_type = models.CharField(max_length=20, choices=DATA_TYPES)
    is_required = models.BooleanField(default=False)
    default_value = models.CharField(max_length=500, blank=True)
    
    # Validation rules
    validation_regex = models.CharField(max_length=500, blank=True)
    min_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=20, decimal_places=2, null=True, blank=True)
    min_length = models.IntegerField(null=True, blank=True)
    max_length = models.IntegerField(null=True, blank=True)
    
    # Store arrays as JSON (Python 3.13 compatible, no PostgreSQL required)
    allowed_values_json = models.JSONField(default=list, blank=True, help_text="Array of allowed values")
    
    # Formatting
    format_template = models.CharField(max_length=255, blank=True, help_text="e.g., '${:,.2f}' for currency")
    
    # Metadata
    description = models.TextField(blank=True)
    help_text = models.TextField(blank=True)
    example_value = models.CharField(max_length=500, blank=True)
    
    # SEO for searching (JSON instead of ArrayField)
    aliases_json = models.JSONField(default=list, blank=True, help_text="Alternative names")
    tags_json = models.JSONField(default=list, blank=True, help_text="Tags for categorization")
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sec_field_definitions'
        unique_together = ['data_source', 'field_name']
        ordering = ['data_source', 'field_name']
        verbose_name = 'Field Definition'
        verbose_name_plural = 'Field Definitions'
    
    def __str__(self):
        return f"{self.display_name} ({self.field_path})"
    
    @property
    def allowed_values(self):
        """Helper property for backward compatibility"""
        return self.allowed_values_json
    
    @property
    def aliases(self):
        """Helper property for backward compatibility"""
        return self.aliases_json
    
    @property
    def tags(self):
        """Helper property for backward compatibility"""
        return self.tags_json


class SECFormType(models.Model):
    """SEC Form type catalog"""
    FORM_TYPES = [
        ('FORM_D', 'SEC Form D (Reg D)'),
        ('FORM_C', 'SEC Form C (Reg CF)'),
        ('FORM_1A', 'SEC Form 1-A (Reg A)'),
        ('FORM_10', 'SEC Form 10'),
        ('PPM', 'Private Placement Memorandum'),
        ('SUBSCRIPTION', 'Subscription Agreement'),
    ]
    
    form_type = models.CharField(max_length=20, choices=FORM_TYPES, unique=True)
    display_name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'sec_form_types'
        verbose_name = 'SEC Form Type'
        verbose_name_plural = 'SEC Form Types'
    
    def __str__(self):
        return self.display_name


class SECDocumentTemplate(models.Model):
    """Jinja templates for SEC forms"""
    template_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    
    name = models.CharField(max_length=255)
    form_type = models.ForeignKey(SECFormType, on_delete=models.CASCADE, related_name='templates')
    
    # Template content
    template_content = models.TextField(help_text="Jinja2 template content")
    template_file_path = models.CharField(max_length=500, blank=True)
    
    # Version control
    version = models.CharField(max_length=50, default='1.0')
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sec_document_templates'
        ordering = ['-is_default', 'form_type', 'version']
        verbose_name = 'SEC Document Template'
        verbose_name_plural = 'SEC Document Templates'
    
    def __str__(self):
        return f"{self.name} (v{self.version})"


class FieldMappingRule(models.Model):
    """
    Defines how to map a template variable to data sources
    """
    TRANSFORMATION_TYPES = [
        ('DIRECT', 'Direct Mapping'),
        ('EXPRESSION', 'Expression/Formula'),
        ('CONCATENATE', 'Concatenate Multiple Fields'),
        ('LOOKUP', 'Lookup Table'),
        ('CONDITIONAL', 'Conditional Logic'),
        ('FUNCTION', 'Custom Function'),
    ]
    
    rule_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Template association
    template = models.ForeignKey(SECDocumentTemplate, on_delete=models.CASCADE, related_name='mapping_rules')
    
    # Mapping definition
    template_variable = models.CharField(max_length=200, help_text="e.g., 'issuer_name'")
    
    # Source field(s)
    source_field = models.ForeignKey(
        FieldDefinition,
        on_delete=models.PROTECT,
        related_name='mapping_rules',
        null=True,
        blank=True
    )
    source_fields = models.ManyToManyField(
        FieldDefinition,
        related_name='multi_mapping_rules',
        blank=True
    )
    
    # Transformation
    transformation_type = models.CharField(max_length=20, choices=TRANSFORMATION_TYPES, default='DIRECT')
    transformation_expression = models.TextField(blank=True)
    
    # Conditional logic (JSON instead of complex custom field)
    conditions = models.JSONField(default=dict, blank=True)
    
    # Fallback values
    fallback_value = models.CharField(max_length=500, blank=True)
    fallback_field = models.ForeignKey(
        FieldDefinition,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='fallback_mappings'
    )
    
    # Formatting
    apply_formatting = models.BooleanField(default=True)
    custom_format = models.CharField(max_length=255, blank=True)
    
    # Priority
    priority = models.IntegerField(default=0)
    
    # Metadata
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sec_field_mapping_rules'
        ordering = ['-priority', 'template', 'template_variable']
        unique_together = ['template', 'template_variable', 'priority']
        verbose_name = 'Field Mapping Rule'
        verbose_name_plural = 'Field Mapping Rules'
    
    def __str__(self):
        return f"{self.template_variable} → {self.source_field if self.source_field else 'Complex'}"


class MappingPreset(models.Model):
    """Reusable mapping configurations"""
    preset_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Applicable contexts
    form_types = models.ManyToManyField(SECFormType, blank=True)
    
    # Store as JSON instead of ArrayField
    offering_types_json = models.JSONField(default=list, blank=True, help_text="e.g., ['REG_D', 'REG_A']")
    
    # Mapping configuration
    mapping_config = models.JSONField(help_text="Complete mapping configuration")
    
    # Usage tracking
    times_applied = models.IntegerField(default=0)
    
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'sec_mapping_presets'
        ordering = ['-is_default', 'name']
        verbose_name = 'Mapping Preset'
        verbose_name_plural = 'Mapping Presets'
    
    def __str__(self):
        return self.name
    
    @property
    def offering_types(self):
        """Helper property for backward compatibility"""
        return self.offering_types_json