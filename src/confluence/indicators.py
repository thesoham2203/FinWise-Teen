"""
Technical Indicators Module.

Implements individual technical indicators with zone-based analysis.
Uses pandas-ta for calculations where appropriate.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

try:
    import pandas_ta as ta
except ImportError:
    ta = None

from src.models.signal import IndicatorSignal, SignalDirection


class BaseIndicator(ABC):
    """Abstract base class for indicators."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Indicator name."""
        pass
    
    @abstractmethod
    def calculate(self, data: pd.DataFrame) -> IndicatorSignal:
        """
        Calculate indicator signal.
        
        Args:
            data: DataFrame with OHLCV columns
            
        Returns:
            IndicatorSignal with score and direction
        """
        pass


@dataclass
class VWAPBands:
    """VWAP with standard deviation bands."""
    vwap: float
    upper_1: float  # +1 SD
    lower_1: float  # -1 SD
    upper_2: float  # +2 SD
    lower_2: float  # -2 SD


class VWAPIndicator(BaseIndicator):
    """
    VWAP Indicator with deviation bands.
    
    Signals:
    - Price above VWAP but below +1SD: Bullish (score 1)
    - Price above +1SD: Strong bullish but extended (score 0.5)
    - Price below VWAP but above -1SD: Bearish (score 1)
    - Price below -1SD: Strong bearish but extended (score 0.5)
    - Price at VWAP: Neutral (score 0)
    """
    
    @property
    def name(self) -> str:
        return "VWAP"
    
    def calculate(self, data: pd.DataFrame) -> IndicatorSignal:
        """Calculate VWAP signal."""
        if data is None or len(data) < 5:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning="Insufficient data for VWAP calculation"
            )
        
        # Calculate VWAP
        vwap_data = self._calculate_vwap(data)
        current_price = data['close'].iloc[-1]
        
        if vwap_data is None:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning="Failed to calculate VWAP"
            )
        
        # Determine signal based on position relative to VWAP bands
        signal, score, reason = self._get_signal(current_price, vwap_data)
        
        return IndicatorSignal(
            name=self.name,
            signal=signal,
            score=score,
            value=vwap_data.vwap,
            reasoning=reason
        )
    
    def _calculate_vwap(self, data: pd.DataFrame) -> Optional[VWAPBands]:
        """Calculate VWAP and deviation bands."""
        try:
            # Typical price
            typical_price = (data['high'] + data['low'] + data['close']) / 3
            
            # VWAP calculation
            cumulative_tp_vol = (typical_price * data['volume']).cumsum()
            cumulative_vol = data['volume'].cumsum()
            
            vwap_series = cumulative_tp_vol / cumulative_vol
            vwap = vwap_series.iloc[-1]
            
            # Standard deviation for bands
            squared_diff = ((typical_price - vwap_series) ** 2 * data['volume']).cumsum()
            variance = squared_diff / cumulative_vol
            std = np.sqrt(variance.iloc[-1])
            
            return VWAPBands(
                vwap=vwap,
                upper_1=vwap + std,
                lower_1=vwap - std,
                upper_2=vwap + 2 * std,
                lower_2=vwap - 2 * std,
            )
        except Exception:
            return None
    
    def _get_signal(
        self,
        price: float,
        bands: VWAPBands
    ) -> Tuple[SignalDirection, float, str]:
        """Get signal based on price position."""
        if price > bands.upper_2:
            return (
                SignalDirection.LONG,
                0.5,
                f"Price ({price:.2f}) extended above +2SD ({bands.upper_2:.2f})"
            )
        elif price > bands.upper_1:
            return (
                SignalDirection.LONG,
                1.0,
                f"Price ({price:.2f}) between +1SD and +2SD"
            )
        elif price > bands.vwap:
            return (
                SignalDirection.LONG,
                1.5,
                f"Price ({price:.2f}) above VWAP ({bands.vwap:.2f})"
            )
        elif price < bands.lower_2:
            return (
                SignalDirection.SHORT,
                0.5,
                f"Price ({price:.2f}) extended below -2SD ({bands.lower_2:.2f})"
            )
        elif price < bands.lower_1:
            return (
                SignalDirection.SHORT,
                1.0,
                f"Price ({price:.2f}) between -1SD and -2SD"
            )
        elif price < bands.vwap:
            return (
                SignalDirection.SHORT,
                1.5,
                f"Price ({price:.2f}) below VWAP ({bands.vwap:.2f})"
            )
        else:
            return (
                SignalDirection.NEUTRAL,
                0,
                f"Price ({price:.2f}) at VWAP ({bands.vwap:.2f})"
            )


class EMAIndicator(BaseIndicator):
    """
    EMA 9/21 Indicator.
    
    Signals:
    - EMA9 > EMA21 with price > EMA9: Strong bullish (score 2)
    - EMA9 > EMA21 with price between EMAs: Bullish (score 1)
    - EMA9 < EMA21 with price < EMA9: Strong bearish (score 2)
    - EMA9 < EMA21 with price between EMAs: Bearish (score 1)
    - EMAs crossed recently: Potential reversal (score 0.5)
    """
    
    def __init__(self, fast_period: int = 9, slow_period: int = 21):
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    @property
    def name(self) -> str:
        return f"EMA_{self.fast_period}/{self.slow_period}"
    
    def calculate(self, data: pd.DataFrame) -> IndicatorSignal:
        """Calculate EMA crossover signal."""
        min_periods = self.slow_period + 5
        
        if data is None or len(data) < min_periods:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning=f"Insufficient data (need {min_periods} periods)"
            )
        
        # Calculate EMAs
        ema_fast = data['close'].ewm(span=self.fast_period, adjust=False).mean()
        ema_slow = data['close'].ewm(span=self.slow_period, adjust=False).mean()
        
        current_price = data['close'].iloc[-1]
        current_ema_fast = ema_fast.iloc[-1]
        current_ema_slow = ema_slow.iloc[-1]
        
        # Previous values for crossover detection
        prev_ema_fast = ema_fast.iloc[-2]
        prev_ema_slow = ema_slow.iloc[-2]
        
        # Determine signal
        signal, score, reason = self._get_signal(
            price=current_price,
            ema_fast=current_ema_fast,
            ema_slow=current_ema_slow,
            prev_ema_fast=prev_ema_fast,
            prev_ema_slow=prev_ema_slow,
        )
        
        return IndicatorSignal(
            name=self.name,
            signal=signal,
            score=score,
            value=current_ema_fast,
            reasoning=reason
        )
    
    def _get_signal(
        self,
        price: float,
        ema_fast: float,
        ema_slow: float,
        prev_ema_fast: float,
        prev_ema_slow: float,
    ) -> Tuple[SignalDirection, float, str]:
        """Get signal based on EMA positions."""
        # Check for recent crossover
        bullish_cross = prev_ema_fast <= prev_ema_slow and ema_fast > ema_slow
        bearish_cross = prev_ema_fast >= prev_ema_slow and ema_fast < ema_slow
        
        if bullish_cross:
            return (
                SignalDirection.LONG,
                2.0,
                f"Bullish EMA crossover! EMA{self.fast_period} crossed above EMA{self.slow_period}"
            )
        
        if bearish_cross:
            return (
                SignalDirection.SHORT,
                2.0,
                f"Bearish EMA crossover! EMA{self.fast_period} crossed below EMA{self.slow_period}"
            )
        
        # No crossover - check alignment
        if ema_fast > ema_slow:
            if price > ema_fast:
                return (
                    SignalDirection.LONG,
                    1.5,
                    f"Strong bullish: Price > EMA{self.fast_period} > EMA{self.slow_period}"
                )
            elif price > ema_slow:
                return (
                    SignalDirection.LONG,
                    1.0,
                    f"Bullish pullback: Price between EMAs, trend is up"
                )
            else:
                return (
                    SignalDirection.NEUTRAL,
                    0.5,
                    f"Potential trend weakening: Price below both EMAs"
                )
        else:  # ema_fast <= ema_slow
            if price < ema_fast:
                return (
                    SignalDirection.SHORT,
                    1.5,
                    f"Strong bearish: Price < EMA{self.fast_period} < EMA{self.slow_period}"
                )
            elif price < ema_slow:
                return (
                    SignalDirection.SHORT,
                    1.0,
                    f"Bearish pullback: Price between EMAs, trend is down"
                )
            else:
                return (
                    SignalDirection.NEUTRAL,
                    0.5,
                    f"Potential reversal: Price above both EMAs in downtrend"
                )


class RSIIndicator(BaseIndicator):
    """
    RSI Zone-based Indicator.
    
    Zones:
    - Oversold (<30): Bullish reversal potential
    - Neutral-Low (30-45): Slight bearish bias
    - Neutral (45-55): No bias
    - Neutral-High (55-70): Slight bullish bias
    - Overbought (>70): Bearish reversal potential
    
    Signals consider trend context for better accuracy.
    """
    
    def __init__(self, period: int = 14):
        self.period = period
    
    @property
    def name(self) -> str:
        return f"RSI_{self.period}"
    
    def calculate(self, data: pd.DataFrame) -> IndicatorSignal:
        """Calculate RSI signal."""
        min_periods = self.period + 5
        
        if data is None or len(data) < min_periods:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning=f"Insufficient data (need {min_periods} periods)"
            )
        
        # Calculate RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        current_rsi = rsi.iloc[-1]
        prev_rsi = rsi.iloc[-2] if len(rsi) > 1 else current_rsi
        
        # Determine signal based on zone
        signal, score, reason = self._get_signal(current_rsi, prev_rsi)
        
        return IndicatorSignal(
            name=self.name,
            signal=signal,
            score=score,
            value=current_rsi,
            reasoning=reason
        )
    
    def _get_signal(
        self,
        rsi: float,
        prev_rsi: float
    ) -> Tuple[SignalDirection, float, str]:
        """Get signal based on RSI zone."""
        rsi_direction = "rising" if rsi > prev_rsi else "falling"
        
        if rsi < 25:
            return (
                SignalDirection.LONG,
                2.0,
                f"RSI {rsi:.1f} - Strongly oversold, reversal likely ({rsi_direction})"
            )
        elif rsi < 30:
            return (
                SignalDirection.LONG,
                1.5,
                f"RSI {rsi:.1f} - Oversold zone ({rsi_direction})"
            )
        elif rsi < 40:
            return (
                SignalDirection.LONG,
                0.5 if rsi_direction == "rising" else 0,
                f"RSI {rsi:.1f} - Lower neutral zone ({rsi_direction})"
            )
        elif rsi < 60:
            return (
                SignalDirection.NEUTRAL,
                0,
                f"RSI {rsi:.1f} - Neutral zone ({rsi_direction})"
            )
        elif rsi < 70:
            return (
                SignalDirection.SHORT,
                0.5 if rsi_direction == "falling" else 0,
                f"RSI {rsi:.1f} - Upper neutral zone ({rsi_direction})"
            )
        elif rsi < 75:
            return (
                SignalDirection.SHORT,
                1.5,
                f"RSI {rsi:.1f} - Overbought zone ({rsi_direction})"
            )
        else:
            return (
                SignalDirection.SHORT,
                2.0,
                f"RSI {rsi:.1f} - Strongly overbought, reversal likely ({rsi_direction})"
            )


class VolumeIndicator(BaseIndicator):
    """
    Volume Analysis Indicator.
    
    Compares current volume to 20-period average and analyzes
    volume trends relative to price movement.
    """
    
    def __init__(self, period: int = 20):
        self.period = period
    
    @property
    def name(self) -> str:
        return "Volume"
    
    def calculate(self, data: pd.DataFrame) -> IndicatorSignal:
        """Calculate volume signal."""
        if data is None or len(data) < self.period:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning=f"Insufficient data (need {self.period} periods)"
            )
        
        current_volume = data['volume'].iloc[-1]
        avg_volume = data['volume'].rolling(window=self.period).mean().iloc[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1.0
        
        # Price direction
        price_change = data['close'].iloc[-1] - data['close'].iloc[-2]
        price_up = price_change > 0
        
        # Determine signal
        signal, score, reason = self._get_signal(volume_ratio, price_up)
        
        return IndicatorSignal(
            name=self.name,
            signal=signal,
            score=score,
            value=volume_ratio,
            reasoning=reason
        )
    
    def _get_signal(
        self,
        volume_ratio: float,
        price_up: bool
    ) -> Tuple[SignalDirection, float, str]:
        """Get signal based on volume analysis."""
        if volume_ratio > 2.0:
            # Very high volume
            if price_up:
                return (
                    SignalDirection.LONG,
                    2.0,
                    f"Very high volume ({volume_ratio:.1f}x avg) with price up - strong buying"
                )
            else:
                return (
                    SignalDirection.SHORT,
                    2.0,
                    f"Very high volume ({volume_ratio:.1f}x avg) with price down - strong selling"
                )
        elif volume_ratio > 1.5:
            # Above average volume
            if price_up:
                return (
                    SignalDirection.LONG,
                    1.5,
                    f"Above average volume ({volume_ratio:.1f}x) confirming upward move"
                )
            else:
                return (
                    SignalDirection.SHORT,
                    1.5,
                    f"Above average volume ({volume_ratio:.1f}x) confirming downward move"
                )
        elif volume_ratio > 0.8:
            # Normal volume
            return (
                SignalDirection.NEUTRAL,
                0.5,
                f"Normal volume ({volume_ratio:.1f}x avg)"
            )
        else:
            # Low volume - weak conviction
            return (
                SignalDirection.NEUTRAL,
                0,
                f"Low volume ({volume_ratio:.1f}x avg) - weak conviction"
            )


class PriceActionIndicator(BaseIndicator):
    """
    Price Action Pattern Indicator.
    
    Analyzes candlestick patterns and price structure.
    """
    
    @property
    def name(self) -> str:
        return "PriceAction"
    
    def calculate(self, data: pd.DataFrame) -> IndicatorSignal:
        """Calculate price action signal."""
        if data is None or len(data) < 5:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning="Insufficient data for price action analysis"
            )
        
        # Get last few candles
        last_candle = data.iloc[-1]
        prev_candle = data.iloc[-2]
        
        # Calculate candle properties
        body = abs(last_candle['close'] - last_candle['open'])
        range_size = last_candle['high'] - last_candle['low']
        body_ratio = body / range_size if range_size > 0 else 0
        
        is_bullish = last_candle['close'] > last_candle['open']
        is_bearish = last_candle['close'] < last_candle['open']
        
        # Upper and lower wicks
        if is_bullish:
            upper_wick = last_candle['high'] - last_candle['close']
            lower_wick = last_candle['open'] - last_candle['low']
        else:
            upper_wick = last_candle['high'] - last_candle['open']
            lower_wick = last_candle['close'] - last_candle['low']
        
        # Analyze patterns
        signals = []
        
        # Large bullish candle
        if is_bullish and body_ratio > 0.7:
            signals.append(("LONG", 1.0, "Strong bullish candle with large body"))
        
        # Large bearish candle
        if is_bearish and body_ratio > 0.7:
            signals.append(("SHORT", 1.0, "Strong bearish candle with large body"))
        
        # Hammer (bullish reversal)
        if lower_wick > body * 2 and upper_wick < body * 0.5:
            signals.append(("LONG", 1.5, "Hammer pattern - potential bullish reversal"))
        
        # Shooting star (bearish reversal)
        if upper_wick > body * 2 and lower_wick < body * 0.5:
            signals.append(("SHORT", 1.5, "Shooting star pattern - potential bearish reversal"))
        
        # Engulfing patterns
        prev_body = abs(prev_candle['close'] - prev_candle['open'])
        if body > prev_body * 1.5:
            if is_bullish and prev_candle['close'] < prev_candle['open']:
                signals.append(("LONG", 2.0, "Bullish engulfing pattern"))
            elif is_bearish and prev_candle['close'] > prev_candle['open']:
                signals.append(("SHORT", 2.0, "Bearish engulfing pattern"))
        
        # Doji (indecision)
        if body_ratio < 0.1:
            signals.append(("NEUTRAL", 0.5, "Doji - market indecision"))
        
        # Aggregate signals
        if not signals:
            return IndicatorSignal(
                name=self.name,
                signal=SignalDirection.NEUTRAL,
                score=0,
                reasoning="No significant price action patterns"
            )
        
        # Take the highest score signal
        best_signal = max(signals, key=lambda x: x[1])
        direction = SignalDirection.LONG if best_signal[0] == "LONG" else (
            SignalDirection.SHORT if best_signal[0] == "SHORT" else SignalDirection.NEUTRAL
        )
        
        return IndicatorSignal(
            name=self.name,
            signal=direction,
            score=best_signal[1],
            reasoning=best_signal[2]
        )
