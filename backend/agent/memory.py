"""
Memory System - Persistent User Data
====================================
Handles:
- User preferences (fashion, travel, meetings)
- Contact book
- Conversation history
- Task history
- Meeting history

Uses Supabase for persistence.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict

from dotenv import load_dotenv
load_dotenv()

# Try to import Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")


# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Contact:
    """A contact in the user's address book"""
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    relationship: str = "other"  # colleague, friend, family, other
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Preference:
    """A user preference"""
    category: str  # fashion, travel, food, meetings, general
    key: str
    value: Any
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class UserProfile:
    """Complete user profile with all data"""
    id: str
    email: str
    name: Optional[str] = None
    phone: Optional[str] = None
    telegram_id: Optional[str] = None
    contacts: List[Contact] = field(default_factory=list)
    preferences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def get_preference(self, category: str, key: str, default: Any = None) -> Any:
        """Get a preference value"""
        return self.preferences.get(category, {}).get(key, default)
    
    def set_preference(self, category: str, key: str, value: Any):
        """Set a preference value"""
        if category not in self.preferences:
            self.preferences[category] = {}
        self.preferences[category][key] = value
    
    def find_contact(self, name: str) -> Optional[Contact]:
        """Find a contact by name (fuzzy match)"""
        name_lower = name.lower()
        for contact in self.contacts:
            if name_lower in contact.name.lower():
                return contact
        return None
    
    def add_contact(self, contact: Contact):
        """Add or update a contact"""
        # Check if exists
        for i, existing in enumerate(self.contacts):
            if existing.id == contact.id or (
                existing.email and existing.email == contact.email
            ):
                self.contacts[i] = contact
                return
        self.contacts.append(contact)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "phone": self.phone,
            "telegram_id": self.telegram_id,
            "contacts": [c.to_dict() for c in self.contacts],
            "preferences": self.preferences,
            "created_at": self.created_at.isoformat() if isinstance(self.created_at, datetime) else self.created_at
        }
    
    @staticmethod
    def from_dict(data: Dict) -> "UserProfile":
        return UserProfile(
            id=data.get("id", ""),
            email=data.get("email", ""),
            name=data.get("name"),
            phone=data.get("phone"),
            telegram_id=data.get("telegram_id"),
            contacts=[Contact(**c) for c in data.get("contacts", [])],
            preferences=data.get("preferences", {}),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.utcnow().isoformat()))
        )


# =============================================================================
# MEMORY CLASS
# =============================================================================

class Memory:
    """
    Persistent memory system using Supabase.
    Falls back to in-memory storage if Supabase unavailable.
    """
    
    def __init__(self):
        self.client: Optional[Client] = None
        self._local_users: Dict[str, UserProfile] = {}
        self._local_history: Dict[str, List[Dict]] = {}
        
        # Initialize Supabase client
        if SUPABASE_AVAILABLE and SUPABASE_URL and SUPABASE_KEY:
            try:
                self.client = create_client(SUPABASE_URL, SUPABASE_KEY)
                print("[MEMORY] Connected to Supabase")
            except Exception as e:
                print(f"[MEMORY] Supabase connection failed: {e}")
                self.client = None
        else:
            print("[MEMORY] Using in-memory storage (Supabase not configured)")
    
    # -------------------------------------------------------------------------
    # User Operations
    # -------------------------------------------------------------------------
    
    async def get_user(self, user_id: str) -> Optional[UserProfile]:
        """Get user profile by ID"""
        if self.client:
            try:
                response = self.client.table("users").select("*").eq("id", user_id).single().execute()
                if response.data:
                    user_data = response.data
                    # Also fetch contacts
                    contacts_resp = self.client.table("contacts").select("*").eq("user_id", user_id).execute()
                    user_data["contacts"] = contacts_resp.data or []
                    # Fetch preferences
                    prefs_resp = self.client.table("preferences").select("*").eq("user_id", user_id).execute()
                    prefs = {}
                    for p in prefs_resp.data or []:
                        cat = p.get("category", "general")
                        if cat not in prefs:
                            prefs[cat] = {}
                        prefs[cat][p.get("key", "")] = p.get("value")
                    user_data["preferences"] = prefs
                    return UserProfile.from_dict(user_data)
            except Exception as e:
                print(f"[MEMORY] Error fetching user: {e}")
        
        # Fallback to local
        return self._local_users.get(user_id)
    
    async def get_or_create_user(self, email: str, name: Optional[str] = None) -> UserProfile:
        """Get user by email or create new"""
        if self.client:
            try:
                # Try to find existing
                response = self.client.table("users").select("*").eq("email", email).single().execute()
                if response.data:
                    return await self.get_user(response.data["id"])
            except:
                pass
            
            # Create new user
            try:
                import uuid
                new_user = {
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "name": name,
                    "created_at": datetime.utcnow().isoformat()
                }
                self.client.table("users").insert(new_user).execute()
                return UserProfile(id=new_user["id"], email=email, name=name)
            except Exception as e:
                print(f"[MEMORY] Error creating user: {e}")
        
        # Fallback to local
        import uuid
        user_id = str(uuid.uuid4())
        user = UserProfile(id=user_id, email=email, name=name)
        self._local_users[user_id] = user
        return user
    
    async def save_user(self, user: UserProfile):
        """Save user profile"""
        if self.client:
            try:
                user_data = {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "phone": user.phone,
                    "telegram_id": user.telegram_id
                }
                self.client.table("users").upsert(user_data).execute()
                
                # Save contacts
                for contact in user.contacts:
                    contact_data = contact.to_dict()
                    contact_data["user_id"] = user.id
                    self.client.table("contacts").upsert(contact_data).execute()
                
                # Save preferences
                for category, prefs in user.preferences.items():
                    for key, value in prefs.items():
                        pref_data = {
                            "user_id": user.id,
                            "category": category,
                            "key": key,
                            "value": json.dumps(value) if not isinstance(value, str) else value
                        }
                        # Upsert based on user_id + category + key
                        self.client.table("preferences").upsert(
                            pref_data, 
                            on_conflict="user_id,category,key"
                        ).execute()
                
            except Exception as e:
                print(f"[MEMORY] Error saving user: {e}")
        
        # Always update local cache
        self._local_users[user.id] = user
    
    # -------------------------------------------------------------------------
    # Contact Operations
    # -------------------------------------------------------------------------
    
    async def add_contact(self, user_id: str, contact: Contact):
        """Add a contact for a user"""
        user = await self.get_user(user_id)
        if user:
            user.add_contact(contact)
            await self.save_user(user)
    
    async def find_contact(self, user_id: str, name: str) -> Optional[Contact]:
        """Find a contact by name"""
        user = await self.get_user(user_id)
        if user:
            return user.find_contact(name)
        return None
    
    # -------------------------------------------------------------------------
    # Preference Operations
    # -------------------------------------------------------------------------
    
    async def get_preference(self, user_id: str, category: str, key: str, default: Any = None) -> Any:
        """Get a user preference"""
        user = await self.get_user(user_id)
        if user:
            return user.get_preference(category, key, default)
        return default
    
    async def set_preference(self, user_id: str, category: str, key: str, value: Any):
        """Set a user preference"""
        user = await self.get_user(user_id)
        if user:
            user.set_preference(category, key, value)
            await self.save_user(user)
    
    # -------------------------------------------------------------------------
    # Conversation History
    # -------------------------------------------------------------------------
    
    async def save_message(self, user_id: str, session_id: str, role: str, content: str, metadata: Dict = None):
        """Save a message to history"""
        if self.client:
            try:
                msg_data = {
                    "user_id": user_id,
                    "session_id": session_id,
                    "role": role,
                    "content": content,
                    "metadata": json.dumps(metadata or {}),
                    "created_at": datetime.utcnow().isoformat()
                }
                self.client.table("messages").insert(msg_data).execute()
            except Exception as e:
                print(f"[MEMORY] Error saving message: {e}")
        
        # Local fallback
        if session_id not in self._local_history:
            self._local_history[session_id] = []
        self._local_history[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    async def get_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Get conversation history"""
        if self.client:
            try:
                response = self.client.table("messages").select("*").eq(
                    "session_id", session_id
                ).order("created_at", desc=False).limit(limit).execute()
                return response.data or []
            except Exception as e:
                print(f"[MEMORY] Error fetching history: {e}")
        
        return self._local_history.get(session_id, [])[-limit:]
    
    # -------------------------------------------------------------------------
    # Meeting Operations
    # -------------------------------------------------------------------------
    
    async def save_meeting(self, user_id: str, meeting_data: Dict):
        """Save a meeting record"""
        if self.client:
            try:
                meeting_data["user_id"] = user_id
                meeting_data["created_at"] = datetime.utcnow().isoformat()
                self.client.table("meetings").insert(meeting_data).execute()
            except Exception as e:
                print(f"[MEMORY] Error saving meeting: {e}")
    
    async def get_meetings(self, user_id: str, upcoming_only: bool = True) -> List[Dict]:
        """Get user's meetings"""
        if self.client:
            try:
                query = self.client.table("meetings").select("*").eq("user_id", user_id)
                if upcoming_only:
                    query = query.gte("scheduled_at", datetime.utcnow().isoformat())
                response = query.order("scheduled_at", desc=False).execute()
                return response.data or []
            except Exception as e:
                print(f"[MEMORY] Error fetching meetings: {e}")
        return []
    
    # -------------------------------------------------------------------------
    # Task/Reminder Operations
    # -------------------------------------------------------------------------
    
    async def save_reminder(self, user_id: str, reminder_data: Dict):
        """Save a reminder"""
        if self.client:
            try:
                reminder_data["user_id"] = user_id
                reminder_data["created_at"] = datetime.utcnow().isoformat()
                self.client.table("reminders").insert(reminder_data).execute()
            except Exception as e:
                print(f"[MEMORY] Error saving reminder: {e}")
    
    async def get_pending_reminders(self, user_id: str) -> List[Dict]:
        """Get pending reminders"""
        if self.client:
            try:
                response = self.client.table("reminders").select("*").eq(
                    "user_id", user_id
                ).eq("sent", False).order("trigger_at", desc=False).execute()
                return response.data or []
            except Exception as e:
                print(f"[MEMORY] Error fetching reminders: {e}")
        return []


# =============================================================================
# SINGLETON INSTANCE
# =============================================================================

_memory: Optional[Memory] = None


def get_memory() -> Memory:
    """Get the global memory instance"""
    global _memory
    if _memory is None:
        _memory = Memory()
    return _memory
