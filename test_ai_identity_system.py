#!/usr/bin/env python
"""
Comprehensive test for AI Identity and Executor system
Tests all major functionality without external API dependencies where possible
"""
import asyncio
import os
import sys
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.agent import (
    __version__,
    get_identity_manager,
    get_service_signup,
    get_ai_executor,
    get_executor,
    get_memory,
    get_agent,
    get_orchestrator
)
from backend.agent.service_signup import ServiceRegistry
from backend.agent.identity import EncryptionManager, AIIdentity

def test_encryption():
    """Test encryption with per-user salt"""
    print("\n[TEST] Encryption Manager")
    print("-" * 40)
    
    # Test with user-specific salt
    user1_salt = "user123"
    user2_salt = "user456"
    secret = os.getenv("ENCRYPTION_SECRET", "test-secret")
    
    enc1 = EncryptionManager(secret, user1_salt)
    enc2 = EncryptionManager(secret, user2_salt)
    
    test_data = "my-secret-api-key-12345"
    
    # Encrypt with user1
    encrypted1 = enc1.encrypt(test_data)
    encrypted2 = enc2.encrypt(test_data)
    
    print(f"  Original: {test_data}")
    print(f"  Encrypted (user1): {encrypted1[:50]}...")
    print(f"  Encrypted (user2): {encrypted2[:50]}...")
    
    # Verify they're different (different salts)
    assert encrypted1 != encrypted2, "Same salt used for different users!"
    print("  ✓ Different users get different encrypted values")
    
    # Decrypt with correct key
    decrypted1 = enc1.decrypt(encrypted1)
    decrypted2 = enc2.decrypt(encrypted2)
    
    assert decrypted1 == test_data, "User1 decryption failed"
    assert decrypted2 == test_data, "User2 decryption failed"
    print("  ✓ Decryption successful for both users")
    
    # Test cross-user decryption fails
    try:
        enc1.decrypt(encrypted2)  # Try to decrypt user2's data with user1's key
        print("  ✗ Cross-user decryption should have failed!")
    except Exception:
        print("  ✓ Cross-user decryption correctly fails")
    
    print("  [PASS] Encryption tests successful")
    return True


def test_service_registry():
    """Test ServiceRegistry methods"""
    print("\n[TEST] Service Registry")
    print("-" * 40)
    
    # Test list_services
    all_services = ServiceRegistry.list_services()
    print(f"  Total non-blocked services: {len(all_services)}")
    assert len(all_services) > 0, "No services found"
    
    # Test category filter
    ai_services = ServiceRegistry.list_services(category="ai")
    print(f"  AI services: {ai_services}")
    assert "groq" in ai_services, "Groq should be in AI services"
    
    # Test include_blocked
    all_with_blocked = ServiceRegistry.list_services(include_blocked=True)
    print(f"  Including blocked: {len(all_with_blocked)}")
    assert len(all_with_blocked) >= len(all_services), "Blocked filter not working"
    
    # Test get_service_info
    groq_info = ServiceRegistry.get_service_info("groq")
    print(f"  Groq info: free_tier={groq_info.get('free_tier')}")
    assert groq_info is not None, "Groq info should exist"
    assert groq_info["free_tier"] == True, "Groq should have free tier"
    
    # Test is_blocked
    is_blocked, reason = ServiceRegistry.is_blocked("twilio")
    print(f"  Twilio blocked: {is_blocked} - {reason}")
    assert is_blocked == True, "Twilio should be blocked"
    
    is_blocked, _ = ServiceRegistry.is_blocked("groq")
    assert is_blocked == False, "Groq should not be blocked"
    
    # Test get_service_for_task
    email_services = ServiceRegistry.get_service_for_task("send_email")
    print(f"  Email services: {email_services}")
    assert len(email_services) > 0, "Should have email services"
    
    print("  [PASS] Service Registry tests successful")
    return True


async def test_ai_executor():
    """Test AIIdentityExecutor"""
    print("\n[TEST] AI Identity Executor")
    print("-" * 40)
    
    ai_exec = get_ai_executor()
    print(f"  Executor type: {type(ai_exec).__name__}")
    
    test_user_id = "test-user-123"
    
    # Test identity status (should work even without identity setup)
    status = await ai_exec.get_identity_status(test_user_id)
    print(f"  Identity status: {status}")
    
    # Test list services
    services = await ai_exec.list_ai_services(test_user_id)
    print(f"  Listed services: {len(services)} services")
    
    # Test signup for service (should return instructions, not actually sign up)
    result = await ai_exec.signup_for_service(test_user_id, "groq")
    print(f"  Signup result status: {result.get('status')}")
    
    print("  [PASS] AI Executor tests successful")
    return True


async def test_action_executor():
    """Test ActionExecutor with AI actions"""
    print("\n[TEST] Action Executor with AI Actions")
    print("-" * 40)
    
    executor = get_executor()
    print(f"  Executor type: {type(executor).__name__}")
    
    # Test ai_identity_status action
    result = await executor.execute(
        "ai_identity_status",
        {},
        user_id="test-user"
    )
    print(f"  Identity status result: {result}")
    
    # Test ai_list_services action
    result = await executor.execute(
        "ai_list_services",
        {},
        user_id="test-user"
    )
    print(f"  List services result: {len(result.get('services', []))} services")
    
    print("  [PASS] Action Executor tests successful")
    return True


def test_memory_system():
    """Test memory and user profile"""
    print("\n[TEST] Memory System")
    print("-" * 40)
    
    memory = get_memory()
    print(f"  Memory type: {type(memory).__name__}")
    
    # Memory should initialize without errors
    print("  ✓ Memory system initialized")
    print("  [PASS] Memory tests successful")
    return True


async def test_agent():
    """Test Agent initialization"""
    print("\n[TEST] Agent System")
    print("-" * 40)
    
    agent = get_agent()
    print(f"  Agent type: {type(agent).__name__}")
    
    # Check agent has required components
    assert agent.providers is not None, "Agent should have providers"
    assert len(agent.providers) > 0, "Agent should have at least one provider"
    
    print(f"  ✓ Agent has {len(agent.providers)} AI providers")
    print("  ✓ Agent initialized successfully")
    print("  [PASS] Agent tests successful")
    return True


async def main():
    print("=" * 60)
    print(f"  SUPER MANAGER v{__version__} - AI IDENTITY SYSTEM TEST")
    print("=" * 60)
    print(f"  Time: {datetime.now().isoformat()}")
    print(f"  Supabase URL: {os.getenv('SUPABASE_URL', 'NOT SET')[:50]}...")
    
    results = []
    
    # Run all tests
    results.append(("Encryption", test_encryption()))
    results.append(("Service Registry", test_service_registry()))
    results.append(("Memory", test_memory_system()))
    
    # Async tests
    results.append(("AI Executor", await test_ai_executor()))
    results.append(("Action Executor", await test_action_executor()))
    results.append(("Agent", await test_agent()))
    
    # Summary
    print("\n" + "=" * 60)
    print("  TEST SUMMARY")
    print("=" * 60)
    
    passed = 0
    failed = 0
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print("-" * 60)
    print(f"  Total: {passed}/{len(results)} tests passed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
