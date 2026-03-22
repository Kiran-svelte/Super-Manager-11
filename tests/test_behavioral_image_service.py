"""
Behavioral Tests: Image Service
=================================
Tests that the image service ACTUALLY works:
- ImageGenerationService class
- Provider detection
- Fallback behavior

README Requirements:
- Multiple image generation providers
- Together AI, Replicate, Stability AI, OpenAI
"""

import pytest
import os
from unittest.mock import patch

from backend.core.image_service import ImageGenerationService


class TestImageGenerationServiceInit:
    """Test ImageGenerationService initialization"""
    
    def test_can_instantiate(self):
        """ImageGenerationService should be instantiatable"""
        service = ImageGenerationService()
        assert service is not None
    
    def test_has_together_key_attr(self):
        """Should have together_key attribute"""
        service = ImageGenerationService()
        assert hasattr(service, "together_key")
    
    def test_has_replicate_key_attr(self):
        """Should have replicate_key attribute"""
        service = ImageGenerationService()
        assert hasattr(service, "replicate_key")
    
    def test_has_stability_key_attr(self):
        """Should have stability_key attribute"""
        service = ImageGenerationService()
        assert hasattr(service, "stability_key")
    
    def test_has_openai_key_attr(self):
        """Should have openai_key attribute"""
        service = ImageGenerationService()
        assert hasattr(service, "openai_key")
    
    def test_has_available_providers(self):
        """Should have available_providers list"""
        service = ImageGenerationService()
        assert hasattr(service, "available_providers")
        assert isinstance(service.available_providers, list)


class TestProviderDetection:
    """Test provider detection"""
    
    def test_has_providers_method(self):
        """Should have has_providers method"""
        service = ImageGenerationService()
        assert hasattr(service, "has_providers")
        assert callable(service.has_providers)
    
    def test_has_providers_returns_bool(self):
        """has_providers should return boolean"""
        service = ImageGenerationService()
        result = service.has_providers()
        assert isinstance(result, bool)
    
    @patch.dict(os.environ, {"TOGETHER_API_KEY": "test-key"}, clear=True)
    def test_detects_together_provider(self):
        """Should detect Together provider when key set"""
        service = ImageGenerationService()
        assert "together" in service.available_providers
    
    @patch.dict(os.environ, {"REPLICATE_API_KEY": "test-key"}, clear=True)
    def test_detects_replicate_provider(self):
        """Should detect Replicate provider when key set"""
        service = ImageGenerationService()
        assert "replicate" in service.available_providers
    
    @patch.dict(os.environ, {"STABILITY_API_KEY": "test-key"}, clear=True)
    def test_detects_stability_provider(self):
        """Should detect Stability provider when key set"""
        service = ImageGenerationService()
        assert "stability" in service.available_providers
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"}, clear=True)
    def test_detects_openai_provider(self):
        """Should detect OpenAI provider when key set"""
        service = ImageGenerationService()
        assert "openai" in service.available_providers


class TestGenerateImagesMethod:
    """Test generate_images method"""
    
    def test_has_generate_images_method(self):
        """Should have generate_images method"""
        service = ImageGenerationService()
        assert hasattr(service, "generate_images")
        assert callable(service.generate_images)
    
    def test_generate_images_is_async(self):
        """generate_images should be async"""
        import inspect
        service = ImageGenerationService()
        assert inspect.iscoroutinefunction(service.generate_images)
    
    @pytest.mark.asyncio
    async def test_no_providers_returns_error(self):
        """Should return error when no providers available"""
        with patch.dict(os.environ, {}, clear=True):
            # Clear all API keys
            service = ImageGenerationService()
            service.available_providers = []
            
            result = await service.generate_images("test prompt")
            
            assert result["success"] is False
            assert "error" in result


class TestPromptEnhancement:
    """Test prompt enhancement functionality"""
    
    def test_has_enhance_prompt_method(self):
        """Should have _enhance_prompt method"""
        service = ImageGenerationService()
        assert hasattr(service, "_enhance_prompt")
        assert callable(service._enhance_prompt)


class TestFallbackTools:
    """Test fallback tools functionality"""
    
    def test_has_fallback_tools_method(self):
        """Should have _get_fallback_tools method"""
        service = ImageGenerationService()
        assert hasattr(service, "_get_fallback_tools")
        assert callable(service._get_fallback_tools)
    
    def test_fallback_tools_returns_list(self):
        """_get_fallback_tools should return list"""
        service = ImageGenerationService()
        result = service._get_fallback_tools()
        assert isinstance(result, list)


class TestProviderMethods:
    """Test individual provider methods exist"""
    
    def test_has_together_method(self):
        """Should have _generate_with_together method"""
        service = ImageGenerationService()
        assert hasattr(service, "_generate_with_together")
        assert callable(service._generate_with_together)
    
    def test_has_replicate_method(self):
        """Should have _generate_with_replicate method"""
        service = ImageGenerationService()
        assert hasattr(service, "_generate_with_replicate")
        assert callable(service._generate_with_replicate)
    
    def test_has_stability_method(self):
        """Should have _generate_with_stability method"""
        service = ImageGenerationService()
        assert hasattr(service, "_generate_with_stability")
        assert callable(service._generate_with_stability)
    
    def test_has_openai_method(self):
        """Should have _generate_with_openai method"""
        service = ImageGenerationService()
        assert hasattr(service, "_generate_with_openai")
        assert callable(service._generate_with_openai)
    
    def test_provider_methods_are_async(self):
        """Provider methods should be async"""
        import inspect
        service = ImageGenerationService()
        
        assert inspect.iscoroutinefunction(service._generate_with_together)
        assert inspect.iscoroutinefunction(service._generate_with_replicate)
        assert inspect.iscoroutinefunction(service._generate_with_stability)
        assert inspect.iscoroutinefunction(service._generate_with_openai)


class TestGenerateImagesParameters:
    """Test generate_images accepts correct parameters"""
    
    @pytest.mark.asyncio
    async def test_accepts_prompt(self):
        """Should accept prompt parameter"""
        service = ImageGenerationService()
        service.available_providers = []
        
        # Should not raise
        result = await service.generate_images("A beautiful sunset")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_accepts_num_images(self):
        """Should accept num_images parameter"""
        service = ImageGenerationService()
        service.available_providers = []
        
        result = await service.generate_images("test", num_images=3)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_accepts_style(self):
        """Should accept style parameter"""
        service = ImageGenerationService()
        service.available_providers = []
        
        result = await service.generate_images("test", style="logo")
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_accepts_dimensions(self):
        """Should accept width and height parameters"""
        service = ImageGenerationService()
        service.available_providers = []
        
        result = await service.generate_images("test", width=512, height=512)
        assert result is not None


class TestServiceResponseFormat:
    """Test response format"""
    
    @pytest.mark.asyncio
    async def test_error_response_format(self):
        """Error response should have expected fields"""
        with patch.dict(os.environ, {}, clear=True):
            service = ImageGenerationService()
            service.available_providers = []
            
            result = await service.generate_images("test")
            
            assert "success" in result
            assert result["success"] is False
            assert "error" in result


class TestEdgeCases:
    """Test edge cases"""
    
    def test_empty_prompt_enhancement(self):
        """Should handle empty prompt"""
        service = ImageGenerationService()
        result = service._enhance_prompt("", "logo")
        # Should not crash
        assert result is not None
    
    def test_special_characters_in_prompt(self):
        """Should handle special characters in prompt"""
        service = ImageGenerationService()
        result = service._enhance_prompt("A logo with <script>alert('xss')</script>", "logo")
        # Should not crash
        assert result is not None
    
    def test_unicode_prompt(self):
        """Should handle unicode in prompt"""
        service = ImageGenerationService()
        result = service._enhance_prompt("一个漂亮的日落 🌅", "art")
        # Should not crash
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_zero_images(self):
        """Should handle num_images=0"""
        service = ImageGenerationService()
        service.available_providers = []
        
        # Should not crash
        result = await service.generate_images("test", num_images=0)
        assert result is not None
    
    @pytest.mark.asyncio
    async def test_very_large_dimensions(self):
        """Should handle very large dimensions"""
        service = ImageGenerationService()
        service.available_providers = []
        
        # Should not crash
        result = await service.generate_images("test", width=4096, height=4096)
        assert result is not None
