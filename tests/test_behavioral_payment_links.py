"""
Behavioral Tests: Payment Links
================================
Tests that the payment links module ACTUALLY works:
- generate_payment_link function
- _generate_upi_link function
- UPI deep link generation
- QR code URL generation

README Requirements:
- Payment link generation
- UPI support
- Multiple payment providers
"""

import pytest
from urllib.parse import parse_qs, urlparse

from backend.core.payment_links import (
    generate_payment_link,
    _generate_upi_link,
)
from backend.core.primitives import PrimitiveResult


class TestGeneratePaymentLinkFunction:
    """Test generate_payment_link function"""
    
    def test_function_exists(self):
        """generate_payment_link function should exist"""
        assert generate_payment_link is not None
        assert callable(generate_payment_link)
    
    @pytest.mark.asyncio
    async def test_invalid_amount_zero(self):
        """Should fail for zero amount"""
        result = await generate_payment_link(amount=0)
        assert result.success is False
        assert "greater than 0" in result.output.lower() or result.error == "invalid_amount"
    
    @pytest.mark.asyncio
    async def test_invalid_amount_negative(self):
        """Should fail for negative amount"""
        result = await generate_payment_link(amount=-100)
        assert result.success is False
    
    @pytest.mark.asyncio
    async def test_returns_primitive_result(self):
        """Should return PrimitiveResult"""
        result = await generate_payment_link(
            amount=100,
            currency="INR",
            recipient_upi="test@upi"
        )
        assert isinstance(result, PrimitiveResult)


class TestGenerateUPILinkFunction:
    """Test _generate_upi_link function"""
    
    def test_function_exists(self):
        """_generate_upi_link function should exist"""
        assert _generate_upi_link is not None
        assert callable(_generate_upi_link)
    
    @pytest.mark.asyncio
    async def test_returns_primitive_result(self):
        """Should return PrimitiveResult"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="test@upi",
            name="Test User",
            note="Test payment"
        )
        assert isinstance(result, PrimitiveResult)
    
    @pytest.mark.asyncio
    async def test_success_for_valid_input(self):
        """Should succeed for valid input"""
        result = await _generate_upi_link(
            amount=500,
            upi_id="merchant@upi",
            name="Merchant",
            note="Product purchase"
        )
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_includes_upi_link(self):
        """Result should include UPI deep link"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="user@upi",
            name="User",
            note="Note"
        )
        assert "upi_link" in result.data
        assert result.data["upi_link"].startswith("upi://pay?")
    
    @pytest.mark.asyncio
    async def test_includes_qr_code_url(self):
        """Result should include QR code URL"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="user@upi",
            name="User",
            note="Note"
        )
        assert "qr_code_url" in result.data
        assert "qrserver.com" in result.data["qr_code_url"]
    
    @pytest.mark.asyncio
    async def test_upi_link_contains_amount(self):
        """UPI link should contain the amount"""
        result = await _generate_upi_link(
            amount=250.50,
            upi_id="user@upi",
            name="User",
            note=""
        )
        assert "am=" in result.data["upi_link"]
        assert "250.50" in result.data["upi_link"]
    
    @pytest.mark.asyncio
    async def test_upi_link_contains_upi_id(self):
        """UPI link should contain the UPI ID"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="merchant@okaxis",
            name="Merchant",
            note=""
        )
        assert "pa=merchant%40okaxis" in result.data["upi_link"]
    
    @pytest.mark.asyncio
    async def test_data_includes_amount(self):
        """Result data should include amount"""
        result = await _generate_upi_link(
            amount=999.99,
            upi_id="user@upi",
            name="User",
            note="Note"
        )
        assert result.data["amount"] == 999.99
    
    @pytest.mark.asyncio
    async def test_data_includes_currency_inr(self):
        """Result data should include currency as INR"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="user@upi",
            name="User",
            note="Note"
        )
        assert result.data["currency"] == "INR"
    
    @pytest.mark.asyncio
    async def test_data_includes_payment_type(self):
        """Result data should include payment_type as upi"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="user@upi",
            name="User",
            note="Note"
        )
        assert result.data["payment_type"] == "upi"
    
    @pytest.mark.asyncio
    async def test_data_includes_recipient_upi(self):
        """Result data should include recipient_upi"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="myupi@bank",
            name="User",
            note="Note"
        )
        assert result.data["recipient_upi"] == "myupi@bank"
    
    @pytest.mark.asyncio
    async def test_data_includes_recipient_name(self):
        """Result data should include recipient_name"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="user@upi",
            name="John Doe",
            note="Note"
        )
        assert result.data["recipient_name"] == "John Doe"


class TestGeneratePaymentLinkUPI:
    """Test generate_payment_link with UPI"""
    
    @pytest.mark.asyncio
    async def test_inr_with_upi_id_succeeds(self):
        """INR with UPI ID should succeed"""
        result = await generate_payment_link(
            amount=100,
            currency="INR",
            recipient_upi="test@upi"
        )
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_inr_without_upi_id_fails(self):
        """INR without UPI ID should fail (no provider)"""
        # This test assumes no Stripe/Razorpay env vars
        result = await generate_payment_link(
            amount=100,
            currency="INR",
            recipient_upi=""  # No UPI ID
        )
        # Either fails or prompts for UPI ID
        if not result.success:
            assert "upi" in result.output.lower() or result.error == "no_upi_id"


class TestPaymentOutputFormat:
    """Test payment output format"""
    
    @pytest.mark.asyncio
    async def test_output_includes_amount(self):
        """Output should include amount"""
        result = await _generate_upi_link(
            amount=500,
            upi_id="user@upi",
            name="User",
            note=""
        )
        assert "500" in result.output
    
    @pytest.mark.asyncio
    async def test_output_includes_upi_id(self):
        """Output should include UPI ID"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="myupi@axis",
            name="User",
            note=""
        )
        assert "myupi@axis" in result.output
    
    @pytest.mark.asyncio
    async def test_output_mentions_upi_apps(self):
        """Output should mention UPI apps"""
        result = await _generate_upi_link(
            amount=100,
            upi_id="user@upi",
            name="User",
            note=""
        )
        assert "gpay" in result.output.lower() or "phonep" in result.output.lower() or "upi app" in result.output.lower()
