"""
Behavioral Tests: Config Validation
=====================================
Tests that config ACTUALLY:
- Validates environment variables
- Enforces minimum lengths (secret_key >= 16, encryption_secret >= 32)
- Validates app_env (development, staging, production, testing)
- Validates log_level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Has sensible defaults
- Port validation (1-65535)

README Requirements:
- Python 3.11+
- FastAPI v0.104+
- Pydantic validation
- ENCRYPTION_SECRET minimum 32 characters
"""

import pytest
import os
from pydantic import ValidationError

from backend.config import Settings


class TestSettingsDefaults:
    """Test default settings values"""
    
    def test_app_name_default(self):
        """Default app name should be 'Super Manager'"""
        settings = Settings()
        assert settings.app_name == "Super Manager"
    
    def test_app_env_default(self):
        """Default app_env should be 'development'"""
        settings = Settings()
        assert settings.app_env == "development"
    
    def test_debug_default_false(self):
        """Debug should be False by default"""
        settings = Settings()
        assert settings.debug is False
    
    def test_log_level_default_info(self):
        """Log level should default to INFO"""
        settings = Settings()
        assert settings.log_level == "INFO"
    
    def test_port_default(self):
        """Default port should be 8000"""
        settings = Settings()
        assert settings.port == 8000
    
    def test_host_default(self):
        """Default host should be 0.0.0.0"""
        settings = Settings()
        assert settings.host == "0.0.0.0"
    
    def test_ai_model_default(self):
        """Default AI model should be llama-3.3-70b-versatile (Groq)"""
        settings = Settings()
        assert settings.ai_model == "llama-3.3-70b-versatile"
    
    def test_ai_temperature_default(self):
        """Default AI temperature should be 0.7"""
        settings = Settings()
        assert settings.ai_temperature == 0.7
    
    def test_rate_limit_default(self):
        """Default rate limit should be 100/minute"""
        settings = Settings()
        assert settings.rate_limit_per_minute == 100
    
    def test_jwt_expiry_default(self):
        """Default JWT expiry should be 24 hours"""
        settings = Settings()
        assert settings.jwt_expiry_hours == 24


class TestSettingsValidation:
    """Test settings validation"""
    
    def test_app_env_valid_values(self):
        """app_env should accept development, staging, production, testing"""
        for env in ["development", "staging", "production", "testing"]:
            settings = Settings(app_env=env)
            assert settings.app_env == env
    
    def test_app_env_case_insensitive(self):
        """app_env validation should be case insensitive"""
        settings = Settings(app_env="PRODUCTION")
        assert settings.app_env == "production"
    
    def test_app_env_invalid_value_raises(self):
        """Invalid app_env should raise ValidationError"""
        with pytest.raises(ValidationError):
            Settings(app_env="invalid_env")
    
    def test_log_level_valid_values(self):
        """log_level should accept standard logging levels"""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = Settings(log_level=level)
            assert settings.log_level == level
    
    def test_log_level_case_insensitive(self):
        """log_level validation should normalize to uppercase"""
        settings = Settings(log_level="debug")
        assert settings.log_level == "DEBUG"
    
    def test_log_level_invalid_value_raises(self):
        """Invalid log_level should raise ValidationError"""
        with pytest.raises(ValidationError):
            Settings(log_level="VERBOSE")
    
    def test_port_must_be_positive(self):
        """Port must be >= 1"""
        with pytest.raises(ValidationError):
            Settings(port=0)
    
    def test_port_must_be_below_65536(self):
        """Port must be <= 65535"""
        with pytest.raises(ValidationError):
            Settings(port=65536)
    
    def test_port_valid_values(self):
        """Valid port values should work"""
        settings = Settings(port=8080)
        assert settings.port == 8080
    
    def test_workers_must_be_positive(self):
        """Workers must be >= 1"""
        with pytest.raises(ValidationError):
            Settings(workers=0)
    
    def test_ai_temperature_range(self):
        """AI temperature must be 0.0-2.0"""
        with pytest.raises(ValidationError):
            Settings(ai_temperature=-0.1)
        with pytest.raises(ValidationError):
            Settings(ai_temperature=2.1)
    
    def test_ai_max_tokens_positive(self):
        """ai_max_tokens must be >= 1"""
        with pytest.raises(ValidationError):
            Settings(ai_max_tokens=0)


class TestSecuritySettings:
    """Test security-related settings"""
    
    def test_secret_key_min_length(self):
        """secret_key must be at least 16 characters"""
        with pytest.raises(ValidationError):
            Settings(secret_key="short")  # Less than 16 chars
    
    def test_secret_key_valid_length(self):
        """secret_key with 16+ chars should work"""
        settings = Settings(secret_key="a" * 16)
        assert len(settings.secret_key) >= 16
    
    def test_encryption_secret_min_length(self):
        """encryption_secret must be at least 32 characters (README requirement)"""
        with pytest.raises(ValidationError):
            Settings(encryption_secret="only20characters...")  # Less than 32 chars
    
    def test_encryption_secret_valid_length(self):
        """encryption_secret with 32+ chars should work"""
        settings = Settings(encryption_secret="a" * 32)
        assert len(settings.encryption_secret) >= 32
    
    def test_jwt_algorithm_default(self):
        """JWT algorithm should default to HS256"""
        settings = Settings()
        assert settings.jwt_algorithm == "HS256"


class TestCorsSettings:
    """Test CORS settings"""
    
    def test_cors_origins_default(self):
        """CORS origins should have localhost defaults"""
        settings = Settings()
        assert "localhost" in settings.cors_origins
    
    def test_cors_origins_list_property(self):
        """cors_origins_list should parse comma-separated string"""
        settings = Settings(cors_origins="http://a.com,http://b.com,http://c.com")
        origins = settings.cors_origins_list
        assert len(origins) == 3
        assert "http://a.com" in origins
        assert "http://b.com" in origins
        assert "http://c.com" in origins
    
    def test_cors_origins_list_handles_whitespace(self):
        """cors_origins_list should trim whitespace"""
        settings = Settings(cors_origins="  http://a.com  ,  http://b.com  ")
        origins = settings.cors_origins_list
        assert "http://a.com" in origins
        assert "http://b.com" in origins


class TestEnvironmentProperties:
    """Test environment detection properties"""
    
    def test_is_production(self):
        """is_production should be True only in production"""
        settings = Settings(app_env="production")
        assert settings.is_production is True
        
        settings = Settings(app_env="development")
        assert settings.is_production is False
    
    def test_is_development(self):
        """is_development should be True only in development"""
        settings = Settings(app_env="development")
        assert settings.is_development is True
        
        settings = Settings(app_env="production")
        assert settings.is_development is False


class TestOptionalSettings:
    """Test optional settings behavior"""
    
    def test_api_keys_optional(self):
        """API keys should be optional (None or string)"""
        settings = Settings()
        # API keys can be None or a string (loaded from env or .env file)
        assert settings.groq_api_key is None or isinstance(settings.groq_api_key, str)
        # OpenAI and other fallbacks are optional
        assert settings.sambanova_api_key is None or isinstance(settings.sambanova_api_key, str)
    
    def test_database_settings_optional(self):
        """Database settings should be optional"""
        settings = Settings()
        # These can be None or from env
        assert settings.database_url is None or isinstance(settings.database_url, str)
    
    def test_email_settings_optional(self):
        """Email settings should be optional"""
        settings = Settings()
        assert settings.smtp_host is None or isinstance(settings.smtp_host, str)
        assert settings.smtp_email is None or isinstance(settings.smtp_email, str)


class TestBackupSettings:
    """Test backup configuration"""
    
    def test_backup_enabled_default(self):
        """Backup should be enabled by default"""
        settings = Settings()
        assert settings.backup_enabled is True
    
    def test_backup_retention_default(self):
        """Backup retention should default to 30 days"""
        settings = Settings()
        assert settings.backup_retention_days == 30
    
    def test_backup_dir_default(self):
        """Backup directory should have a default"""
        settings = Settings()
        assert settings.backup_dir == "./backups"


class TestCacheSettings:
    """Test cache configuration"""
    
    def test_cache_enabled_default(self):
        """Cache should be enabled by default"""
        settings = Settings()
        assert settings.cache_enabled is True
    
    def test_cache_ttl_default(self):
        """Cache TTL should default to 300 seconds (5 minutes)"""
        settings = Settings()
        assert settings.cache_ttl == 300


class TestSmtpSettings:
    """Test SMTP configuration"""
    
    def test_smtp_port_default(self):
        """SMTP port should default to 587 (TLS)"""
        settings = Settings()
        assert settings.smtp_port == 587
    
    def test_smtp_use_tls_default(self):
        """SMTP should use TLS by default"""
        settings = Settings()
        assert settings.smtp_use_tls is True
