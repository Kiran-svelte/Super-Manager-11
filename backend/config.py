"""
Super Manager - Environment Configuration
==========================================

Centralized configuration management with validation, defaults,
and environment-specific settings.
"""

import os
from typing import Optional, List, Any
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings can be overridden via environment variables.
    """
    
    # ==========================================================================
    # Application Settings
    # ==========================================================================
    app_name: str = Field(default="Super Manager", description="Application name")
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    secret_key: str = Field(default="change-me-in-production", min_length=16, description="Secret key for JWT/sessions")
    
    # ==========================================================================
    # Server Settings
    # ==========================================================================
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, ge=1, le=65535, description="Server port")
    workers: int = Field(default=4, ge=1, description="Number of worker processes")
    
    # ==========================================================================
    # AI/LLM Settings
    # ==========================================================================
    groq_api_key: Optional[str] = Field(default=None, description="Groq API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key (fallback)")
    ai_model: str = Field(default="llama-3.3-70b-versatile", description="Default AI model")
    ai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="AI temperature")
    ai_max_tokens: int = Field(default=2048, ge=1, description="Max tokens for AI response")
    
    # ==========================================================================
    # Database Settings
    # ==========================================================================
    supabase_url: Optional[str] = Field(default=None, description="Supabase project URL")
    supabase_key: Optional[str] = Field(default=None, description="Supabase anon/service key")
    database_url: Optional[str] = Field(default=None, description="PostgreSQL connection URL")
    
    # ==========================================================================
    # Cache Settings
    # ==========================================================================
    redis_url: Optional[str] = Field(default=None, description="Redis connection URL")
    cache_ttl: int = Field(default=300, description="Default cache TTL in seconds")
    cache_enabled: bool = Field(default=True, description="Enable caching")
    
    # ==========================================================================
    # Security Settings
    # ==========================================================================
    cors_origins: str = Field(
        default="http://localhost:3000,http://localhost:5173",
        description="Comma-separated CORS origins"
    )
    rate_limit_per_minute: int = Field(default=100, ge=1, description="Rate limit per minute")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expiry_hours: int = Field(default=24, ge=1, description="JWT expiry in hours")
    
    # ==========================================================================
    # Email Settings
    # ==========================================================================
    smtp_host: Optional[str] = Field(default=None, description="SMTP server host")
    smtp_port: int = Field(default=587, description="SMTP server port")
    smtp_email: Optional[str] = Field(default=None, description="SMTP email address")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_use_tls: bool = Field(default=True, description="Use TLS for SMTP")
    
    # ==========================================================================
    # Telegram Settings
    # ==========================================================================
    telegram_bot_token: Optional[str] = Field(default=None, description="Telegram bot token")
    telegram_chat_id: Optional[str] = Field(default=None, description="Default Telegram chat ID")
    
    # ==========================================================================
    # Monitoring Settings
    # ==========================================================================
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    health_check_interval: int = Field(default=30, description="Health check interval in seconds")
    
    # ==========================================================================
    # Backup Settings
    # ==========================================================================
    backup_enabled: bool = Field(default=True, description="Enable automated backups")
    backup_dir: str = Field(default="./backups", description="Backup directory")
    backup_retention_days: int = Field(default=30, description="Backup retention in days")
    
    # ==========================================================================
    # Validators
    # ==========================================================================
    
    @field_validator("app_env")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = ["development", "staging", "production", "testing"]
        if v.lower() not in allowed:
            raise ValueError(f"app_env must be one of: {', '.join(allowed)}")
        return v.lower()
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in allowed:
            raise ValueError(f"log_level must be one of: {', '.join(allowed)}")
        return v.upper()
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list"""
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.app_env == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.app_env == "development"
    
    def validate_required(self) -> List[str]:
        """Validate required settings and return list of missing ones"""
        missing = []
        
        if self.is_production:
            if not self.groq_api_key:
                missing.append("GROQ_API_KEY")
            if not self.supabase_url:
                missing.append("SUPABASE_URL")
            if not self.supabase_key:
                missing.append("SUPABASE_KEY")
            if self.secret_key == "change-me-in-production":
                missing.append("SECRET_KEY (must be changed from default)")
        
        return missing
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # Ignore extra env vars
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to avoid re-parsing environment on every call.
    """
    return Settings()


def validate_settings() -> None:
    """
    Validate settings on startup.
    
    Raises ValueError if required settings are missing in production.
    """
    settings = get_settings()
    missing = settings.validate_required()
    
    if missing:
        raise ValueError(
            f"Missing required configuration for {settings.app_env}: {', '.join(missing)}"
        )


# Convenience exports
settings = get_settings()
