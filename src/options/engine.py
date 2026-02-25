"""
Options Intelligence Engine.

Analyzes options data to derive market intelligence:
- ΔOI (Change in Open Interest)
- ATM straddle behavior
- PCR (Put-Call Ratio) changes
- OI walls (support/resistance)
- IV expansion/crush
- Conflict resolution (conflicting signals = NO TRADE)
"""

from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np

from src.models.market_data import OptionsChain, OptionData
from src.models.signal import OptionsIntelligence, SignalDirection


class OptionsIntelligenceEngine:
    """
    Options Intelligence Engine.
    
    Analyzes options chain data to derive actionable intelligence.
    Key principle: Conflicting signals result in NO TRADE.
    """
    
    def __init__(self):
        """Initialize the options intelligence engine."""
        # Historical data for comparison
        self._prev_chain: Optional[OptionsChain] = None
        self._prev_pcr: Optional[float] = None
        self._prev_straddle: Optional[float] = None
        
        # IV historical data
        self._iv_history: List[float] = []
        self._iv_lookback = 20
        
        # Thresholds
        self._pcr_bullish_threshold = 1.2  # PCR > 1.2 = bullish
        self._pcr_bearish_threshold = 0.8  # PCR < 0.8 = bearish
        self._oi_significant_change_pct = 5  # 5% change is significant
    
    def analyze(
        self,
        chain: OptionsChain,
        spot_price: float,
    ) -> OptionsIntelligence:
        """
        Analyze options chain for intelligence.
        
        Args:
            chain: Current options chain
            spot_price: Current spot price
            
        Returns:
            OptionsIntelligence with full analysis
        """
        reasoning = []
        conflict_reasons = []
        
        # Calculate core metrics
        current_pcr = chain.pcr
        atm_straddle = chain.atm_straddle_premium
        
        # Get ATM IV
        atm_call = chain.atm_call
        atm_put = chain.atm_put
        atm_iv = ((atm_call.greeks.iv if atm_call else 0) + 
                  (atm_put.greeks.iv if atm_put else 0)) / 2
        
        # Store IV for percentile calculation
        self._iv_history.append(atm_iv)
        if len(self._iv_history) > self._iv_lookback:
            self._iv_history = self._iv_history[-self._iv_lookback:]
        
        # Analyze OI changes
        delta_oi_calls, delta_oi_puts, oi_buildup = self._analyze_oi_changes(
            chain, reasoning
        )
        
        # Analyze PCR
        pcr_change = 0.0
        pcr_interpretation = "neutral"
        if self._prev_pcr is not None:
            pcr_change = current_pcr - self._prev_pcr
            pcr_interpretation = self._interpret_pcr(current_pcr, pcr_change, reasoning)
        else:
            pcr_interpretation = self._interpret_pcr(current_pcr, 0, reasoning)
        
        # Analyze straddle
        straddle_change = 0.0
        if self._prev_straddle is not None:
            straddle_change = atm_straddle - self._prev_straddle
        
        # Analyze IV
        iv_percentile = self._calculate_iv_percentile(atm_iv)
        iv_status = self._get_iv_status(iv_percentile)
        iv_trend = self._get_iv_trend(atm_iv)
        
        # Get OI walls
        oi_walls = chain.get_oi_walls()
        call_wall = oi_walls["call_walls"][0] if oi_walls["call_walls"] else (0, 0)
        put_wall = oi_walls["put_walls"][0] if oi_walls["put_walls"] else (0, 0)
        
        # Calculate max pain
        max_pain = chain.get_max_pain()
        distance_to_max_pain = spot_price - max_pain
        
        # Determine direction signals
        direction_signals = []
        
        # From OI buildup
        if oi_buildup in ["long_buildup", "short_covering"]:
            direction_signals.append(SignalDirection.LONG)
        elif oi_buildup in ["short_buildup", "long_unwinding"]:
            direction_signals.append(SignalDirection.SHORT)
        
        # From PCR
        if pcr_interpretation == "bullish":
            direction_signals.append(SignalDirection.LONG)
        elif pcr_interpretation == "bearish":
            direction_signals.append(SignalDirection.SHORT)
        
        # From OI walls
        wall_direction = self._analyze_oi_walls(
            spot_price, call_wall[0], put_wall[0], reasoning
        )
        if wall_direction:
            direction_signals.append(wall_direction)
        
        # Conflict detection
        has_conflict = self._detect_conflicts(
            direction_signals, oi_buildup, pcr_interpretation, iv_trend,
            conflict_reasons
        )
        
        # Determine final direction
        if has_conflict:
            direction = SignalDirection.NEUTRAL
            reasoning.append("⚠️ Conflicting signals detected - NO TRADE")
        else:
            direction = self._aggregate_direction(direction_signals)
        
        # Calculate confidence
        confidence = self._calculate_confidence(
            direction_signals, conflict_reasons, iv_status
        )
        
        # Store for next comparison
        self._prev_chain = chain
        self._prev_pcr = current_pcr
        self._prev_straddle = atm_straddle
        
        return OptionsIntelligence(
            direction=direction,
            confidence=confidence,
            delta_oi_calls=delta_oi_calls,
            delta_oi_puts=delta_oi_puts,
            oi_buildup_type=oi_buildup,
            atm_straddle_premium=round(atm_straddle, 2),
            atm_straddle_change=round(straddle_change, 2),
            atm_iv=round(atm_iv, 2),
            current_pcr=round(current_pcr, 3),
            pcr_change=round(pcr_change, 3),
            pcr_interpretation=pcr_interpretation,
            call_wall_strike=call_wall[0],
            call_wall_oi=call_wall[1],
            put_wall_strike=put_wall[0],
            put_wall_oi=put_wall[1],
            iv_percentile=round(iv_percentile, 1),
            iv_status=iv_status,
            iv_trend=iv_trend,
            max_pain_strike=max_pain,
            distance_to_max_pain=round(distance_to_max_pain, 2),
            has_conflict=has_conflict,
            conflict_reasons=conflict_reasons,
            reasoning=reasoning,
            timestamp=datetime.now(),
        )
    
    def _analyze_oi_changes(
        self,
        chain: OptionsChain,
        reasoning: List[str],
    ) -> Tuple[int, int, str]:
        """
        Analyze OI changes to determine buildup type.
        
        Returns:
            (delta_calls, delta_puts, buildup_type)
        """
        total_call_oi_change = sum(c.oi_change for c in chain.calls)
        total_put_oi_change = sum(p.oi_change for p in chain.puts)
        
        # Determine buildup type
        buildup = "neutral"
        
        # Get price direction (simplified - check ATM straddle change)
        price_up = chain.spot_price > chain.atm_strike
        
        if total_call_oi_change > 0 and total_put_oi_change > 0:
            # Both increasing
            if total_put_oi_change > total_call_oi_change:
                buildup = "long_buildup"  # Put writers adding = bullish
                reasoning.append(
                    f"Long buildup: Both OI increasing, puts +{total_put_oi_change} > calls +{total_call_oi_change}"
                )
            else:
                buildup = "short_buildup"  # Call writers adding = bearish
                reasoning.append(
                    f"Short buildup: Both OI increasing, calls +{total_call_oi_change} > puts +{total_put_oi_change}"
                )
        
        elif total_call_oi_change < 0 and total_put_oi_change < 0:
            # Both decreasing
            if abs(total_call_oi_change) > abs(total_put_oi_change):
                buildup = "short_covering"  # Call unwinding = bullish
                reasoning.append(
                    f"Short covering: Call OI unwinding {total_call_oi_change}"
                )
            else:
                buildup = "long_unwinding"  # Put unwinding = bearish
                reasoning.append(
                    f"Long unwinding: Put OI unwinding {total_put_oi_change}"
                )
        
        elif total_put_oi_change > 0 and total_call_oi_change <= 0:
            buildup = "long_buildup"
            reasoning.append(f"Put OI building (+{total_put_oi_change}) - bullish signal")
        
        elif total_call_oi_change > 0 and total_put_oi_change <= 0:
            buildup = "short_buildup"
            reasoning.append(f"Call OI building (+{total_call_oi_change}) - bearish signal")
        
        return total_call_oi_change, total_put_oi_change, buildup
    
    def _interpret_pcr(
        self,
        pcr: float,
        change: float,
        reasoning: List[str],
    ) -> str:
        """Interpret PCR value and change."""
        if pcr > self._pcr_bullish_threshold:
            reasoning.append(f"PCR {pcr:.2f} > {self._pcr_bullish_threshold} - Bullish (put writers active)")
            return "bullish"
        elif pcr < self._pcr_bearish_threshold:
            reasoning.append(f"PCR {pcr:.2f} < {self._pcr_bearish_threshold} - Bearish (call writers active)")
            return "bearish"
        else:
            reasoning.append(f"PCR {pcr:.2f} - Neutral range")
            return "neutral"
    
    def _analyze_oi_walls(
        self,
        spot: float,
        call_wall: float,
        put_wall: float,
        reasoning: List[str],
    ) -> Optional[SignalDirection]:
        """Analyze OI walls for direction."""
        if call_wall == 0 or put_wall == 0:
            return None
        
        distance_to_call = call_wall - spot
        distance_to_put = spot - put_wall
        
        # Check which wall is closer
        if distance_to_call > 0 and distance_to_put > 0:
            if distance_to_call < distance_to_put:
                reasoning.append(
                    f"Call wall at {call_wall} is closer ({distance_to_call:.0f} pts) - resistance ahead"
                )
                return SignalDirection.SHORT  # Resistance nearby
            else:
                reasoning.append(
                    f"Put wall at {put_wall} is closer ({distance_to_put:.0f} pts) - support nearby"
                )
                return SignalDirection.LONG  # Support nearby
        
        return None
    
    def _calculate_iv_percentile(self, current_iv: float) -> float:
        """Calculate IV percentile rank."""
        if len(self._iv_history) < 5:
            return 50.0
        
        sorted_ivs = sorted(self._iv_history)
        rank = sum(1 for iv in sorted_ivs if iv < current_iv)
        return (rank / len(sorted_ivs)) * 100
    
    def _get_iv_status(self, percentile: float) -> str:
        """Get IV status from percentile."""
        if percentile < 20:
            return "low"
        elif percentile < 50:
            return "normal"
        elif percentile < 80:
            return "elevated"
        else:
            return "extreme"
    
    def _get_iv_trend(self, current_iv: float) -> str:
        """Determine IV trend."""
        if len(self._iv_history) < 3:
            return "stable"
        
        recent = self._iv_history[-3:]
        if all(recent[i] < recent[i+1] for i in range(len(recent)-1)):
            return "expanding"
        elif all(recent[i] > recent[i+1] for i in range(len(recent)-1)):
            return "contracting"
        return "stable"
    
    def _detect_conflicts(
        self,
        direction_signals: List[SignalDirection],
        oi_buildup: str,
        pcr_interpretation: str,
        iv_trend: str,
        conflict_reasons: List[str],
    ) -> bool:
        """
        Detect conflicting signals.
        
        Key principle: Conflicts = NO TRADE
        """
        has_conflict = False
        
        # Check for mixed direction signals
        long_signals = sum(1 for s in direction_signals if s == SignalDirection.LONG)
        short_signals = sum(1 for s in direction_signals if s == SignalDirection.SHORT)
        
        if long_signals > 0 and short_signals > 0:
            has_conflict = True
            conflict_reasons.append(
                f"Mixed direction signals: {long_signals} bullish, {short_signals} bearish"
            )
        
        # Check OI vs PCR conflict
        if oi_buildup in ["long_buildup", "short_covering"] and pcr_interpretation == "bearish":
            has_conflict = True
            conflict_reasons.append(
                f"OI shows {oi_buildup} but PCR is bearish"
            )
        elif oi_buildup in ["short_buildup", "long_unwinding"] and pcr_interpretation == "bullish":
            has_conflict = True
            conflict_reasons.append(
                f"OI shows {oi_buildup} but PCR is bullish"
            )
        
        # IV expanding with unclear direction = caution
        if iv_trend == "expanding" and len(set(direction_signals)) > 1:
            has_conflict = True
            conflict_reasons.append(
                "IV expanding with unclear direction - market uncertainty"
            )
        
        return has_conflict
    
    def _aggregate_direction(
        self,
        signals: List[SignalDirection],
    ) -> SignalDirection:
        """Aggregate multiple direction signals."""
        if not signals:
            return SignalDirection.NEUTRAL
        
        long_count = sum(1 for s in signals if s == SignalDirection.LONG)
        short_count = sum(1 for s in signals if s == SignalDirection.SHORT)
        
        if long_count > short_count:
            return SignalDirection.LONG
        elif short_count > long_count:
            return SignalDirection.SHORT
        return SignalDirection.NEUTRAL
    
    def _calculate_confidence(
        self,
        direction_signals: List[SignalDirection],
        conflicts: List[str],
        iv_status: str,
    ) -> float:
        """Calculate confidence score (0-1)."""
        if conflicts:
            return 0.0
        
        if not direction_signals:
            return 0.0
        
        # Base confidence from signal agreement
        total = len(direction_signals)
        dominant = max(
            sum(1 for s in direction_signals if s == SignalDirection.LONG),
            sum(1 for s in direction_signals if s == SignalDirection.SHORT),
        )
        
        agreement_ratio = dominant / total if total > 0 else 0
        
        # Adjust for IV status
        iv_multiplier = {
            "low": 0.8,  # Low IV = lower confidence
            "normal": 1.0,
            "elevated": 0.9,
            "extreme": 0.7,
        }
        
        confidence = agreement_ratio * iv_multiplier.get(iv_status, 1.0)
        return round(min(confidence, 1.0), 2)
    
    def reset_day(self) -> None:
        """Reset for new trading day."""
        self._prev_chain = None
        self._prev_pcr = None
        self._prev_straddle = None
        # Keep IV history for percentile calculations
