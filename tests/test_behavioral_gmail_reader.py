"""
Behavioral Tests: Gmail Reader
===============================
Tests that the Gmail reader module ACTUALLY works:
- GOOGLE_AVAILABLE flag
- Email dataclass
- VerificationCode dataclass
- GmailReader class
- OTP_PATTERNS and VERIFICATION_LINK_PATTERNS

README Requirements:
- Email verification handling
- OTP extraction
- OAuth integration
"""

import pytest
import re
from datetime import datetime

from backend.agent.gmail_reader import (
    GOOGLE_AVAILABLE,
    Email,
    VerificationCode,
    GmailReader,
)


class TestGoogleAvailable:
    """Test Google library availability flag"""
    
    def test_google_available_is_bool(self):
        """GOOGLE_AVAILABLE should be boolean"""
        assert isinstance(GOOGLE_AVAILABLE, bool)


class TestEmailDataclass:
    """Test Email dataclass"""
    
    def test_can_create(self):
        """Email should be creatable"""
        email = Email(
            id="msg-1",
            thread_id="thread-1",
            subject="Test Subject",
            sender="sender@example.com",
            recipient="me@example.com",
            date=datetime.now(),
            body_text="Hello",
            body_html="<p>Hello</p>",
            snippet="Hello..."
        )
        assert email is not None
    
    def test_has_id(self):
        """Should have id"""
        email = Email(
            id="my-id",
            thread_id="t",
            subject="s",
            sender="s@e.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="",
            body_html="",
            snippet=""
        )
        assert email.id == "my-id"
    
    def test_has_thread_id(self):
        """Should have thread_id"""
        email = Email(
            id="i",
            thread_id="my-thread",
            subject="s",
            sender="s@e.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="",
            body_html="",
            snippet=""
        )
        assert email.thread_id == "my-thread"
    
    def test_has_subject(self):
        """Should have subject"""
        email = Email(
            id="i",
            thread_id="t",
            subject="My Subject",
            sender="s@e.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="",
            body_html="",
            snippet=""
        )
        assert email.subject == "My Subject"
    
    def test_has_sender(self):
        """Should have sender"""
        email = Email(
            id="i",
            thread_id="t",
            subject="s",
            sender="from@example.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="",
            body_html="",
            snippet=""
        )
        assert email.sender == "from@example.com"
    
    def test_has_recipient(self):
        """Should have recipient"""
        email = Email(
            id="i",
            thread_id="t",
            subject="s",
            sender="s@e.com",
            recipient="to@example.com",
            date=datetime.now(),
            body_text="",
            body_html="",
            snippet=""
        )
        assert email.recipient == "to@example.com"
    
    def test_has_date(self):
        """Should have date"""
        now = datetime.now()
        email = Email(
            id="i",
            thread_id="t",
            subject="s",
            sender="s@e.com",
            recipient="r@e.com",
            date=now,
            body_text="",
            body_html="",
            snippet=""
        )
        assert email.date == now
    
    def test_has_body_text(self):
        """Should have body_text"""
        email = Email(
            id="i",
            thread_id="t",
            subject="s",
            sender="s@e.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="My email body",
            body_html="",
            snippet=""
        )
        assert email.body_text == "My email body"
    
    def test_has_body_html(self):
        """Should have body_html"""
        email = Email(
            id="i",
            thread_id="t",
            subject="s",
            sender="s@e.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="",
            body_html="<p>HTML body</p>",
            snippet=""
        )
        assert email.body_html == "<p>HTML body</p>"
    
    def test_has_snippet(self):
        """Should have snippet"""
        email = Email(
            id="i",
            thread_id="t",
            subject="s",
            sender="s@e.com",
            recipient="r@e.com",
            date=datetime.now(),
            body_text="",
            body_html="",
            snippet="Preview text..."
        )
        assert email.snippet == "Preview text..."


class TestVerificationCodeDataclass:
    """Test VerificationCode dataclass"""
    
    def test_can_create_default(self):
        """VerificationCode should be creatable with defaults"""
        code = VerificationCode()
        assert code is not None
    
    def test_default_code_is_none(self):
        """Default code should be None"""
        code = VerificationCode()
        assert code.code is None
    
    def test_default_link_is_none(self):
        """Default link should be None"""
        code = VerificationCode()
        assert code.link is None
    
    def test_default_otp_is_none(self):
        """Default otp should be None"""
        code = VerificationCode()
        assert code.otp is None
    
    def test_default_source_email_id_is_none(self):
        """Default source_email_id should be None"""
        code = VerificationCode()
        assert code.source_email_id is None
    
    def test_default_service_is_none(self):
        """Default service should be None"""
        code = VerificationCode()
        assert code.service is None
    
    def test_can_set_code(self):
        """Should accept code"""
        code = VerificationCode(code="123456")
        assert code.code == "123456"
    
    def test_can_set_link(self):
        """Should accept link"""
        code = VerificationCode(link="https://example.com/verify?token=abc")
        assert code.link == "https://example.com/verify?token=abc"
    
    def test_can_set_otp(self):
        """Should accept otp"""
        code = VerificationCode(otp="7890")
        assert code.otp == "7890"
    
    def test_can_set_source_email_id(self):
        """Should accept source_email_id"""
        code = VerificationCode(source_email_id="msg-123")
        assert code.source_email_id == "msg-123"
    
    def test_can_set_service(self):
        """Should accept service"""
        code = VerificationCode(service="groq")
        assert code.service == "groq"
    
    def test_full_creation(self):
        """Should accept all fields"""
        code = VerificationCode(
            code="123456",
            link="https://verify.com",
            otp="7890",
            source_email_id="msg-1",
            service="openai"
        )
        assert code.code == "123456"
        assert code.link == "https://verify.com"
        assert code.otp == "7890"
        assert code.source_email_id == "msg-1"
        assert code.service == "openai"


class TestGmailReaderInit:
    """Test GmailReader initialization"""
    
    def test_can_instantiate(self):
        """GmailReader should be instantiatable"""
        reader = GmailReader()
        assert reader is not None
    
    def test_has_client_id(self):
        """Should have client_id"""
        reader = GmailReader(client_id="my-client-id")
        assert reader.client_id == "my-client-id"
    
    def test_has_client_secret(self):
        """Should have client_secret"""
        reader = GmailReader(client_secret="my-secret")
        assert reader.client_secret == "my-secret"
    
    def test_has_refresh_token(self):
        """Should have refresh_token"""
        reader = GmailReader(refresh_token="my-token")
        assert reader.refresh_token == "my-token"
    
    def test_has_user_email(self):
        """Should have user_email"""
        reader = GmailReader(user_email="me@gmail.com")
        assert reader.user_email == "me@gmail.com"
    
    def test_service_starts_none(self):
        """Internal service should start as None"""
        reader = GmailReader()
        assert reader._service is None
    
    def test_credentials_starts_none(self):
        """Internal credentials should start as None"""
        reader = GmailReader()
        assert reader._credentials is None


class TestGmailReaderOTPPatterns:
    """Test OTP_PATTERNS"""
    
    def test_otp_patterns_exist(self):
        """OTP_PATTERNS should exist"""
        assert hasattr(GmailReader, "OTP_PATTERNS")
    
    def test_otp_patterns_is_list(self):
        """OTP_PATTERNS should be list"""
        assert isinstance(GmailReader.OTP_PATTERNS, list)
    
    def test_otp_patterns_not_empty(self):
        """OTP_PATTERNS should not be empty"""
        assert len(GmailReader.OTP_PATTERNS) > 0
    
    def test_otp_patterns_are_valid_regex(self):
        """Each pattern should be valid regex"""
        for pattern in GmailReader.OTP_PATTERNS:
            # Should compile without error
            compiled = re.compile(pattern)
            assert compiled is not None
    
    def test_matches_4_digit_code(self):
        """Should match 4-digit OTP"""
        text = "Your code is 1234"
        for pattern in GmailReader.OTP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                break
        else:
            pytest.fail("No pattern matched 4-digit code")
    
    def test_matches_6_digit_code(self):
        """Should match 6-digit OTP"""
        text = "Your verification code: 123456"
        for pattern in GmailReader.OTP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                break
        else:
            pytest.fail("No pattern matched 6-digit code")


class TestGmailReaderVerificationLinkPatterns:
    """Test VERIFICATION_LINK_PATTERNS"""
    
    def test_verification_link_patterns_exist(self):
        """VERIFICATION_LINK_PATTERNS should exist"""
        assert hasattr(GmailReader, "VERIFICATION_LINK_PATTERNS")
    
    def test_verification_link_patterns_is_list(self):
        """VERIFICATION_LINK_PATTERNS should be list"""
        assert isinstance(GmailReader.VERIFICATION_LINK_PATTERNS, list)
    
    def test_verification_link_patterns_not_empty(self):
        """VERIFICATION_LINK_PATTERNS should not be empty"""
        assert len(GmailReader.VERIFICATION_LINK_PATTERNS) > 0
    
    def test_verification_link_patterns_are_valid_regex(self):
        """Each pattern should be valid regex"""
        for pattern in GmailReader.VERIFICATION_LINK_PATTERNS:
            compiled = re.compile(pattern)
            assert compiled is not None
    
    def test_matches_verify_link(self):
        """Should match verify link"""
        text = "Click here: https://example.com/verify/abc123"
        for pattern in GmailReader.VERIFICATION_LINK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                break
        else:
            pytest.fail("No pattern matched verify link")
    
    def test_matches_confirm_link(self):
        """Should match confirm link"""
        text = "Confirm: https://site.com/confirm?token=xyz"
        for pattern in GmailReader.VERIFICATION_LINK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                break
        else:
            pytest.fail("No pattern matched confirm link")
    
    def test_matches_token_link(self):
        """Should match token link"""
        text = "https://api.example.com/auth?token=abc123def"
        for pattern in GmailReader.VERIFICATION_LINK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                break
        else:
            pytest.fail("No pattern matched token link")


class TestGmailReaderMethods:
    """Test GmailReader methods"""
    
    def test_has_get_credentials_method(self):
        """Should have _get_credentials method"""
        reader = GmailReader()
        assert hasattr(reader, "_get_credentials")
    
    def test_has_get_service_method(self):
        """Should have _get_service method"""
        reader = GmailReader()
        assert hasattr(reader, "_get_service")
    
    def test_has_fetch_recent_emails_method(self):
        """Should have fetch_recent_emails method"""
        reader = GmailReader()
        assert hasattr(reader, "fetch_recent_emails")
        assert callable(reader.fetch_recent_emails)
    
    def test_fetch_recent_emails_is_async(self):
        """fetch_recent_emails should be async"""
        import inspect
        reader = GmailReader()
        assert inspect.iscoroutinefunction(reader.fetch_recent_emails)


class TestEmailTypes:
    """Test type correctness"""
    
    def test_email_is_dataclass(self):
        """Email should be a dataclass"""
        from dataclasses import is_dataclass
        assert is_dataclass(Email)
    
    def test_verification_code_is_dataclass(self):
        """VerificationCode should be a dataclass"""
        from dataclasses import is_dataclass
        assert is_dataclass(VerificationCode)
    
    def test_email_fields_count(self):
        """Email should have 9 fields"""
        from dataclasses import fields
        email_fields = fields(Email)
        assert len(email_fields) == 9
    
    def test_verification_code_fields_count(self):
        """VerificationCode should have 5 fields"""
        from dataclasses import fields
        vc_fields = fields(VerificationCode)
        assert len(vc_fields) == 5


class TestPatternBehavior:
    """Test pattern matching behavior"""
    
    def test_otp_extracts_correct_code(self):
        """OTP pattern should extract correct code"""
        text = "Your verification code is 987654"
        for pattern in GmailReader.OTP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                assert match.group(1) == "987654"
                return
        pytest.fail("No pattern matched and extracted code")
    
    def test_link_pattern_extracts_full_url(self):
        """Link pattern should extract full URL"""
        text = "Click: https://example.com/verify/token123"
        for pattern in GmailReader.VERIFICATION_LINK_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                url = match.group(1)
                assert url.startswith("https://")
                assert "verify" in url
                return
        pytest.fail("No pattern extracted URL")
