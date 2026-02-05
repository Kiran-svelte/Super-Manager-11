"""
File-based session storage for conversation persistence
"""
import json
import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import threading

class FileSessionStore:
    """Thread-safe file-based session storage"""
    
    def __init__(self, storage_dir: str = "sessions"):
        self.storage_dir = storage_dir
        self.lock = threading.Lock()
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(self.storage_dir):
            os.makedirs(self.storage_dir)
    
    def _get_session_path(self, session_id: str) -> str:
        """Get file path for session"""
        return os.path.join(self.storage_dir, f"{session_id}.json")
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]):
        """Save session to file"""
        with self.lock:
            session_path = self._get_session_path(session_id)
            
            # Add metadata
            data_with_meta = {
                "session_id": session_id,
                "data": session_data,
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
            
            with open(session_path, 'w') as f:
                json.dump(data_with_meta, f, indent=2, default=str)
            
            print(f"[SESSION_STORE] Saved session {session_id} to {session_path}")
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Load session from file"""
        with self.lock:
            session_path = self._get_session_path(session_id)
            
            if not os.path.exists(session_path):
                print(f"[SESSION_STORE] Session {session_id} not found")
                return None
            
            try:
                with open(session_path, 'r') as f:
                    data_with_meta = json.load(f)
                
                # Check expiration
                expires_at = datetime.fromisoformat(data_with_meta["expires_at"])
                if datetime.utcnow() > expires_at:
                    print(f"[SESSION_STORE] Session {session_id} expired")
                    os.remove(session_path)
                    return None
                
                print(f"[SESSION_STORE] Loaded session {session_id}")
                return data_with_meta["data"]
            
            except Exception as e:
                print(f"[SESSION_STORE] Error loading session {session_id}: {e}")
                return None
    
    def delete_session(self, session_id: str):
        """Delete session file"""
        with self.lock:
            session_path = self._get_session_path(session_id)
            if os.path.exists(session_path):
                os.remove(session_path)
                print(f"[SESSION_STORE] Deleted session {session_id}")
    
    def list_sessions(self) -> list:
        """List all active sessions"""
        with self.lock:
            sessions = []
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    session_id = filename[:-5]  # Remove .json
                    sessions.append(session_id)
            return sessions
    
    def cleanup_expired(self):
        """Remove expired sessions"""
        with self.lock:
            now = datetime.utcnow()
            for filename in os.listdir(self.storage_dir):
                if filename.endswith('.json'):
                    session_path = os.path.join(self.storage_dir, filename)
                    try:
                        with open(session_path, 'r') as f:
                            data = json.load(f)
                        expires_at = datetime.fromisoformat(data["expires_at"])
                        if now > expires_at:
                            os.remove(session_path)
                            print(f"[SESSION_STORE] Cleaned up expired session: {filename}")
                    except Exception as e:
                        print(f"[SESSION_STORE] Error cleaning up {filename}: {e}")

# Global instance
_session_store = None

def get_session_store() -> FileSessionStore:
    """Get or create global session store instance"""
    global _session_store
    if _session_store is None:
        _session_store = FileSessionStore()
        print(f"[SESSION_STORE] Created new FileSessionStore instance")
    return _session_store
