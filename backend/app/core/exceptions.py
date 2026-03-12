"""Custom exceptions for the Joulaa platform"""

from typing import Any, Dict, Optional
from fastapi import HTTPException, status


class JoulaaException(Exception):
    """Base exception for Joulaa platform"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class JoulaaHTTPException(HTTPException):
    """Base HTTP exception for Joulaa platform"""
    
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        self.error_code = error_code
        self.details = details or {}
        super().__init__(
            status_code=status_code,
            detail={
                "message": message,
                "error_code": error_code,
                "details": self.details
            },
            headers=headers
        )


# Authentication & Authorization Exceptions
class AuthenticationError(JoulaaHTTPException):
    """Authentication failed"""
    
    def __init__(self, message: str = "Authentication failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            message=message,
            error_code="AUTH_FAILED",
            **kwargs
        )


class AuthorizationError(JoulaaHTTPException):
    """Authorization failed"""
    
    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="AUTH_INSUFFICIENT_PERMISSIONS",
            **kwargs
        )


class PermissionError(AuthorizationError):
    """Backward-compatible generic permission error"""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(message=message, **kwargs)


class TokenExpiredError(AuthenticationError):
    """Token has expired"""
    
    def __init__(self, message: str = "Token has expired", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTH_TOKEN_EXPIRED",
            **kwargs
        )


class InvalidTokenError(AuthenticationError):
    """Invalid token provided"""
    
    def __init__(self, message: str = "Invalid token", **kwargs):
        super().__init__(
            message=message,
            error_code="AUTH_INVALID_TOKEN",
            **kwargs
        )


# User & Organization Exceptions
class UserNotFoundError(JoulaaHTTPException):
    """User not found"""
    
    def __init__(self, message: str = "User not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="USER_NOT_FOUND",
            **kwargs
        )


class UserAlreadyExistsError(JoulaaHTTPException):
    """User already exists"""
    
    def __init__(self, message: str = "User already exists", **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="USER_ALREADY_EXISTS",
            **kwargs
        )


class OrganizationNotFoundError(JoulaaHTTPException):
    """Organization not found"""
    
    def __init__(self, message: str = "Organization not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="ORGANIZATION_NOT_FOUND",
            **kwargs
        )


class NotFoundError(JoulaaHTTPException):
    """Backward-compatible generic not found error"""

    def __init__(self, message: str = "Resource not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="NOT_FOUND",
            **kwargs
        )


class OrganizationLimitExceededError(JoulaaHTTPException):
    """Organization limit exceeded"""
    
    def __init__(self, message: str = "Organization limit exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="ORGANIZATION_LIMIT_EXCEEDED",
            **kwargs
        )


class OrganizationPermissionError(AuthorizationError):
    """Organization permission denied"""

    def __init__(self, message: str = "Organization access denied", **kwargs):
        super().__init__(message=message, **kwargs)


class OrganizationValidationError(JoulaaHTTPException):
    """Organization validation failed"""

    def __init__(self, message: str = "Organization validation failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="ORGANIZATION_VALIDATION_FAILED",
            **kwargs
        )


# Agent Exceptions
class AgentNotFoundError(JoulaaHTTPException):
    """Agent not found"""
    
    def __init__(self, message: str = "Agent not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="AGENT_NOT_FOUND",
            **kwargs
        )


class AgentPermissionError(JoulaaHTTPException):
    """Agent permission denied"""
    
    def __init__(self, message: str = "Agent access denied", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="AGENT_PERMISSION_DENIED",
            **kwargs
        )


class AgentValidationError(JoulaaHTTPException):
    """Agent validation failed"""
    
    def __init__(self, message: str = "Agent validation failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="AGENT_VALIDATION_FAILED",
            **kwargs
        )


class AgentLimitExceededError(JoulaaHTTPException):
    """Agent limit exceeded"""
    
    def __init__(self, message: str = "Agent limit exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="AGENT_LIMIT_EXCEEDED",
            **kwargs
        )


class AgentUnavailableError(JoulaaHTTPException):
    """Agent is unavailable"""
    
    def __init__(self, message: str = "Agent is currently unavailable", **kwargs):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_code="AGENT_UNAVAILABLE",
            **kwargs
        )


# Conversation Exceptions
class ConversationNotFoundError(JoulaaHTTPException):
    """Conversation not found"""
    
    def __init__(self, message: str = "Conversation not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="CONVERSATION_NOT_FOUND",
            **kwargs
        )


class ConversationPermissionError(JoulaaHTTPException):
    """Conversation permission denied"""
    
    def __init__(self, message: str = "Conversation access denied", **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=message,
            error_code="CONVERSATION_PERMISSION_DENIED",
            **kwargs
        )


class ConversationValidationError(JoulaaHTTPException):
    """Conversation validation failed"""

    def __init__(self, message: str = "Conversation validation failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="CONVERSATION_VALIDATION_FAILED",
            **kwargs
        )


class MessageNotFoundError(JoulaaHTTPException):
    """Message not found"""

    def __init__(self, message: str = "Message not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="MESSAGE_NOT_FOUND",
            **kwargs
        )


class MessageValidationError(JoulaaHTTPException):
    """Message validation failed"""
    
    def __init__(self, message: str = "Message validation failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="MESSAGE_VALIDATION_FAILED",
            **kwargs
        )


# Integration Exceptions
class IntegrationError(JoulaaHTTPException):
    """Integration error"""
    
    def __init__(self, message: str = "Integration error", **kwargs):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=message,
            error_code="INTEGRATION_ERROR",
            **kwargs
        )


class IntegrationNotFoundError(JoulaaHTTPException):
    """Integration not found"""
    
    def __init__(self, message: str = "Integration not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="INTEGRATION_NOT_FOUND",
            **kwargs
        )


class IntegrationConfigurationError(JoulaaHTTPException):
    """Integration configuration error"""
    
    def __init__(self, message: str = "Integration configuration error", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="INTEGRATION_CONFIGURATION_ERROR",
            **kwargs
        )


# AI Service Exceptions
class AIServiceError(JoulaaHTTPException):
    """AI service error"""
    
    def __init__(self, message: str = "AI service error", **kwargs):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=message,
            error_code="AI_SERVICE_ERROR",
            **kwargs
        )


class AIServiceUnavailableError(JoulaaHTTPException):
    """AI service unavailable"""
    
    def __init__(self, message: str = "AI service is currently unavailable", **kwargs):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=message,
            error_code="AI_SERVICE_UNAVAILABLE",
            **kwargs
        )


class AIServiceQuotaExceededError(JoulaaHTTPException):
    """AI service quota exceeded"""
    
    def __init__(self, message: str = "AI service quota exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="AI_SERVICE_QUOTA_EXCEEDED",
            **kwargs
        )


class AIModelNotFoundError(JoulaaHTTPException):
    """AI model not found"""
    
    def __init__(self, message: str = "AI model not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="AI_MODEL_NOT_FOUND",
            **kwargs
        )


# Rate Limiting Exceptions
class RateLimitExceededError(JoulaaHTTPException):
    """Rate limit exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None, **kwargs):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            headers=headers,
            **kwargs
        )


class ConflictError(JoulaaHTTPException):
    """Backward-compatible generic conflict error"""

    def __init__(self, message: str = "Resource conflict", **kwargs):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            message=message,
            error_code="CONFLICT",
            **kwargs
        )


# File & Storage Exceptions
class FileNotFoundError(JoulaaHTTPException):
    """File not found"""
    
    def __init__(self, message: str = "File not found", **kwargs):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            message=message,
            error_code="FILE_NOT_FOUND",
            **kwargs
        )


class FileUploadError(JoulaaHTTPException):
    """File upload error"""
    
    def __init__(self, message: str = "File upload failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="FILE_UPLOAD_ERROR",
            **kwargs
        )


class FileSizeExceededError(JoulaaHTTPException):
    """File size exceeded"""
    
    def __init__(self, message: str = "File size exceeded limit", **kwargs):
        super().__init__(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            message=message,
            error_code="FILE_SIZE_EXCEEDED",
            **kwargs
        )


class UnsupportedFileTypeError(JoulaaHTTPException):
    """Unsupported file type"""
    
    def __init__(self, message: str = "Unsupported file type", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="UNSUPPORTED_FILE_TYPE",
            **kwargs
        )


# Billing & Subscription Exceptions
class BillingError(JoulaaHTTPException):
    """Billing error"""
    
    def __init__(self, message: str = "Billing error", **kwargs):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            message=message,
            error_code="BILLING_ERROR",
            **kwargs
        )


class SubscriptionExpiredError(JoulaaHTTPException):
    """Subscription expired"""
    
    def __init__(self, message: str = "Subscription has expired", **kwargs):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            message=message,
            error_code="SUBSCRIPTION_EXPIRED",
            **kwargs
        )


class SubscriptionLimitExceededError(JoulaaHTTPException):
    """Subscription limit exceeded"""
    
    def __init__(self, message: str = "Subscription limit exceeded", **kwargs):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            message=message,
            error_code="SUBSCRIPTION_LIMIT_EXCEEDED",
            **kwargs
        )


# Validation Exceptions
class ValidationError(JoulaaHTTPException):
    """General validation error"""
    
    def __init__(self, message: str = "Validation failed", **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=message,
            error_code="VALIDATION_ERROR",
            **kwargs
        )


class RequiredFieldError(ValidationError):
    """Required field missing"""
    
    def __init__(self, field_name: str, **kwargs):
        super().__init__(
            message=f"Required field '{field_name}' is missing",
            error_code="REQUIRED_FIELD_MISSING",
            details={"field": field_name},
            **kwargs
        )


class InvalidFieldError(ValidationError):
    """Invalid field value"""
    
    def __init__(self, field_name: str, reason: str = "Invalid value", **kwargs):
        super().__init__(
            message=f"Invalid value for field '{field_name}': {reason}",
            error_code="INVALID_FIELD_VALUE",
            details={"field": field_name, "reason": reason},
            **kwargs
        )


# Database Exceptions
class DatabaseError(JoulaaException):
    """Database error"""
    
    def __init__(self, message: str = "Database error", **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            **kwargs
        )


class DatabaseConnectionError(DatabaseError):
    """Database connection error"""
    
    def __init__(self, message: str = "Database connection failed", **kwargs):
        super().__init__(
            message=message,
            error_code="DATABASE_CONNECTION_ERROR",
            **kwargs
        )


# External Service Exceptions
class ExternalServiceError(JoulaaHTTPException):
    """External service error"""
    
    def __init__(self, service_name: str, message: str = "External service error", **kwargs):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            message=f"{service_name}: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            details={"service": service_name},
            **kwargs
        )


class ExternalServiceUnavailableError(JoulaaHTTPException):
    """External service unavailable"""
    
    def __init__(self, service_name: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            message=f"{service_name} is currently unavailable",
            error_code="EXTERNAL_SERVICE_UNAVAILABLE",
            details={"service": service_name},
            **kwargs
        )


# Feature Flag Exceptions
class FeatureNotEnabledError(JoulaaHTTPException):
    """Feature not enabled"""
    
    def __init__(self, feature_name: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            message=f"Feature '{feature_name}' is not enabled",
            error_code="FEATURE_NOT_ENABLED",
            details={"feature": feature_name},
            **kwargs
        )


# Regional & Localization Exceptions
class UnsupportedLanguageError(JoulaaHTTPException):
    """Unsupported language"""
    
    def __init__(self, language: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Language '{language}' is not supported",
            error_code="UNSUPPORTED_LANGUAGE",
            details={"language": language},
            **kwargs
        )


class UnsupportedRegionError(JoulaaHTTPException):
    """Unsupported region"""
    
    def __init__(self, region: str, **kwargs):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message=f"Region '{region}' is not supported",
            error_code="UNSUPPORTED_REGION",
            details={"region": region},
            **kwargs
        )
