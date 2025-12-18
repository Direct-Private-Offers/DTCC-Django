"""
Common OpenAPI schemas for Swagger documentation
"""
from drf_spectacular.utils import OpenApiResponse, extend_schema_serializer
from drf_spectacular.types import OpenApiTypes
from rest_framework import serializers


class ErrorResponseSerializer(serializers.Serializer):
    """Standard error response schema"""
    success = serializers.BooleanField(default=False)
    error = serializers.CharField()
    timestamp = serializers.DateTimeField()


class SuccessResponseSerializer(serializers.Serializer):
    """Standard success response schema"""
    success = serializers.BooleanField(default=True)
    timestamp = serializers.DateTimeField()


# Common response examples
ERROR_400 = OpenApiResponse(
    response=ErrorResponseSerializer,
    description="Bad Request - Invalid input data",
    examples=[
        {
            "success": False,
            "error": "ISIN parameter required",
            "timestamp": "2025-01-15T10:30:00Z"
        },
        {
            "success": False,
            "error": {"isin": ["This field is required."]},
            "timestamp": "2025-01-15T10:30:00Z"
        }
    ]
)

ERROR_401 = OpenApiResponse(
    response=ErrorResponseSerializer,
    description="Unauthorized - Missing or invalid authentication",
    examples=[
        {
            "success": False,
            "error": "Authentication credentials were not provided.",
            "timestamp": "2025-01-15T10:30:00Z"
        }
    ]
)

ERROR_403 = OpenApiResponse(
    response=ErrorResponseSerializer,
    description="Forbidden - Insufficient permissions",
    examples=[
        {
            "success": False,
            "error": "You do not have permission to perform this action.",
            "timestamp": "2025-01-15T10:30:00Z"
        },
        {
            "success": False,
            "error": "Investor not authorized for this security",
            "timestamp": "2025-01-15T10:30:00Z"
        }
    ]
)

ERROR_404 = OpenApiResponse(
    response=ErrorResponseSerializer,
    description="Not Found - Resource does not exist",
    examples=[
        {
            "success": False,
            "error": "Security with ISIN US0378331005 not found",
            "timestamp": "2025-01-15T10:30:00Z"
        },
        {
            "success": False,
            "error": "Settlement not found",
            "timestamp": "2025-01-15T10:30:00Z"
        }
    ]
)

ERROR_500 = OpenApiResponse(
    response=ErrorResponseSerializer,
    description="Internal Server Error",
    examples=[
        {
            "success": False,
            "error": "Failed to process issuance: Connection timeout",
            "timestamp": "2025-01-15T10:30:00Z"
        }
    ]
)

