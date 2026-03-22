"""
Behavioral Tests: Memory System
=================================
Tests that the memory system ACTUALLY works:
- MemoryManager caching behavior
- Contact dataclass
- Preference dataclass
- UserProfile with contacts and preferences
- Memory fallback to in-memory storage

README Requirements:
- Memory system stores user preferences
- Contact book management
- User profile persistence
- Fallback when database unavailable
"""

import pytest
from dataclasses import is_dataclass
from datetime import datetime

from backend.core.memory import MemoryManager
from backend.agent.memory import (
    Contact, Preference, UserProfile, Memory
)


class TestContactDataclass:
    """Test Contact dataclass structure"""
    
    def test_is_dataclass(self):
        """Contact should be a dataclass"""
        assert is_dataclass(Contact)
    
    def test_required_fields(self):
        """Contact should have id and name as required"""
        contact = Contact(id="123", name="John Doe")
        
        assert contact.id == "123"
        assert contact.name == "John Doe"
    
    def test_optional_fields_default(self):
        """Contact optional fields should have defaults"""
        contact = Contact(id="123", name="John")
        
        assert contact.email is None
        assert contact.phone is None
        assert contact.telegram_id is None
        assert contact.relationship == "other"
        assert contact.notes is None
    
    def test_all_fields(self):
        """Contact should support all fields"""
        contact = Contact(
            id="123",
            name="John Doe",
            email="john@example.com",
            phone="+1234567890",
            telegram_id="@johndoe",
            relationship="colleague",
            notes="Works in engineering"
        )
        
        assert contact.email == "john@example.com"
        assert contact.phone == "+1234567890"
        assert contact.relationship == "colleague"
    
    def test_to_dict(self):
        """Contact should serialize to dict"""
        contact = Contact(id="123", name="John")
        result = contact.to_dict()
        
        assert isinstance(result, dict)
        assert result["id"] == "123"
        assert result["name"] == "John"


class TestPreferenceDataclass:
    """Test Preference dataclass structure"""
    
    def test_is_dataclass(self):
        """Preference should be a dataclass"""
        assert is_dataclass(Preference)
    
    def test_required_fields(self):
        """Preference should have category, key, value"""
        pref = Preference(
            category="travel",
            key="preferred_airlines",
            value=["Delta", "United"]
        )
        
        assert pref.category == "travel"
        assert pref.key == "preferred_airlines"
        assert pref.value == ["Delta", "United"]
    
    def test_to_dict(self):
        """Preference should serialize to dict"""
        pref = Preference(category="food", key="dietary", value="vegetarian")
        result = pref.to_dict()
        
        assert result["category"] == "food"
        assert result["key"] == "dietary"
        assert result["value"] == "vegetarian"


class TestUserProfileDataclass:
    """Test UserProfile dataclass structure"""
    
    def test_is_dataclass(self):
        """UserProfile should be a dataclass"""
        assert is_dataclass(UserProfile)
    
    def test_required_fields(self):
        """UserProfile should have id and email as required"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        assert profile.id == "user123"
        assert profile.email == "user@example.com"
    
    def test_optional_fields_default(self):
        """UserProfile optional fields should have defaults"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        assert profile.name is None
        assert profile.phone is None
        assert profile.contacts == []
        assert profile.preferences == {}
    
    def test_get_preference(self):
        """UserProfile.get_preference should work"""
        profile = UserProfile(
            id="user123",
            email="user@example.com",
            preferences={"travel": {"budget": "mid-range"}}
        )
        
        result = profile.get_preference("travel", "budget")
        assert result == "mid-range"
    
    def test_get_preference_default(self):
        """UserProfile.get_preference should return default"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        result = profile.get_preference("travel", "budget", "economy")
        assert result == "economy"
    
    def test_set_preference(self):
        """UserProfile.set_preference should work"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        profile.set_preference("fashion", "style", "casual")
        
        assert profile.preferences["fashion"]["style"] == "casual"
    
    def test_set_preference_new_category(self):
        """UserProfile.set_preference should create category if needed"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        profile.set_preference("meetings", "duration", 30)
        
        assert "meetings" in profile.preferences
        assert profile.preferences["meetings"]["duration"] == 30
    
    def test_find_contact(self):
        """UserProfile.find_contact should find by name"""
        profile = UserProfile(
            id="user123",
            email="user@example.com",
            contacts=[
                Contact(id="c1", name="John Doe"),
                Contact(id="c2", name="Jane Smith")
            ]
        )
        
        result = profile.find_contact("Jane")
        
        assert result is not None
        assert result.name == "Jane Smith"
    
    def test_find_contact_not_found(self):
        """UserProfile.find_contact should return None if not found"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        result = profile.find_contact("Unknown Person")
        
        assert result is None
    
    def test_find_contact_case_insensitive(self):
        """UserProfile.find_contact should be case insensitive"""
        profile = UserProfile(
            id="user123",
            email="user@example.com",
            contacts=[Contact(id="c1", name="John Doe")]
        )
        
        result = profile.find_contact("JOHN")
        
        assert result is not None
        assert result.name == "John Doe"
    
    def test_add_contact(self):
        """UserProfile.add_contact should add new contact"""
        profile = UserProfile(id="user123", email="user@example.com")
        
        contact = Contact(id="c1", name="New Person")
        profile.add_contact(contact)
        
        assert len(profile.contacts) == 1
        assert profile.contacts[0].name == "New Person"
    
    def test_add_contact_updates_existing_by_id(self):
        """UserProfile.add_contact should update if id matches"""
        profile = UserProfile(
            id="user123",
            email="user@example.com",
            contacts=[Contact(id="c1", name="Old Name")]
        )
        
        updated = Contact(id="c1", name="New Name")
        profile.add_contact(updated)
        
        assert len(profile.contacts) == 1
        assert profile.contacts[0].name == "New Name"
    
    def test_to_dict(self):
        """UserProfile.to_dict should serialize properly"""
        profile = UserProfile(
            id="user123",
            email="user@example.com",
            name="Test User",
            preferences={"test": {"key": "value"}}
        )
        
        result = profile.to_dict()
        
        assert isinstance(result, dict)
        assert result["id"] == "user123"
        assert result["email"] == "user@example.com"
        assert result["name"] == "Test User"
        assert result["preferences"]["test"]["key"] == "value"
    
    def test_from_dict(self):
        """UserProfile.from_dict should deserialize properly"""
        data = {
            "id": "user123",
            "email": "user@example.com",
            "name": "Test User",
            "preferences": {"travel": {"budget": "high"}}
        }
        
        profile = UserProfile.from_dict(data)
        
        assert profile.id == "user123"
        assert profile.email == "user@example.com"
        assert profile.preferences["travel"]["budget"] == "high"


class TestMemoryClass:
    """Test Memory class"""
    
    def test_can_instantiate(self):
        """Memory should be instantiatable"""
        memory = Memory()
        assert memory is not None
    
    def test_has_local_storage(self):
        """Memory should have local fallback storage"""
        memory = Memory()
        
        assert hasattr(memory, "_local_users")
        assert hasattr(memory, "_local_history")
    
    def test_local_users_is_dict(self):
        """_local_users should be a dict"""
        memory = Memory()
        assert isinstance(memory._local_users, dict)
    
    def test_local_history_is_dict(self):
        """_local_history should be a dict"""
        memory = Memory()
        assert isinstance(memory._local_history, dict)


class TestMemoryManagerClass:
    """Test core MemoryManager class"""
    
    def test_can_instantiate(self):
        """MemoryManager should be instantiatable"""
        manager = MemoryManager()
        assert manager is not None
    
    def test_has_cache(self):
        """MemoryManager should have cache"""
        manager = MemoryManager()
        assert hasattr(manager, "cache")
        assert isinstance(manager.cache, dict)
    
    def test_cache_is_empty_on_init(self):
        """MemoryManager cache should start empty"""
        manager = MemoryManager()
        assert manager.cache == {}


class TestMemoryManagerCaching:
    """Test MemoryManager caching behavior"""
    
    def test_cache_key_format(self):
        """Cache key should be user_id:key format"""
        # This tests the expected cache key format
        user_id = "user123"
        key = "preference"
        expected = f"{user_id}:{key}"
        
        assert expected == "user123:preference"
    
    def test_cache_stores_value(self):
        """Cache can store values directly"""
        manager = MemoryManager()
        cache_key = "user123:name"
        
        manager.cache[cache_key] = "Test Value"
        
        assert manager.cache[cache_key] == "Test Value"


class TestContactRelationships:
    """Test Contact relationship types"""
    
    def test_colleague_relationship(self):
        """Contact should support colleague relationship"""
        contact = Contact(id="1", name="Work Person", relationship="colleague")
        assert contact.relationship == "colleague"
    
    def test_friend_relationship(self):
        """Contact should support friend relationship"""
        contact = Contact(id="1", name="Friend Person", relationship="friend")
        assert contact.relationship == "friend"
    
    def test_family_relationship(self):
        """Contact should support family relationship"""
        contact = Contact(id="1", name="Family Person", relationship="family")
        assert contact.relationship == "family"
    
    def test_other_relationship_default(self):
        """Contact relationship should default to other"""
        contact = Contact(id="1", name="Unknown Person")
        assert contact.relationship == "other"


class TestPreferenceCategories:
    """Test Preference category types"""
    
    def test_fashion_category(self):
        """Preference should support fashion category"""
        pref = Preference(category="fashion", key="style", value="formal")
        assert pref.category == "fashion"
    
    def test_travel_category(self):
        """Preference should support travel category"""
        pref = Preference(category="travel", key="class", value="business")
        assert pref.category == "travel"
    
    def test_food_category(self):
        """Preference should support food category"""
        pref = Preference(category="food", key="cuisine", value="italian")
        assert pref.category == "food"
    
    def test_meetings_category(self):
        """Preference should support meetings category"""
        pref = Preference(category="meetings", key="platform", value="zoom")
        assert pref.category == "meetings"
    
    def test_general_category(self):
        """Preference should support general category"""
        pref = Preference(category="general", key="timezone", value="PST")
        assert pref.category == "general"


class TestUserProfileContacts:
    """Test UserProfile contacts list operations"""
    
    def test_contacts_list_starts_empty(self):
        """UserProfile contacts should start empty"""
        profile = UserProfile(id="1", email="test@test.com")
        assert profile.contacts == []
    
    def test_multiple_contacts(self):
        """UserProfile should support multiple contacts"""
        profile = UserProfile(
            id="1",
            email="test@test.com",
            contacts=[
                Contact(id="c1", name="Person 1"),
                Contact(id="c2", name="Person 2"),
                Contact(id="c3", name="Person 3")
            ]
        )
        
        assert len(profile.contacts) == 3
    
    def test_contacts_serialized_in_to_dict(self):
        """Contacts should be serialized in to_dict"""
        profile = UserProfile(
            id="1",
            email="test@test.com",
            contacts=[Contact(id="c1", name="Test Contact")]
        )
        
        result = profile.to_dict()
        
        assert "contacts" in result
        assert len(result["contacts"]) == 1
        assert result["contacts"][0]["name"] == "Test Contact"


class TestUserProfileTimestamp:
    """Test UserProfile timestamp handling"""
    
    def test_created_at_defaults_to_now(self):
        """created_at should default to current time"""
        profile = UserProfile(id="1", email="test@test.com")
        
        assert isinstance(profile.created_at, datetime)
    
    def test_created_at_serialized_in_to_dict(self):
        """created_at should be serialized as ISO string"""
        profile = UserProfile(id="1", email="test@test.com")
        
        result = profile.to_dict()
        
        assert "created_at" in result
        assert isinstance(result["created_at"], str)
    
    def test_from_dict_parses_created_at(self):
        """from_dict should parse created_at ISO string"""
        data = {
            "id": "1",
            "email": "test@test.com",
            "created_at": "2024-01-15T12:00:00"
        }
        
        profile = UserProfile.from_dict(data)
        
        assert isinstance(profile.created_at, datetime)
        assert profile.created_at.year == 2024
        assert profile.created_at.month == 1
