"""
Configuration Management Module.

Provides typed, validated configuration with safe defaults.
All configuration is loaded from environment variables.
"""

from datetime import time
from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    
    All settings have safe defaults and are validated on startup.
    """
    
    # ===========================================
    # Supabase Configuration
    # ===========================================
    supabase_url: str = Field(
        default="https://your-project.supabase.co",
        description="Supabase project URL"
    )
    supabase_key: str = Field(
        default="your-supabase-anon-key",
        description="Supabase anonymous key"
    )
    
    # ===========================================
    # Trading Parameters
    # ===========================================
    trading_capital: float = Field(
        default=500000.0,
        ge=10000,
        description="Total trading capital in INR"
    )
    max_risk_per_trade_pct: float = Field(
        default=1.0,
        ge=0.1,
        le=2.0,
        description="Maximum risk per trade as percentage of capital"
    )
    max_daily_loss_pct: float = Field(
        default=1.5,
        ge=0.5,
        le=3.0,
        description="Maximum daily loss as percentage of capital"
    )
    max_trades_per_day: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum number of trades per day"
    )
    max_consecutive_losses: int = Field(
        default=2,
        ge=1,
        le=5,
        description="Maximum consecutive losses before hard shutdown"
    )
    
    # ===========================================
    # Market Hours (IST)
    # ===========================================
    market_open_hour: int = Field(default=9, ge=0, le=23)
    market_open_minute: int = Field(default=15, ge=0, le=59)
    market_close_hour: int = Field(default=15, ge=0, le=23)
    market_close_minute: int = Field(default=30, ge=0, le=59)
    opening_range_end_minute: int = Field(default=30, ge=15, le=45)
    
    # ===========================================
    # Buffer Configuration
    # ===========================================
    data_buffer_size: int = Field(
        default=100,
        ge=20,
        le=500,
        description="Size of sliding window buffer for market data"
    )
    min_buffer_fill_pct: float = Field(
        default=80.0,
        ge=50.0,
        le=100.0,
        description="Minimum buffer fill percentage before trading allowed"
    )
    
    # ===========================================
    # Data Validation
    # ===========================================
    max_data_staleness_seconds: int = Field(
        default=5,
        ge=1,
        le=30,
        description="Maximum allowed data staleness in seconds"
    )
    max_latency_ms: int = Field(
        default=500,
        ge=100,
        le=2000,
        description="Maximum allowed latency in milliseconds"
    )
    
    # ===========================================
    # Trading Thresholds
    # ===========================================
    min_confluence_score: float = Field(
        default=7.0,
        ge=5.0,
        le=10.0,
        description="Minimum confluence score for trade eligibility"
    )
    min_risk_reward: float = Field(
        default=2.0,
        ge=1.5,
        le=5.0,
        description="Minimum risk-reward ratio for trade acceptance"
    )
    
    # ===========================================
    # API Configuration
    # ===========================================
    api_host: str = Field(default="0.0.0.0")
    api_port: int = Field(default=8000, ge=1000, le=65535)
    
    # ===========================================
    # Streamlit Configuration
    # ===========================================
    streamlit_port: int = Field(default=8501, ge=1000, le=65535)
    
    # ===========================================
    # Logging
    # ===========================================
    log_level: str = Field(default="INFO")
    
    # ===========================================
    # Broker Configuration (Stubbed)
    # ===========================================
    broker_api_key: str = Field(default="your-broker-api-key")
    broker_api_secret: str = Field(default="your-broker-api-secret")
    
    # ===========================================
    # AI Configuration
    # ===========================================
    gemini_api_key: str = Field(default="", description="Gemini AI API Key")

    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }
    
    @property
    def market_open_time(self) -> time:
        """Get market open time as a time object."""
        return time(hour=self.market_open_hour, minute=self.market_open_minute)
    
    @property
    def market_close_time(self) -> time:
        """Get market close time as a time object."""
        return time(hour=self.market_close_hour, minute=self.market_close_minute)
    
    @property
    def opening_range_end_time(self) -> time:
        """Get opening range end time as a time object."""
        return time(hour=self.market_open_hour, minute=self.opening_range_end_minute)
    
    @property
    def max_risk_amount(self) -> float:
        """Calculate maximum risk amount per trade in INR."""
        return self.trading_capital * (self.max_risk_per_trade_pct / 100)
    
    @property
    def max_daily_loss_amount(self) -> float:
        """Calculate maximum daily loss amount in INR."""
        return self.trading_capital * (self.max_daily_loss_pct / 100)
    
    @property
    def min_buffer_fill_count(self) -> int:
        """Calculate minimum buffer fill count."""
        return int(self.data_buffer_size * (self.min_buffer_fill_pct / 100))
    
    def is_supabase_configured(self) -> bool:
        """Check if Supabase is properly configured."""
        return (
            self.supabase_url != "https://your-project.supabase.co"
            and self.supabase_key != "your-supabase-anon-key"
        )
    
    def is_broker_configured(self) -> bool:
        """Check if broker API is properly configured."""
        return (
            self.broker_api_key != "your-broker-api-key"
            and self.broker_api_secret != "your-broker-api-secret"
        )


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Returns:
        Settings: Application settings
    """
    return Settings()


# Create global settings instance
settings = get_settings()
