#!/usr/bin/env python
"""Test all AI Identity components"""

from backend.agent import __version__
from backend.agent import get_identity_manager, get_service_signup, get_ai_executor
from backend.agent.service_signup import ServiceRegistry

print(f"Super Manager v{__version__}")
print("=" * 50)

# Test each component
mgr = get_identity_manager()
print("1. AI Identity Manager: OK")

signup = get_service_signup()
print("2. Service Signup: OK")

ai_exec = get_ai_executor()
print("3. AI Executor: OK")

# Test service registry
services = ServiceRegistry.list_services()
print(f"4. Available services: {len(services)}")

ai_services = ServiceRegistry.list_services(category="ai")
email_services = ServiceRegistry.list_services(category="email")
msg_services = ServiceRegistry.list_services(category="messaging")

print(f"   - AI: {ai_services}")
print(f"   - Email: {email_services}")
print(f"   - Messaging: {msg_services}")

# Test blocked check
is_blocked, reason = ServiceRegistry.is_blocked("twilio")
print(f"5. Twilio blocked: {is_blocked} ({reason})")

# Test get_service_for_task
services_for_email = ServiceRegistry.get_service_for_task("send_email")
print(f"6. Services for email: {services_for_email}")

print("=" * 50)
print("ALL COMPONENTS INITIALIZED SUCCESSFULLY!")
