"""
Market Data Models.

Pydantic models for spot, futures, options, and VIX data.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field


class OHLCV(BaseModel):
    """Open-High-Low-Close-Volume data structure."""
    
    open: float = Field(..., description="Opening price")
    high: float = Field(..., description="High price")
    low: float = Field(..., description="Low price")
    close: float = Field(..., description="Closing price")
    volume: int = Field(default=0, ge=0, description="Volume traded")
    
    @property
    def range(self) -> float:
        """Calculate the price range."""
        return self.high - self.low
    
    @property
    def body(self) -> float:
        """Calculate the candle body size."""
        return abs(self.close - self.open)
    
    @property
    def is_bullish(self) -> bool:
        """Check if the candle is bullish."""
        return self.close > self.open
    
    @property
    def is_bearish(self) -> bool:
        """Check if the candle is bearish."""
        return self.close < self.open


class SpotData(BaseModel):
    """
    Bank Nifty Spot Index Data.
    
    Contains current LTP, OHLC for the session, and volume information.
    """
    
    symbol: str = Field(default="BANKNIFTY", description="Symbol name")
    ltp: float = Field(..., gt=0, description="Last traded price")
    ohlcv: OHLCV = Field(..., description="Today's OHLCV data")
    prev_close: float = Field(..., gt=0, description="Previous day close")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    @property
    def change(self) -> float:
        """Calculate absolute change from previous close."""
        return self.ltp - self.prev_close
    
    @property
    def change_pct(self) -> float:
        """Calculate percentage change from previous close."""
        return (self.change / self.prev_close) * 100 if self.prev_close > 0 else 0.0
    
    @property
    def day_range_pct(self) -> float:
        """Calculate today's range as percentage of previous close."""
        return (self.ohlcv.range / self.prev_close) * 100 if self.prev_close > 0 else 0.0


class FuturesData(BaseModel):
    """
    Bank Nifty Futures Data.
    
    Contains futures price, OI, and basis information.
    """
    
    symbol: str = Field(..., description="Futures symbol (e.g., BANKNIFTY24JANFUT)")
    ltp: float = Field(..., gt=0, description="Last traded price")
    ohlcv: OHLCV = Field(..., description="Today's OHLCV data")
    open_interest: int = Field(..., ge=0, description="Open Interest")
    oi_change: int = Field(default=0, description="Change in OI from previous day")
    expiry: datetime = Field(..., description="Expiry date")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    def calculate_basis(self, spot_price: float) -> float:
        """
        Calculate basis (premium/discount) against spot.
        
        Args:
            spot_price: Current spot price
            
        Returns:
            Basis in points
        """
        return self.ltp - spot_price
    
    def calculate_basis_pct(self, spot_price: float) -> float:
        """
        Calculate basis as percentage of spot.
        
        Args:
            spot_price: Current spot price
            
        Returns:
            Basis percentage
        """
        if spot_price <= 0:
            return 0.0
        return (self.calculate_basis(spot_price) / spot_price) * 100


class OptionGreeks(BaseModel):
    """Option Greeks for risk analysis."""
    
    delta: float = Field(default=0.0, ge=-1.0, le=1.0, description="Delta")
    gamma: float = Field(default=0.0, ge=0.0, description="Gamma")
    theta: float = Field(default=0.0, description="Theta (daily decay)")
    vega: float = Field(default=0.0, ge=0.0, description="Vega")
    iv: float = Field(default=0.0, ge=0.0, description="Implied Volatility %")


class OptionData(BaseModel):
    """
    Single Option Contract Data.
    
    Contains option price, Greeks, and OI information.
    """
    
    symbol: str = Field(..., description="Option symbol")
    strike: float = Field(..., gt=0, description="Strike price")
    option_type: str = Field(..., pattern="^(CE|PE)$", description="CE or PE")
    ltp: float = Field(..., ge=0, description="Last traded price")
    bid: float = Field(default=0.0, ge=0, description="Best bid price")
    ask: float = Field(default=0.0, ge=0, description="Best ask price")
    open_interest: int = Field(..., ge=0, description="Open Interest")
    oi_change: int = Field(default=0, description="Change in OI")
    volume: int = Field(default=0, ge=0, description="Volume traded")
    greeks: OptionGreeks = Field(default_factory=OptionGreeks, description="Option Greeks")
    expiry: datetime = Field(..., description="Expiry date")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        return self.ask - self.bid if self.ask > 0 and self.bid > 0 else 0.0
    
    @property
    def spread_pct(self) -> float:
        """Calculate bid-ask spread as percentage of LTP."""
        if self.ltp <= 0:
            return 0.0
        return (self.spread / self.ltp) * 100
    
    @property
    def is_itm(self) -> bool:
        """
        Check if option is in-the-money.
        Note: Requires spot price comparison, this is a placeholder.
        """
        return False  # Will be set based on spot comparison


class OptionsChain(BaseModel):
    """
    Options Chain Data.
    
    Contains ATM ± 5 strikes for both CE and PE.
    """
    
    underlying: str = Field(default="BANKNIFTY", description="Underlying symbol")
    spot_price: float = Field(..., gt=0, description="Current spot price")
    atm_strike: float = Field(..., gt=0, description="ATM strike price")
    expiry: datetime = Field(..., description="Expiry date")
    calls: List[OptionData] = Field(default_factory=list, description="Call options")
    puts: List[OptionData] = Field(default_factory=list, description="Put options")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    @property
    def atm_call(self):
        """Get ATM call option. Returns Optional[OptionData]."""
        for call in self.calls:
            if call.strike == self.atm_strike:
                return call
        return None
    
    @property
    def atm_put(self):
        """Get ATM put option. Returns Optional[OptionData]."""
        for put in self.puts:
            if put.strike == self.atm_strike:
                return put
        return None
    
    @property
    def atm_straddle_premium(self) -> float:
        """Calculate ATM straddle premium."""
        atm_call = self.atm_call
        atm_put = self.atm_put
        if atm_call and atm_put:
            return atm_call.ltp + atm_put.ltp
        return 0.0
    
    @property
    def total_call_oi(self) -> int:
        """Get total call OI."""
        return sum(c.open_interest for c in self.calls)
    
    @property
    def total_put_oi(self) -> int:
        """Get total put OI."""
        return sum(p.open_interest for p in self.puts)
    
    @property
    def pcr(self) -> float:
        """Calculate Put-Call Ratio based on OI."""
        total_call = self.total_call_oi
        if total_call == 0:
            return 0.0
        return self.total_put_oi / total_call
    
    def get_max_pain(self) -> float:
        """
        Calculate max pain strike.
        
        Returns:
            Strike price where maximum loss occurs for option writers
        """
        if not self.calls or not self.puts:
            return self.atm_strike
        
        strikes = sorted(set(c.strike for c in self.calls))
        min_pain = float('inf')
        max_pain_strike = self.atm_strike
        
        for strike in strikes:
            pain = 0.0
            # Calculate pain for call writers
            for call in self.calls:
                if call.strike < strike:
                    pain += (strike - call.strike) * call.open_interest
            # Calculate pain for put writers
            for put in self.puts:
                if put.strike > strike:
                    pain += (put.strike - strike) * put.open_interest
            
            if pain < min_pain:
                min_pain = pain
                max_pain_strike = strike
        
        return max_pain_strike
    
    def get_oi_walls(self):
        """
        Get significant OI walls (support/resistance).
        
        Returns:
            Dict with 'call_walls' and 'put_walls' as lists of (strike, oi)
        """
        # Sort calls by OI descending and get top 3
        call_walls = sorted(
            [(c.strike, c.open_interest) for c in self.calls],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # Sort puts by OI descending and get top 3
        put_walls = sorted(
            [(p.strike, p.open_interest) for p in self.puts],
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        return {
            "call_walls": call_walls,  # Resistance levels
            "put_walls": put_walls,    # Support levels
        }


class VIXData(BaseModel):
    """
    India VIX Data.
    
    Contains VIX value and direction.
    """
    
    symbol: str = Field(default="INDIAVIX", description="Symbol")
    value: float = Field(..., ge=0, description="Current VIX value")
    prev_close: float = Field(..., ge=0, description="Previous close")
    ohlcv: Optional[OHLCV] = Field(default=None, description="Today's OHLCV")
    timestamp: datetime = Field(..., description="Data timestamp")
    
    @property
    def change(self) -> float:
        """Calculate absolute change."""
        return self.value - self.prev_close
    
    @property
    def change_pct(self) -> float:
        """Calculate percentage change."""
        if self.prev_close <= 0:
            return 0.0
        return (self.change / self.prev_close) * 100
    
    @property
    def direction(self) -> str:
        """
        Get VIX direction.
        
        Returns:
            'rising', 'falling', or 'stable'
        """
        change_pct = self.change_pct
        if change_pct > 3:
            return "rising"
        elif change_pct < -3:
            return "falling"
        return "stable"
    
    @property
    def level(self) -> str:
        """
        Get VIX level category.
        
        Returns:
            'low', 'normal', 'elevated', or 'extreme'
        """
        if self.value < 12:
            return "low"
        elif self.value < 18:
            return "normal"
        elif self.value < 25:
            return "elevated"
        return "extreme"


class MarketSnapshot(BaseModel):
    """
    Complete Market Snapshot.
    
    Contains spot, futures, options chain, and VIX data.
    """
    
    spot: SpotData = Field(..., description="Spot data")
    futures: FuturesData = Field(..., description="Futures data")
    options_chain: OptionsChain = Field(..., description="Options chain")
    vix: VIXData = Field(..., description="VIX data")
    timestamp: datetime = Field(..., description="Snapshot timestamp")
    
    @property
    def is_valid(self) -> bool:
        """Check if all data is valid and fresh."""
        now = datetime.now()
        max_staleness = 10  # seconds
        
        timestamps = [
            self.spot.timestamp,
            self.futures.timestamp,
            self.options_chain.timestamp,
            self.vix.timestamp,
        ]
        
        for ts in timestamps:
            if (now - ts).total_seconds() > max_staleness:
                return False
        return True
    
    @property
    def futures_basis(self) -> float:
        """Get futures basis against spot."""
        return self.futures.calculate_basis(self.spot.ltp)
