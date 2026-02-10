"""
SECURE ACTIONS FRAMEWORK
=========================
This module provides security controls for sensitive operations:
- Multi-step confirmation for payments
- Transaction logging
- Audit trails
- Action verification

SECURITY LEVELS:
- LOW: Simple confirmation (reminders, notes)
- MEDIUM: Double confirmation (emails, meetings)
- HIGH: Multi-step verification (payments, bookings)
- CRITICAL: Requires external verification (bank transfers, identity verification)
"""
import os
import uuid
import hashlib
import hmac
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
import json

# Try to import database
try:
    from ..database_supabase import get_db
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False


class SecurityLevel(str, Enum):
    """Security level for different action types"""
    LOW = "low"         # Simple confirmation
    MEDIUM = "medium"   # Double confirmation with summary
    HIGH = "high"       # Multi-step verification
    CRITICAL = "critical"  # External verification required


class ActionStatus(str, Enum):
    """Status of a secure action"""
    PENDING = "pending"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    AWAITING_VERIFICATION = "awaiting_verification"
    VERIFIED = "verified"
    EXECUTED = "executed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class SecureAction:
    """A secure action that requires verification before execution"""
    id: str
    action_type: str
    security_level: SecurityLevel
    status: ActionStatus
    user_id: str
    session_id: str
    parameters: Dict[str, Any]
    confirmations: List[Dict] = field(default_factory=list)
    verification_code: Optional[str] = None
    verification_expires: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    executed_at: Optional[datetime] = None
    result: Optional[Dict] = None
    audit_log: List[Dict] = field(default_factory=list)
    
    def add_audit(self, action: str, details: str = ""):
        """Add audit log entry"""
        self.audit_log.append({
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "details": details
        })
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage"""
        return {
            "id": self.id,
            "action_type": self.action_type,
            "security_level": self.security_level.value,
            "status": self.status.value,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "parameters": self.parameters,
            "confirmations": self.confirmations,
            "verification_code": self.verification_code,
            "verification_expires": self.verification_expires.isoformat() if self.verification_expires else None,
            "created_at": self.created_at.isoformat(),
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "result": self.result,
            "audit_log": self.audit_log
        }


# Security level assignments for different action types
ACTION_SECURITY_LEVELS = {
    # LOW - Simple confirmations
    "reminder": SecurityLevel.LOW,
    "note": SecurityLevel.LOW,
    "search": SecurityLevel.LOW,
    
    # MEDIUM - Double confirmation
    "email": SecurityLevel.MEDIUM,
    "meeting": SecurityLevel.MEDIUM,
    "message": SecurityLevel.MEDIUM,
    
    # HIGH - Multi-step verification
    "payment": SecurityLevel.HIGH,
    "booking": SecurityLevel.HIGH,
    "purchase": SecurityLevel.HIGH,
    "subscription": SecurityLevel.HIGH,
    
    # CRITICAL - External verification
    "bank_transfer": SecurityLevel.CRITICAL,
    "identity_verification": SecurityLevel.CRITICAL,
    "aadhar_verification": SecurityLevel.CRITICAL,
    "account_deletion": SecurityLevel.CRITICAL,
}


# In-memory store (replace with database in production)
_pending_actions: Dict[str, SecureAction] = {}
_action_history: List[SecureAction] = []


class SecureActionManager:
    """
    Manages secure actions with proper verification flows.
    
    This ensures:
    1. All sensitive actions are logged
    2. Multi-step confirmation for payments/bookings
    3. Verification codes for high-security actions
    4. Complete audit trail
    """
    
    def __init__(self):
        self.secret_key = os.getenv("ACTION_SECRET_KEY", "super-manager-secure-2024")
    
    def get_security_level(self, action_type: str) -> SecurityLevel:
        """Get security level for an action type"""
        return ACTION_SECURITY_LEVELS.get(action_type.lower(), SecurityLevel.MEDIUM)
    
    def create_action(
        self,
        action_type: str,
        user_id: str,
        session_id: str,
        parameters: Dict[str, Any]
    ) -> SecureAction:
        """Create a new secure action"""
        action_id = f"action_{uuid.uuid4().hex[:12]}"
        security_level = self.get_security_level(action_type)
        
        action = SecureAction(
            id=action_id,
            action_type=action_type,
            security_level=security_level,
            status=ActionStatus.PENDING,
            user_id=user_id,
            session_id=session_id,
            parameters=parameters
        )
        
        action.add_audit("created", f"Action created with security level: {security_level.value}")
        
        # Store in pending actions
        _pending_actions[action_id] = action
        
        return action
    
    def get_confirmation_flow(self, action: SecureAction) -> Dict[str, Any]:
        """Get the confirmation flow for an action based on security level"""
        
        if action.security_level == SecurityLevel.LOW:
            return {
                "steps": ["confirm"],
                "message": f"Confirm: {self._get_action_summary(action)}",
                "options": [
                    {"label": "Yes, proceed", "value": "confirm"},
                    {"label": "Cancel", "value": "cancel"}
                ]
            }
        
        elif action.security_level == SecurityLevel.MEDIUM:
            return {
                "steps": ["review", "confirm"],
                "message": self._get_detailed_summary(action),
                "options": [
                    {"label": "Confirm & Execute", "value": "confirm"},
                    {"label": "Edit Details", "value": "edit"},
                    {"label": "Cancel", "value": "cancel"}
                ],
                "show_details": True
            }
        
        elif action.security_level == SecurityLevel.HIGH:
            return {
                "steps": ["review", "verify_details", "final_confirm"],
                "message": self._get_security_warning(action),
                "options": [
                    {"label": "Continue to Verification", "value": "verify"},
                    {"label": "Cancel", "value": "cancel"}
                ],
                "show_details": True,
                "show_warning": True,
                "requires_verification": True
            }
        
        else:  # CRITICAL
            return {
                "steps": ["review", "otp_verification", "final_confirm"],
                "message": self._get_critical_warning(action),
                "options": [
                    {"label": "Request OTP", "value": "request_otp"},
                    {"label": "Cancel", "value": "cancel"}
                ],
                "show_details": True,
                "show_warning": True,
                "requires_otp": True,
                "blocked": True,  # Cannot proceed without external verification
                "blocked_reason": "This action requires external verification (OTP) which is not yet configured."
            }
    
    def _get_action_summary(self, action: SecureAction) -> str:
        """Get brief summary of action"""
        params = action.parameters
        
        if action.action_type == "email":
            return f"Send email to {params.get('to', 'recipient')}"
        elif action.action_type == "meeting":
            return f"Create meeting: {params.get('title', 'Untitled')}"
        elif action.action_type == "payment":
            return f"Pay ₹{params.get('amount', '0')} to {params.get('to', 'recipient')}"
        elif action.action_type == "booking":
            return f"Book: {params.get('item', params.get('service', 'item'))}"
        else:
            return f"Execute {action.action_type}"
    
    def _get_detailed_summary(self, action: SecureAction) -> str:
        """Get detailed summary with all parameters"""
        params = action.parameters
        details = [f"**Action:** {action.action_type.upper()}"]
        
        for key, value in params.items():
            if value and key not in ['_internal', '_debug']:
                details.append(f"• **{key.replace('_', ' ').title()}:** {value}")
        
        details.append(f"\n*Action ID: {action.id}*")
        return "\n".join(details)
    
    def _get_security_warning(self, action: SecureAction) -> str:
        """Get security warning for high-security actions"""
        summary = self._get_detailed_summary(action)
        
        warning = """
⚠️ **SECURITY NOTICE**

This action involves a financial transaction or booking. Please verify all details carefully.

"""
        if action.action_type == "payment":
            warning += """
**Important:**
- Ensure the recipient details are correct
- Verify the amount before confirming
- A transaction record will be created
- This action cannot be undone automatically

"""
        elif action.action_type == "booking":
            warning += """
**Note:**
- This is a REQUEST to book, not a confirmed booking
- You will be redirected to the official booking platform
- Payment will be handled securely on the provider's website
- We do NOT store your payment information

"""
        return warning + summary
    
    def _get_critical_warning(self, action: SecureAction) -> str:
        """Get critical warning for very sensitive actions"""
        return f"""
🚨 **CRITICAL SECURITY ACTION**

This action requires additional verification:
- One-Time Password (OTP) verification
- This action will be logged and audited
- Cannot be undone

**Action:** {action.action_type}
**Parameters:** {json.dumps(action.parameters, indent=2)}

Please ensure you understand the implications before proceeding.
"""
    
    def add_confirmation(self, action_id: str, confirmation_type: str, value: str) -> Dict:
        """Add a confirmation step to an action"""
        if action_id not in _pending_actions:
            return {"error": "Action not found", "success": False}
        
        action = _pending_actions[action_id]
        
        if action.status in [ActionStatus.EXECUTED, ActionStatus.CANCELLED]:
            return {"error": "Action already completed", "success": False}
        
        action.confirmations.append({
            "type": confirmation_type,
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
        action.add_audit("confirmation_added", f"Added {confirmation_type} confirmation")
        
        # Update status based on security level and confirmations
        if action.security_level == SecurityLevel.LOW:
            if value == "confirm":
                action.status = ActionStatus.VERIFIED
            elif value == "cancel":
                action.status = ActionStatus.CANCELLED
        
        elif action.security_level == SecurityLevel.MEDIUM:
            if len(action.confirmations) >= 1 and value == "confirm":
                action.status = ActionStatus.VERIFIED
            elif value == "cancel":
                action.status = ActionStatus.CANCELLED
        
        elif action.security_level == SecurityLevel.HIGH:
            # For HIGH security, we don't auto-execute
            # We return instructions for external verification
            if value == "verify":
                action.status = ActionStatus.AWAITING_VERIFICATION
            elif value == "cancel":
                action.status = ActionStatus.CANCELLED
        
        return {"success": True, "action": action.to_dict()}
    
    def get_action(self, action_id: str) -> Optional[SecureAction]:
        """Get an action by ID"""
        return _pending_actions.get(action_id) or self._get_from_history(action_id)
    
    def _get_from_history(self, action_id: str) -> Optional[SecureAction]:
        """Get action from history"""
        for action in _action_history:
            if action.id == action_id:
                return action
        return None
    
    def complete_action(self, action_id: str, result: Dict) -> Dict:
        """Mark action as completed"""
        if action_id not in _pending_actions:
            return {"error": "Action not found", "success": False}
        
        action = _pending_actions[action_id]
        action.status = ActionStatus.EXECUTED
        action.executed_at = datetime.now()
        action.result = result
        action.add_audit("executed", f"Action completed: {result.get('message', 'Done')}")
        
        # Move to history
        _action_history.append(action)
        del _pending_actions[action_id]
        
        # TODO: Store in database
        
        return {"success": True, "action": action.to_dict()}
    
    def get_user_action_history(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get action history for a user"""
        user_actions = [
            a.to_dict() for a in _action_history 
            if a.user_id == user_id
        ]
        return user_actions[-limit:]


# Singleton instance
_manager: Optional[SecureActionManager] = None


def get_secure_action_manager() -> SecureActionManager:
    """Get secure action manager singleton"""
    global _manager
    if _manager is None:
        _manager = SecureActionManager()
    return _manager


# =============================================================================
# BOOKING DISCLAIMER GENERATOR
# =============================================================================

def get_booking_disclaimer(service_type: str, provider: str = "") -> str:
    """Generate appropriate disclaimer for booking-type actions"""
    
    if service_type in ["movie", "concert", "event"]:
        return f"""
📋 **BOOKING INFORMATION**

I can help you find tickets and pricing, but I **cannot directly book** tickets.

**How to proceed:**
1. I'll search for available options
2. I'll provide direct links to official booking platforms
3. You complete the booking on their secure website

**Supported Platforms:**
- BookMyShow
- PayTM Movies
- Official venue websites

*Your payment information stays with the official provider - I never see or store it.*
"""
    
    elif service_type in ["flight", "travel"]:
        return f"""
✈️ **FLIGHT BOOKING INFORMATION**

I can search and compare flights, but booking happens on official platforms.

**I can help with:**
- Finding best prices across airlines
- Comparing flight options
- Providing direct booking links

**You'll book on:**
- Airline official websites
- MakeMyTrip, Yatra, Goibibo, etc.

*Always verify details before completing booking.*
"""
    
    elif service_type in ["hotel", "accommodation"]:
        return f"""
🏨 **HOTEL BOOKING INFORMATION**

I can find hotels and compare prices; booking is done externally.

**I can help with:**
- Finding hotels matching your criteria
- Comparing prices across platforms
- Checking ratings and reviews

**Booking platforms:**
- Hotel official websites
- Booking.com, MakeMyTrip, Agoda, etc.

*Prices may vary; always confirm on booking site.*
"""
    
    elif service_type in ["cab", "ride", "taxi"]:
        return f"""
🚗 **RIDE BOOKING INFORMATION**

I cannot book rides directly. Please use the respective apps.

**Supported Apps:**
- Uber, Ola, Rapido (ride-hailing)
- Rental: Zoomcar, Drivezy

*I can help estimate costs and provide app links.*
"""
    
    elif service_type in ["restaurant", "table"]:
        return f"""
🍽️ **RESTAURANT RESERVATION**

I can help find restaurants but cannot book tables directly.

**Options:**
- Dineout, EazyDiner for reservations
- Call the restaurant directly
- Walk-in (check availability)

*I can provide restaurant details and contact information.*
"""
    
    else:
        return f"""
ℹ️ **SERVICE NOTICE**

I can help research and find options for {service_type}, but actual booking or payment must be completed on official platforms.

**Why?**
- Security: Your payment info stays with verified providers
- Verification: Bookings are confirmed directly by providers
- Support: You get official customer support

*I'll provide all the links and information you need to complete the booking yourself.*
"""


def get_payment_disclaimer() -> str:
    """Get disclaimer for payment-related actions"""
    return """
💳 **PAYMENT NOTICE**

I **cannot process real payments**. Here's what I can do:

✅ **What I CAN do:**
- Calculate total amounts
- Find payment links/UPI IDs
- Provide bill details
- Generate payment reminders

❌ **What I CANNOT do:**
- Process actual bank transfers
- Access your bank account
- Store payment credentials
- Complete transactions on your behalf

**For actual payments, please:**
1. Use your banking app directly
2. Use official payment apps (GPay, Paytm, PhonePe)
3. Visit the service provider's payment page

*This is for your security - payment transactions should always be done through verified, secure channels.*
"""
