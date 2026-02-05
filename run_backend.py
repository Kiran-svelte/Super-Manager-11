"""
Standalone script to run the backend server
"""
import uvicorn
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add backend to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path.parent.absolute()))

if __name__ == "__main__":
    # Check for .env file
    env_file = Path(".env")
    if not env_file.exists():
        print("[WARN] Warning: .env file not found")
        print("   Create .env with:")
        print("   - OPENAI_API_KEY=your_key")
        print("   - FIREBASE_CREDENTIALS_PATH=path/to/credentials.json")
        print()
    
    print("🚀 Starting Super Manager Backend...")
    print("   API will be available at: http://localhost:8000")
    print("   API docs at: http://localhost:8000/docs")
    print()
    
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend"]
    )

