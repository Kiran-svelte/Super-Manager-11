"""
Behavioral Tests: Errors Module
=================================
Tests that the errors module ACTUALLY works:
- ErrorSeverity enum
- ErrorCategory enum
- SuperManagerError base class
- Specific error classes

README Requirements:
- Custom exception hierarchy
- Error tracking
- User-friendly error responses
"""

import pytest
from datetime import datetime

from backend.core.errors import (
    ErrorSeverity,
    ErrorCategory,
    SuperManagerError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
)


class TestErrorSeverityEnum:
    """Test ErrorSeverity enum"""
    
    def test_debug_value(self):
        """DEBUG should have correct value"""
        assert ErrorSeverity.DEBUG == "debug"
    
    def test_info_value(self):
        """INFO should have correct value"""
        assert ErrorSeverity.INFO == "info"
    
    def test_warning_value(self):
        """WARNING should have correct value"""
        assert ErrorSeverity.WARNING == "warning"
    
    def test_error_value(self):
        """ERROR should have correct value"""
        assert ErrorSeverity.ERROR == "error"
    
    def test_critical_value(self):
        """CRITICAL should have correct value"""
        assert ErrorSeverity.CRITICAL == "critical"
    
    def test_all_severities(self):
        """Should have exactly 5 severities"""
        severities = list(ErrorSeverity)
        assert len(severities) == 5


class TestErrorCategoryEnum:
    """Test ErrorCategory enum"""
    
    def test_validation_value(self):
        """VALIDATION should have correct value"""
        assert ErrorCategory.VALIDATION == "validation"
    
    def test_authentication_value(self):
        """AUTHENTICATION should have correct value"""
        assert ErrorCategory.AUTHENTICATION == "authentication"
    
    def test_authorization_value(self):
        """AUTHORIZATION should have correct value"""
        assert ErrorCategory.AUTHORIZATION == "authorization"
    
    def test_not_found_value(self):
        """NOT_FOUND should have correct value"""
        assert ErrorCategory.NOT_FOUND == "not_found"
    
    def test_rate_limit_value(self):
        """RATE_LIMIT should have correct value"""
        assert ErrorCategory.RATE_LIMIT == "rate_limit"
    
    def test_external_api_value(self):
        """EXTERNAL_API should have correct value"""
        assert ErrorCategory.EXTERNAL_API == "external_api"
    
    def test_database_value(self):
        """DATABASE should have correct value"""
        assert ErrorCategory.DATABASE == "database"
    
    def test_network_value(self):
        """NETWORK should have correct value"""
        assert ErrorCategory.NETWORK == "network"
    
    def test_internal_value(self):
        """INTERNAL should have correct value"""
        assert ErrorCategory.INTERNAL == "internal"
    
    def test_timeout_value(self):
        """TIMEOUT should have correct value"""
        assert ErrorCategory.TIMEOUT == "timeout"


class TestSuperManagerError:
    """Test SuperManagerError base class"""
    
    def test_can_create(self):
        """SuperManagerError should be creatable"""
        error = SuperManagerError("Test error")
        assert error is not None
    
    def test_is_exception(self):
        """SuperManagerError should be an Exception"""
        error = SuperManagerError("Test error")
        assert isinstance(error, Exception)
    
    def test_has_message(self):
        """Should have message"""
        error = SuperManagerError("Something went wrong")
        assert error.message == "Something went wrong"
    
    def test_default_error_code(self):
        """Should have default error_code"""
        error = SuperManagerError("Test")
        assert error.error_code == "UNKNOWN_ERROR"
    
    def test_custom_error_code(self):
        """Should accept custom error_code"""
        error = SuperManagerError("Test", error_code="CUSTOM_ERROR")
        assert error.error_code == "CUSTOM_ERROR"
    
    def test_default_severity(self):
        """Should have default severity of ERROR"""
        error = SuperManagerError("Test")
        assert error.severity == ErrorSeverity.ERROR
    
    def test_custom_severity(self):
        """Should accept custom severity"""
        error = SuperManagerError("Test", severity=ErrorSeverity.WARNING)
        assert error.severity == ErrorSeverity.WARNING
    
    def test_default_category(self):
        """Should have default category of INTERNAL"""
        error = SuperManagerError("Test")
        assert error.category == ErrorCategory.INTERNAL
    
    def test_custom_category(self):
        """Should accept custom category"""
        error = SuperManagerError("Test", category=ErrorCategory.DATABASE)
        assert error.category == ErrorCategory.DATABASE
    
    def test_default_details_empty(self):
        """Should have default empty details"""
        error = SuperManagerError("Test")
        assert error.details == {}
    
    def test_custom_details(self):
        """Should accept custom details"""
        error = SuperManagerError("Test", details={"key": "value"})
        assert error.details["key"] == "value"
    
    def test_default_user_message(self):
        """Should have default user message"""
        error = SuperManagerError("Test")
        assert "error" in error.user_message.lower()
    
    def test_custom_user_message(self):
        """Should accept custom user_message"""
        error = SuperManagerError("Test", user_message="Please try again")
        assert error.user_message == "Please try again"
    
    def test_default_recoverable(self):
        """Should be recoverable by default"""
        error = SuperManagerError("Test")
        assert error.recoverable is True
    
    def test_custom_recoverable(self):
        """Should accept custom recoverable"""
        error = SuperManagerError("Test", recoverable=False)
        assert error.recoverable is False
    
    def test_default_http_status(self):
        """Should have default http_status of 500"""
        error = SuperManagerError("Test")
        assert error.http_status == 500
    
    def test_custom_http_status(self):
        """Should accept custom http_status"""
        error = SuperManagerError("Test", http_status=400)
        assert error.http_status == 400
    
    def test_has_error_id(self):
        """Should generate error_id"""
        error = SuperManagerError("Test")
        assert hasattr(error, "error_id")
        assert len(error.error_id) == 8
    
    def test_has_timestamp(self):
        """Should have timestamp"""
        error = SuperManagerError("Test")
        assert hasattr(error, "timestamp")
        assert isinstance(error.timestamp, datetime)


class TestSuperManagerErrorSerialization:
    """Test SuperManagerError serialization"""
    
    def test_to_dict_returns_dict(self):
        """to_dict should return dictionary"""
        error = SuperManagerError("Test")
        result = error.to_dict()
        assert isinstance(result, dict)
    
    def test_to_dict_has_error_flag(self):
        """to_dict should have error=True"""
        error = SuperManagerError("Test")
        result = error.to_dict()
        assert result["error"] is True
    
    def test_to_dict_has_error_id(self):
        """to_dict should have error_id"""
        error = SuperManagerError("Test")
        result = error.to_dict()
        assert "error_id" in result
    
    def test_to_dict_has_code(self):
        """to_dict should have code"""
        error = SuperManagerError("Test", error_code="MY_CODE")
        result = error.to_dict()
        assert result["code"] == "MY_CODE"
    
    def test_to_dict_has_user_message(self):
        """to_dict should use user_message, not internal message"""
        error = SuperManagerError("Internal error", user_message="User friendly")
        result = error.to_dict()
        assert result["message"] == "User friendly"
    
    def test_to_dict_has_category(self):
        """to_dict should have category value"""
        error = SuperManagerError("Test", category=ErrorCategory.DATABASE)
        result = error.to_dict()
        assert result["category"] == "database"
    
    def test_to_dict_has_timestamp(self):
        """to_dict should have timestamp"""
        error = SuperManagerError("Test")
        result = error.to_dict()
        assert "timestamp" in result
    
    def test_to_dict_has_recoverable(self):
        """to_dict should have recoverable"""
        error = SuperManagerError("Test", recoverable=False)
        result = error.to_dict()
        assert result["recoverable"] is False
    
    def test_to_log_dict_has_internal_message(self):
        """to_log_dict should include internal message"""
        error = SuperManagerError("Internal details")
        result = error.to_log_dict()
        assert result["internal_message"] == "Internal details"
    
    def test_to_log_dict_has_details(self):
        """to_log_dict should include details"""
        error = SuperManagerError("Test", details={"key": "value"})
        result = error.to_log_dict()
        assert result["details"]["key"] == "value"


class TestValidationError:
    """Test ValidationError class"""
    
    def test_can_create(self):
        """ValidationError should be creatable"""
        error = ValidationError("Invalid email")
        assert error is not None
    
    def test_is_super_manager_error(self):
        """Should be SuperManagerError"""
        error = ValidationError("Invalid email")
        assert isinstance(error, SuperManagerError)
    
    def test_error_code(self):
        """Should have VALIDATION_ERROR code"""
        error = ValidationError("Invalid")
        assert error.error_code == "VALIDATION_ERROR"
    
    def test_category(self):
        """Should have VALIDATION category"""
        error = ValidationError("Invalid")
        assert error.category == ErrorCategory.VALIDATION
    
    def test_http_status(self):
        """Should have 400 status"""
        error = ValidationError("Invalid")
        assert error.http_status == 400
    
    def test_field_in_details(self):
        """Should store field in details"""
        error = ValidationError("Invalid email", field="email")
        assert error.details["field"] == "email"


class TestAuthenticationError:
    """Test AuthenticationError class"""
    
    def test_can_create(self):
        """AuthenticationError should be creatable"""
        error = AuthenticationError()
        assert error is not None
    
    def test_default_message(self):
        """Should have default message"""
        error = AuthenticationError()
        assert "Authentication" in error.message or "auth" in error.message.lower()
    
    def test_error_code(self):
        """Should have AUTH_REQUIRED code"""
        error = AuthenticationError()
        assert error.error_code == "AUTH_REQUIRED"
    
    def test_category(self):
        """Should have AUTHENTICATION category"""
        error = AuthenticationError()
        assert error.category == ErrorCategory.AUTHENTICATION
    
    def test_http_status(self):
        """Should have 401 status"""
        error = AuthenticationError()
        assert error.http_status == 401


class TestAuthorizationError:
    """Test AuthorizationError class"""
    
    def test_can_create(self):
        """AuthorizationError should be creatable"""
        error = AuthorizationError()
        assert error is not None
    
    def test_error_code(self):
        """Should have FORBIDDEN code"""
        error = AuthorizationError()
        assert error.error_code == "FORBIDDEN"
    
    def test_category(self):
        """Should have AUTHORIZATION category"""
        error = AuthorizationError()
        assert error.category == ErrorCategory.AUTHORIZATION
    
    def test_http_status(self):
        """Should have 403 status"""
        error = AuthorizationError()
        assert error.http_status == 403
    
    def test_resource_in_details(self):
        """Should store resource in details"""
        error = AuthorizationError(resource="admin_panel")
        assert error.details["resource"] == "admin_panel"


class TestNotFoundError:
    """Test NotFoundError class"""
    
    def test_can_create(self):
        """NotFoundError should be creatable"""
        error = NotFoundError("User")
        assert error is not None
    
    def test_message_format(self):
        """Should format message with resource type"""
        error = NotFoundError("User")
        assert "User" in error.message
        assert "not found" in error.message.lower()
    
    def test_message_with_id(self):
        """Should include ID in message"""
        error = NotFoundError("User", resource_id="123")
        assert "123" in error.message
    
    def test_error_code(self):
        """Should have NOT_FOUND code"""
        error = NotFoundError("Task")
        assert error.error_code == "NOT_FOUND"
    
    def test_category(self):
        """Should have NOT_FOUND category"""
        error = NotFoundError("Task")
        assert error.category == ErrorCategory.NOT_FOUND
    
    def test_http_status(self):
        """Should have 404 status"""
        error = NotFoundError("Task")
        assert error.http_status == 404
    
    def test_details_have_resource_info(self):
        """Should store resource info in details"""
        error = NotFoundError("User", resource_id="abc123")
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "abc123"


class TestErrorRaising:
    """Test raising and catching errors"""
    
    def test_raise_validation_error(self):
        """Should be raisable"""
        with pytest.raises(ValidationError):
            raise ValidationError("Invalid input")
    
    def test_catch_as_super_manager_error(self):
        """Should be catchable as base class"""
        with pytest.raises(SuperManagerError):
            raise ValidationError("Invalid input")
    
    def test_catch_as_exception(self):
        """Should be catchable as Exception"""
        with pytest.raises(Exception):
            raise ValidationError("Invalid input")
    
    def test_access_error_attributes(self):
        """Should access attributes after catching"""
        try:
            raise NotFoundError("User", resource_id="123")
        except NotFoundError as e:
            assert e.http_status == 404
            assert e.details["resource_id"] == "123"


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_message(self):
        """Should handle empty message"""
        error = SuperManagerError("")
        assert error.message == ""
    
    def test_very_long_message(self):
        """Should handle very long message"""
        long_msg = "x" * 10000
        error = SuperManagerError(long_msg)
        assert len(error.message) == 10000
    
    def test_unicode_message(self):
        """Should handle unicode message"""
        error = SuperManagerError("错误信息 🎉")
        assert "错误" in error.message
    
    def test_nested_details(self):
        """Should handle nested details"""
        error = SuperManagerError("Test", details={
            "user": {"id": 1, "name": "test"},
            "context": ["a", "b", "c"]
        })
        assert error.details["user"]["id"] == 1
