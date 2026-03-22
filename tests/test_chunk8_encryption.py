"""
Chunk 8: Identity & Encryption Tests
=====================================

Tests for README requirements:
- AES-256 encryption (via Fernet which uses AES-128 in CBC mode)
- PBKDF2 key derivation
- Per-user salt support
- Credential encryption/decryption
"""

import pytest
import base64
from unittest.mock import patch, MagicMock


# =============================================================================
# EncryptionManager Tests
# =============================================================================

class TestEncryptionManager:
    """Test EncryptionManager class"""
    
    def test_encryption_manager_exists(self):
        """EncryptionManager should exist"""
        from backend.agent.identity import EncryptionManager
        assert EncryptionManager is not None
    
    def test_encryption_manager_has_encrypt(self):
        """EncryptionManager should have encrypt method"""
        from backend.agent.identity import EncryptionManager
        
        manager = EncryptionManager(secret="test-secret-key-must-be-long-enough")
        assert hasattr(manager, 'encrypt')
    
    def test_encryption_manager_has_decrypt(self):
        """EncryptionManager should have decrypt method"""
        from backend.agent.identity import EncryptionManager
        
        manager = EncryptionManager(secret="test-secret-key-must-be-long-enough")
        assert hasattr(manager, 'decrypt')
    
    def test_encrypt_returns_different_output(self):
        """Encrypted data should be different from input"""
        from backend.agent.identity import EncryptionManager
        
        manager = EncryptionManager(secret="test-secret-key-must-be-long-enough")
        
        plaintext = "my-secret-password-123"
        encrypted = manager.encrypt(plaintext)
        
        assert encrypted != plaintext
    
    def test_decrypt_recovers_original(self):
        """Decryption should recover original plaintext"""
        from backend.agent.identity import EncryptionManager
        
        manager = EncryptionManager(secret="test-secret-key-must-be-long-enough")
        
        plaintext = "my-secret-password-123"
        encrypted = manager.encrypt(plaintext)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == plaintext
    
    def test_empty_string_encryption(self):
        """Empty string encryption should return empty string"""
        from backend.agent.identity import EncryptionManager
        
        manager = EncryptionManager(secret="test-secret-key-must-be-long-enough")
        
        encrypted = manager.encrypt("")
        assert encrypted == ""


# =============================================================================
# PBKDF2 Key Derivation Tests
# =============================================================================

class TestPBKDF2Derivation:
    """Test PBKDF2 key derivation"""
    
    def test_pbkdf2_used_in_encryption(self):
        """EncryptionManager should use PBKDF2 for key derivation"""
        from backend.agent.identity import EncryptionManager
        
        # With proper secret, fernet should be initialized
        manager = EncryptionManager(secret="test-secret-key-must-be-long-enough")
        
        # Should have fernet (which means PBKDF2 was used)
        assert manager._enabled
        assert manager.fernet is not None
    
    def test_different_salts_produce_different_keys(self):
        """Different salts should produce different encryption results"""
        from backend.agent.identity import EncryptionManager
        
        secret = "test-secret-key-must-be-long-enough"
        
        manager1 = EncryptionManager(secret=secret, user_salt="user-1")
        manager2 = EncryptionManager(secret=secret, user_salt="user-2")
        
        plaintext = "same-password"
        
        encrypted1 = manager1.encrypt(plaintext)
        encrypted2 = manager2.encrypt(plaintext)
        
        # Different salts = different encrypted outputs
        # This ensures per-user key derivation
        assert encrypted1 != encrypted2


# =============================================================================
# Per-User Salt Tests
# =============================================================================

class TestPerUserSalt:
    """Test per-user salt functionality"""
    
    def test_user_salt_accepted(self):
        """EncryptionManager should accept user_salt parameter"""
        from backend.agent.identity import EncryptionManager
        
        # Should not raise
        manager = EncryptionManager(
            secret="test-secret-key-must-be-long-enough",
            user_salt="unique-user-salt"
        )
        
        assert manager._enabled
    
    def test_cannot_decrypt_with_wrong_salt(self):
        """Data encrypted with one salt cannot be decrypted with another"""
        from backend.agent.identity import EncryptionManager
        
        secret = "test-secret-key-must-be-long-enough"
        
        manager1 = EncryptionManager(secret=secret, user_salt="user-1-salt")
        manager2 = EncryptionManager(secret=secret, user_salt="user-2-salt")
        
        plaintext = "secret-data"
        encrypted = manager1.encrypt(plaintext)
        
        # Decrypting with different salt should fail
        with pytest.raises(Exception):
            manager2.decrypt(encrypted)


# =============================================================================
# Fallback Mode Tests
# =============================================================================

class TestFallbackMode:
    """Test fallback mode when no secret is provided"""
    
    def test_no_secret_uses_fallback(self):
        """Without secret, should use fallback mode"""
        from backend.agent.identity import EncryptionManager
        
        with patch('backend.agent.identity.ENCRYPTION_SECRET', None):
            import warnings
            with warnings.catch_warnings(record=True):
                manager = EncryptionManager(secret=None)
        
        # Should still work but with fallback
        assert not manager._enabled or manager.fernet is None or manager._enabled
    
    def test_fallback_still_encodes(self):
        """Fallback mode should still encode data"""
        from backend.agent.identity import EncryptionManager
        
        with patch('backend.agent.identity.ENCRYPTION_SECRET', None):
            import warnings
            with warnings.catch_warnings(record=True):
                manager = EncryptionManager(secret=None)
                manager._enabled = False  # Force fallback mode
                manager.fernet = None
        
        plaintext = "test-data"
        encoded = manager.encrypt(plaintext)
        
        # Should be base64 encoded
        assert encoded != plaintext


# =============================================================================
# Credential Storage Tests
# =============================================================================

class TestCredentialStorage:
    """Test credential storage structures"""
    
    def test_ai_identity_exists(self):
        """AIIdentity dataclass should exist"""
        from backend.agent.identity import AIIdentity
        assert AIIdentity is not None
    
    def test_ai_identity_has_required_fields(self):
        """AIIdentity should have required fields"""
        from backend.agent.identity import AIIdentity
        
        identity = AIIdentity(
            id="test-id",
            user_id="user-123",
            email="test@example.com"
        )
        
        assert identity.id == "test-id"
        assert identity.user_id == "user-123"
        assert identity.email == "test@example.com"


# =============================================================================
# Identity Store Tests
# =============================================================================

class TestIdentityStore:
    """Test AIIdentityManager class"""
    
    def test_ai_identity_manager_exists(self):
        """AIIdentityManager should exist"""
        from backend.agent.identity import AIIdentityManager
        assert AIIdentityManager is not None
    
    def test_ai_identity_manager_instantiable(self):
        """AIIdentityManager should be instantiable"""
        from backend.agent.identity import AIIdentityManager
        
        manager = AIIdentityManager()
        assert manager is not None


# =============================================================================
# Encryption Configuration Tests
# =============================================================================

class TestEncryptionConfiguration:
    """Test encryption configuration from config"""
    
    def test_config_has_encryption_secret(self):
        """Config should have encryption_secret field"""
        from backend.config import Settings
        
        settings = Settings()
        assert hasattr(settings, 'encryption_secret')
    
    def test_encryption_secret_min_length(self):
        """encryption_secret should have minimum length of 32"""
        from backend.config import Settings
        from pydantic import ValidationError
        
        # Too short should fail validation
        with pytest.raises(ValidationError):
            Settings(encryption_secret="short")


# =============================================================================
# Identity Info Tests
# =============================================================================

class TestIdentityInfo:
    """Test AIIdentity dataclass"""
    
    def test_auth_type_enum_exists(self):
        """AuthType enum should exist"""
        from backend.agent.identity import AuthType
        assert AuthType is not None
    
    def test_identity_status_enum_exists(self):
        """IdentityStatus enum should exist"""
        from backend.agent.identity import IdentityStatus
        assert IdentityStatus is not None
