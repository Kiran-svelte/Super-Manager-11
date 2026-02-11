"""
Payment Tool - UPI
===================
Generate UPI payment links and deep links.
Free, no API key needed. Requires user confirmation.
"""

import re
import secrets
from datetime import datetime

from .base import Tool, ToolResult


class PaymentLinkTool(Tool):
    name = "generate_payment_link"
    description = "Generate a UPI payment link for sending money"
    parameters = {
        "amount": {"description": "Amount in INR", "required": True, "type": "number"},
        "payee_upi": {"description": "Recipient's UPI ID (e.g. name@upi)", "required": True, "type": "string"},
        "description": {"description": "Payment description/note", "required": False, "type": "string"},
    }
    requires_confirmation = True

    async def execute(self, **params) -> ToolResult:
        amount = params.get("amount", 0)
        payee_upi = params.get("payee_upi", "")
        description = params.get("description", "Payment")

        if not amount or amount <= 0:
            return ToolResult(success=False, output="Invalid amount. Must be greater than 0.", error="invalid_amount")

        if not payee_upi:
            return ToolResult(success=False, output="No UPI ID provided.", error="missing_upi")

        # Validate UPI format
        if not re.match(r"^[\w.\-]+@[\w]+$", payee_upi):
            return ToolResult(
                success=False,
                output=f"Invalid UPI ID format: {payee_upi}. Expected format: name@bank",
                error="invalid_upi_format",
            )

        # Generate transaction reference
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        tx_ref = f"SM-{timestamp}-{secrets.token_hex(3).upper()}"

        # Build UPI URL (RFC 7891)
        upi_params = {
            "pa": payee_upi,
            "pn": payee_upi.split("@")[0],
            "am": f"{amount:.2f}",
            "cu": "INR",
            "tr": tx_ref,
            "tn": description[:50],
        }
        upi_url = "upi://pay?" + "&".join(f"{k}={v}" for k, v in upi_params.items())

        # Deep links for popular UPI apps
        query_part = upi_url.split("?")[1]
        deep_links = {
            "gpay": f"gpay://upi/pay?{query_part}",
            "phonepe": f"phonepe://pay?{query_part}",
            "paytm": f"paytmmp://pay?{query_part}",
        }

        return ToolResult(
            success=True,
            output=(
                f"Payment link created!\n"
                f"Amount: Rs. {amount:.2f}\n"
                f"To: {payee_upi}\n"
                f"Ref: {tx_ref}\n\n"
                f"UPI Link: {upi_url}\n"
                f"Open in GPay, PhonePe, or Paytm to pay."
            ),
            data={
                "upi_link": upi_url,
                "amount": amount,
                "payee_upi": payee_upi,
                "transaction_ref": tx_ref,
                "deep_links": deep_links,
                "ui_components": {
                    "type": "button_group",
                    "buttons": [
                        {"id": "pay_gpay", "label": f"Pay Rs.{amount:.0f} via GPay", "url": deep_links["gpay"], "style": "primary"},
                        {"id": "pay_phonepe", "label": "PhonePe", "url": deep_links["phonepe"], "style": "secondary"},
                        {"id": "pay_paytm", "label": "Paytm", "url": deep_links["paytm"], "style": "secondary"},
                    ],
                },
            },
        )
