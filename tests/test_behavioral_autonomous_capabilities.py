"""
Behavioral Tests: Autonomous Capabilities
==========================================
Tests that the autonomous capability system ACTUALLY works:
- CapabilityType enum
- ServiceInfo dataclass
- AcquiredCapability dataclass
- ServiceRegistry

README Requirements:
- Autonomous capability acquisition
- Service registry
- API key management
"""

import pytest
from dataclasses import is_dataclass
from datetime import datetime

from backend.core.autonomous_capabilities import (
    CapabilityType,
    ServiceInfo,
    AcquiredCapability,
    ServiceRegistry,
)


class TestCapabilityTypeEnum:
    """Test CapabilityType enum"""
    
    def test_has_image_generation(self):
        """Should have IMAGE_GENERATION"""
        assert hasattr(CapabilityType, "IMAGE_GENERATION")
        assert CapabilityType.IMAGE_GENERATION.value == "image_generation"
    
    def test_has_email_sending(self):
        """Should have EMAIL_SENDING"""
        assert hasattr(CapabilityType, "EMAIL_SENDING")
        assert CapabilityType.EMAIL_SENDING.value == "email_sending"
    
    def test_has_web_search(self):
        """Should have WEB_SEARCH"""
        assert hasattr(CapabilityType, "WEB_SEARCH")
        assert CapabilityType.WEB_SEARCH.value == "web_search"
    
    def test_has_payment_processing(self):
        """Should have PAYMENT_PROCESSING"""
        assert hasattr(CapabilityType, "PAYMENT_PROCESSING")
        assert CapabilityType.PAYMENT_PROCESSING.value == "payment_processing"
    
    def test_has_ai_chat(self):
        """Should have AI_CHAT"""
        assert hasattr(CapabilityType, "AI_CHAT")
        assert CapabilityType.AI_CHAT.value == "ai_chat"
    
    def test_has_code_execution(self):
        """Should have CODE_EXECUTION"""
        assert hasattr(CapabilityType, "CODE_EXECUTION")
        assert CapabilityType.CODE_EXECUTION.value == "code_execution"
    
    def test_has_file_storage(self):
        """Should have FILE_STORAGE"""
        assert hasattr(CapabilityType, "FILE_STORAGE")
        assert CapabilityType.FILE_STORAGE.value == "file_storage"
    
    def test_has_sms_sending(self):
        """Should have SMS_SENDING"""
        assert hasattr(CapabilityType, "SMS_SENDING")
        assert CapabilityType.SMS_SENDING.value == "sms_sending"
    
    def test_has_voice_call(self):
        """Should have VOICE_CALL"""
        assert hasattr(CapabilityType, "VOICE_CALL")
        assert CapabilityType.VOICE_CALL.value == "voice_call"
    
    def test_has_video_generation(self):
        """Should have VIDEO_GENERATION"""
        assert hasattr(CapabilityType, "VIDEO_GENERATION")
        assert CapabilityType.VIDEO_GENERATION.value == "video_generation"


class TestServiceInfoDataclass:
    """Test ServiceInfo dataclass"""
    
    def test_is_dataclass(self):
        """ServiceInfo should be a dataclass"""
        assert is_dataclass(ServiceInfo)
    
    def test_can_create(self):
        """ServiceInfo should be creatable"""
        info = ServiceInfo(
            name="Test Service",
            capability=CapabilityType.IMAGE_GENERATION,
            signup_url="https://test.com",
            api_key_env="TEST_API_KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=False,
            requires_payment=False,
            api_key_location="Settings"
        )
        assert info is not None
    
    def test_has_name(self):
        """Should have name"""
        info = ServiceInfo(
            name="MyService",
            capability=CapabilityType.AI_CHAT,
            signup_url="https://test.com",
            api_key_env="KEY",
            free_tier=True,
            signup_method="api",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.name == "MyService"
    
    def test_has_capability(self):
        """Should have capability"""
        info = ServiceInfo(
            name="Svc",
            capability=CapabilityType.EMAIL_SENDING,
            signup_url="https://test.com",
            api_key_env="KEY",
            free_tier=True,
            signup_method="api",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.capability == CapabilityType.EMAIL_SENDING
    
    def test_has_signup_url(self):
        """Should have signup_url"""
        info = ServiceInfo(
            name="Svc",
            capability=CapabilityType.AI_CHAT,
            signup_url="https://example.com/signup",
            api_key_env="KEY",
            free_tier=True,
            signup_method="api",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.signup_url == "https://example.com/signup"
    
    def test_has_api_key_env(self):
        """Should have api_key_env"""
        info = ServiceInfo(
            name="Svc",
            capability=CapabilityType.AI_CHAT,
            signup_url="url",
            api_key_env="MY_API_KEY",
            free_tier=True,
            signup_method="api",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.api_key_env == "MY_API_KEY"
    
    def test_has_free_tier(self):
        """Should have free_tier flag"""
        info = ServiceInfo(
            name="Svc",
            capability=CapabilityType.AI_CHAT,
            signup_url="url",
            api_key_env="KEY",
            free_tier=True,
            signup_method="api",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.free_tier is True
    
    def test_has_signup_method(self):
        """Should have signup_method"""
        info = ServiceInfo(
            name="Svc",
            capability=CapabilityType.AI_CHAT,
            signup_url="url",
            api_key_env="KEY",
            free_tier=True,
            signup_method="browser",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.signup_method == "browser"
    
    def test_default_notes_empty(self):
        """Default notes should be empty string"""
        info = ServiceInfo(
            name="Svc",
            capability=CapabilityType.AI_CHAT,
            signup_url="url",
            api_key_env="KEY",
            free_tier=True,
            signup_method="api",
            requires_verification=False,
            requires_payment=False,
            api_key_location="loc"
        )
        assert info.notes == ""


class TestAcquiredCapabilityDataclass:
    """Test AcquiredCapability dataclass"""
    
    def test_is_dataclass(self):
        """AcquiredCapability should be a dataclass"""
        assert is_dataclass(AcquiredCapability)
    
    def test_can_create(self):
        """AcquiredCapability should be creatable"""
        cap = AcquiredCapability(
            capability=CapabilityType.IMAGE_GENERATION,
            service_name="Test Service",
            api_key="sk-test-123"
        )
        assert cap is not None
    
    def test_has_capability(self):
        """Should have capability"""
        cap = AcquiredCapability(
            capability=CapabilityType.EMAIL_SENDING,
            service_name="Svc",
            api_key="key"
        )
        assert cap.capability == CapabilityType.EMAIL_SENDING
    
    def test_has_service_name(self):
        """Should have service_name"""
        cap = AcquiredCapability(
            capability=CapabilityType.AI_CHAT,
            service_name="My Service",
            api_key="key"
        )
        assert cap.service_name == "My Service"
    
    def test_has_api_key(self):
        """Should have api_key"""
        cap = AcquiredCapability(
            capability=CapabilityType.AI_CHAT,
            service_name="Svc",
            api_key="my-secret-key"
        )
        assert cap.api_key == "my-secret-key"
    
    def test_default_api_secret_none(self):
        """Default api_secret should be None"""
        cap = AcquiredCapability(
            capability=CapabilityType.AI_CHAT,
            service_name="Svc",
            api_key="key"
        )
        assert cap.api_secret is None
    
    def test_has_acquired_at_timestamp(self):
        """Should have acquired_at timestamp"""
        cap = AcquiredCapability(
            capability=CapabilityType.AI_CHAT,
            service_name="Svc",
            api_key="key"
        )
        assert isinstance(cap.acquired_at, datetime)
    
    def test_default_expires_at_none(self):
        """Default expires_at should be None"""
        cap = AcquiredCapability(
            capability=CapabilityType.AI_CHAT,
            service_name="Svc",
            api_key="key"
        )
        assert cap.expires_at is None
    
    def test_default_usage_limit_none(self):
        """Default usage_limit should be None"""
        cap = AcquiredCapability(
            capability=CapabilityType.AI_CHAT,
            service_name="Svc",
            api_key="key"
        )
        assert cap.usage_limit is None


class TestServiceRegistryClass:
    """Test ServiceRegistry class"""
    
    def test_class_exists(self):
        """ServiceRegistry class should exist"""
        assert ServiceRegistry is not None
    
    def test_has_services(self):
        """Should have SERVICES dict"""
        assert hasattr(ServiceRegistry, "SERVICES")
    
    def test_services_is_dict(self):
        """SERVICES should be a dict"""
        assert isinstance(ServiceRegistry.SERVICES, dict)
    
    def test_services_not_empty(self):
        """SERVICES should not be empty"""
        assert len(ServiceRegistry.SERVICES) > 0
    
    def test_all_services_are_serviceinfo(self):
        """All services should be ServiceInfo instances"""
        for name, info in ServiceRegistry.SERVICES.items():
            assert isinstance(info, ServiceInfo)


class TestServiceRegistryImageGeneration:
    """Test image generation services in registry"""
    
    def test_has_pollinations(self):
        """Should have pollinations service"""
        assert "pollinations" in ServiceRegistry.SERVICES
    
    def test_pollinations_is_image_generation(self):
        """Pollinations should be for image generation"""
        assert ServiceRegistry.SERVICES["pollinations"].capability == CapabilityType.IMAGE_GENERATION
    
    def test_pollinations_is_free(self):
        """Pollinations should be free tier"""
        assert ServiceRegistry.SERVICES["pollinations"].free_tier is True
    
    def test_has_together_ai(self):
        """Should have together_ai service"""
        assert "together_ai" in ServiceRegistry.SERVICES
    
    def test_has_replicate(self):
        """Should have replicate service"""
        assert "replicate" in ServiceRegistry.SERVICES


class TestServiceRegistryEmailServices:
    """Test email services in registry"""
    
    def test_has_resend(self):
        """Should have resend service"""
        assert "resend" in ServiceRegistry.SERVICES
    
    def test_resend_is_email(self):
        """Resend should be for email sending"""
        assert ServiceRegistry.SERVICES["resend"].capability == CapabilityType.EMAIL_SENDING
    
    def test_has_sendgrid(self):
        """Should have sendgrid service"""
        assert "sendgrid" in ServiceRegistry.SERVICES


class TestServiceRegistryPaymentFlag:
    """Test payment requirements in registry"""
    
    def test_all_services_have_payment_flag(self):
        """All services should have requires_payment flag"""
        for name, info in ServiceRegistry.SERVICES.items():
            assert hasattr(info, "requires_payment")
    
    def test_all_services_have_verification_flag(self):
        """All services should have requires_verification flag"""
        for name, info in ServiceRegistry.SERVICES.items():
            assert hasattr(info, "requires_verification")


class TestServiceRegistrySignupMethods:
    """Test signup methods in registry"""
    
    def test_signup_methods_valid(self):
        """Signup methods should be valid types"""
        valid_methods = {"api", "browser", "manual", "none"}
        for name, info in ServiceRegistry.SERVICES.items():
            assert info.signup_method in valid_methods, f"{name} has invalid method {info.signup_method}"
