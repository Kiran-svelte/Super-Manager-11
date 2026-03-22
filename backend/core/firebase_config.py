"""
Firebase Configuration and Database Management
================================================
Handles Firebase Admin SDK setup and Firestore operations for storing
AI identities, OAuth tokens, and service credentials.

Setup:
1. Download service account JSON from Firebase Console
2. Set FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON env var
3. Initialize the Firebase app

Author: Super Manager AI
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, asdict
from functools import lru_cache

logger = logging.getLogger(__name__)

# Check for Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logger.warning("firebase-admin not installed. Run: pip install firebase-admin")

# Global Firebase app instance
_firebase_app = None
_firestore_db = None


@dataclass
class FirebaseConfig:
    """Firebase configuration"""
    project_id: str = ""
    client_email: str = ""
    private_key_id: str = ""
    credentials_path: str = ""
    credentials_json: str = ""
    
    @classmethod
    def from_env(cls) -> 'FirebaseConfig':
        """Load configuration from environment variables"""
        return cls(
            project_id=os.getenv("FIREBASE_PROJECT_ID", "super-manager-dff69"),
            client_email=os.getenv("FIREBASE_CLIENT_EMAIL", ""),
            private_key_id=os.getenv("FIREBASE_PRIVATE_KEY_ID", ""),
            credentials_path=os.getenv("FIREBASE_CREDENTIALS_PATH", ""),
            credentials_json=os.getenv("FIREBASE_CREDENTIALS_JSON", ""),
        )


def get_firebase_credentials() -> Optional[Any]:
    """
    Get Firebase credentials from environment.
    
    Priority:
    1. FIREBASE_CREDENTIALS_JSON (inline JSON string)
    2. FIREBASE_CREDENTIALS_PATH (path to service account JSON file)
    """
    if not FIREBASE_AVAILABLE:
        return None
    
    config = FirebaseConfig.from_env()
    
    # Try inline JSON first
    if config.credentials_json:
        try:
            cred_dict = json.loads(config.credentials_json)
            return credentials.Certificate(cred_dict)
        except Exception as e:
            logger.error(f"Failed to parse FIREBASE_CREDENTIALS_JSON: {e}")
    
    # Try credentials file path
    if config.credentials_path and os.path.exists(config.credentials_path):
        try:
            return credentials.Certificate(config.credentials_path)
        except Exception as e:
            logger.error(f"Failed to load credentials from {config.credentials_path}: {e}")
    
    # Try default location
    default_paths = [
        "firebase-credentials.json",
        "backend/firebase-credentials.json",
        os.path.join(os.path.dirname(__file__), "..", "firebase-credentials.json"),
    ]
    
    for path in default_paths:
        if os.path.exists(path):
            try:
                return credentials.Certificate(path)
            except Exception as e:
                logger.warning(f"Failed to load from {path}: {e}")
    
    logger.warning("No Firebase credentials found")
    return None


def init_firebase() -> bool:
    """
    Initialize Firebase Admin SDK.
    
    Returns True if successful, False otherwise.
    """
    global _firebase_app, _firestore_db
    
    if not FIREBASE_AVAILABLE:
        logger.error("Firebase Admin SDK not available")
        return False
    
    # Check if already initialized
    if _firebase_app is not None:
        return True
    
    try:
        # Check for existing apps
        try:
            _firebase_app = firebase_admin.get_app()
            logger.info("Firebase already initialized, using existing app")
        except ValueError:
            # No app exists, initialize new one
            cred = get_firebase_credentials()
            if cred is None:
                logger.error("No Firebase credentials available")
                return False
            
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        
        # Initialize Firestore
        _firestore_db = firestore.client()
        logger.info("Firestore client initialized")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize Firebase: {e}")
        return False


def get_firestore_db():
    """Get Firestore database client"""
    global _firestore_db
    
    if _firestore_db is None:
        if not init_firebase():
            return None
    
    return _firestore_db


class FirebaseIdentityStore:
    """
    Firebase Firestore storage for AI identities and OAuth credentials.
    
    Collections:
    - ai_identities: User AI identity configurations
    - oauth_tokens: OAuth tokens for various services
    - service_credentials: API keys and service account credentials
    """
    
    def __init__(self):
        self.db = get_firestore_db()
        self.collection_name = "ai_identities"
        self.oauth_collection = "oauth_tokens"
        self.credentials_collection = "service_credentials"
    
    @property
    def available(self) -> bool:
        """Check if Firebase is available"""
        return self.db is not None
    
    async def save_identity(
        self,
        user_id: str,
        identity_data: Dict[str, Any]
    ) -> bool:
        """
        Save AI identity for a user.
        
        Args:
            user_id: User identifier
            identity_data: Identity configuration dict
            
        Returns:
            True if successful
        """
        if not self.available:
            logger.warning("Firebase not available, cannot save identity")
            return False
        
        try:
            # Add metadata
            identity_data["updated_at"] = datetime.utcnow().isoformat()
            if "created_at" not in identity_data:
                identity_data["created_at"] = datetime.utcnow().isoformat()
            
            # Save to Firestore
            doc_ref = self.db.collection(self.collection_name).document(user_id)
            doc_ref.set(identity_data, merge=True)
            
            logger.info(f"Saved identity for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save identity: {e}")
            return False
    
    async def get_identity(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get AI identity for a user.
        
        Args:
            user_id: User identifier
            
        Returns:
            Identity data dict or None
        """
        if not self.available:
            return None
        
        try:
            doc_ref = self.db.collection(self.collection_name).document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            return None
            
        except Exception as e:
            logger.error(f"Failed to get identity: {e}")
            return None
    
    async def delete_identity(self, user_id: str) -> bool:
        """Delete AI identity for a user"""
        if not self.available:
            return False
        
        try:
            doc_ref = self.db.collection(self.collection_name).document(user_id)
            doc_ref.delete()
            logger.info(f"Deleted identity for user {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete identity: {e}")
            return False
    
    async def list_identities(self, limit: int = 100) -> List[Dict[str, Any]]:
        """List all AI identities"""
        if not self.available:
            return []
        
        try:
            docs = self.db.collection(self.collection_name).limit(limit).stream()
            return [{"id": doc.id, **doc.to_dict()} for doc in docs]
        except Exception as e:
            logger.error(f"Failed to list identities: {e}")
            return []
    
    # =========================================================================
    # OAuth Token Management
    # =========================================================================
    
    async def save_oauth_token(
        self,
        user_id: str,
        service: str,
        token_data: Dict[str, Any]
    ) -> bool:
        """
        Save OAuth token for a service.
        
        Args:
            user_id: User identifier
            service: Service name (gmail, zoom, google, etc.)
            token_data: Token information including access_token, refresh_token, etc.
        """
        if not self.available:
            return False
        
        try:
            # Structure: oauth_tokens/{user_id}/services/{service}
            doc_ref = self.db.collection(self.oauth_collection)\
                .document(user_id)\
                .collection("services")\
                .document(service)
            
            token_data["updated_at"] = datetime.utcnow().isoformat()
            token_data["service"] = service
            
            doc_ref.set(token_data, merge=True)
            logger.info(f"Saved {service} OAuth token for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save OAuth token: {e}")
            return False
    
    async def get_oauth_token(
        self,
        user_id: str,
        service: str
    ) -> Optional[Dict[str, Any]]:
        """Get OAuth token for a service"""
        if not self.available:
            return None
        
        try:
            doc_ref = self.db.collection(self.oauth_collection)\
                .document(user_id)\
                .collection("services")\
                .document(service)
            
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
            
        except Exception as e:
            logger.error(f"Failed to get OAuth token: {e}")
            return None
    
    async def get_all_oauth_tokens(self, user_id: str) -> Dict[str, Dict[str, Any]]:
        """Get all OAuth tokens for a user"""
        if not self.available:
            return {}
        
        try:
            docs = self.db.collection(self.oauth_collection)\
                .document(user_id)\
                .collection("services")\
                .stream()
            
            return {doc.id: doc.to_dict() for doc in docs}
            
        except Exception as e:
            logger.error(f"Failed to get OAuth tokens: {e}")
            return {}
    
    async def delete_oauth_token(self, user_id: str, service: str) -> bool:
        """Delete OAuth token for a service"""
        if not self.available:
            return False
        
        try:
            doc_ref = self.db.collection(self.oauth_collection)\
                .document(user_id)\
                .collection("services")\
                .document(service)
            
            doc_ref.delete()
            logger.info(f"Deleted {service} OAuth token for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete OAuth token: {e}")
            return False
    
    # =========================================================================
    # Service Credentials Management  
    # =========================================================================
    
    async def save_service_credential(
        self,
        user_id: str,
        service: str,
        credential_data: Dict[str, Any]
    ) -> bool:
        """Save encrypted service credentials (API keys, etc.)"""
        if not self.available:
            return False
        
        try:
            doc_ref = self.db.collection(self.credentials_collection)\
                .document(user_id)\
                .collection("services")\
                .document(service)
            
            credential_data["updated_at"] = datetime.utcnow().isoformat()
            credential_data["service"] = service
            
            doc_ref.set(credential_data, merge=True)
            logger.info(f"Saved {service} credentials for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save credentials: {e}")
            return False
    
    async def get_service_credential(
        self,
        user_id: str,
        service: str
    ) -> Optional[Dict[str, Any]]:
        """Get service credentials"""
        if not self.available:
            return None
        
        try:
            doc_ref = self.db.collection(self.credentials_collection)\
                .document(user_id)\
                .collection("services")\
                .document(service)
            
            doc = doc_ref.get()
            return doc.to_dict() if doc.exists else None
            
        except Exception as e:
            logger.error(f"Failed to get credentials: {e}")
            return None


# Global store instance
_identity_store: Optional[FirebaseIdentityStore] = None


def get_firebase_identity_store() -> FirebaseIdentityStore:
    """Get the global Firebase identity store"""
    global _identity_store
    
    if _identity_store is None:
        _identity_store = FirebaseIdentityStore()
    
    return _identity_store


# =============================================================================
# Helper Functions
# =============================================================================

def is_firebase_configured() -> bool:
    """Check if Firebase is properly configured"""
    return FIREBASE_AVAILABLE and get_firebase_credentials() is not None


def get_firebase_status() -> Dict[str, Any]:
    """Get Firebase configuration status"""
    config = FirebaseConfig.from_env()
    
    return {
        "sdk_available": FIREBASE_AVAILABLE,
        "credentials_configured": get_firebase_credentials() is not None,
        "project_id": config.project_id,
        "credentials_path": bool(config.credentials_path),
        "credentials_json": bool(config.credentials_json),
        "firestore_ready": get_firestore_db() is not None,
    }
