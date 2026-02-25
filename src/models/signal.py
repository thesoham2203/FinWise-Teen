"""
Trade Signal Models.

Pydantic models for trade signals and confluence scoring.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class SignalDirection(str, Enum):
    """Trade signal direction."""
    
    LONG = "LONG"
    SHORT = "SHORT"
    NEUTRAL = "NEUTRAL"


class IndicatorSignal(BaseModel):
    """
    Individual Indicator Signal.
    
    Contains the signal from a single indicator with its score contribution.
    """
    
    name: str = Field(..., description="Indicator name")
    signal: SignalDirection = Field(..., description="Signal direction")
    score: float = Field(..., ge=0, le=2, description="Score contribution (0-2)")
    value: float = Field(default=0.0, description="Indicator value")
    threshold: Optional[float] = Field(default=None, description="Threshold used")
    reasoning: str = Field(default="", description="Signal reasoning")
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "signal": self.signal.value,
            "score": self.score,
            "value": self.value,
            "reasoning": self.reasoning,
        }


class ConfluenceScore(BaseModel):
    """
    Technical Confluence Score.
    
    Aggregates all indicator signals into a confluence score.
    """
    
    total_score: float = Field(..., ge=0, description="Total confluence score")
    max_possible_score: float = Field(default=10.0, ge=0, description="Maximum possible score")
    direction: SignalDirection = Field(..., description="Overall direction")
    is_eligible: bool = Field(default=False, description="Meets minimum score threshold")
    
    # Individual indicator signals
    vwap_signal: Optional[IndicatorSignal] = Field(default=None)
    ema_signal: Optional[IndicatorSignal] = Field(default=None)
    rsi_signal: Optional[IndicatorSignal] = Field(default=None)
    volume_signal: Optional[IndicatorSignal] = Field(default=None)
    price_action_signal: Optional[IndicatorSignal] = Field(default=None)
    
    # Additional context
    bullish_count: int = Field(default=0, ge=0, description="Number of bullish signals")
    bearish_count: int = Field(default=0, ge=0, description="Number of bearish signals")
    neutral_count: int = Field(default=0, ge=0, description="Number of neutral signals")
    
    reasoning: List[str] = Field(
        default_factory=list,
        description="List of reasoning points"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Score calculation timestamp"
    )
    
    @property
    def score_percentage(self) -> float:
        """Get score as percentage of max possible."""
        if self.max_possible_score <= 0:
            return 0.0
        return (self.total_score / self.max_possible_score) * 100
    
    def get_all_signals(self) -> List[IndicatorSignal]:
        """Get all non-None indicator signals."""
        signals = []
        for signal in [
            self.vwap_signal,
            self.ema_signal,
            self.rsi_signal,
            self.volume_signal,
            self.price_action_signal,
        ]:
            if signal is not None:
                signals.append(signal)
        return signals
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        status = "✅ ELIGIBLE" if self.is_eligible else "❌ NOT ELIGIBLE"
        return (
            f"Score: {self.total_score:.1f}/{self.max_possible_score:.0f} | "
            f"Direction: {self.direction.value} | "
            f"Bull: {self.bullish_count} Bear: {self.bearish_count} | "
            f"{status}"
        )


class OptionsIntelligence(BaseModel):
    """
    Options Intelligence Analysis.
    
    Contains OI, IV, and PCR analysis results.
    """
    
    # Direction signals
    direction: SignalDirection = Field(
        default=SignalDirection.NEUTRAL,
        description="Overall options-based direction"
    )
    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Confidence level (0-1)"
    )
    
    # OI Analysis
    delta_oi_calls: int = Field(default=0, description="Change in call OI")
    delta_oi_puts: int = Field(default=0, description="Change in put OI")
    oi_buildup_type: str = Field(
        default="neutral",
        description="long_buildup, short_buildup, long_unwinding, short_covering, neutral"
    )
    
    # ATM Analysis
    atm_straddle_premium: float = Field(default=0.0, ge=0, description="ATM straddle premium")
    atm_straddle_change: float = Field(default=0.0, description="Straddle change from open")
    atm_iv: float = Field(default=0.0, ge=0, description="ATM IV")
    
    # PCR Analysis
    current_pcr: float = Field(default=0.0, ge=0, description="Current PCR")
    pcr_change: float = Field(default=0.0, description="PCR change from previous")
    pcr_interpretation: str = Field(
        default="neutral",
        description="bullish, bearish, neutral"
    )
    
    # OI Walls
    call_wall_strike: float = Field(default=0.0, description="Highest call OI strike")
    call_wall_oi: int = Field(default=0, description="Call wall OI")
    put_wall_strike: float = Field(default=0.0, description="Highest put OI strike")
    put_wall_oi: int = Field(default=0, description="Put wall OI")
    
    # IV Analysis
    iv_percentile: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="IV percentile rank"
    )
    iv_status: str = Field(
        default="normal",
        description="low, normal, elevated, extreme"
    )
    iv_trend: str = Field(
        default="stable",
        description="expanding, contracting, stable"
    )
    
    # Max Pain
    max_pain_strike: float = Field(default=0.0, description="Max pain strike")
    distance_to_max_pain: float = Field(
        default=0.0,
        description="Distance from current price to max pain"
    )
    
    # Conflict Detection
    has_conflict: bool = Field(
        default=False,
        description="Whether conflicting signals exist"
    )
    conflict_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for conflict if any"
    )
    
    reasoning: List[str] = Field(
        default_factory=list,
        description="Analysis reasoning"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        conflict_status = "⚠️ CONFLICT" if self.has_conflict else "✅ CLEAR"
        return (
            f"Direction: {self.direction.value} | "
            f"PCR: {self.current_pcr:.2f} | "
            f"IV: {self.iv_status.upper()} | "
            f"Buildup: {self.oi_buildup_type.upper()} | "
            f"{conflict_status}"
        )


class TradeSignal(BaseModel):
    """
    Complete Trade Signal.
    
    Aggregates regime, confluence, and options intelligence
    into a final trade signal.
    """
    
    signal_id: str = Field(..., description="Unique signal ID")
    timestamp: datetime = Field(..., description="Signal generation time")
    
    # Direction
    direction: SignalDirection = Field(..., description="Signal direction")
    
    # Validity
    is_valid: bool = Field(
        default=False,
        description="Whether signal is valid for trading"
    )
    validity_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for validity/invalidity"
    )
    
    # Component Scores
    regime_score: float = Field(default=0.0, ge=0, le=10)
    confluence_score: float = Field(default=0.0, ge=0, le=10)
    options_score: float = Field(default=0.0, ge=0, le=10)
    total_score: float = Field(default=0.0, ge=0, le=30)
    
    # Detailed Analysis
    regime_type: str = Field(default="", description="Current regime")
    volatility_level: str = Field(default="", description="Current volatility")
    
    confluence_details: Optional[ConfluenceScore] = Field(default=None)
    options_intel: Optional[OptionsIntelligence] = Field(default=None)
    
    # Trade Suggestion
    suggested_setup: str = Field(default="", description="Suggested trade setup")
    suggested_instrument: str = Field(
        default="",
        description="Suggested instrument (FUT/CE/PE)"
    )
    
    # Full Reasoning Chain
    reasoning_chain: List[str] = Field(
        default_factory=list,
        description="Complete reasoning chain"
    )
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        return (
            f"Signal: {self.direction.value} | "
            f"Score: {self.total_score:.1f}/30 | "
            f"Regime: {self.regime_type} | "
            f"{status}"
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "signal_id": self.signal_id,
            "timestamp": self.timestamp.isoformat(),
            "direction": self.direction.value,
            "is_valid": self.is_valid,
            "regime_type": self.regime_type,
            "confluence_score": self.confluence_score,
            "options_score": self.options_score,
            "total_score": self.total_score,
            "suggested_setup": self.suggested_setup,
            "reasoning": self.reasoning_chain,
        }
