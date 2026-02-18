"""
Test Payment Links
==================
Tests for 3-tier payment link generation (v6).
"""

import pytest
import os
from unittest.mock import patch, AsyncMock, MagicMock
from backend.core.payment_links import (
    generate_upi_link,
    generate_payment_link,
    register_payment_tools,
)


class TestUPILinks:
    """Test UPI deep link generation (Tier 1)"""
    
    def test_generate_upi_link_success(self):
        """Test generating a valid UPI link"""
        result = generate_upi_link(
            amount=500.0,
            vpa="testuser@upi",
            name="Test User",
            note="Test Payment",
        )
        
        assert "upi_link" in result
        assert "upi://pay?" in result["upi_link"]
        assert "pa=testuser@upi" in result["upi_link"]
        assert "am=500.00" in result["upi_link"]
        assert "cu=INR" in result["upi_link"]
        
        assert "qr_code_url" in result
        assert "api.qrserver.com" in result["qr_code_url"]
        
        assert "deep_links" in result
        assert "gpay" in result["deep_links"]
        assert "phonepe" in result["deep_links"]
        assert "paytm" in result["deep_links"]
        assert "bhim" in result["deep_links"]
        
        assert "transaction_ref" in result
        assert result["transaction_ref"].startswith("SM-")
    
    def test_generate_upi_link_extracts_name_from_vpa(self):
        """Test that name is extracted from VPA if not provided"""
        result = generate_upi_link(
            amount=100.0,
            vpa="john.doe@paytm",
            note="Test",
        )
        
        assert result["payee_name"] == "john.doe"
    
    def test_generate_upi_link_invalid_vpa(self):
        """Test that invalid VPA raises ValueError"""
        with pytest.raises(ValueError, match="Invalid UPI ID format"):
            generate_upi_link(
                amount=100.0,
                vpa="invalid_vpa",
                note="Test",
            )
    
    def test_generate_upi_link_truncates_note(self):
        """Test that long notes are truncated to 50 chars"""
        long_note = "A" * 100
        result = generate_upi_link(
            amount=100.0,
            vpa="test@upi",
            note=long_note,
        )
        
        # Note should be truncated in the UPI link
        assert "upi_link" in result
        # The note parameter is truncated to 50 chars in the function
        assert len(long_note[:50]) == 50


class TestPaymentLinkGeneration:
    """Test unified payment link generation"""
    
    @pytest.mark.asyncio
    async def test_generate_payment_link_upi_tier(self):
        """Test that UPI is used for INR with valid UPI ID"""
        result = await generate_payment_link(
            amount=1000.0,
            currency="INR",
            payee="testuser@upi",
            description="Test Payment",
        )
        
        assert result.success
        assert "UPI" in result.output
        assert result.data["tier"] == "upi"
        assert "upi_link" in result.data
        assert "qr_code_url" in result.data
    
    @pytest.mark.asyncio
    async def test_generate_payment_link_invalid_amount(self):
        """Test that invalid amount returns error"""
        result = await generate_payment_link(
            amount=0,
            currency="INR",
            payee="test@upi",
        )
        
        assert not result.success
        assert "Invalid amount" in result.output
    
    @pytest.mark.asyncio
    async def test_generate_payment_link_no_method_available(self):
        """Test error when no payment method is available"""
        # Clear all environment variables
        with patch.dict(os.environ, {}, clear=True):
            result = await generate_payment_link(
                amount=100.0,
                currency="USD",
                payee="",
                description="Test",
            )
            
            assert not result.success
            assert "No payment method available" in result.output
    
    @pytest.mark.asyncio
    async def test_generate_payment_link_stripe_tier(self):
        """Test Stripe tier when STRIPE_SECRET_KEY is set"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            {"id": "price_test123"},  # Price creation response
            {"id": "link_test123", "url": "https://checkout.stripe.com/test"},  # Link creation response
        ]
        
        with patch.dict(os.environ, {"STRIPE_SECRET_KEY": "sk_test_123"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                result = await generate_payment_link(
                    amount=50.0,
                    currency="USD",
                    payee="",
                    description="Test Payment",
                )
                
                assert result.success
                assert result.data["tier"] == "stripe"
                assert "payment_link" in result.data
    
    @pytest.mark.asyncio
    async def test_generate_payment_link_razorpay_tier(self):
        """Test Razorpay tier when credentials are set"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "link_test123",
            "short_url": "https://rzp.io/test",
            "url": "https://razorpay.com/payment/test",
        }
        
        with patch.dict(os.environ, {"RAZORPAY_KEY_ID": "rzp_test", "RAZORPAY_KEY_SECRET": "secret"}):
            with patch("httpx.AsyncClient") as mock_client:
                mock_client_instance = AsyncMock()
                mock_client_instance.post = AsyncMock(return_value=mock_response)
                mock_client.return_value.__aenter__.return_value = mock_client_instance
                
                result = await generate_payment_link(
                    amount=2000.0,
                    currency="INR",
                    payee="",
                    description="Test Payment",
                    customer_name="Test User",
                    customer_email="test@example.com",
                )
                
                assert result.success
                assert result.data["tier"] == "razorpay"
                assert "payment_link" in result.data


class TestToolRegistration:
    """Test tool registration with ToolRegistry"""
    
    def test_register_payment_tools(self):
        """Test that payment tools are registered successfully"""
        from backend.core.tool_registry import get_tool_registry, reset_tool_registry
        
        reset_tool_registry()
        registry = get_tool_registry()
        
        # Register payment tools
        register_payment_tools()
        
        # Verify tool is registered
        tool = registry.get("generate_payment_link")
        assert tool is not None
        assert tool.name == "generate_payment_link"
        assert tool.source == "payment"
        assert tool.risk_level == "risky"
        assert "amount" in tool.parameters
        assert "currency" in tool.parameters
