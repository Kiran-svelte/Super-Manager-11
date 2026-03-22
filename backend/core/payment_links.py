"""
Payment Links - Multi-tier Payment Link Generation
====================================================
Generates shareable payment links for collecting payments.

Tiers (in priority order):
1. UPI Deep Links (FREE, no API key, India only)
2. Stripe Payment Links (per-txn fees, needs STRIPE_SECRET_KEY)
3. Razorpay (existing integration, needs RAZORPAY_KEY_ID)

Registers as a tool with ToolRegistry on import.
"""

import os
import logging
from typing import Dict, Any, Optional
from urllib.parse import quote, urlencode

import httpx

from .primitives import PrimitiveResult

logger = logging.getLogger(__name__)


async def generate_payment_link(
    amount: float,
    currency: str = "INR",
    recipient_name: str = "",
    description: str = "",
    recipient_upi: str = "",
) -> PrimitiveResult:
    """
    Generate a shareable payment link.

    For INR: Creates UPI deep link + QR code (completely free).
    For other currencies: Tries Stripe, then Razorpay.
    """
    # Convert string to float if needed (LLM sometimes passes strings)
    try:
        amount = float(amount) if isinstance(amount, str) else amount
    except (ValueError, TypeError):
        return PrimitiveResult(
            success=False,
            output="Invalid amount format.",
            error="invalid_amount",
        )
    
    if amount <= 0:
        return PrimitiveResult(
            success=False,
            output="Amount must be greater than 0.",
            error="invalid_amount",
        )

    currency = currency.upper()

    # Tier 1: UPI Deep Links (free, INR only)
    if currency == "INR" and recipient_upi:
        return await _generate_upi_link(amount, recipient_upi, recipient_name, description)

    # Tier 2: Stripe Payment Links
    stripe_key = os.getenv("STRIPE_SECRET_KEY", "")
    if stripe_key:
        return await _generate_stripe_link(amount, currency, description, stripe_key)

    # Tier 3: Razorpay
    razorpay_key = os.getenv("RAZORPAY_KEY_ID", "")
    razorpay_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    if razorpay_key and razorpay_secret:
        return await _generate_razorpay_link(
            amount, currency, description, razorpay_key, razorpay_secret
        )

    # No payment provider available
    if currency == "INR":
        return PrimitiveResult(
            success=False,
            output="For INR payments, please provide a UPI ID (e.g., name@upi). No other payment provider is configured.",
            error="no_upi_id",
        )

    return PrimitiveResult(
        success=False,
        output="No payment provider configured. Set STRIPE_SECRET_KEY or RAZORPAY_KEY_ID environment variables.",
        error="no_payment_provider",
    )


async def _generate_upi_link(
    amount: float,
    upi_id: str,
    name: str,
    note: str,
) -> PrimitiveResult:
    """Generate UPI deep link + QR code. Completely free, no API key."""
    params = {
        "pa": upi_id,
        "pn": name or "Payment",
        "am": f"{amount:.2f}",
        "cu": "INR",
    }
    if note:
        params["tn"] = note[:50]

    upi_link = f"upi://pay?{urlencode(params)}"

    # Generate QR code via free API
    qr_data = quote(upi_link)
    qr_url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={qr_data}"

    output_lines = [
        f"Payment link generated for Rs {amount:.2f}",
        f"",
        f"UPI ID: {upi_id}",
        f"Recipient: {name or 'N/A'}",
        f"Amount: Rs {amount:.2f}",
        f"Note: {note or 'N/A'}",
        f"",
        f"UPI Deep Link: {upi_link}",
        f"QR Code: {qr_url}",
        f"",
        f"Share the UPI link or QR code with the payer. They can scan/click to pay instantly via any UPI app (GPay, PhonePe, Paytm, etc.).",
    ]

    return PrimitiveResult(
        success=True,
        output="\n".join(output_lines),
        data={
            "payment_type": "upi",
            "upi_link": upi_link,
            "qr_code_url": qr_url,
            "amount": amount,
            "currency": "INR",
            "recipient_upi": upi_id,
            "recipient_name": name,
        },
    )


async def _generate_stripe_link(
    amount: float,
    currency: str,
    description: str,
    api_key: str,
) -> PrimitiveResult:
    """Generate Stripe Payment Link via API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a price first
            price_resp = await client.post(
                "https://api.stripe.com/v1/prices",
                headers={"Authorization": f"Bearer {api_key}"},
                data={
                    "unit_amount": int(amount * 100),
                    "currency": currency.lower(),
                    "product_data[name]": description or "Payment",
                },
            )

            if price_resp.status_code != 200:
                error = price_resp.json().get("error", {}).get("message", price_resp.text[:200])
                return PrimitiveResult(
                    success=False,
                    output=f"Stripe price creation failed: {error}",
                    error=str(error),
                )

            price_id = price_resp.json()["id"]

            # Create payment link
            link_resp = await client.post(
                "https://api.stripe.com/v1/payment_links",
                headers={"Authorization": f"Bearer {api_key}"},
                data={
                    "line_items[0][price]": price_id,
                    "line_items[0][quantity]": 1,
                },
            )

            if link_resp.status_code != 200:
                error = link_resp.json().get("error", {}).get("message", link_resp.text[:200])
                return PrimitiveResult(
                    success=False,
                    output=f"Stripe link creation failed: {error}",
                    error=str(error),
                )

            link_data = link_resp.json()
            payment_url = link_data["url"]

            return PrimitiveResult(
                success=True,
                output=f"Stripe payment link created!\nAmount: {currency} {amount:.2f}\nLink: {payment_url}\n\nShare this link with the payer.",
                data={
                    "payment_type": "stripe",
                    "payment_url": payment_url,
                    "amount": amount,
                    "currency": currency,
                    "stripe_link_id": link_data["id"],
                },
            )

    except Exception as e:
        return PrimitiveResult(
            success=False,
            output=f"Stripe payment link generation failed: {str(e)}",
            error=str(e),
        )


async def _generate_razorpay_link(
    amount: float,
    currency: str,
    description: str,
    key_id: str,
    key_secret: str,
) -> PrimitiveResult:
    """Generate Razorpay Payment Link via API."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.razorpay.com/v1/payment_links",
                auth=(key_id, key_secret),
                json={
                    "amount": int(amount * 100),
                    "currency": currency,
                    "description": description or "Payment",
                    "callback_url": "",
                    "callback_method": "get",
                },
            )

            if resp.status_code not in (200, 201):
                error = resp.json().get("error", {}).get("description", resp.text[:200])
                return PrimitiveResult(
                    success=False,
                    output=f"Razorpay link creation failed: {error}",
                    error=str(error),
                )

            link_data = resp.json()
            payment_url = link_data.get("short_url", link_data.get("url", ""))

            return PrimitiveResult(
                success=True,
                output=f"Razorpay payment link created!\nAmount: {currency} {amount:.2f}\nLink: {payment_url}\n\nShare this link with the payer.",
                data={
                    "payment_type": "razorpay",
                    "payment_url": payment_url,
                    "amount": amount,
                    "currency": currency,
                    "razorpay_link_id": link_data.get("id"),
                },
            )

    except Exception as e:
        return PrimitiveResult(
            success=False,
            output=f"Razorpay payment link generation failed: {str(e)}",
            error=str(e),
        )


def register_payment_tools():
    """Register payment tools with the ToolRegistry"""
    try:
        from .tool_registry import get_tool_registry, ToolDef

        registry = get_tool_registry()
        registry.register(ToolDef(
            name="generate_payment_link",
            description="Generate a shareable payment link (UPI for INR, Stripe/Razorpay for other currencies)",
            parameters='amount (float), currency (str, default "INR"), recipient_name (str), description (str), recipient_upi (str, for INR payments)',
            returns="Payment link URL + QR code for UPI",
            risk_level="risky",
            source="payment",
            handler=generate_payment_link,
        ))
        logger.info("[PAYMENT_LINKS] Registered generate_payment_link tool")
    except Exception as e:
        logger.warning(f"[PAYMENT_LINKS] Failed to register: {e}")
