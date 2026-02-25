"""
Technical Confluence Scoring Engine.

Aggregates all indicator signals into a confluence score.
Trade eligibility requires score >= 7 (configurable).
"""

from datetime import datetime
from typing import List, Optional
import uuid

import pandas as pd

from src.config import settings
from src.confluence.indicators import (
    BaseIndicator,
    EMAIndicator,
    PriceActionIndicator,
    RSIIndicator,
    VolumeIndicator,
    VWAPIndicator,
)
from src.models.signal import (
    ConfluenceScore,
    IndicatorSignal,
    SignalDirection,
)


class ConfluenceEngine:
    """
    Technical Confluence Scoring Engine.
    
    Aggregates signals from multiple indicators:
    - VWAP (0-2 points)
    - EMA 9/21 (0-2 points)
    - RSI (0-2 points)
    - Volume (0-2 points)
    - Price Action (0-2 points)
    
    Total max score: 10
    Minimum eligible score: 7 (configurable)
    """
    
    def __init__(self, min_score: float = None):
        """
        Initialize confluence engine.
        
        Args:
            min_score: Minimum score for trade eligibility (default from settings)
        """
        self.min_score = min_score or settings.min_confluence_score
        
        # Initialize indicators
        self.indicators: List[BaseIndicator] = [
            VWAPIndicator(),
            EMAIndicator(fast_period=9, slow_period=21),
            RSIIndicator(period=14),
            VolumeIndicator(period=20),
            PriceActionIndicator(),
        ]
        
        self.max_score = len(self.indicators) * 2  # 10 points max
    
    def calculate_confluence(
        self,
        data: pd.DataFrame,
        regime_direction: Optional[SignalDirection] = None
    ) -> ConfluenceScore:
        """
        Calculate the confluence score from all indicators.
        
        Args:
            data: DataFrame with OHLCV columns
            regime_direction: Expected direction from regime analysis
            
        Returns:
            ConfluenceScore with detailed breakdown
        """
        signals: List[IndicatorSignal] = []
        total_score = 0.0
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0
        reasoning = []
        
        # Calculate each indicator
        for indicator in self.indicators:
            signal = indicator.calculate(data)
            signals.append(signal)
            
            # Apply score based on alignment with regime
            if regime_direction and regime_direction != SignalDirection.NEUTRAL:
                if signal.signal == regime_direction:
                    # Aligned with regime - full score
                    total_score += signal.score
                elif signal.signal == SignalDirection.NEUTRAL:
                    # Neutral - half score
                    total_score += signal.score * 0.5
                else:
                    # Against regime - no score (but not negative)
                    pass
            else:
                # No regime direction - use raw scores
                total_score += signal.score
            
            # Count signal directions
            if signal.signal == SignalDirection.LONG:
                bullish_count += 1
            elif signal.signal == SignalDirection.SHORT:
                bearish_count += 1
            else:
                neutral_count += 1
            
            reasoning.append(f"{signal.name}: {signal.reasoning}")
        
        # Determine overall direction
        if bullish_count > bearish_count + neutral_count:
            direction = SignalDirection.LONG
        elif bearish_count > bullish_count + neutral_count:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL
        
        # Check eligibility
        is_eligible = (
            total_score >= self.min_score
            and direction != SignalDirection.NEUTRAL
        )
        
        # Create result
        result = ConfluenceScore(
            total_score=round(total_score, 1),
            max_possible_score=self.max_score,
            direction=direction,
            is_eligible=is_eligible,
            bullish_count=bullish_count,
            bearish_count=bearish_count,
            neutral_count=neutral_count,
            reasoning=reasoning,
            timestamp=datetime.now(),
        )
        
        # Assign individual signals
        for signal in signals:
            if signal.name == "VWAP":
                result.vwap_signal = signal
            elif signal.name.startswith("EMA"):
                result.ema_signal = signal
            elif signal.name.startswith("RSI"):
                result.rsi_signal = signal
            elif signal.name == "Volume":
                result.volume_signal = signal
            elif signal.name == "PriceAction":
                result.price_action_signal = signal
        
        return result
    
    def get_trade_direction(
        self,
        confluence: ConfluenceScore
    ) -> Optional[SignalDirection]:
        """
        Get trade direction from confluence.
        
        Returns:
            SignalDirection if eligible, None if not
        """
        if not confluence.is_eligible:
            return None
        return confluence.direction
    
    def explain_score(self, confluence: ConfluenceScore) -> List[str]:
        """
        Generate detailed explanation of the score.
        
        Args:
            confluence: Confluence score to explain
            
        Returns:
            List of explanation strings
        """
        explanation = []
        
        # Overall status
        status = "✅ ELIGIBLE" if confluence.is_eligible else "❌ NOT ELIGIBLE"
        explanation.append(
            f"Confluence Score: {confluence.total_score}/{confluence.max_possible_score} - {status}"
        )
        
        # Direction summary
        explanation.append(
            f"Direction: {confluence.direction.value} "
            f"(Bullish: {confluence.bullish_count}, "
            f"Bearish: {confluence.bearish_count}, "
            f"Neutral: {confluence.neutral_count})"
        )
        
        # Individual indicator breakdown
        explanation.append("\nIndicator Breakdown:")
        for signal in confluence.get_all_signals():
            score_bar = "█" * int(signal.score * 2) + "░" * (4 - int(signal.score * 2))
            emoji = "🟢" if signal.signal == SignalDirection.LONG else (
                "🔴" if signal.signal == SignalDirection.SHORT else "⚪"
            )
            explanation.append(
                f"  {emoji} {signal.name}: [{score_bar}] {signal.score:.1f}/2.0"
            )
            explanation.append(f"      {signal.reasoning}")
        
        # Eligibility reasoning
        if not confluence.is_eligible:
            explanation.append("\nRejection Reasons:")
            if confluence.total_score < self.min_score:
                explanation.append(
                    f"  - Score {confluence.total_score} below minimum {self.min_score}"
                )
            if confluence.direction == SignalDirection.NEUTRAL:
                explanation.append("  - No clear directional bias")
        
        return explanation


def create_ohlcv_dataframe(
    prices: List[float],
    opens: List[float] = None,
    highs: List[float] = None,
    lows: List[float] = None,
    volumes: List[int] = None,
) -> pd.DataFrame:
    """
    Create a DataFrame from price data.
    
    Args:
        prices: List of close prices
        opens: List of open prices (optional)
        highs: List of high prices (optional)
        lows: List of low prices (optional)
        volumes: List of volumes (optional)
        
    Returns:
        DataFrame with OHLCV columns
    """
    n = len(prices)
    
    return pd.DataFrame({
        'open': opens if opens else prices,
        'high': highs if highs else [p * 1.001 for p in prices],
        'low': lows if lows else [p * 0.999 for p in prices],
        'close': prices,
        'volume': volumes if volumes else [100000] * n,
    })
