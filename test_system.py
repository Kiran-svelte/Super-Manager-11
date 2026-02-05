"""
Test script for Super Manager system
Run this to verify all components are working
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

load_dotenv()

async def test_components():
    """Test all core components"""
    print("🧪 Testing Super Manager Components...\n")
    
    # Test 1: Plugin System
    print("1. Testing Plugin System...")
    try:
        from core.plugins import PluginManager
        plugin_manager = PluginManager()
        plugins = plugin_manager.get_all_plugins()
        print(f"   ✅ Found {len(plugins)} plugins: {list(plugins.keys())}")
        
        # Test plugin execution
        test_step = {
            "id": 1,
            "action": "test action",
            "plugin": "general",
            "parameters": {}
        }
        result = await plugins["general"].execute(test_step, {})
        print(f"   ✅ Plugin execution works: {result.get('status')}")
    except Exception as e:
        print(f"   ❌ Plugin test failed: {e}")
        return False
    
    # Test 2: Intent Parser
    print("\n2. Testing Intent Parser...")
    try:
        from core.intent_parser import IntentParser
        parser = IntentParser()
        
        if not os.getenv("OPENAI_API_KEY"):
            print("   ⚠️  OPENAI_API_KEY not set, skipping LLM-based parsing")
            print("   ✅ Intent parser initialized (pattern matching available)")
        else:
            intent = await parser.parse("Schedule a meeting tomorrow at 2pm")
            print(f"   ✅ Intent parsed: {intent.get('quick_classification', 'N/A')}")
    except Exception as e:
        print(f"   ❌ Intent parser test failed: {e}")
        return False
    
    # Test 3: Memory Manager
    print("\n3. Testing Memory Manager...")
    try:
        from core.memory import MemoryManager
        from database import init_db, AsyncSessionLocal
        
        await init_db()
        memory_manager = MemoryManager()
        
        async with AsyncSessionLocal() as session:
            await memory_manager.set_memory(session, "test_user", "test_key", "test_value")
            value = await memory_manager.get_memory(session, "test_user", "test_key")
            if value == "test_value":
                print("   ✅ Memory storage and retrieval works")
            else:
                print(f"   ❌ Memory retrieval failed: got {value}")
                return False
    except Exception as e:
        print(f"   ❌ Memory test failed: {e}")
        return False
    
    # Test 4: Task Planner
    print("\n4. Testing Task Planner...")
    try:
        from core.task_planner import TaskPlanner
        planner = TaskPlanner()
        
        test_intent = {
            "action": "test",
            "category": "general",
            "entities": {}
        }
        
        if not os.getenv("OPENAI_API_KEY"):
            print("   ⚠️  OPENAI_API_KEY not set, using fallback plan")
        
        plan = await planner.create_plan(test_intent)
        print(f"   ✅ Plan created with {len(plan.get('steps', []))} steps")
    except Exception as e:
        print(f"   ❌ Task planner test failed: {e}")
        return False
    
    # Test 5: Agent Manager
    print("\n5. Testing Agent Manager...")
    try:
        from core.agent import AgentManager
        agent = AgentManager()
        
        if not os.getenv("OPENAI_API_KEY"):
            print("   ⚠️  OPENAI_API_KEY not set, agent will use fallback methods")
        else:
            print("   ✅ Agent manager initialized")
    except Exception as e:
        print(f"   ❌ Agent test failed: {e}")
        return False
    
    print("\n✅ All component tests passed!")
    print("\n📝 Next steps:")
    print("   1. Set OPENAI_API_KEY in .env file")
    print("   2. Run: python -m uvicorn backend.main:app --reload")
    print("   3. Run: cd frontend && npm run dev")
    print("   4. Open http://localhost:3000")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_components())
    sys.exit(0 if success else 1)

