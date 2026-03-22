import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag
from typing import Optional

class CryptoVault:
    """
    AES-256-GCM encryption utility for secure storage of integration tokens.
    Implements Layer 6 Security Requirements from README.
    """
    
    def __init__(self, master_key: Optional[bytes] = None):
        # In a real environment, this should come from a secure KMS or env var.
        # Fallback to a development key if not provided (NOT for production).
        env_key = os.environ.get("ENCRYPTION_MASTER_KEY")
        if env_key:
            self.key = base64.b64decode(env_key)
        elif master_key:
            self.key = master_key
        else:
            # 32 bytes for AES-256
            self.key = b'01234567890123456789012345678901'
            
    def encrypt(self, plaintext: str) -> str:
        """Encrypt string using AES-256-GCM."""
        aesgcm = AESGCM(self.key)
        nonce = os.urandom(12) # 96-bit nonce is recommended for GCM
        ciphertext = aesgcm.encrypt(nonce, plaintext.encode('utf-8'), None)
        # Store as base64 combined nonce + ciphertext
        return base64.b64encode(nonce + ciphertext).decode('utf-8')

    def decrypt(self, encrypted_b64: str) -> str:
        """Decrypt string using AES-256-GCM."""
        try:
            encrypted_data = base64.b64decode(encrypted_b64)
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            aesgcm = AESGCM(self.key)
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            return plaintext.decode('utf-8')
        except (ValueError, InvalidTag, TypeError) as e:
            raise ValueError(f"Decryption failed: {str(e)}")

# Singleton instance for the application
vault = CryptoVault()
