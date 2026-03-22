"""
Behavioral Tests: Session Store
==================================
Tests that the session store ACTUALLY works:
- FileSessionStore initialization
- Session save/load/delete
- Expiration handling
- Thread safety
- Cleanup functionality

README Requirements:
- File-based session storage
- 2-hour session expiration
- Thread-safe operations
"""

import pytest
import os
import tempfile
import shutil
import json
from datetime import datetime, timedelta

from backend.core.session_store import FileSessionStore


class TestFileSessionStoreInit:
    """Test FileSessionStore initialization"""
    
    def test_can_instantiate(self):
        """FileSessionStore should be instantiatable"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            assert store is not None
    
    def test_has_storage_dir(self):
        """FileSessionStore should have storage_dir"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            assert store.storage_dir == tmpdir
    
    def test_has_lock(self):
        """FileSessionStore should have thread lock"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            assert hasattr(store, "lock")
    
    def test_creates_directory(self):
        """FileSessionStore should create storage directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, "new_sessions")
            assert not os.path.exists(new_dir)
            
            store = FileSessionStore(storage_dir=new_dir)
            
            assert os.path.exists(new_dir)
    
    def test_default_directory(self):
        """FileSessionStore should have default directory"""
        store = FileSessionStore()
        assert store.storage_dir == "sessions"
        
        # Cleanup
        if os.path.exists("sessions"):
            shutil.rmtree("sessions")


class TestSessionPath:
    """Test _get_session_path method"""
    
    def test_returns_correct_path(self):
        """_get_session_path should return correct file path"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            path = store._get_session_path("session123")
            
            expected = os.path.join(tmpdir, "session123.json")
            assert path == expected
    
    def test_adds_json_extension(self):
        """_get_session_path should add .json extension"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            path = store._get_session_path("my-session")
            
            assert path.endswith(".json")


class TestSaveSession:
    """Test save_session method"""
    
    def test_creates_file(self):
        """save_session should create session file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"data": "test"})
            
            session_path = os.path.join(tmpdir, "session1.json")
            assert os.path.exists(session_path)
    
    def test_saves_session_data(self):
        """save_session should save session data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"key": "value", "count": 42})
            
            session_path = os.path.join(tmpdir, "session1.json")
            with open(session_path) as f:
                saved = json.load(f)
            
            assert saved["data"]["key"] == "value"
            assert saved["data"]["count"] == 42
    
    def test_adds_metadata(self):
        """save_session should add metadata"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"data": "test"})
            
            session_path = os.path.join(tmpdir, "session1.json")
            with open(session_path) as f:
                saved = json.load(f)
            
            assert "session_id" in saved
            assert "created_at" in saved
            assert "expires_at" in saved
    
    def test_sets_expiration(self):
        """save_session should set 2-hour expiration"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            before = datetime.utcnow()
            store.save_session("session1", {"data": "test"})
            
            session_path = os.path.join(tmpdir, "session1.json")
            with open(session_path) as f:
                saved = json.load(f)
            
            expires_at = datetime.fromisoformat(saved["expires_at"])
            
            # Should expire approximately 2 hours from now
            expected_min = before + timedelta(hours=1, minutes=59)
            expected_max = before + timedelta(hours=2, minutes=1)
            
            assert expected_min < expires_at < expected_max
    
    def test_overwrites_existing(self):
        """save_session should overwrite existing session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"version": 1})
            store.save_session("session1", {"version": 2})
            
            session_path = os.path.join(tmpdir, "session1.json")
            with open(session_path) as f:
                saved = json.load(f)
            
            assert saved["data"]["version"] == 2


class TestGetSession:
    """Test get_session method"""
    
    def test_returns_session_data(self):
        """get_session should return session data"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"key": "value"})
            
            result = store.get_session("session1")
            
            assert result is not None
            assert result["key"] == "value"
    
    def test_returns_none_for_nonexistent(self):
        """get_session should return None for nonexistent session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            result = store.get_session("nonexistent")
            
            assert result is None
    
    def test_returns_none_for_expired(self):
        """get_session should return None for expired session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            # Create expired session manually
            session_path = os.path.join(tmpdir, "expired.json")
            expired_data = {
                "session_id": "expired",
                "data": {"test": "data"},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
            with open(session_path, 'w') as f:
                json.dump(expired_data, f)
            
            result = store.get_session("expired")
            
            assert result is None
    
    def test_deletes_expired_on_access(self):
        """get_session should delete expired session file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            # Create expired session manually
            session_path = os.path.join(tmpdir, "expired.json")
            expired_data = {
                "session_id": "expired",
                "data": {"test": "data"},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
            with open(session_path, 'w') as f:
                json.dump(expired_data, f)
            
            store.get_session("expired")
            
            assert not os.path.exists(session_path)


class TestDeleteSession:
    """Test delete_session method"""
    
    def test_deletes_session_file(self):
        """delete_session should delete session file"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"data": "test"})
            session_path = os.path.join(tmpdir, "session1.json")
            assert os.path.exists(session_path)
            
            store.delete_session("session1")
            
            assert not os.path.exists(session_path)
    
    def test_safe_for_nonexistent(self):
        """delete_session should be safe for nonexistent session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            # Should not raise
            store.delete_session("nonexistent")


class TestListSessions:
    """Test list_sessions method"""
    
    def test_returns_empty_list_when_empty(self):
        """list_sessions should return empty list when no sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            result = store.list_sessions()
            
            assert result == []
    
    def test_returns_session_ids(self):
        """list_sessions should return session IDs"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"data": "a"})
            store.save_session("session2", {"data": "b"})
            store.save_session("session3", {"data": "c"})
            
            result = store.list_sessions()
            
            assert len(result) == 3
            assert "session1" in result
            assert "session2" in result
            assert "session3" in result
    
    def test_excludes_non_json_files(self):
        """list_sessions should exclude non-json files"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"data": "test"})
            
            # Create non-json file
            other_file = os.path.join(tmpdir, "readme.txt")
            with open(other_file, 'w') as f:
                f.write("test")
            
            result = store.list_sessions()
            
            assert len(result) == 1
            assert "session1" in result


class TestCleanupExpired:
    """Test cleanup_expired method"""
    
    def test_removes_expired_sessions(self):
        """cleanup_expired should remove expired sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            # Create expired session
            expired_path = os.path.join(tmpdir, "expired.json")
            expired_data = {
                "session_id": "expired",
                "data": {"test": "data"},
                "created_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() - timedelta(hours=1)).isoformat()
            }
            with open(expired_path, 'w') as f:
                json.dump(expired_data, f)
            
            # Create valid session
            store.save_session("valid", {"data": "test"})
            
            store.cleanup_expired()
            
            assert not os.path.exists(expired_path)
            assert os.path.exists(os.path.join(tmpdir, "valid.json"))
    
    def test_keeps_valid_sessions(self):
        """cleanup_expired should keep valid sessions"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("session1", {"data": "a"})
            store.save_session("session2", {"data": "b"})
            
            store.cleanup_expired()
            
            sessions = store.list_sessions()
            assert len(sessions) == 2


class TestSessionDataTypes:
    """Test session storage with different data types"""
    
    def test_stores_strings(self):
        """Session should store strings"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("s1", {"message": "Hello, world!"})
            result = store.get_session("s1")
            
            assert result["message"] == "Hello, world!"
    
    def test_stores_numbers(self):
        """Session should store numbers"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("s1", {"count": 42, "ratio": 3.14})
            result = store.get_session("s1")
            
            assert result["count"] == 42
            assert result["ratio"] == 3.14
    
    def test_stores_lists(self):
        """Session should store lists"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("s1", {"items": [1, 2, 3, "four"]})
            result = store.get_session("s1")
            
            assert result["items"] == [1, 2, 3, "four"]
    
    def test_stores_nested_dicts(self):
        """Session should store nested dicts"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            store.save_session("s1", {
                "user": {
                    "name": "John",
                    "settings": {"theme": "dark"}
                }
            })
            result = store.get_session("s1")
            
            assert result["user"]["name"] == "John"
            assert result["user"]["settings"]["theme"] == "dark"


class TestConversationHistory:
    """Test storing conversation history"""
    
    def test_stores_message_history(self):
        """Session should store message history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            history = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"}
            ]
            
            store.save_session("chat1", {"history": history})
            result = store.get_session("chat1")
            
            assert len(result["history"]) == 3
            assert result["history"][0]["role"] == "user"
            assert result["history"][1]["role"] == "assistant"
    
    def test_appends_to_history(self):
        """Session should support appending to history"""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = FileSessionStore(storage_dir=tmpdir)
            
            # Initial save
            store.save_session("chat1", {
                "history": [{"role": "user", "content": "Hello"}]
            })
            
            # Load, modify, save
            data = store.get_session("chat1")
            data["history"].append({"role": "assistant", "content": "Hi!"})
            store.save_session("chat1", data)
            
            # Verify
            result = store.get_session("chat1")
            assert len(result["history"]) == 2
