"""
Secure Payment System
Provides real payment integration with proper security, verification, and audit trails.
"""

import asyncio
import hashlib
import hmac
import json
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging
import aiohttp
import os

logger = logging.getLogger(__name__)


class PaymentStatus(Enum):
    """Payment status stages"""
    INITIALIZED = "initialized"
    PENDING_VERIFICATION = "pending_verification"
    OTP_SENT = "otp_sent"
    OTP_VERIFIED = "otp_verified"
    PROCESSING = "processing"
    AWAITING_PAYMENT = "awaiting_payment"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentMethod(Enum):
    """Supported payment methods"""
    UPI = "upi"
    CARD = "card"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class SecurityLevel(Enum):
    """Security levels for payment amounts"""
    LOW = 1      # < ₹500
    MEDIUM = 2   # ₹500 - ₹5,000
    HIGH = 3     # ₹5,000 - ₹50,000
    CRITICAL = 4 # > ₹50,000


@dataclass
class PaymentVerification:
    """Verification requirements for a payment"""
    requires_otp: bool = False
    requires_pin: bool = False
    requires_cvv: bool = False
    requires_2fa: bool = False
    requires_biometric: bool = False
    otp_sent_to: Optional[str] = None
    otp_sent_at: Optional[datetime] = None
    otp_expires_at: Optional[datetime] = None
    otp_attempts: int = 0
    max_otp_attempts: int = 3
    otp_hash: Optional[str] = None


@dataclass
class PaymentAudit:
    """Audit trail for payment"""
    payment_id: str
    events: List[Dict] = field(default_factory=list)
    
    def add_event(self, event_type: str, details: Dict):
        self.events.append({
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "details": details
        })


@dataclass
class PaymentTransaction:
    """Complete payment transaction record"""
    payment_id: str
    user_id: str
    amount: float
    currency: str = "INR"
    description: str = ""
    merchant_id: str = ""
    merchant_name: str = ""
    status: PaymentStatus = PaymentStatus.INITIALIZED
    method: Optional[PaymentMethod] = None
    security_level: SecurityLevel = SecurityLevel.MEDIUM
    verification: PaymentVerification = field(default_factory=PaymentVerification)
    audit: PaymentAudit = None
    
    # Line items
    items: List[Dict] = field(default_factory=list)
    
    # Transaction details
    reference_id: str = field(default_factory=lambda: f"TXN{secrets.token_hex(8).upper()}")
    gateway_transaction_id: Optional[str] = None
    gateway_response: Optional[Dict] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Security tokens
    session_token: str = field(default_factory=lambda: secrets.token_urlsafe(32))
    payment_token: str = field(default_factory=lambda: secrets.token_urlsafe(48))
    
    def __post_init__(self):
        if not self.audit:
            self.audit = PaymentAudit(payment_id=self.payment_id)
            self.audit.add_event("payment_created", {
                "amount": self.amount,
                "currency": self.currency
            })
        
        # Set security level based on amount
        if self.amount < 500:
            self.security_level = SecurityLevel.LOW
        elif self.amount < 5000:
            self.security_level = SecurityLevel.MEDIUM
        elif self.amount < 50000:
            self.security_level = SecurityLevel.HIGH
        else:
            self.security_level = SecurityLevel.CRITICAL
        
        # Set verification requirements based on security level
        if self.security_level.value >= SecurityLevel.MEDIUM.value:
            self.verification.requires_otp = True
        if self.security_level.value >= SecurityLevel.HIGH.value:
            self.verification.requires_2fa = True
        if self.security_level.value >= SecurityLevel.CRITICAL.value:
            self.verification.requires_biometric = True
    
    def to_dict(self) -> Dict:
        return {
            "payment_id": self.payment_id,
            "user_id": self.user_id,
            "amount": self.amount,
            "formatted_amount": f"₹{self.amount:,.2f}",
            "currency": self.currency,
            "description": self.description,
            "merchant_id": self.merchant_id,
            "merchant_name": self.merchant_name,
            "status": self.status.value,
            "method": self.method.value if self.method else None,
            "security_level": self.security_level.value,
            "items": self.items,
            "reference_id": self.reference_id,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "requires_otp": self.verification.requires_otp,
            "requires_2fa": self.verification.requires_2fa
        }


class OTPService:
    """OTP generation and verification service"""
    
    def __init__(self):
        self.otp_store: Dict[str, Dict] = {}  # In production, use Redis or similar
    
    def generate_otp(self, identifier: str, length: int = 6) -> str:
        """Generate a new OTP"""
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(length)])
        otp_hash = hashlib.sha256(f"{identifier}:{otp}".encode()).hexdigest()
        
        self.otp_store[identifier] = {
            "hash": otp_hash,
            "created_at": datetime.now(),
            "expires_at": datetime.now() + timedelta(minutes=5),
            "attempts": 0
        }
        
        return otp
    
    def verify_otp(self, identifier: str, otp: str) -> Tuple[bool, str]:
        """Verify an OTP"""
        stored = self.otp_store.get(identifier)
        
        if not stored:
            return False, "OTP not found or expired"
        
        if datetime.now() > stored["expires_at"]:
            del self.otp_store[identifier]
            return False, "OTP has expired"
        
        if stored["attempts"] >= 3:
            del self.otp_store[identifier]
            return False, "Maximum attempts exceeded"
        
        stored["attempts"] += 1
        
        otp_hash = hashlib.sha256(f"{identifier}:{otp}".encode()).hexdigest()
        
        if otp_hash == stored["hash"]:
            del self.otp_store[identifier]
            return True, "OTP verified successfully"
        
        return False, f"Invalid OTP. {3 - stored['attempts']} attempts remaining"


class PaymentGatewayBase:
    """Base class for payment gateway integrations"""
    
    async def create_payment(self, transaction: PaymentTransaction) -> Dict:
        raise NotImplementedError
    
    async def verify_payment(self, transaction_id: str) -> Dict:
        raise NotImplementedError
    
    async def process_refund(self, transaction_id: str, amount: float) -> Dict:
        raise NotImplementedError


class RazorpayGateway(PaymentGatewayBase):
    """Razorpay payment gateway integration"""
    
    def __init__(self, key_id: str = None, key_secret: str = None):
        self.key_id = key_id or os.getenv("RAZORPAY_KEY_ID")
        self.key_secret = key_secret or os.getenv("RAZORPAY_KEY_SECRET")
        self.base_url = "https://api.razorpay.com/v1"
    
    async def create_payment(self, transaction: PaymentTransaction) -> Dict:
        """Create a Razorpay payment order"""
        if not self.key_id or not self.key_secret:
            return {
                "success": False,
                "error": "Razorpay credentials not configured",
                "demo_mode": True,
                "demo_payment_link": f"https://rzp.io/demo/{transaction.payment_id}"
            }
        
        async with aiohttp.ClientSession() as session:
            auth = aiohttp.BasicAuth(self.key_id, self.key_secret)
            
            payload = {
                "amount": int(transaction.amount * 100),  # Amount in paise
                "currency": transaction.currency,
                "receipt": transaction.reference_id,
                "notes": {
                    "description": transaction.description,
                    "merchant_id": transaction.merchant_id
                }
            }
            
            try:
                async with session.post(
                    f"{self.base_url}/orders",
                    json=payload,
                    auth=auth
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "order_id": data["id"],
                            "amount": data["amount"] / 100,
                            "currency": data["currency"],
                            "payment_link": f"https://rzp.io/i/{data['id']}"
                        }
                    else:
                        error_data = await response.json()
                        return {
                            "success": False,
                            "error": error_data.get("error", {}).get("description", "Unknown error")
                        }
            except Exception as e:
                logger.error(f"Razorpay API error: {str(e)}")
                return {
                    "success": False,
                    "error": str(e)
                }
    
    async def verify_payment(self, order_id: str, payment_id: str, signature: str) -> Dict:
        """Verify Razorpay payment signature"""
        if not self.key_secret:
            return {"success": False, "error": "Razorpay not configured"}
        
        expected_signature = hmac.new(
            self.key_secret.encode(),
            f"{order_id}|{payment_id}".encode(),
            hashlib.sha256
        ).hexdigest()
        
        if hmac.compare_digest(expected_signature, signature):
            return {"success": True, "verified": True}
        
        return {"success": False, "error": "Invalid signature"}


class PayPhonePayGateway(PaymentGatewayBase):
    """PhonePe payment gateway integration"""
    
    def __init__(self, merchant_id: str = None, salt_key: str = None, salt_index: str = "1"):
        self.merchant_id = merchant_id or os.getenv("PHONEPE_MERCHANT_ID")
        self.salt_key = salt_key or os.getenv("PHONEPE_SALT_KEY")
        self.salt_index = salt_index
        self.base_url = "https://api.phonepe.com/apis/hermes"
    
    async def create_payment(self, transaction: PaymentTransaction) -> Dict:
        """Create a PhonePe payment"""
        if not self.merchant_id or not self.salt_key:
            return {
                "success": False,
                "error": "PhonePe credentials not configured",
                "demo_mode": True
            }
        
        # PhonePe implementation would go here
        return {"success": False, "error": "PhonePe integration pending"}


class UPIPaymentHandler:
    """Handler for UPI payments"""
    
    @staticmethod
    def generate_upi_link(
        payee_vpa: str,
        payee_name: str,
        amount: float,
        transaction_ref: str,
        description: str = ""
    ) -> Dict:
        """Generate a valid UPI payment link"""
        
        # Validate VPA format
        if not re.match(r'^[\w\.\-]+@[\w]+$', payee_vpa):
            return {
                "success": False,
                "error": "Invalid UPI VPA format"
            }
        
        # Build UPI URL
        upi_params = {
            "pa": payee_vpa,  # Payee VPA
            "pn": payee_name.replace(" ", "%20"),  # Payee name
            "am": f"{amount:.2f}",  # Amount
            "cu": "INR",  # Currency
            "tr": transaction_ref,  # Transaction reference
            "tn": description.replace(" ", "%20")[:50]  # Transaction note
        }
        
        upi_url = "upi://pay?" + "&".join([f"{k}={v}" for k, v in upi_params.items()])
        
        return {
            "success": True,
            "upi_link": upi_url,
            "payee_vpa": payee_vpa,
            "payee_name": payee_name,
            "amount": amount,
            "transaction_ref": transaction_ref,
            "deep_links": {
                "gpay": f"gpay://upi/pay?{upi_url.split('?')[1]}",
                "phonepe": f"phonepe://pay?{upi_url.split('?')[1]}",
                "paytm": f"paytmmp://pay?{upi_url.split('?')[1]}"
            }
        }
    
    @staticmethod
    def validate_upi_id(upi_id: str) -> bool:
        """Validate UPI ID format"""
        pattern = r'^[\w\.\-]+@[a-zA-Z]+$'
        return bool(re.match(pattern, upi_id))


class SecurePaymentService:
    """Main service for handling secure payments"""
    
    def __init__(self):
        self.transactions: Dict[str, PaymentTransaction] = {}
        self.otp_service = OTPService()
        self.razorpay = RazorpayGateway()
        self.upi_handler = UPIPaymentHandler()
    
    def generate_payment_id(self) -> str:
        """Generate unique payment ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        random_part = secrets.token_hex(4).upper()
        return f"PAY-{timestamp}-{random_part}"
    
    async def initiate_payment(
        self,
        user_id: str,
        amount: float,
        description: str,
        merchant_id: str,
        merchant_name: str,
        items: List[Dict] = None,
        method: PaymentMethod = None
    ) -> Dict:
        """Initiate a new payment"""
        
        # Create transaction
        payment_id = self.generate_payment_id()
        transaction = PaymentTransaction(
            payment_id=payment_id,
            user_id=user_id,
            amount=amount,
            description=description,
            merchant_id=merchant_id,
            merchant_name=merchant_name,
            items=items or [],
            method=method,
            expires_at=datetime.now() + timedelta(minutes=15)
        )
        
        self.transactions[payment_id] = transaction
        
        # Return response based on security level
        response = {
            "success": True,
            "payment_id": payment_id,
            "amount": amount,
            "formatted_amount": f"₹{amount:,.2f}",
            "status": transaction.status.value,
            "security_level": transaction.security_level.value,
            "expires_in_minutes": 15,
            "session_token": transaction.session_token
        }
        
        # Add verification requirements
        if transaction.verification.requires_otp:
            response["requires_otp"] = True
            response["next_step"] = "send_otp"
        else:
            response["next_step"] = "select_payment_method"
        
        return response
    
    async def send_verification_otp(
        self,
        payment_id: str,
        phone_number: str,
        session_token: str
    ) -> Dict:
        """Send OTP for payment verification"""
        
        transaction = self.transactions.get(payment_id)
        if not transaction:
            return {"success": False, "error": "Payment not found"}
        
        if transaction.session_token != session_token:
            return {"success": False, "error": "Invalid session"}
        
        if transaction.expires_at and datetime.now() > transaction.expires_at:
            transaction.status = PaymentStatus.EXPIRED
            return {"success": False, "error": "Payment has expired"}
        
        # Generate and "send" OTP
        otp = self.otp_service.generate_otp(payment_id)
        
        # In production, integrate with SMS gateway
        # For now, log it (in production, NEVER log OTPs)
        logger.info(f"[DEV ONLY] OTP for {payment_id}: {otp}")
        
        # Update transaction
        transaction.verification.otp_sent_to = self._mask_phone(phone_number)
        transaction.verification.otp_sent_at = datetime.now()
        transaction.verification.otp_expires_at = datetime.now() + timedelta(minutes=5)
        transaction.status = PaymentStatus.OTP_SENT
        
        transaction.audit.add_event("otp_sent", {
            "phone": self._mask_phone(phone_number)
        })
        
        return {
            "success": True,
            "message": f"OTP sent to {self._mask_phone(phone_number)}",
            "expires_in_seconds": 300,
            "next_step": "verify_otp"
        }
    
    async def verify_otp(
        self,
        payment_id: str,
        otp: str,
        session_token: str
    ) -> Dict:
        """Verify payment OTP"""
        
        transaction = self.transactions.get(payment_id)
        if not transaction:
            return {"success": False, "error": "Payment not found"}
        
        if transaction.session_token != session_token:
            return {"success": False, "error": "Invalid session"}
        
        # Verify OTP
        verified, message = self.otp_service.verify_otp(payment_id, otp)
        
        if verified:
            transaction.status = PaymentStatus.OTP_VERIFIED
            transaction.audit.add_event("otp_verified", {})
            
            return {
                "success": True,
                "message": "OTP verified successfully",
                "next_step": "select_payment_method"
            }
        
        transaction.verification.otp_attempts += 1
        transaction.audit.add_event("otp_failed", {
            "attempts": transaction.verification.otp_attempts
        })
        
        return {
            "success": False,
            "error": message
        }
    
    async def process_payment(
        self,
        payment_id: str,
        method: PaymentMethod,
        payment_details: Dict,
        session_token: str
    ) -> Dict:
        """Process the payment through selected method"""
        
        transaction = self.transactions.get(payment_id)
        if not transaction:
            return {"success": False, "error": "Payment not found"}
        
        if transaction.session_token != session_token:
            return {"success": False, "error": "Invalid session"}
        
        # Verify OTP was verified if required
        if transaction.verification.requires_otp and transaction.status != PaymentStatus.OTP_VERIFIED:
            return {"success": False, "error": "OTP verification required"}
        
        transaction.method = method
        transaction.status = PaymentStatus.PROCESSING
        transaction.audit.add_event("payment_processing", {"method": method.value})
        
        # Process based on payment method
        if method == PaymentMethod.UPI:
            return await self._process_upi_payment(transaction, payment_details)
        elif method == PaymentMethod.CARD:
            return await self._process_card_payment(transaction, payment_details)
        else:
            return await self._process_gateway_payment(transaction, payment_details)
    
    async def _process_upi_payment(
        self,
        transaction: PaymentTransaction,
        details: Dict
    ) -> Dict:
        """Process UPI payment"""
        
        payee_vpa = details.get("payee_vpa") or os.getenv("MERCHANT_UPI_ID", "merchant@upi")
        payee_name = details.get("payee_name") or transaction.merchant_name
        
        upi_result = self.upi_handler.generate_upi_link(
            payee_vpa=payee_vpa,
            payee_name=payee_name,
            amount=transaction.amount,
            transaction_ref=transaction.reference_id,
            description=transaction.description
        )
        
        if not upi_result["success"]:
            return upi_result
        
        transaction.status = PaymentStatus.AWAITING_PAYMENT
        transaction.audit.add_event("upi_link_generated", {
            "payee_vpa": payee_vpa
        })
        
        return {
            "success": True,
            "payment_id": transaction.payment_id,
            "status": "awaiting_payment",
            "payment_method": "upi",
            "upi_link": upi_result["upi_link"],
            "payee_vpa": payee_vpa,
            "payee_name": payee_name,
            "amount": transaction.amount,
            "formatted_amount": f"₹{transaction.amount:,.2f}",
            "reference_id": transaction.reference_id,
            "deep_links": upi_result["deep_links"],
            "expires_at": transaction.expires_at.isoformat() if transaction.expires_at else None,
            "instructions": [
                "Click on your preferred UPI app below",
                "Or scan the QR code with any UPI app",
                "Complete the payment in the app",
                "Return here after payment"
            ],
            "next_step": "await_payment_confirmation"
        }
    
    async def _process_card_payment(
        self,
        transaction: PaymentTransaction,
        details: Dict
    ) -> Dict:
        """Process card payment through gateway"""
        
        # Create Razorpay order
        gateway_result = await self.razorpay.create_payment(transaction)
        
        if not gateway_result.get("success"):
            return {
                "success": False,
                "error": gateway_result.get("error", "Payment gateway error"),
                "demo_mode": gateway_result.get("demo_mode", False)
            }
        
        transaction.gateway_transaction_id = gateway_result.get("order_id")
        transaction.status = PaymentStatus.AWAITING_PAYMENT
        
        return {
            "success": True,
            "payment_id": transaction.payment_id,
            "gateway_order_id": gateway_result.get("order_id"),
            "payment_link": gateway_result.get("payment_link"),
            "amount": transaction.amount,
            "next_step": "complete_payment_on_gateway"
        }
    
    async def _process_gateway_payment(
        self,
        transaction: PaymentTransaction,
        details: Dict
    ) -> Dict:
        """Process payment through payment gateway"""
        return await self._process_card_payment(transaction, details)
    
    async def verify_payment_status(self, payment_id: str) -> Dict:
        """Check payment status"""
        
        transaction = self.transactions.get(payment_id)
        if not transaction:
            return {"success": False, "error": "Payment not found"}
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": transaction.status.value,
            "amount": transaction.amount,
            "reference_id": transaction.reference_id,
            "completed": transaction.status == PaymentStatus.COMPLETED
        }
    
    async def confirm_payment(
        self,
        payment_id: str,
        confirmation_data: Dict
    ) -> Dict:
        """Confirm payment completion (called by webhook or manual confirmation)"""
        
        transaction = self.transactions.get(payment_id)
        if not transaction:
            return {"success": False, "error": "Payment not found"}
        
        transaction.status = PaymentStatus.COMPLETED
        transaction.completed_at = datetime.now()
        transaction.gateway_response = confirmation_data
        
        transaction.audit.add_event("payment_completed", {
            "gateway_response": confirmation_data
        })
        
        return {
            "success": True,
            "payment_id": payment_id,
            "status": "completed",
            "reference_id": transaction.reference_id,
            "amount": transaction.amount,
            "completed_at": transaction.completed_at.isoformat(),
            "receipt": self._generate_receipt(transaction)
        }
    
    def _generate_receipt(self, transaction: PaymentTransaction) -> Dict:
        """Generate payment receipt"""
        return {
            "receipt_id": f"RCP-{transaction.reference_id}",
            "payment_id": transaction.payment_id,
            "reference_id": transaction.reference_id,
            "amount": transaction.amount,
            "formatted_amount": f"₹{transaction.amount:,.2f}",
            "merchant": transaction.merchant_name,
            "description": transaction.description,
            "items": transaction.items,
            "payment_method": transaction.method.value if transaction.method else None,
            "status": "PAID",
            "paid_at": transaction.completed_at.isoformat() if transaction.completed_at else None,
            "created_at": transaction.created_at.isoformat()
        }
    
    def _mask_phone(self, phone: str) -> str:
        """Mask phone number for privacy"""
        if len(phone) >= 10:
            return f"******{phone[-4:]}"
        return "******" + phone[-2:]
    
    def get_transaction(self, payment_id: str) -> Optional[PaymentTransaction]:
        """Get transaction by ID"""
        return self.transactions.get(payment_id)


# Webhook handler for payment gateways
class PaymentWebhookHandler:
    """Handle webhooks from payment gateways"""
    
    def __init__(self, payment_service: SecurePaymentService):
        self.payment_service = payment_service
    
    async def handle_razorpay_webhook(
        self,
        payload: Dict,
        signature: str
    ) -> Dict:
        """Handle Razorpay webhook"""
        
        # Verify webhook signature
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if webhook_secret:
            expected_signature = hmac.new(
                webhook_secret.encode(),
                json.dumps(payload, separators=(',', ':')).encode(),
                hashlib.sha256
            ).hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                return {"success": False, "error": "Invalid signature"}
        
        event = payload.get("event")
        
        if event == "payment.captured":
            payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
            order_id = payment_entity.get("order_id")
            
            # Find transaction by gateway order ID
            for txn in self.payment_service.transactions.values():
                if txn.gateway_transaction_id == order_id:
                    return await self.payment_service.confirm_payment(
                        txn.payment_id,
                        payment_entity
                    )
        
        return {"success": True, "message": "Webhook processed"}
