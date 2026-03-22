"""
Behavioral Tests: AI Identity Manager
======================================
Tests that the identity module ACTUALLY works:
- AuthType enum
- IdentityStatus enum
- AIIdentity dataclass
- EncryptionManager class

README Requirements:
- Identity management
- Credential encryption
- Service authentication
"""

import pytest
import base64
from dataclasses import is_dataclass, fields

from backend.agent.identity import (
    SUPABASE_URL,
    SUPABASE_KEY,
    CAPTCHA_API_KEY,
    ENCRYPTION_SECRET,
    AuthType,
    IdentityStatus,
    AIIdentity,
    EncryptionManager,
)


class TestConfigurationVariables:
    """Test configuration environment variables"""
    
    def test_supabase_url_is_string(self):
        """SUPABASE_URL should be string"""
        assert isinstance(SUPABASE_URL, str)
    
    def test_supabase_key_is_string(self):
        """SUPABASE_KEY should be string"""
        assert isinstance(SUPABASE_KEY, str)
    
    def test_captcha_api_key_is_string(self):
        """CAPTCHA_API_KEY should be string"""
        assert isinstance(CAPTCHA_API_KEY, str)
    
    def test_encryption_secret_is_string(self):
        """ENCRYPTION_SECRET should be string"""
        assert isinstance(ENCRYPTION_SECRET, str)


class TestAuthTypeEnum:
    """Test AuthType enum"""
    
    def test_has_app_password(self):
        """Should have APP_PASSWORD auth type"""
        assert hasattr(AuthType, "APP_PASSWORD")
        assert AuthType.APP_PASSWORD.value == "app_password"
    
    def test_has_oauth(self):
        """Should have OAUTH auth type"""
        assert hasattr(AuthType, "OAUTH")
        assert AuthType.OAUTH.value == "oauth"
    
    def test_auth_type_count(self):
        """Should have 2 auth types"""
        assert len(AuthType) == 2


class TestIdentityStatusEnum:
    """Test IdentityStatus enum"""
    
    def test_has_pending_setup(self):
        """Should have PENDING_SETUP status"""
        assert hasattr(IdentityStatus, "PENDING_SETUP")
        assert IdentityStatus.PENDING_SETUP.value == "pending_setup"
    
    def test_has_active(self):
        """Should have ACTIVE status"""
        assert hasattr(IdentityStatus, "ACTIVE")
        assert IdentityStatus.ACTIVE.value == "active"
    
    def test_has_suspended(self):
        """Should have SUSPENDED status"""
        assert hasattr(IdentityStatus, "SUSPENDED")
        assert IdentityStatus.SUSPENDED.value == "suspended"
    
    def test_has_verification_needed(self):
        """Should have VERIFICATION_NEEDED status"""
        assert hasattr(IdentityStatus, "VERIFICATION_NEEDED")
        assert IdentityStatus.VERIFICATION_NEEDED.value == "verification_needed"
    
    def test_identity_status_count(self):
        """Should have 4 statuses"""
        assert len(IdentityStatus) == 4


class TestAIIdentityDataclass:
    """Test AIIdentity dataclass"""
    
    def test_is_dataclass(self):
        """AIIdentity should be a dataclass"""
        assert is_dataclass(AIIdentity)
    
    def test_can_create_minimal(self):
        """AIIdentity should be creatable with minimal fields"""
        identity = AIIdentity(
            id="id-1",
            user_id="user-1",
            email="ai@example.com"
        )
        assert identity is not None
    
    def test_has_id(self):
        """Should have id"""
        identity = AIIdentity(id="my-id", user_id="u", email="ai@test.com")
        assert identity.id == "my-id"
    
    def test_has_user_id(self):
        """Should have user_id"""
        identity = AIIdentity(id="i", user_id="my-user", email="ai@test.com")
        assert identity.user_id == "my-user"
    
    def test_has_email(self):
        """Should have email"""
        identity = AIIdentity(id="i", user_id="u", email="myai@example.com")
        assert identity.email == "myai@example.com"
    
    def test_default_display_name(self):
        """Default display_name should be 'AI Assistant'"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.display_name == "AI Assistant"
    
    def test_default_auth_type(self):
        """Default auth_type should be APP_PASSWORD"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.auth_type == AuthType.APP_PASSWORD
    
    def test_default_status(self):
        """Default status should be PENDING_SETUP"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.status == IdentityStatus.PENDING_SETUP
    
    def test_default_can_send_email(self):
        """Default can_send_email should be False"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.can_send_email is False
    
    def test_default_can_read_email(self):
        """Default can_read_email should be False"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.can_read_email is False
    
    def test_default_can_signup_services(self):
        """Default can_signup_services should be False"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.can_signup_services is False
    
    def test_default_metadata_empty(self):
        """Default metadata should be empty dict"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert identity.metadata == {}
    
    def test_has_private_password_field(self):
        """Should have _password field"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert hasattr(identity, "_password")
        assert identity._password is None
    
    def test_has_private_oauth_token_field(self):
        """Should have _oauth_token field"""
        identity = AIIdentity(id="i", user_id="u", email="ai@test.com")
        assert hasattr(identity, "_oauth_token")
        assert identity._oauth_token is None


class TestAIIdentityCustomValues:
    """Test AIIdentity with custom values"""
    
    def test_custom_display_name(self):
        """Should accept custom display_name"""
        identity = AIIdentity(
            id="i", user_id="u", email="ai@test.com",
            display_name="Super AI"
        )
        assert identity.display_name == "Super AI"
    
    def test_custom_auth_type(self):
        """Should accept custom auth_type"""
        identity = AIIdentity(
            id="i", user_id="u", email="ai@test.com",
            auth_type=AuthType.OAUTH
        )
        assert identity.auth_type == AuthType.OAUTH
    
    def test_custom_status(self):
        """Should accept custom status"""
        identity = AIIdentity(
            id="i", user_id="u", email="ai@test.com",
            status=IdentityStatus.ACTIVE
        )
        assert identity.status == IdentityStatus.ACTIVE
    
    def test_enable_capabilities(self):
        """Should accept capability flags"""
        identity = AIIdentity(
            id="i", user_id="u", email="ai@test.com",
            can_send_email=True,
            can_read_email=True,
            can_signup_services=True
        )
        assert identity.can_send_email is True
        assert identity.can_read_email is True
        assert identity.can_signup_services is True


class TestEncryptionManagerInit:
    """Test EncryptionManager initialization"""
    
    def test_can_instantiate_without_secret(self):
        """EncryptionManager should be instantiatable without secret"""
        manager = EncryptionManager(secret="")
        assert manager is not None
    
    def test_can_instantiate_with_secret(self):
        """EncryptionManager should be instantiatable with secret"""
        manager = EncryptionManager(secret="my-secret-key")
        assert manager is not None
    
    def test_enabled_with_secret(self):
        """_enabled should be True with secret"""
        manager = EncryptionManager(secret="my-secret-key")
        assert manager._enabled is True
    
    def test_disabled_without_secret(self):
        """_enabled should be False without secret"""
        manager = EncryptionManager(secret="")
        assert manager._enabled is False


class TestEncryptionManagerEncrypt:
    """Test EncryptionManager encrypt method"""
    
    def test_has_encrypt_method(self):
        """Should have encrypt method"""
        manager = EncryptionManager(secret="test")
        assert hasattr(manager, "encrypt")
        assert callable(manager.encrypt)
    
    def test_encrypt_returns_string(self):
        """encrypt should return string"""
        manager = EncryptionManager(secret="my-secret")
        result = manager.encrypt("hello")
        assert isinstance(result, str)
    
    def test_encrypt_empty_string(self):
        """encrypt should handle empty string"""
        manager = EncryptionManager(secret="my-secret")
        result = manager.encrypt("")
        assert result == ""
    
    def test_encrypt_produces_different_result(self):
        """encrypt should produce different result than input"""
        manager = EncryptionManager(secret="my-secret")
        plaintext = "my-password-123"
        result = manager.encrypt(plaintext)
        assert result != plaintext


class TestEncryptionManagerDecrypt:
    """Test EncryptionManager decrypt method"""
    
    def test_has_decrypt_method(self):
        """Should have decrypt method"""
        manager = EncryptionManager(secret="test")
        assert hasattr(manager, "decrypt")
        assert callable(manager.decrypt)
    
    def test_decrypt_returns_string(self):
        """decrypt should return string"""
        manager = EncryptionManager(secret="my-secret")
        encrypted = manager.encrypt("hello")
        result = manager.decrypt(encrypted)
        assert isinstance(result, str)
    
    def test_decrypt_empty_string(self):
        """decrypt should handle empty string"""
        manager = EncryptionManager(secret="my-secret")
        result = manager.decrypt("")
        assert result == ""


class TestEncryptionRoundTrip:
    """Test encrypt/decrypt round trip"""
    
    def test_round_trip_with_secret(self):
        """Encrypt then decrypt should return original"""
        manager = EncryptionManager(secret="strong-secret-key")
        original = "sensitive-data-12345"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original
    
    def test_round_trip_without_secret(self):
        """Encrypt then decrypt should work even without secret (base64)"""
        manager = EncryptionManager(secret="")
        original = "test-data"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        assert decrypted == original
    
    def test_round_trip_various_strings(self):
        """Round trip should work for various strings"""
        manager = EncryptionManager(secret="test-secret")
        test_strings = [
            "password123",
            "api-key-with-dashes",
            "special!@#$%^&*()",
            "unicode: こんにちは",
            "multi\nline\nstring",
        ]
        for original in test_strings:
            encrypted = manager.encrypt(original)
            decrypted = manager.decrypt(encrypted)
            assert decrypted == original, f"Failed for: {original}"


class TestEncryptionWithUserSalt:
    """Test EncryptionManager with user-specific salt"""
    
    def test_accepts_user_salt(self):
        """Should accept user_salt parameter"""
        manager = EncryptionManager(secret="secret", user_salt="user-123")
        assert manager is not None
    
    def test_different_salts_produce_different_results(self):
        """Different salts should produce different encrypted values"""
        manager1 = EncryptionManager(secret="same-secret", user_salt="user-1")
        manager2 = EncryptionManager(secret="same-secret", user_salt="user-2")
        
        plaintext = "my-password"
        encrypted1 = manager1.encrypt(plaintext)
        encrypted2 = manager2.encrypt(plaintext)
        
        # Different salts should produce different encrypted results
        assert encrypted1 != encrypted2
    
    def test_same_salt_produces_consistent_decryption(self):
        """Same salt should allow decrypting"""
        manager = EncryptionManager(secret="secret", user_salt="user-xyz")
        plaintext = "secret-value"
        encrypted = manager.encrypt(plaintext)
        
        # Recreate manager with same parameters
        manager2 = EncryptionManager(secret="secret", user_salt="user-xyz")
        decrypted = manager2.decrypt(encrypted)
        
        assert decrypted == plaintext


class TestFallbackBase64Encoding:
    """Test base64 fallback when no secret is provided"""
    
    def test_fallback_uses_base64(self):
        """Without secret, should use base64 encoding"""
        manager = EncryptionManager(secret="")
        plaintext = "test-value"
        encrypted = manager.encrypt(plaintext)
        
        # Should be valid base64
        decoded = base64.b64decode(encrypted).decode()
        assert decoded == plaintext
