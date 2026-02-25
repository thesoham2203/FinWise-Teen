"""
Market Regime Models.

Pydantic models for market regime classification.
"""

from datetime import datetime, time
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class RegimeType(str, Enum):
    """Market regime classification types."""
    
    TRENDING_BULLISH = "trending_bullish"
    TRENDING_BEARISH = "trending_bearish"
    RANGE_BOUND = "range_bound"
    VOLATILE = "volatile"
    PRE_BREAKOUT = "pre_breakout"
    OPENING_RANGE = "opening_range"
    NO_TRADE = "no_trade"


class VolatilityLevel(str, Enum):
    """Volatility level classification."""
    
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXTREME = "extreme"


class TrendDirection(str, Enum):
    """Trend direction classification."""
    
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"


class OpeningRange(BaseModel):
    """
    Opening Range Data (9:15 - 9:30).
    
    Captures the high and low of the first 15 minutes.
    """
    
    high: float = Field(..., gt=0, description="Opening range high")
    low: float = Field(..., gt=0, description="Opening range low")
    captured: bool = Field(default=False, description="Whether OR is fully captured")
    start_time: time = Field(default=time(9, 15), description="OR start time")
    end_time: time = Field(default=time(9, 30), description="OR end time")
    timestamp: datetime = Field(..., description="Capture timestamp")
    
    @property
    def range(self) -> float:
        """Calculate opening range size."""
        return self.high - self.low
    
    @property
    def midpoint(self) -> float:
        """Calculate opening range midpoint."""
        return (self.high + self.low) / 2
    
    def is_breakout_up(self, price: float) -> bool:
        """Check if price has broken out above OR high."""
        return price > self.high
    
    def is_breakout_down(self, price: float) -> bool:
        """Check if price has broken out below OR low."""
        return price < self.low
    
    def get_position(self, price: float) -> str:
        """
        Get price position relative to opening range.
        
        Returns:
            'above', 'below', 'upper_half', 'lower_half'
        """
        if price > self.high:
            return "above"
        elif price < self.low:
            return "below"
        elif price >= self.midpoint:
            return "upper_half"
        return "lower_half"


class MarketRegime(BaseModel):
    """
    Market Regime Classification Result.
    
    Contains the current market regime, volatility level,
    allowed trade setups, and explanations.
    """
    
    regime: RegimeType = Field(..., description="Current market regime")
    volatility: VolatilityLevel = Field(..., description="Current volatility level")
    trend_direction: TrendDirection = Field(
        default=TrendDirection.SIDEWAYS,
        description="Overall trend direction"
    )
    allowed_setups: List[str] = Field(
        default_factory=list,
        description="List of allowed trade setups for this regime"
    )
    trade_allowed: bool = Field(
        default=False,
        description="Whether trading is allowed in current conditions"
    )
    
    # Component Analysis
    opening_range: Optional[OpeningRange] = Field(
        default=None,
        description="Opening range data"
    )
    atr_ratio: float = Field(
        default=1.0,
        ge=0,
        description="Current ATR / 20-day ATR ratio"
    )
    vwap_slope: float = Field(
        default=0.0,
        description="VWAP slope (positive = uptrend)"
    )
    price_vs_vwap: str = Field(
        default="at",
        description="Price position vs VWAP: above, below, at"
    )
    prev_day_high: float = Field(default=0.0, ge=0, description="Previous day high")
    prev_day_low: float = Field(default=0.0, ge=0, description="Previous day low")
    vix_direction: str = Field(
        default="stable",
        description="VIX direction: rising, falling, stable"
    )
    vix_level: str = Field(
        default="normal",
        description="VIX level: low, normal, elevated, extreme"
    )
    
    # Explanations
    regime_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for regime classification"
    )
    trade_rejection_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons why trading may not be allowed"
    )
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Classification timestamp"
    )
    
    def get_setup_for_regime(self) -> List[str]:
        """
        Get recommended setups based on regime.
        
        Returns:
            List of recommended trade setups
        """
        setups_map = {
            RegimeType.TRENDING_BULLISH: [
                "pullback_to_ema",
                "vwap_retest",
                "breakout_continuation",
            ],
            RegimeType.TRENDING_BEARISH: [
                "pullback_to_ema",
                "vwap_retest",
                "breakdown_continuation",
            ],
            RegimeType.RANGE_BOUND: [
                "range_reversal",
                "mean_reversion",
            ],
            RegimeType.VOLATILE: [
                "wait_for_clarity",
            ],
            RegimeType.PRE_BREAKOUT: [
                "breakout_anticipation",
                "wait_for_confirmation",
            ],
            RegimeType.OPENING_RANGE: [
                "or_breakout",
                "or_failure",
            ],
            RegimeType.NO_TRADE: [],
        }
        return setups_map.get(self.regime, [])
    
    def to_summary(self) -> str:
        """
        Generate human-readable regime summary.
        
        Returns:
            Summary string
        """
        status = "✅ TRADE ALLOWED" if self.trade_allowed else "❌ NO TRADE"
        return (
            f"Regime: {self.regime.value.upper()} | "
            f"Volatility: {self.volatility.value.upper()} | "
            f"Trend: {self.trend_direction.value.upper()} | "
            f"{status}"
        )


class RegimeAnalysisComponents(BaseModel):
    """
    Individual components used for regime analysis.
    
    This captures all the data points used to determine the regime.
    """
    
    # Price Action
    current_price: float = Field(..., description="Current LTP")
    prev_close: float = Field(..., description="Previous close")
    day_high: float = Field(..., description="Today's high")
    day_low: float = Field(..., description="Today's low")
    
    # Opening Range
    or_high: Optional[float] = Field(default=None, description="Opening range high")
    or_low: Optional[float] = Field(default=None, description="Opening range low")
    or_captured: bool = Field(default=False, description="Is OR captured")
    
    # ATR Analysis
    current_atr: float = Field(default=0.0, ge=0, description="Current period ATR")
    atr_20: float = Field(default=0.0, ge=0, description="20-period ATR")
    
    # VWAP Analysis
    vwap: float = Field(default=0.0, ge=0, description="Current VWAP")
    vwap_upper: float = Field(default=0.0, ge=0, description="VWAP upper band")
    vwap_lower: float = Field(default=0.0, ge=0, description="VWAP lower band")
    
    # Previous Day Reference
    prev_day_high: float = Field(default=0.0, ge=0, description="Previous day high")
    prev_day_low: float = Field(default=0.0, ge=0, description="Previous day low")
    
    # VIX
    vix_value: float = Field(default=0.0, ge=0, description="Current VIX")
    vix_change_pct: float = Field(default=0.0, description="VIX change %")
    
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )
