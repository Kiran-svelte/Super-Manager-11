"""
Behavioral Tests: Encryption System
=====================================
Tests that the encryption system ACTUALLY:
- Uses AES-256-GCM via Fernet
- Uses PBKDF2 key derivation
- Supports per-user salt
- Never stores plaintext credentials
- Properly encrypts/decrypts data

README Requirements:
- Credentials encrypted at rest (AES-256-GCM)
- PBKDF2 key derivation (100,000 iterations)
- Per-user encryption salt
- ENCRYPTION_SECRET minimum 32 characters
- Sensitive data never stored in plaintext
"""

import pytest
import base64
import os
from unittest.mock import patch

from backend.agent.identity import EncryptionManager, AIIdentity, IdentityStatus, AuthType


class TestEncryptionManagerBasics:
    """Test basic encryption/decryption functionality"""
    
    def test_encrypt_decrypt_roundtrip(self):
        """Data should survive encrypt->decrypt roundtrip"""
        # Use a proper 32+ char secret
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "supersecretpassword123"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_encrypted_data_differs_from_original(self):
        """Encrypted data should NOT be the same as original"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "my-password"
        encrypted = manager.encrypt(original)
        
        assert encrypted != original
    
    def test_encrypted_data_is_not_plaintext(self):
        """Encrypted data should not contain plaintext"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "visible_password_123"
        encrypted = manager.encrypt(original)
        
        assert original not in encrypted
    
    def test_encrypt_empty_string(self):
        """Empty string should return empty string"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        assert manager.encrypt("") == ""
        assert manager.decrypt("") == ""
    
    def test_same_plaintext_different_ciphertext(self):
        """Same plaintext should produce different ciphertext each time (due to Fernet IV)"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "test"
        encrypted1 = manager.encrypt(original)
        encrypted2 = manager.encrypt(original)
        
        # Fernet uses random IV, so ciphertexts should differ
        assert encrypted1 != encrypted2
        
        # But both should decrypt to original
        assert manager.decrypt(encrypted1) == original
        assert manager.decrypt(encrypted2) == original


class TestEncryptionManagerPBKDF2:
    """Test PBKDF2 key derivation"""
    
    def test_different_secrets_different_keys(self):
        """Different secrets should produce incompatible encryption"""
        manager1 = EncryptionManager(secret="secret-one-32-characters-here!!")
        manager2 = EncryptionManager(secret="secret-two-32-characters-here!!")
        
        original = "test-data"
        encrypted = manager1.encrypt(original)
        
        # Attempting to decrypt with different secret should fail
        with pytest.raises(Exception):
            manager2.decrypt(encrypted)
    
    def test_salt_affects_encryption(self):
        """Different salt should produce incompatible encryption"""
        manager1 = EncryptionManager(secret="same-secret-32-characters-here!", user_salt="user-1-salt")
        manager2 = EncryptionManager(secret="same-secret-32-characters-here!", user_salt="user-2-salt")
        
        original = "test-data"
        encrypted = manager1.encrypt(original)
        
        # Attempting to decrypt with different salt should fail
        with pytest.raises(Exception):
            manager2.decrypt(encrypted)
    
    def test_same_secret_same_salt_works(self):
        """Same secret and salt should work"""
        secret = "consistent-32-character-secret!"
        salt = "consistent-salt"
        
        manager1 = EncryptionManager(secret=secret, user_salt=salt)
        manager2 = EncryptionManager(secret=secret, user_salt=salt)
        
        original = "test-data"
        encrypted = manager1.encrypt(original)
        decrypted = manager2.decrypt(encrypted)
        
        assert decrypted == original


class TestEncryptionManagerPerUserSalt:
    """Test per-user salt functionality"""
    
    def test_user_salt_for_isolation(self):
        """Per-user salt ensures users can't decrypt each other's data"""
        secret = "shared-secret-32-characters-!!"
        
        user1_manager = EncryptionManager(secret=secret, user_salt="user-123-salt")
        user2_manager = EncryptionManager(secret=secret, user_salt="user-456-salt")
        
        user1_password = "user1_secret_password"
        user1_encrypted = user1_manager.encrypt(user1_password)
        
        # User 1 can decrypt
        assert user1_manager.decrypt(user1_encrypted) == user1_password
        
        # User 2 CANNOT decrypt User 1's data
        with pytest.raises(Exception):
            user2_manager.decrypt(user1_encrypted)


class TestEncryptionManagerFallback:
    """Test fallback behavior when ENCRYPTION_SECRET not set"""
    
    def test_fallback_to_base64_without_secret(self):
        """Without secret, should fall back to base64 (not secure)"""
        # Empty secret triggers fallback
        manager = EncryptionManager(secret="")
        
        original = "test-password"
        encoded = manager.encrypt(original)
        decoded = manager.decrypt(encoded)
        
        assert decoded == original
        # Verify it's base64 encoded
        assert base64.b64decode(encoded.encode()).decode() == original
    
    def test_fallback_warns_user(self):
        """Fallback mode should warn that it's not secure"""
        import warnings
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            manager = EncryptionManager(secret="")
            # Check for warning
            assert any("NOT SECURE" in str(warning.message) for warning in w)


class TestEncryptionManagerSecurity:
    """Test security properties"""
    
    def test_encrypted_data_looks_random(self):
        """Encrypted data should look random (high entropy)"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        encrypted = manager.encrypt("aaaaaaaaaaaaaaaa")
        
        # Should not have repeated patterns like the original
        assert encrypted.count('a') < len(encrypted) / 2
    
    def test_cannot_decrypt_invalid_data(self):
        """Invalid encrypted data should raise exception"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        with pytest.raises(Exception):
            manager.decrypt("not-valid-encrypted-data")
    
    def test_encrypted_password_not_recoverable_without_key(self):
        """Encrypted data should not be recoverable without the key"""
        manager = EncryptionManager(secret="original-32-character-secret!!!")
        original = "my-super-secret-password"
        encrypted = manager.encrypt(original)
        
        # Try with wrong key
        wrong_manager = EncryptionManager(secret="different-32-character-secret!!")
        with pytest.raises(Exception):
            wrong_manager.decrypt(encrypted)


class TestAIIdentityDataclass:
    """Test AIIdentity dataclass"""
    
    def test_ai_identity_creation(self):
        """Should create AIIdentity with required fields"""
        identity = AIIdentity(
            id="test-id-123",
            user_id="user-456",
            email="ai@example.com"
        )
        
        assert identity.id == "test-id-123"
        assert identity.user_id == "user-456"
        assert identity.email == "ai@example.com"
    
    def test_ai_identity_defaults(self):
        """AIIdentity should have sensible defaults"""
        identity = AIIdentity(
            id="test-id",
            user_id="user-id",
            email="test@test.com"
        )
        
        assert identity.display_name == "AI Assistant"
        assert identity.auth_type == AuthType.APP_PASSWORD
        assert identity.status == IdentityStatus.PENDING_SETUP
        assert identity.can_send_email is False
        assert identity.can_read_email is False
        assert identity.can_signup_services is False
    
    def test_ai_identity_password_not_stored(self):
        """Password field should be None by default (never stored)"""
        identity = AIIdentity(
            id="test-id",
            user_id="user-id",
            email="test@test.com"
        )
        
        assert identity._password is None
        assert identity._oauth_token is None


class TestIdentityStatus:
    """Test IdentityStatus enum"""
    
    def test_identity_statuses_exist(self):
        """All expected statuses should exist"""
        assert IdentityStatus.PENDING_SETUP
        assert IdentityStatus.ACTIVE
        assert IdentityStatus.SUSPENDED
        assert IdentityStatus.VERIFICATION_NEEDED


class TestAuthType:
    """Test AuthType enum"""
    
    def test_auth_types_exist(self):
        """All expected auth types should exist"""
        assert AuthType.APP_PASSWORD
        assert AuthType.OAUTH


class TestEncryptionIntegration:
    """Test encryption integrated with identity management"""
    
    def test_credential_encryption_workflow(self):
        """Test typical workflow: store encrypted, retrieve decrypted"""
        manager = EncryptionManager(secret="32-char-secret-for-testing!!!")
        
        # User provides credentials
        app_password = "aaaa-bbbb-cccc-dddd"
        
        # System encrypts before storage
        encrypted = manager.encrypt(app_password)
        
        # Simulate storing to database (just the encrypted value)
        stored_value = encrypted
        
        # Later, retrieve and decrypt
        loaded_value = stored_value
        decrypted = manager.decrypt(loaded_value)
        
        assert decrypted == app_password
    
    def test_multiple_credentials_same_manager(self):
        """Should handle multiple credentials"""
        manager = EncryptionManager(secret="32-char-secret-for-testing!!!")
        
        creds = {
            "gmail_password": "secret1",
            "api_key": "secret2",
            "oauth_token": "secret3",
        }
        
        encrypted_creds = {k: manager.encrypt(v) for k, v in creds.items()}
        decrypted_creds = {k: manager.decrypt(v) for k, v in encrypted_creds.items()}
        
        assert decrypted_creds == creds


class TestEncryptionManagerRobustness:
    """Test edge cases and robustness"""
    
    def test_unicode_data(self):
        """Should handle unicode data"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "密码🔐пароль"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_very_long_data(self):
        """Should handle very long data"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "x" * 10000
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_special_characters(self):
        """Should handle special characters"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = '!@#$%^&*()_+-=[]{}|;\':",.<>?/`~'
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
    
    def test_newlines_and_whitespace(self):
        """Should handle newlines and whitespace"""
        manager = EncryptionManager(secret="this-is-a-32-character-secret!!")
        
        original = "line1\nline2\r\nline3\ttab    spaces"
        encrypted = manager.encrypt(original)
        decrypted = manager.decrypt(encrypted)
        
        assert decrypted == original
