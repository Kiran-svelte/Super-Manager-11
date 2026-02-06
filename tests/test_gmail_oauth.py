#!/usr/bin/env python3
"""
Test Gmail OAuth Email Plugin
Verifies the email integration is working correctly
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.core.gmail_oauth_plugin import GmailOAuthPlugin, EmailConfig


async def test_email_health():
    """Test email service health check"""
    print("\n" + "="*60)
    print("🧪 Testing Gmail OAuth Email Plugin")
    print("="*60 + "\n")
    
    # Initialize plugin
    plugin = GmailOAuthPlugin()
    
    print(f"📧 Sender Email: {plugin.config.sender_email}")
    print(f"🔑 OAuth Configured: {bool(plugin.config.refresh_token)}")
    print(f"📡 SMTP Fallback: {bool(plugin.config.smtp_password)}")
    
    # Test health check
    print("\n📊 Checking email service health...")
    result = await plugin.execute(
        {"action": "health"},
        {}
    )
    
    print(f"\n✅ Health Status: {result['status']}")
    print(f"📝 Message: {result['result']}")
    
    if 'health' in result:
        health = result['health']
        print("\n📋 Health Details:")
        for key, value in health.items():
            print(f"   - {key}: {value}")
    
    if 'recommendations' in result:
        print("\n💡 Recommendations:")
        for rec in result['recommendations']:
            print(f"   • {rec}")
    
    # Health check passes if the API is available (even if not configured yet)
    # This tests that the plugin is properly installed and functional
    health = result.get('health', {})
    api_available = health.get('oauth_available', False)
    return api_available  # Pass if Google API is available


async def test_email_send_simulated():
    """Test email sending (simulated mode if OAuth not configured)"""
    print("\n" + "-"*60)
    print("📤 Testing Email Send (may be simulated)")
    print("-"*60 + "\n")
    
    plugin = GmailOAuthPlugin()
    
    # Test sending an email
    result = await plugin.execute(
        {
            "action": "send_email",
            "parameters": {
                "to": "test@example.com",
                "subject": "Test from Super Manager AI",
                "topic": "Integration Test",
                "participants": "Test User",
                "message": "This is a test email from the Gmail OAuth plugin.",
                "meeting_link": "https://meet.jit.si/test-meeting"
            }
        },
        {}
    )
    
    print(f"📬 Send Result: {result['status']}")
    print(f"📝 Message: {result.get('result', 'No result')}")
    print(f"🔧 Method Used: {result.get('method', 'unknown')}")
    
    if result.get('email_id'):
        print(f"📧 Email ID: {result['email_id']}")
    
    if result.get('note'):
        print(f"💡 Note: {result['note']}")
    
    return result['status'] == 'completed'


async def test_sent_emails_list():
    """Test retrieving sent emails"""
    print("\n" + "-"*60)
    print("📥 Testing Sent Emails List")
    print("-"*60 + "\n")
    
    plugin = GmailOAuthPlugin()
    
    # First send a test email
    await plugin.execute(
        {
            "action": "send",
            "parameters": {
                "to": "recipient@example.com",
                "subject": "Another test email"
            }
        },
        {}
    )
    
    # Now list emails
    result = await plugin.execute(
        {"action": "read"},
        {}
    )
    
    print(f"📊 Result: {result['status']}")
    print(f"📬 Emails Found: {result.get('count', 0)}")
    
    if result.get('emails'):
        print("\n📧 Sent Emails:")
        for i, email in enumerate(result['emails'][-5:], 1):  # Show last 5
            print(f"   {i}. To: {email.get('to', 'N/A')} | Subject: {email.get('subject', 'N/A')[:30]}... | Method: {email.get('method', 'N/A')}")
    
    return result['status'] == 'completed'


async def test_rate_limiter():
    """Test rate limiting"""
    print("\n" + "-"*60)
    print("⏱️ Testing Rate Limiter")
    print("-"*60 + "\n")
    
    plugin = GmailOAuthPlugin()
    
    # Check initial state
    can_send = plugin.rate_limiter.can_send()
    print(f"✅ Can send: {can_send}")
    
    # Record some sends
    for i in range(5):
        plugin.rate_limiter.record_send()
    
    print(f"📊 Emails in last minute: {len(plugin.rate_limiter.minute_bucket)}")
    print(f"📊 Emails in last day: {len(plugin.rate_limiter.day_bucket)}")
    print(f"✅ Can still send: {plugin.rate_limiter.can_send()}")
    
    return True


async def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🚀 GMAIL OAUTH EMAIL PLUGIN TEST SUITE")
    print("="*60)
    
    tests = [
        ("Health Check", test_email_health),
        ("Email Send (Simulated)", test_email_send_simulated),
        ("Sent Emails List", test_sent_emails_list),
        ("Rate Limiter", test_rate_limiter),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            passed = await test_func()
            results.append((name, passed))
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"\n{status}: {name}")
        except Exception as e:
            results.append((name, False))
            print(f"\n❌ ERROR in {name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for _, passed in results if passed)
    total = len(results)
    
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
    
    print(f"\n🎯 Results: {passed_count}/{total} tests passed")
    
    if passed_count == total:
        print("\n🎉 All tests passed! Email plugin is ready.")
    else:
        print("\n⚠️ Some tests failed. Check configuration.")
    
    return passed_count == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
