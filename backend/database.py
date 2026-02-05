"""
Firebase Firestore Database setup for Super Manager
"""
from google.cloud import firestore
from google.oauth2 import service_account
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path
import os
import json

# Initialize Firestore client
_firestore_client: Optional[firestore.Client] = None

def get_firestore_client() -> firestore.Client:
    """Get or create Firestore client"""
    global _firestore_client
    
    if _firestore_client is None:
        # Check for service account JSON
        credentials_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
        credentials_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        if credentials_path:
            # Resolve relative paths
            if not os.path.isabs(credentials_path):
                # Make path relative to project root
                project_root = Path(__file__).parent.parent.absolute()
                credentials_path = os.path.join(project_root, credentials_path)
            
            # Normalize path
            credentials_path = os.path.normpath(credentials_path)
            
            if os.path.exists(credentials_path):
                # Load from file
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                _firestore_client = firestore.Client(credentials=credentials, project=credentials.project_id)
            else:
                raise FileNotFoundError(f"Firebase credentials file not found: {credentials_path}")
        elif credentials_json:
            # Load from JSON string
            credentials_info = json.loads(credentials_json)
            credentials = service_account.Credentials.from_service_account_info(credentials_info)
            _firestore_client = firestore.Client(credentials=credentials, project=credentials_info.get('project_id'))
        else:
            # Use default credentials (for local development with gcloud auth)
            _firestore_client = firestore.Client()
    
    return _firestore_client

async def init_db():
    """Initialize Firestore (no-op, Firestore doesn't need initialization)"""
    try:
        client = get_firestore_client()
        # Test connection
        try:
            # Try to read from a test collection to verify connection
            test_ref = client.collection('_test').limit(1)
            list(test_ref.stream())
            print("[OK] Firestore connection successful")
        except Exception as e:
            error_msg = str(e)
            if "SERVICE_DISABLED" in error_msg or "403" in error_msg:
                print("[WARN] Firestore API not enabled yet")
                print("      Enable it at: https://console.developers.google.com/apis/api/firestore.googleapis.com/overview?project=super-manager-d7ae9")
                print("      The system will continue but database operations may fail until API is enabled.")
            else:
                print(f"[WARN] Firestore connection test failed: {e}")
                print("      Make sure FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON is set")
    except FileNotFoundError as e:
        print(f"[WARN] Firebase credentials file not found: {e}")
        print("      The system will continue but database operations will fail.")
    except Exception as e:
        print(f"[WARN] Firebase initialization error: {e}")
        print("      The system will continue but database operations may fail.")

# Firestore collection helpers
def get_tasks_collection():
    """Get tasks collection reference"""
    return get_firestore_client().collection('tasks')

def get_memories_collection():
    """Get memories collection reference"""
    return get_firestore_client().collection('memories')

def get_conversations_collection():
    """Get conversations collection reference"""
    return get_firestore_client().collection('conversations')

# Data models (for type hints and validation)
class Task:
    """Task model for Firestore"""
    def __init__(self, user_id: str, intent: str, status: str = "pending", 
                 result: Optional[str] = None, steps: List[Dict] = None, 
                 task_metadata: Dict = None, doc_id: Optional[str] = None):
        self.id = doc_id
        self.user_id = user_id
        self.intent = intent
        self.status = status
        self.result = result
        self.steps = steps or []
        self.task_metadata = task_metadata or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dict"""
        data = {
            'user_id': self.user_id,
            'intent': self.intent,
            'status': self.status,
            'result': self.result,
            'steps': self.steps,
            'task_metadata': self.task_metadata,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
        return {k: v for k, v in data.items() if v is not None}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: str) -> 'Task':
        """Create Task from Firestore document"""
        task = cls(
            user_id=data.get('user_id', ''),
            intent=data.get('intent', ''),
            status=data.get('status', 'pending'),
            result=data.get('result'),
            steps=data.get('steps', []),
            task_metadata=data.get('task_metadata', {}),
            doc_id=doc_id
        )
        if 'created_at' in data:
            task.created_at = data['created_at']
        if 'updated_at' in data:
            task.updated_at = data['updated_at']
        return task

class Memory:
    """Memory model for Firestore"""
    def __init__(self, user_id: str, key: str, value: Any, 
                 context: Dict = None, doc_id: Optional[str] = None):
        self.id = doc_id
        self.user_id = user_id
        self.key = key
        self.value = value
        self.context = context or {}
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dict"""
        # Store value as string if it's not already a string
        value_str = self.value
        if not isinstance(self.value, str):
            try:
                value_str = json.dumps(self.value)
            except:
                value_str = str(self.value)
        
        return {
            'user_id': self.user_id,
            'key': self.key,
            'value': value_str,
            'context': self.context,
            'created_at': self.created_at,
            'updated_at': self.updated_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: str) -> 'Memory':
        """Create Memory from Firestore document"""
        value = data.get('value', '')
        # Try to parse JSON if it's a string
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except:
                pass  # Keep as string if not JSON
        
        memory = cls(
            user_id=data.get('user_id', ''),
            key=data.get('key', ''),
            value=value,
            context=data.get('context', {}),
            doc_id=doc_id
        )
        if 'created_at' in data:
            memory.created_at = data['created_at']
        if 'updated_at' in data:
            memory.updated_at = data['updated_at']
        return memory

class Conversation:
    """Conversation model for Firestore"""
    def __init__(self, user_id: str, message: str, response: str, 
                 intent: Optional[str] = None, doc_id: Optional[str] = None):
        self.id = doc_id
        self.user_id = user_id
        self.message = message
        self.response = response
        self.intent = intent
        self.created_at = datetime.utcnow()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to Firestore-compatible dict"""
        return {
            'user_id': self.user_id,
            'message': self.message,
            'response': self.response,
            'intent': self.intent,
            'created_at': self.created_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any], doc_id: str) -> 'Conversation':
        """Create Conversation from Firestore document"""
        conv = cls(
            user_id=data.get('user_id', ''),
            message=data.get('message', ''),
            response=data.get('response', ''),
            intent=data.get('intent'),
            doc_id=doc_id
        )
        if 'created_at' in data:
            conv.created_at = data['created_at']
        return conv

# Database operations
async def create_task(task: Task) -> str:
    """Create a new task in Firestore"""
    _, doc_ref = get_tasks_collection().add(task.to_dict())
    return doc_ref.id

async def get_task(task_id: str) -> Optional[Task]:
    """Get task by ID"""
    doc = get_tasks_collection().document(task_id).get()
    if doc.exists:
        return Task.from_dict(doc.to_dict(), doc.id)
    return None

async def get_tasks_by_user(user_id: str, limit: int = 20) -> List[Task]:
    """Get tasks for a user"""
    query = get_tasks_collection().where('user_id', '==', user_id).order_by('created_at', direction=firestore.Query.DESCENDING).limit(limit)
    tasks = []
    for doc in query.stream():
        data = doc.to_dict()
        tasks.append(Task.from_dict(data, doc.id))
    return tasks

async def update_task(task_id: str, updates: Dict[str, Any]):
    """Update a task"""
    updates['updated_at'] = datetime.utcnow()
    get_tasks_collection().document(task_id).update(updates)

async def create_memory(memory: Memory) -> str:
    """Create a new memory in Firestore"""
    _, doc_ref = get_memories_collection().add(memory.to_dict())
    return doc_ref.id

async def get_memory_by_key(user_id: str, key: str) -> Optional[Memory]:
    """Get memory by user_id and key"""
    query = get_memories_collection().where('user_id', '==', user_id).where('key', '==', key).limit(1)
    docs = list(query.stream())
    if docs:
        data = docs[0].to_dict()
        return Memory.from_dict(data, docs[0].id)
    return None

async def get_memories_by_user(user_id: str) -> List[Memory]:
    """Get all memories for a user"""
    query = get_memories_collection().where('user_id', '==', user_id)
    memories = []
    for doc in query.stream():
        data = doc.to_dict()
        memories.append(Memory.from_dict(data, doc.id))
    return memories

async def update_memory(memory_id: str, updates: Dict[str, Any]):
    """Update a memory"""
    updates['updated_at'] = datetime.utcnow()
    get_memories_collection().document(memory_id).update(updates)

async def search_memories(user_id: str, query: str) -> List[Memory]:
    """Search memories by query"""
    all_memories = await get_memories_by_user(user_id)
    query_lower = query.lower()
    matching = []
    for memory in all_memories:
        if query_lower in memory.key.lower() or (memory.value and query_lower in str(memory.value).lower()):
            matching.append(memory)
    return matching

# Dependency for FastAPI (compatible with old interface)
async def get_db():
    """Dependency for getting database (Firestore doesn't need sessions)"""
    # Return the Firestore client for compatibility
    yield get_firestore_client()
