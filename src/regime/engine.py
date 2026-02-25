"""
Market Regime Classification Engine.

Classifies market into regimes based on:
- Opening Range (9:15-9:30)
- ATR vs 20-day ATR
- VWAP slope and position
- Previous day High/Low
- VIX direction and level
"""

from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from src.config import settings
from src.models.market_data import MarketSnapshot, SpotData, VIXData
from src.models.regime import (
    MarketRegime,
    OpeningRange,
    RegimeAnalysisComponents,
    RegimeType,
    TrendDirection,
    VolatilityLevel,
)


class MarketRegimeEngine:
    """
    Market Regime Classification Engine.
    
    Analyzes market conditions and classifies into regimes
    with allowed setups and trade permissions.
    """
    
    def __init__(self):
        """Initialize the regime engine."""
        # Opening range tracking
        self._opening_range: Optional[OpeningRange] = None
        self._or_candles: List[SpotData] = []
        
        # Historical data for ATR calculation
        self._daily_ranges: List[float] = []
        self._atr_period = 14
        self._atr_lookback = 20
        
        # Previous day data
        self._prev_day_high: float = 0.0
        self._prev_day_low: float = 0.0
        self._prev_day_close: float = 0.0
        
        # VWAP tracking
        self._vwap_values: List[float] = []
        
        # Thresholds
        self._atr_high_threshold = 1.3  # ATR > 1.3x average = high volatility
        self._atr_extreme_threshold = 1.8  # ATR > 1.8x = extreme
        self._vwap_slope_threshold = 0.1  # Minimum slope for trend
    
    def set_previous_day_data(
        self,
        high: float,
        low: float,
        close: float
    ) -> None:
        """
        Set previous day OHLC data.
        
        Args:
            high: Previous day high
            low: Previous day low
            close: Previous day close
        """
        self._prev_day_high = high
        self._prev_day_low = low
        self._prev_day_close = close
        
        # Add to daily ranges for ATR calculation
        self._daily_ranges.append(high - low)
        if len(self._daily_ranges) > self._atr_lookback:
            self._daily_ranges = self._daily_ranges[-self._atr_lookback:]
    
    def update_opening_range(self, spot: SpotData) -> Optional[OpeningRange]:
        """
        Update opening range during 9:15-9:30.
        
        Args:
            spot: Current spot data
            
        Returns:
            Updated OpeningRange or None if outside OR period
        """
        current_time = datetime.now().time()
        or_start = settings.market_open_time
        or_end = settings.opening_range_end_time
        
        # Check if in OR period
        if not (or_start <= current_time <= or_end):
            # OR period ended
            if self._or_candles and not (self._opening_range and self._opening_range.captured):
                # Finalize OR
                self._finalize_opening_range()
            return self._opening_range
        
        # During OR period - collect candles
        self._or_candles.append(spot)
        
        # Calculate current OR high/low
        or_high = max(s.ohlcv.high for s in self._or_candles)
        or_low = min(s.ohlcv.low for s in self._or_candles)
        
        self._opening_range = OpeningRange(
            high=or_high,
            low=or_low,
            captured=False,
            start_time=or_start,
            end_time=or_end,
            timestamp=datetime.now(),
        )
        
        return self._opening_range
    
    def _finalize_opening_range(self) -> None:
        """Finalize opening range after 9:30."""
        if not self._or_candles:
            return
        
        or_high = max(s.ohlcv.high for s in self._or_candles)
        or_low = min(s.ohlcv.low for s in self._or_candles)
        
        self._opening_range = OpeningRange(
            high=or_high,
            low=or_low,
            captured=True,
            start_time=settings.market_open_time,
            end_time=settings.opening_range_end_time,
            timestamp=datetime.now(),
        )
    
    def calculate_atr(self, current_range: float) -> Tuple[float, float]:
        """
        Calculate current ATR and 20-day average ATR.
        
        Args:
            current_range: Today's range so far
            
        Returns:
            Tuple of (current_atr, average_atr)
        """
        if len(self._daily_ranges) < self._atr_period:
            # Not enough data, use current range
            return current_range, current_range
        
        # Use EMA for ATR calculation
        ranges = self._daily_ranges[-self._atr_period:]
        atr = np.mean(ranges)
        
        # 20-day average ATR
        all_ranges = self._daily_ranges[-self._atr_lookback:]
        avg_atr = np.mean(all_ranges)
        
        return atr, avg_atr
    
    def calculate_vwap_slope(self, prices: List[float], volumes: List[int]) -> float:
        """
        Calculate VWAP and its slope.
        
        Args:
            prices: List of prices
            volumes: List of volumes
            
        Returns:
            VWAP slope (positive = uptrend)
        """
        if len(prices) < 5 or len(volumes) < 5:
            return 0.0
        
        # Calculate cumulative VWAP points
        prices_arr = np.array(prices[-20:])
        volumes_arr = np.array(volumes[-20:])
        
        cumulative_pv = np.cumsum(prices_arr * volumes_arr)
        cumulative_v = np.cumsum(volumes_arr)
        
        # Avoid division by zero
        vwap_series = np.where(cumulative_v > 0, cumulative_pv / cumulative_v, prices_arr)
        
        # Calculate slope (linear regression)
        if len(vwap_series) >= 5:
            x = np.arange(len(vwap_series))
            slope = np.polyfit(x, vwap_series, 1)[0]
            return slope
        
        return 0.0
    
    def determine_volatility(self, atr_ratio: float, vix: VIXData) -> VolatilityLevel:
        """
        Determine volatility level based on ATR ratio and VIX.
        
        Args:
            atr_ratio: Current ATR / Average ATR
            vix: VIX data
            
        Returns:
            VolatilityLevel
        """
        # Consider both ATR and VIX
        vix_level = vix.level  # 'low', 'normal', 'elevated', 'extreme'
        
        if atr_ratio >= self._atr_extreme_threshold or vix_level == "extreme":
            return VolatilityLevel.EXTREME
        elif atr_ratio >= self._atr_high_threshold or vix_level == "elevated":
            return VolatilityLevel.HIGH
        elif atr_ratio >= 0.8 and vix_level in ["normal", "low"]:
            return VolatilityLevel.NORMAL
        else:
            return VolatilityLevel.LOW
    
    def determine_trend(
        self,
        price: float,
        vwap: float,
        vwap_slope: float,
        opening_range: Optional[OpeningRange],
    ) -> TrendDirection:
        """
        Determine trend direction.
        
        Args:
            price: Current price
            vwap: Current VWAP
            vwap_slope: VWAP slope
            opening_range: Opening range data
            
        Returns:
            TrendDirection
        """
        bullish_signals = 0
        bearish_signals = 0
        
        # Price vs VWAP
        if price > vwap * 1.001:  # Above VWAP
            bullish_signals += 1
        elif price < vwap * 0.999:  # Below VWAP
            bearish_signals += 1
        
        # VWAP slope
        if vwap_slope > self._vwap_slope_threshold:
            bullish_signals += 1
        elif vwap_slope < -self._vwap_slope_threshold:
            bearish_signals += 1
        
        # Opening range position
        if opening_range and opening_range.captured:
            if price > opening_range.high:
                bullish_signals += 1
            elif price < opening_range.low:
                bearish_signals += 1
        
        # Determine direction
        if bullish_signals >= 2:
            return TrendDirection.UP
        elif bearish_signals >= 2:
            return TrendDirection.DOWN
        else:
            return TrendDirection.SIDEWAYS
    
    def classify_regime(
        self,
        snapshot: MarketSnapshot,
        prices: List[float] = None,
        volumes: List[int] = None,
    ) -> MarketRegime:
        """
        Classify current market regime.
        
        Args:
            snapshot: Current market snapshot
            prices: Historical prices for VWAP calculation
            volumes: Historical volumes for VWAP calculation
            
        Returns:
            MarketRegime with classification and allowed setups
        """
        reasons = []
        rejection_reasons = []
        
        spot = snapshot.spot
        vix = snapshot.vix
        current_time = datetime.now().time()
        
        # Update opening range
        self.update_opening_range(spot)
        
        # Calculate today's range
        current_range = spot.ohlcv.high - spot.ohlcv.low
        
        # Calculate ATR metrics
        current_atr, avg_atr = self.calculate_atr(current_range)
        atr_ratio = current_atr / avg_atr if avg_atr > 0 else 1.0
        
        # Calculate VWAP and slope
        prices = prices or []
        volumes = volumes or []
        vwap_slope = self.calculate_vwap_slope(prices, volumes)
        
        # Calculate VWAP (simplified - use typical price)
        if prices and volumes:
            total_pv = sum(p * v for p, v in zip(prices, volumes))
            total_v = sum(volumes)
            vwap = total_pv / total_v if total_v > 0 else spot.ltp
        else:
            vwap = spot.ltp
        
        # Determine volatility
        volatility = self.determine_volatility(atr_ratio, vix)
        
        # Determine trend
        trend = self.determine_trend(spot.ltp, vwap, vwap_slope, self._opening_range)
        
        # Price vs VWAP position
        if spot.ltp > vwap * 1.002:
            price_vs_vwap = "above"
        elif spot.ltp < vwap * 0.998:
            price_vs_vwap = "below"
        else:
            price_vs_vwap = "at"
        
        # Classify regime
        regime, reasons = self._determine_regime_type(
            spot=spot,
            volatility=volatility,
            trend=trend,
            vwap_slope=vwap_slope,
            opening_range=self._opening_range,
            vix=vix,
            current_time=current_time,
        )
        
        # Determine allowed setups
        allowed_setups = self._get_allowed_setups(regime, volatility, trend)
        
        # Determine if trade is allowed
        trade_allowed, rejection_reasons = self._is_trade_allowed(
            regime=regime,
            volatility=volatility,
            vix=vix,
            current_time=current_time,
        )
        
        return MarketRegime(
            regime=regime,
            volatility=volatility,
            trend_direction=trend,
            allowed_setups=allowed_setups,
            trade_allowed=trade_allowed,
            opening_range=self._opening_range,
            atr_ratio=round(atr_ratio, 2),
            vwap_slope=round(vwap_slope, 4),
            price_vs_vwap=price_vs_vwap,
            prev_day_high=self._prev_day_high,
            prev_day_low=self._prev_day_low,
            vix_direction=vix.direction,
            vix_level=vix.level,
            regime_reasons=reasons,
            trade_rejection_reasons=rejection_reasons,
            timestamp=datetime.now(),
        )
    
    def _determine_regime_type(
        self,
        spot: SpotData,
        volatility: VolatilityLevel,
        trend: TrendDirection,
        vwap_slope: float,
        opening_range: Optional[OpeningRange],
        vix: VIXData,
        current_time: time,
    ) -> Tuple[RegimeType, List[str]]:
        """
        Determine the regime type based on all factors.
        
        Returns:
            Tuple of (RegimeType, reasons)
        """
        reasons = []
        
        # Check if in opening range period
        or_end = settings.opening_range_end_time
        if current_time <= or_end:
            reasons.append("Within opening range period (9:15-9:30)")
            return RegimeType.OPENING_RANGE, reasons
        
        # Check for extreme volatility
        if volatility == VolatilityLevel.EXTREME:
            reasons.append(f"Extreme volatility detected (VIX: {vix.value})")
            return RegimeType.VOLATILE, reasons
        
        # Check for trending conditions
        if opening_range and opening_range.captured:
            if spot.ltp > opening_range.high:
                if trend == TrendDirection.UP and vwap_slope > 0.05:
                    reasons.append("Price above OR high with positive VWAP slope")
                    reasons.append(f"Bullish trend confirmed (VWAP slope: {vwap_slope:.4f})")
                    return RegimeType.TRENDING_BULLISH, reasons
            
            elif spot.ltp < opening_range.low:
                if trend == TrendDirection.DOWN and vwap_slope < -0.05:
                    reasons.append("Price below OR low with negative VWAP slope")
                    reasons.append(f"Bearish trend confirmed (VWAP slope: {vwap_slope:.4f})")
                    return RegimeType.TRENDING_BEARISH, reasons
        
        # Check for strong trend without OR breakout
        if abs(vwap_slope) > 0.15:
            if vwap_slope > 0:
                reasons.append(f"Strong positive VWAP slope: {vwap_slope:.4f}")
                return RegimeType.TRENDING_BULLISH, reasons
            else:
                reasons.append(f"Strong negative VWAP slope: {vwap_slope:.4f}")
                return RegimeType.TRENDING_BEARISH, reasons
        
        # Check for pre-breakout (price near OR levels with volatility contraction)
        if opening_range and opening_range.captured:
            or_range = opening_range.range
            distance_to_high = abs(spot.ltp - opening_range.high)
            distance_to_low = abs(spot.ltp - opening_range.low)
            
            if min(distance_to_high, distance_to_low) < or_range * 0.3:
                if volatility == VolatilityLevel.LOW:
                    reasons.append("Price near OR levels with low volatility")
                    reasons.append("Potential breakout setup forming")
                    return RegimeType.PRE_BREAKOUT, reasons
        
        # Check for high volatility without clear trend
        if volatility == VolatilityLevel.HIGH:
            reasons.append("High volatility without clear trend")
            return RegimeType.VOLATILE, reasons
        
        # Default to range-bound
        reasons.append("No clear trend or breakout")
        reasons.append(f"Price trading within range (VWAP slope: {vwap_slope:.4f})")
        return RegimeType.RANGE_BOUND, reasons
    
    def _get_allowed_setups(
        self,
        regime: RegimeType,
        volatility: VolatilityLevel,
        trend: TrendDirection,
    ) -> List[str]:
        """
        Get allowed trade setups for current regime.
        
        Returns:
            List of allowed setup names
        """
        setups = []
        
        if regime == RegimeType.TRENDING_BULLISH:
            setups = ["pullback_to_ema9", "pullback_to_vwap", "breakout_continuation"]
            if volatility == VolatilityLevel.LOW:
                setups.append("momentum_entry")
        
        elif regime == RegimeType.TRENDING_BEARISH:
            setups = ["pullback_to_ema9", "pullback_to_vwap", "breakdown_continuation"]
            if volatility == VolatilityLevel.LOW:
                setups.append("momentum_entry")
        
        elif regime == RegimeType.RANGE_BOUND:
            setups = ["range_reversal_long", "range_reversal_short", "mean_reversion"]
        
        elif regime == RegimeType.PRE_BREAKOUT:
            setups = ["breakout_anticipation", "wait_for_confirmation"]
        
        elif regime == RegimeType.OPENING_RANGE:
            setups = ["or_breakout_long", "or_breakout_short", "or_failure_reversal"]
        
        elif regime == RegimeType.VOLATILE:
            setups = ["wait_for_clarity"]
        
        return setups
    
    def _is_trade_allowed(
        self,
        regime: RegimeType,
        volatility: VolatilityLevel,
        vix: VIXData,
        current_time: time,
    ) -> Tuple[bool, List[str]]:
        """
        Determine if trading is allowed in current conditions.
        
        Returns:
            Tuple of (is_allowed, rejection_reasons)
        """
        rejection_reasons = []
        
        # No trade during opening range
        or_end = settings.opening_range_end_time
        if current_time <= or_end:
            rejection_reasons.append("Opening range period - wait for OR completion")
            return False, rejection_reasons
        
        # No trade in extreme volatility
        if volatility == VolatilityLevel.EXTREME:
            rejection_reasons.append(f"Extreme volatility (VIX: {vix.value})")
            return False, rejection_reasons
        
        # No trade in volatile regime
        if regime == RegimeType.VOLATILE:
            rejection_reasons.append("Volatile market conditions - no clear direction")
            return False, rejection_reasons
        
        # No trade if VIX is spiking
        if vix.direction == "rising" and vix.change_pct > 10:
            rejection_reasons.append(f"VIX spiking (+{vix.change_pct:.1f}%)")
            return False, rejection_reasons
        
        # Check market close proximity (no new trades after 3:00 PM)
        close_cutoff = time(15, 0)
        if current_time >= close_cutoff:
            rejection_reasons.append("Too close to market close")
            return False, rejection_reasons
        
        return True, []
    
    def reset_day(self) -> None:
        """Reset for a new trading day."""
        self._opening_range = None
        self._or_candles = []
        self._vwap_values = []
