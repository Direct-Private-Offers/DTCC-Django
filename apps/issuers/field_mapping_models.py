"""
Field Mapping System for SEC Form Generation
Adapted for Python 3.13 + SQLite (no PostgreSQL dependencies)

Replaces ArrayField with JSONField for compatibility.
"""

from django.db import models
import uuid


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
    field_name = models.CharField(max_length=100)  # e.g., "company_name"
    display_name = models.CharField(max_length=255)  # e.g., "Company Name"
    field_path = models.CharField(max_length=500)  # e.g., "issuer.company_name"
    
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
    
    # Store arrays as JSON (Python 3.13 compatible)
    allowed_values_json = models.JSONField(default=list, blank=True, help_text="Array of allowed values")
    
    # Formatting
    format_template = models.CharField(max_length=255, blank=True, help_text="e.g., '${:,.2f}' for currency")
    
    # Metadata
    description = models.TextField(blank=True)
    help_text = models.TextField(blank=True)
    example_value = models.CharField(max_length=500, blank=True)
    
    # SEO for searching (stored as JSON instead of ArrayField)
    aliases_json = models.JSONField(default=list, blank=True, help_text="Alternative names for this field")
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
        """Helper property to access allowed values"""
        return self.allowed_values_json
    
    @property
    def aliases(self):
        """Helper property to access aliases"""
        return self.aliases_json
    
    @property
    def tags(self):
        """Helper property to access tags"""
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
    template_file_path = models.CharField(max_length=500, blank=True, help_text="Path to template file")
    
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
    template_variable = models.CharField(max_length=200, help_text="Variable name in template, e.g., 'issuer_name'")
    
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
    transformation_expression = models.TextField(blank=True, help_text="Python expression or formula")
    
    # Conditional logic
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="""
        Example: {
            "if": "issuer.status == 'active'",
            "then": "issuer.company_name",
            "else": "N/A"
        }
        """
    )
    
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
    
    # Priority (for multiple rules mapping to same variable)
    priority = models.IntegerField(default=0, help_text="Higher number = higher priority")
    
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
        return f"{self.template_variable} → {self.source_field if self.source_field else 'Complex Mapping'}"


class MappingPreset(models.Model):
    """
    Reusable mapping configurations for common scenarios
    """
    preset_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, primary_key=True)
    
    name = models.CharField(max_length=255)
    description = models.TextField()
    
    # Applicable contexts
    form_types = models.ManyToManyField(SECFormType, blank=True)
    
    # Store as JSON instead of ArrayField
    offering_types_json = models.JSONField(
        default=list,
        blank=True,
        help_text="e.g., ['REG_D', 'REG_A']"
    )
    
    # Mapping configuration
    mapping_config = models.JSONField(
        help_text="""
        Complete mapping configuration that can be applied to templates.
        Example: {
            "issuer_name": {
                "source": "issuer.company_name",
                "transformation": "DIRECT"
            },
            "total_amount": {
                "source": ["issuer.total_offering", "issuer.price_per_token"],
                "transformation": "EXPRESSION",
                "expression": "issuer.total_offering * issuer.price_per_token"
            }
        }
        """
    )
    
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
        """Helper property to access offering types"""
        return self.offering_types_json
