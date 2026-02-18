"""
Payment Links - 3-Tier Payment Generation
=========================================
v6 NEW - Enhanced payment link generation with multiple tiers.

Tiers:
1. UPI Deep Links (FREE) - For INR payments via UPI
2. Stripe Payment Links (optional) - For international payments
3. Razorpay (existing) - Fallback for India

Registers with ToolRegistry as "generate_payment_link" (risky).
"""

import os
import re
import json
import secrets
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from urllib.parse import quote

import httpx

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


# =============================================================================
# TIER 1: UPI Deep Links (FREE)
# =============================================================================

def generate_upi_link(
    amount: float,
    vpa: str,
    name: str = "",
    note: str = "Payment",
) -> Dict[str, Any]:
    """
    Generate UPI payment deep link for Indian payments.
    
    Args:
        amount: Amount in INR
        vpa: UPI ID (e.g., username@upi)
        name: Payee name (defaults to username from VPA)
        note: Payment description
    
    Returns:
        Dict with upi_link, qr_code_url, deep_links, and transaction_ref
    """
    # Validate UPI format
    if not re.match(r"^[\w.\-]+@[\w]+$", vpa):
        raise ValueError(f"Invalid UPI ID format: {vpa}. Expected format: name@bank")
    
    # Generate transaction reference
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    tx_ref = f"SM-{timestamp}-{secrets.token_hex(3).upper()}"
    
    # Extract name from VPA if not provided
    if not name:
        name = vpa.split("@")[0]
    
    # Build UPI URL (RFC 7891 standard)
    upi_params = {
        "pa": vpa,  # Payee address
        "pn": name,  # Payee name
        "am": f"{amount:.2f}",  # Amount
        "cu": "INR",  # Currency
        "tr": tx_ref,  # Transaction reference
        "tn": note[:50],  # Transaction note (limited to 50 chars)
    }
    
    upi_url = "upi://pay?" + "&".join(f"{k}={quote(str(v))}" for k, v in upi_params.items())
    
    # Generate QR code URL (using free QR code API)
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={quote(upi_url)}"
    
    # Deep links for popular UPI apps
    query_part = upi_url.split("?")[1]
    deep_links = {
        "gpay": f"tez://upi/pay?{query_part}",  # Google Pay
        "phonepe": f"phonepe://pay?{query_part}",
        "paytm": f"paytmmp://pay?{query_part}",
        "bhim": f"bhim://pay?{query_part}",
    }
    
    return {
        "upi_link": upi_url,
        "qr_code_url": qr_code_url,
        "deep_links": deep_links,
        "transaction_ref": tx_ref,
        "amount": amount,
        "payee_vpa": vpa,
        "payee_name": name,
    }


# =============================================================================
# TIER 2: Stripe Payment Links (Optional)
# =============================================================================

async def generate_stripe_link(
    amount: float,
    currency: str,
    description: str = "Payment",
    success_url: Optional[str] = None,
    cancel_url: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate Stripe Payment Link (requires STRIPE_SECRET_KEY env var).
    
    Args:
        amount: Amount in smallest currency unit (e.g., cents for USD)
        currency: Currency code (e.g., "usd", "eur", "gbp")
        description: Payment description
        success_url: URL to redirect after successful payment
        cancel_url: URL to redirect if payment is cancelled
    
    Returns:
        Dict with payment_link, amount, currency
    
    Raises:
        ValueError: If STRIPE_SECRET_KEY not set
        Exception: If Stripe API call fails
    """
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if not stripe_key:
        raise ValueError("STRIPE_SECRET_KEY environment variable not set")
    
    # Convert amount to smallest unit (cents, paise, etc.)
    # Assume amount is already in the right unit
    amount_int = int(amount)
    
    # Create Stripe Payment Link via API
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # First, create a price object
            price_response = await client.post(
                "https://api.stripe.com/v1/prices",
                headers={
                    "Authorization": f"Bearer {stripe_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "unit_amount": amount_int,
                    "currency": currency,
                    "product_data[name]": description[:100],
                },
            )
            
            if price_response.status_code != 200:
                raise Exception(f"Stripe price creation failed: {price_response.text}")
            
            price_data = price_response.json()
            price_id = price_data["id"]
            
            # Create payment link
            link_data = {
                "line_items[0][price]": price_id,
                "line_items[0][quantity]": 1,
            }
            
            if success_url:
                link_data["after_completion[type]"] = "redirect"
                link_data["after_completion[redirect][url]"] = success_url
            
            link_response = await client.post(
                "https://api.stripe.com/v1/payment_links",
                headers={
                    "Authorization": f"Bearer {stripe_key}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data=link_data,
            )
            
            if link_response.status_code != 200:
                raise Exception(f"Stripe link creation failed: {link_response.text}")
            
            link_result = link_response.json()
            
            return {
                "payment_link": link_result["url"],
                "amount": amount,
                "currency": currency,
                "stripe_price_id": price_id,
                "stripe_link_id": link_result["id"],
            }
    
    except httpx.TimeoutException:
        raise Exception("Stripe API request timed out")
    except Exception as e:
        logger.error(f"Stripe payment link generation failed: {e}")
        raise


# =============================================================================
# TIER 3: Razorpay (Existing)
# =============================================================================

async def generate_razorpay_link(
    amount: float,
    currency: str = "INR",
    description: str = "Payment",
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generate Razorpay Payment Link (requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET).
    
    Args:
        amount: Amount in smallest currency unit (paise for INR)
        currency: Currency code (default "INR")
        description: Payment description
        customer_name: Customer name (optional)
        customer_email: Customer email (optional)
    
    Returns:
        Dict with payment_link, short_url, amount, currency
    
    Raises:
        ValueError: If Razorpay credentials not set
        Exception: If Razorpay API call fails
    """
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    
    if not key_id or not key_secret:
        raise ValueError("RAZORPAY_KEY_ID or RAZORPAY_KEY_SECRET environment variables not set")
    
    # Convert amount to paise
    amount_paise = int(amount * 100) if currency == "INR" else int(amount)
    
    # Create payment link via Razorpay API
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            payload = {
                "amount": amount_paise,
                "currency": currency,
                "description": description[:255],
                "type": "link",
            }
            
            if customer_name:
                payload["customer"] = {"name": customer_name}
                if customer_email:
                    payload["customer"]["email"] = customer_email
            
            response = await client.post(
                "https://api.razorpay.com/v1/payment_links",
                auth=(key_id, key_secret),
                headers={"Content-Type": "application/json"},
                json=payload,
            )
            
            if response.status_code != 200:
                raise Exception(f"Razorpay link creation failed: {response.text}")
            
            result = response.json()
            
            return {
                "payment_link": result["short_url"],
                "long_url": result.get("url", ""),
                "amount": amount,
                "currency": currency,
                "razorpay_link_id": result["id"],
            }
    
    except httpx.TimeoutException:
        raise Exception("Razorpay API request timed out")
    except Exception as e:
        logger.error(f"Razorpay payment link generation failed: {e}")
        raise


# =============================================================================
# MAIN FUNCTION (Unified Interface)
# =============================================================================

async def generate_payment_link(
    amount: float,
    currency: str = "INR",
    payee: str = "",
    description: str = "Payment",
    customer_name: Optional[str] = None,
    customer_email: Optional[str] = None,
) -> PrimitiveResult:
    """
    Generate a payment link using the best available method.
    
    Tier Selection Logic:
    1. If currency == "INR" and payee is UPI ID → UPI deep link (free)
    2. If STRIPE_SECRET_KEY is set → Stripe Payment Link
    3. If RAZORPAY credentials are set → Razorpay Payment Link
    4. Otherwise → Error
    
    Args:
        amount: Amount (in base unit for currency, e.g., rupees for INR)
        currency: Currency code (default "INR")
        payee: UPI ID (for INR) or recipient identifier
        description: Payment description
        customer_name: Customer name (for Razorpay)
        customer_email: Customer email (for Razorpay)
    
    Returns:
        PrimitiveResult with payment link details
    """
    if amount <= 0:
        return PrimitiveResult(
            success=False,
            output="Invalid amount. Must be greater than 0.",
            error="invalid_amount",
        )
    
    # TIER 1: UPI Deep Links (FREE) - For INR payments with UPI ID
    if currency.upper() == "INR" and payee and "@" in payee:
        try:
            result = generate_upi_link(
                amount=amount,
                vpa=payee,
                note=description,
            )
            
            output = f"""Payment link created (UPI)!
Amount: Rs. {amount:.2f}
To: {result['payee_name']} ({result['payee_vpa']})
Transaction Ref: {result['transaction_ref']}

UPI Link: {result['upi_link']}
QR Code: {result['qr_code_url']}

Open in:
- Google Pay: {result['deep_links']['gpay']}
- PhonePe: {result['deep_links']['phonepe']}
- Paytm: {result['deep_links']['paytm']}
- BHIM: {result['deep_links']['bhim']}
"""
            
            return PrimitiveResult(
                success=True,
                output=output,
                data={
                    "tier": "upi",
                    "method": "UPI Deep Link",
                    **result,
                },
            )
        
        except ValueError as e:
            logger.warning(f"UPI link generation failed: {e}")
            # Fall through to other tiers
        except Exception as e:
            logger.error(f"UPI link generation error: {e}")
            # Fall through to other tiers
    
    # TIER 2: Stripe Payment Links (Optional)
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_key:
        try:
            # Convert amount to cents/smallest unit
            if currency.upper() == "INR":
                amount_smallest = int(amount * 100)  # Paise
            elif currency.upper() in ["USD", "EUR", "GBP"]:
                amount_smallest = int(amount * 100)  # Cents
            else:
                amount_smallest = int(amount * 100)  # Default: assume 2 decimals
            
            result = await generate_stripe_link(
                amount=amount_smallest,
                currency=currency.lower(),
                description=description,
            )
            
            output = f"""Payment link created (Stripe)!
Amount: {amount:.2f} {currency.upper()}
Description: {description}

Payment Link: {result['payment_link']}
"""
            
            return PrimitiveResult(
                success=True,
                output=output,
                data={
                    "tier": "stripe",
                    "method": "Stripe Payment Link",
                    **result,
                },
            )
        
        except ValueError as e:
            logger.warning(f"Stripe payment link failed: {e}")
            # Fall through to Razorpay
        except Exception as e:
            logger.error(f"Stripe payment link error: {e}")
            # Fall through to Razorpay
    
    # TIER 3: Razorpay (Existing)
    razorpay_key_id = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    
    if razorpay_key_id and razorpay_key_secret:
        try:
            result = await generate_razorpay_link(
                amount=amount,
                currency=currency.upper(),
                description=description,
                customer_name=customer_name,
                customer_email=customer_email,
            )
            
            output = f"""Payment link created (Razorpay)!
Amount: {amount:.2f} {currency.upper()}
Description: {description}

Payment Link: {result['payment_link']}
"""
            
            return PrimitiveResult(
                success=True,
                output=output,
                data={
                    "tier": "razorpay",
                    "method": "Razorpay Payment Link",
                    **result,
                },
            )
        
        except ValueError as e:
            logger.warning(f"Razorpay payment link failed: {e}")
        except Exception as e:
            logger.error(f"Razorpay payment link error: {e}")
    
    # No payment method available
    return PrimitiveResult(
        success=False,
        output=(
            "No payment method available. To generate payment links:\n"
            "- For INR: Provide a UPI ID (e.g., username@upi) as the payee\n"
            "- For international: Set STRIPE_SECRET_KEY environment variable\n"
            "- For India (alternative): Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET"
        ),
        error="no_payment_method",
    )


# =============================================================================
# TOOL REGISTRATION (Called by brain.py or main.py on startup)
# =============================================================================

def register_payment_tools():
    """
    Register payment tools with ToolRegistry.
    Should be called on application startup.
    """
    try:
        from .tool_registry import get_tool_registry, ToolDef
        
        registry = get_tool_registry()
        
        tool = ToolDef(
            name="generate_payment_link",
            description="Generate a payment link for sending money (UPI/Stripe/Razorpay)",
            parameters={
                "amount": {"type": "number", "description": "Amount in base currency unit (e.g., rupees for INR)"},
                "currency": {"type": "string", "description": "Currency code (default: INR)"},
                "payee": {"type": "string", "description": "UPI ID (for INR) or recipient identifier"},
                "description": {"type": "string", "description": "Payment description"},
                "customer_name": {"type": "string", "description": "Customer name (optional)"},
                "customer_email": {"type": "string", "description": "Customer email (optional)"},
            },
            risk_level="risky",  # Requires user confirmation
            source="payment",
            handler=generate_payment_link,
        )
        
        registry.register(tool)
        logger.info("Registered payment tool: generate_payment_link")
    
    except Exception as e:
        logger.error(f"Failed to register payment tools: {e}")
