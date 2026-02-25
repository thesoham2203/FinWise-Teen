"""
Supabase Client Module.

Manages connection to Supabase Postgres database.
"""

from functools import lru_cache
from typing import Optional
import logging

from supabase import create_client, Client

from src.config import settings


logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Supabase client wrapper.
    
    Provides connection management and basic operations.
    """
    
    _instance: Optional[Client] = None
    
    def __init__(self):
        """Initialize Supabase client."""
        self._client: Optional[Client] = None
    
    def connect(self) -> bool:
        """
        Establish connection to Supabase.
        
        Returns:
            True if connection successful
        """
        if not settings.is_supabase_configured():
            logger.warning(
                "Supabase not configured. Set SUPABASE_URL and SUPABASE_KEY in .env"
            )
            return False
        
        try:
            self._client = create_client(
                settings.supabase_url,
                settings.supabase_key,
            )
            logger.info("Connected to Supabase")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from Supabase."""
        self._client = None
        logger.info("Disconnected from Supabase")
    
    @property
    def client(self) -> Optional[Client]:
        """Get Supabase client instance."""
        return self._client
    
    def is_connected(self) -> bool:
        """Check if connected to Supabase."""
        return self._client is not None
    
    def health_check(self) -> bool:
        """
        Perform health check on Supabase connection.
        
        Returns:
            True if healthy
        """
        if not self._client:
            return False
        
        try:
            # Simple query to test connection
            self._client.table("signals").select("id").limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase health check failed: {e}")
            return False


# Global client instance
_supabase_client: Optional[SupabaseClient] = None


def get_supabase_client() -> SupabaseClient:
    """
    Get the global Supabase client instance.
    
    Returns:
        SupabaseClient instance
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
        _supabase_client.connect()
    
    return _supabase_client


# SQL Schema for reference (run this in Supabase SQL Editor)
SCHEMA_SQL = """
-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Signals table
CREATE TABLE IF NOT EXISTS signals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    direction TEXT NOT NULL,
    is_valid BOOLEAN NOT NULL DEFAULT FALSE,
    regime_type TEXT,
    volatility_level TEXT,
    confluence_score FLOAT,
    options_score FLOAT,
    total_score FLOAT,
    regime_data JSONB,
    confluence_data JSONB,
    options_data JSONB,
    reasoning JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Trade plans table
CREATE TABLE IF NOT EXISTS trade_plans (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    signal_id UUID REFERENCES signals(id),
    plan_id TEXT UNIQUE NOT NULL,
    instrument TEXT NOT NULL,
    instrument_type TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_zone JSONB NOT NULL,
    stop_loss FLOAT NOT NULL,
    target_1 FLOAT NOT NULL,
    target_2 FLOAT NOT NULL,
    risk_reward FLOAT NOT NULL,
    position_size INT NOT NULL,
    risk_amount FLOAT NOT NULL,
    status TEXT DEFAULT 'pending',
    is_valid BOOLEAN DEFAULT FALSE,
    rejection_reasons JSONB,
    reasoning JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Executed trades table
CREATE TABLE IF NOT EXISTS executed_trades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plan_id TEXT REFERENCES trade_plans(plan_id),
    trade_id TEXT UNIQUE NOT NULL,
    instrument TEXT NOT NULL,
    direction TEXT NOT NULL,
    entry_price FLOAT NOT NULL,
    entry_time TIMESTAMPTZ NOT NULL,
    quantity INT NOT NULL,
    exit_price FLOAT,
    exit_time TIMESTAMPTZ,
    exit_reason TEXT,
    pnl_points FLOAT DEFAULT 0,
    pnl_amount FLOAT DEFAULT 0,
    is_closed BOOLEAN DEFAULT FALSE,
    is_winner BOOLEAN,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Daily risk state table
CREATE TABLE IF NOT EXISTS daily_risk_state (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    date DATE UNIQUE NOT NULL,
    trades_taken INT DEFAULT 0,
    max_trades INT DEFAULT 2,
    total_pnl FLOAT DEFAULT 0,
    realized_pnl FLOAT DEFAULT 0,
    consecutive_losses INT DEFAULT 0,
    starting_capital FLOAT NOT NULL,
    current_capital FLOAT NOT NULL,
    max_daily_loss_amount FLOAT NOT NULL,
    remaining_risk_capacity FLOAT NOT NULL,
    hard_shutdown BOOLEAN DEFAULT FALSE,
    shutdown_reason TEXT,
    status TEXT DEFAULT 'normal',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_signals_timestamp ON signals(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_signals_is_valid ON signals(is_valid);
CREATE INDEX IF NOT EXISTS idx_trade_plans_status ON trade_plans(status);
CREATE INDEX IF NOT EXISTS idx_trade_plans_created ON trade_plans(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executed_trades_is_closed ON executed_trades(is_closed);
CREATE INDEX IF NOT EXISTS idx_daily_risk_date ON daily_risk_state(date DESC);
"""
