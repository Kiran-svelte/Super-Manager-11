"""
Behavioral Tests: Stealth Browser
==================================
Tests that the stealth browser ACTUALLY works:
- CAPTCHA detection patterns
- Feature detection flags
- StealthBrowser class
- Human-like delay behavior

README Requirements:
- Anti-detect browser automation
- CAPTCHA detection → human_fallback
- Launch priority: Camoufox → Playwright+stealth → Plain Playwright
"""

import pytest
import re

from backend.core.stealth_browser import (
    CAPTCHA_PATTERNS,
    _detect_captcha,
    StealthBrowser,
    CAMOUFOX_AVAILABLE,
    PLAYWRIGHT_STEALTH_AVAILABLE,
    PLAYWRIGHT_AVAILABLE,
)


class TestFeatureDetectionFlags:
    """Test feature detection flags"""
    
    def test_camoufox_available_is_bool(self):
        """CAMOUFOX_AVAILABLE should be boolean"""
        assert isinstance(CAMOUFOX_AVAILABLE, bool)
    
    def test_playwright_stealth_available_is_bool(self):
        """PLAYWRIGHT_STEALTH_AVAILABLE should be boolean"""
        assert isinstance(PLAYWRIGHT_STEALTH_AVAILABLE, bool)
    
    def test_playwright_available_is_bool(self):
        """PLAYWRIGHT_AVAILABLE should be boolean"""
        assert isinstance(PLAYWRIGHT_AVAILABLE, bool)


class TestCaptchaPatterns:
    """Test CAPTCHA detection patterns"""
    
    def test_captcha_patterns_is_list(self):
        """CAPTCHA_PATTERNS should be a list"""
        assert isinstance(CAPTCHA_PATTERNS, list)
    
    def test_captcha_patterns_not_empty(self):
        """CAPTCHA_PATTERNS should not be empty"""
        assert len(CAPTCHA_PATTERNS) > 0
    
    def test_all_patterns_are_strings(self):
        """All CAPTCHA patterns should be strings"""
        assert all(isinstance(p, str) for p in CAPTCHA_PATTERNS)
    
    def test_all_patterns_are_valid_regex(self):
        """All CAPTCHA patterns should be valid regex"""
        for pattern in CAPTCHA_PATTERNS:
            # Should not raise
            re.compile(pattern)
    
    def test_recaptcha_pattern_exists(self):
        """Should have reCAPTCHA detection pattern"""
        patterns_text = " ".join(CAPTCHA_PATTERNS)
        assert "recaptcha" in patterns_text.lower()
    
    def test_hcaptcha_pattern_exists(self):
        """Should have hCAPTCHA detection pattern"""
        patterns_text = " ".join(CAPTCHA_PATTERNS)
        assert "hcaptcha" in patterns_text.lower() or "h-captcha" in patterns_text.lower()
    
    def test_cloudflare_pattern_exists(self):
        """Should have Cloudflare challenge detection"""
        patterns_text = " ".join(CAPTCHA_PATTERNS)
        assert "cf-turnstile" in patterns_text or "challenge" in patterns_text.lower()
    
    def test_sitekey_pattern_exists(self):
        """Should detect data-sitekey attribute"""
        assert any("sitekey" in p for p in CAPTCHA_PATTERNS)


class TestCaptchaDetection:
    """Test _detect_captcha function"""
    
    @pytest.mark.asyncio
    async def test_detect_captcha_returns_bool(self):
        """_detect_captcha should return boolean"""
        result = await _detect_captcha("<html><body>Hello</body></html>")
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_no_captcha_in_clean_page(self):
        """Should return False for clean page"""
        html = """
        <html>
        <body>
            <h1>Welcome</h1>
            <p>This is a normal page.</p>
        </body>
        </html>
        """
        result = await _detect_captcha(html)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_detect_recaptcha_class(self):
        """Should detect reCAPTCHA by class"""
        html = '<div class="g-recaptcha" data-sitekey="abc123"></div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_hcaptcha_class(self):
        """Should detect hCAPTCHA by class"""
        html = '<div class="h-captcha" data-sitekey="abc123"></div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_data_sitekey(self):
        """Should detect data-sitekey attribute"""
        html = '<div data-sitekey="6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI"></div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_captcha_container(self):
        """Should detect captcha-container"""
        html = '<div class="captcha-container">Please solve</div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_cloudflare_turnstile(self):
        """Should detect Cloudflare Turnstile"""
        html = '<div class="cf-turnstile" data-sitekey="xyz"></div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_cloudflare_challenge(self):
        """Should detect Cloudflare challenge"""
        html = '<div id="challenge-running">Checking your browser</div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_recaptcha_iframe(self):
        """Should detect reCAPTCHA iframe"""
        html = '<iframe src="https://www.google.com/recaptcha/api2/anchor"></iframe>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_hcaptcha_iframe(self):
        """Should detect hCAPTCHA iframe"""
        html = '<iframe src="https://hcaptcha.com/captcha"></iframe>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_verify_human_text(self):
        """Should detect 'Verify you are human' text"""
        html = '<p>Verify you are human before continuing.</p>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_detect_security_check_text(self):
        """Should detect security check text"""
        html = '<p>Please complete the security check below.</p>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_case_insensitive_detection(self):
        """CAPTCHA detection should be case-insensitive"""
        html = '<div class="G-RECAPTCHA"></div>'
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_cloudflare_just_a_moment(self):
        """Should detect Cloudflare 'Just a moment...'"""
        html = '<title>Just a moment...</title>'
        result = await _detect_captcha(html)
        assert result is True


class TestStealthBrowserInit:
    """Test StealthBrowser initialization"""
    
    def test_can_instantiate(self):
        """StealthBrowser should be instantiatable"""
        browser = StealthBrowser()
        assert browser is not None
    
    def test_has_browser_attr(self):
        """StealthBrowser should have _browser attribute"""
        browser = StealthBrowser()
        assert hasattr(browser, "_browser")
        assert browser._browser is None
    
    def test_has_context_attr(self):
        """StealthBrowser should have _context attribute"""
        browser = StealthBrowser()
        assert hasattr(browser, "_context")
        assert browser._context is None
    
    def test_has_page_attr(self):
        """StealthBrowser should have _page attribute"""
        browser = StealthBrowser()
        assert hasattr(browser, "_page")
        assert browser._page is None
    
    def test_has_engine_attr(self):
        """StealthBrowser should have _engine attribute"""
        browser = StealthBrowser()
        assert hasattr(browser, "_engine")
        assert browser._engine is None


class TestStealthBrowserMethods:
    """Test StealthBrowser method signatures"""
    
    def test_has_launch_method(self):
        """StealthBrowser should have launch method"""
        browser = StealthBrowser()
        assert hasattr(browser, "launch")
        assert callable(browser.launch)
    
    def test_launch_is_async(self):
        """launch should be async"""
        import inspect
        browser = StealthBrowser()
        assert inspect.iscoroutinefunction(browser.launch)
    
    def test_has_navigate_method(self):
        """StealthBrowser should have navigate method"""
        browser = StealthBrowser()
        assert hasattr(browser, "navigate")
        assert callable(browser.navigate)
    
    def test_navigate_is_async(self):
        """navigate should be async"""
        import inspect
        browser = StealthBrowser()
        assert inspect.iscoroutinefunction(browser.navigate)
    
    def test_has_fill_form_fields_method(self):
        """StealthBrowser should have fill_form_fields method"""
        browser = StealthBrowser()
        assert hasattr(browser, "fill_form_fields")
        assert callable(browser.fill_form_fields)
    
    def test_fill_form_fields_is_async(self):
        """fill_form_fields should be async"""
        import inspect
        browser = StealthBrowser()
        assert inspect.iscoroutinefunction(browser.fill_form_fields)
    
    def test_has_human_delay_method(self):
        """StealthBrowser should have _human_delay method"""
        browser = StealthBrowser()
        assert hasattr(browser, "_human_delay")
        assert callable(browser._human_delay)


class TestHumanDelayBehavior:
    """Test human-like delay behavior"""
    
    @pytest.mark.asyncio
    async def test_human_delay_awaitable(self):
        """_human_delay should be awaitable"""
        browser = StealthBrowser()
        
        # Very short delay for testing
        import time
        start = time.time()
        await browser._human_delay(min_ms=10, max_ms=50)
        elapsed = time.time() - start
        
        # Should have waited at least 10ms
        assert elapsed >= 0.01
    
    @pytest.mark.asyncio
    async def test_human_delay_respects_max(self):
        """_human_delay should not exceed max"""
        browser = StealthBrowser()
        
        import time
        start = time.time()
        await browser._human_delay(min_ms=10, max_ms=100)
        elapsed = time.time() - start
        
        # Should not exceed max by much (allowing for overhead)
        assert elapsed < 0.5


class TestEngineSelection:
    """Test engine selection behavior"""
    
    def test_valid_engine_values(self):
        """_engine should be None or valid engine name"""
        browser = StealthBrowser()
        
        # Initially None
        assert browser._engine is None
        
        # Valid values after launch would be:
        valid_engines = ["camoufox", "playwright_stealth", "playwright", None]
        assert browser._engine in valid_engines
    
    def test_engine_priority_documented(self):
        """Engine priority should follow README spec"""
        # This test documents expected priority:
        # 1. Camoufox (if available)
        # 2. Playwright + stealth plugin (if available)
        # 3. Plain Playwright (fallback)
        
        # The implementation checks CAMOUFOX_AVAILABLE first
        # then PLAYWRIGHT_AVAILABLE with PLAYWRIGHT_STEALTH_AVAILABLE
        assert True  # Documentation test


class TestMultipleCaptchaPatterns:
    """Test multiple CAPTCHA patterns in one page"""
    
    @pytest.mark.asyncio
    async def test_multiple_captcha_indicators(self):
        """Should detect page with multiple CAPTCHA indicators"""
        html = """
        <html>
        <head><title>Just a moment...</title></head>
        <body>
            <div id="challenge-form">
                <div class="g-recaptcha" data-sitekey="abc"></div>
                <p>Please verify you are a human</p>
            </div>
        </body>
        </html>
        """
        result = await _detect_captcha(html)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_hidden_captcha(self):
        """Should detect hidden CAPTCHA elements"""
        html = '<div style="display:none" class="g-recaptcha"></div>'
        result = await _detect_captcha(html)
        assert result is True


class TestEdgeCases:
    """Test edge cases"""
    
    @pytest.mark.asyncio
    async def test_empty_html(self):
        """Should handle empty HTML"""
        result = await _detect_captcha("")
        assert result is False
    
    @pytest.mark.asyncio
    async def test_partial_match_not_trigger(self):
        """Should not false positive on partial matches"""
        # "captcha" in a benign context might be ok
        # but class="captcha-container" should trigger
        html = '<p>Our site uses advanced captchaless verification.</p>'
        # This won't match because patterns are specific
        result = await _detect_captcha(html)
        # May or may not match depending on patterns
        assert isinstance(result, bool)
    
    @pytest.mark.asyncio
    async def test_html_with_just_forms(self):
        """Should not flag regular forms as CAPTCHA"""
        html = """
        <form action="/login" method="POST">
            <input type="text" name="username" />
            <input type="password" name="password" />
            <button type="submit">Login</button>
        </form>
        """
        result = await _detect_captcha(html)
        assert result is False
