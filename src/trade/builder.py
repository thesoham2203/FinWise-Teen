"""
Trade Construction Engine.

Builds complete trade plans with:
- Entry zone calculation
- Stop-loss determination (ATR-based)
- Target calculation (Fibonacci-based)
- Risk-Reward validation (reject if < 1:2)
- Position sizing based on risk
"""

from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import uuid

from src.config import settings
from src.models.market_data import MarketSnapshot
from src.models.regime import MarketRegime
from src.models.signal import ConfluenceScore, OptionsIntelligence, SignalDirection, TradeSignal
from src.models.trade import (
    EntryZone,
    InstrumentType,
    TradePlan,
    TradeDirection,
    TradeStatus,
)


class TradeBuilder:
    """
    Trade Construction Engine.
    
    Builds complete trade plans from signals.
    Key rule: Reject trades with RR < 1:2
    """
    
    def __init__(
        self,
        capital: float = None,
        risk_per_trade_pct: float = None,
        min_risk_reward: float = None,
    ):
        """
        Initialize trade builder.
        
        Args:
            capital: Trading capital (default from settings)
            risk_per_trade_pct: Risk per trade as % (default from settings)
            min_risk_reward: Minimum risk-reward ratio (default from settings)
        """
        self.capital = capital or settings.trading_capital
        self.risk_per_trade_pct = risk_per_trade_pct or settings.max_risk_per_trade_pct
        self.min_risk_reward = min_risk_reward or settings.min_risk_reward
        
        # Bank Nifty lot size
        self.lot_size = 15
        
        # Position sizing
        self.max_risk_amount = self.capital * (self.risk_per_trade_pct / 100)
    
    def build_trade_plan(
        self,
        signal: TradeSignal,
        snapshot: MarketSnapshot,
        regime: MarketRegime,
        confluence: ConfluenceScore,
        options_intel: OptionsIntelligence,
    ) -> Optional[TradePlan]:
        """
        Build a complete trade plan from a signal.
        
        Args:
            signal: Trade signal
            snapshot: Current market snapshot
            regime: Market regime
            confluence: Confluence score
            options_intel: Options intelligence
            
        Returns:
            TradePlan if valid, None if rejected
        """
        if not signal.is_valid:
            return None
        
        # Determine instrument
        instrument, instrument_type = self._select_instrument(
            signal.direction,
            snapshot,
            options_intel,
        )
        
        # Get current price
        current_price = self._get_instrument_price(instrument_type, snapshot)
        
        # Calculate entry zone
        entry_zone = self._calculate_entry_zone(
            current_price=current_price,
            direction=self._to_trade_direction(signal.direction),
            regime=regime,
            snapshot=snapshot,
        )
        
        # Calculate stop loss
        stop_loss = self._calculate_stop_loss(
            entry_price=entry_zone.optimal,
            direction=self._to_trade_direction(signal.direction),
            regime=regime,
            snapshot=snapshot,
        )
        
        # Calculate targets
        target_1, target_2 = self._calculate_targets(
            entry_price=entry_zone.optimal,
            stop_loss=stop_loss,
            direction=self._to_trade_direction(signal.direction),
        )
        
        # Calculate risk metrics
        risk_points = abs(entry_zone.optimal - stop_loss)
        reward_t1_points = abs(target_1 - entry_zone.optimal)
        reward_t2_points = abs(target_2 - entry_zone.optimal)
        
        risk_reward_t1 = reward_t1_points / risk_points if risk_points > 0 else 0
        risk_reward_t2 = reward_t2_points / risk_points if risk_points > 0 else 0
        
        # Position sizing
        position_size = self._calculate_position_size(
            risk_points=risk_points,
            instrument_type=instrument_type,
        )
        
        # Calculate risk amount
        risk_amount = risk_points * position_size * self.lot_size
        
        # Validate trade
        is_valid, rejection_reasons = self._validate_trade(
            risk_reward_t2=risk_reward_t2,
            risk_amount=risk_amount,
            position_size=position_size,
            regime=regime,
        )
        
        # Build reasoning
        reasoning = self._build_reasoning(
            signal=signal,
            regime=regime,
            confluence=confluence,
            options_intel=options_intel,
        )
        
        # Create trade plan
        plan = TradePlan(
            plan_id=str(uuid.uuid4()),
            signal_id=signal.signal_id,
            instrument=instrument,
            instrument_type=instrument_type,
            direction=self._to_trade_direction(signal.direction),
            entry_zone=entry_zone,
            stop_loss=round(stop_loss, 2),
            target_1=round(target_1, 2),
            target_2=round(target_2, 2),
            risk_points=round(risk_points, 2),
            reward_t1_points=round(reward_t1_points, 2),
            reward_t2_points=round(reward_t2_points, 2),
            risk_reward_t1=round(risk_reward_t1, 2),
            risk_reward_t2=round(risk_reward_t2, 2),
            position_size=position_size,
            lot_size=self.lot_size,
            risk_amount=round(risk_amount, 2),
            status=TradeStatus.PENDING if is_valid else TradeStatus.REJECTED,
            is_valid=is_valid,
            rejection_reasons=rejection_reasons,
            reasoning=reasoning,
            confidence=signal.total_score / 30,  # Normalize to 0-1
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=30),
        )
        
        return plan
    
    def _select_instrument(
        self,
        direction: SignalDirection,
        snapshot: MarketSnapshot,
        options_intel: OptionsIntelligence,
    ) -> Tuple[str, InstrumentType]:
        """
        Select the best instrument for the trade.
        
        Logic:
        - Use futures for trending markets
        - Use options for volatile or uncertain markets
        """
        # For now, default to futures for simplicity
        # In production, this could be more sophisticated
        
        # Get futures symbol
        futures_symbol = snapshot.futures.symbol
        
        # Check if options might be better
        if options_intel.iv_status == "extreme" or options_intel.has_conflict:
            # High IV or conflicts - consider options for defined risk
            chain = snapshot.options_chain
            if direction == SignalDirection.LONG:
                # Buy CE for bullish view
                atm_call = chain.atm_call
                if atm_call:
                    return atm_call.symbol, InstrumentType.CALL_OPTION
            else:
                # Buy PE for bearish view
                atm_put = chain.atm_put
                if atm_put:
                    return atm_put.symbol, InstrumentType.PUT_OPTION
        
        return futures_symbol, InstrumentType.FUTURES
    
    def _get_instrument_price(
        self,
        instrument_type: InstrumentType,
        snapshot: MarketSnapshot,
    ) -> float:
        """Get current price for instrument type."""
        if instrument_type == InstrumentType.FUTURES:
            return snapshot.futures.ltp
        elif instrument_type == InstrumentType.CALL_OPTION:
            atm_call = snapshot.options_chain.atm_call
            return atm_call.ltp if atm_call else 0
        elif instrument_type == InstrumentType.PUT_OPTION:
            atm_put = snapshot.options_chain.atm_put
            return atm_put.ltp if atm_put else 0
        return 0
    
    def _calculate_entry_zone(
        self,
        current_price: float,
        direction: TradeDirection,
        regime: MarketRegime,
        snapshot: MarketSnapshot,
    ) -> EntryZone:
        """
        Calculate optimal entry zone.
        
        Uses structure levels and ATR for zone width.
        """
        # Calculate ATR-based buffer
        if snapshot.spot.ohlcv.range > 0:
            atr_estimate = snapshot.spot.ohlcv.range * 0.5
        else:
            atr_estimate = current_price * 0.002  # 0.2% default
        
        # Zone width based on volatility
        zone_width = atr_estimate * 0.3
        
        if direction == TradeDirection.LONG:
            # For long, we want to buy on dips
            lower = current_price - zone_width
            upper = current_price
            optimal = current_price - (zone_width * 0.3)  # Slight pullback ideal
        else:
            # For short, we want to sell on rallies
            lower = current_price
            upper = current_price + zone_width
            optimal = current_price + (zone_width * 0.3)
        
        return EntryZone(
            lower=round(lower, 2),
            upper=round(upper, 2),
            optimal=round(optimal, 2),
        )
    
    def _calculate_stop_loss(
        self,
        entry_price: float,
        direction: TradeDirection,
        regime: MarketRegime,
        snapshot: MarketSnapshot,
    ) -> float:
        """
        Calculate stop loss based on ATR and structure.
        """
        # ATR-based stop loss
        atr_estimate = snapshot.spot.ohlcv.range * 0.5
        sl_buffer = atr_estimate * 1.5  # 1.5x ATR buffer
        
        # Consider opening range levels
        if regime.opening_range and regime.opening_range.captured:
            or_range = regime.opening_range.range
            sl_buffer = max(sl_buffer, or_range * 0.5)
        
        if direction == TradeDirection.LONG:
            # Stop below entry
            stop_loss = entry_price - sl_buffer
            
            # Consider structure levels
            if regime.opening_range and regime.opening_range.captured:
                or_low = regime.opening_range.low
                if or_low < entry_price:
                    stop_loss = min(stop_loss, or_low - 10)  # 10 point buffer below OR low
        else:
            # Stop above entry
            stop_loss = entry_price + sl_buffer
            
            if regime.opening_range and regime.opening_range.captured:
                or_high = regime.opening_range.high
                if or_high > entry_price:
                    stop_loss = max(stop_loss, or_high + 10)
        
        return stop_loss
    
    def _calculate_targets(
        self,
        entry_price: float,
        stop_loss: float,
        direction: TradeDirection,
    ) -> Tuple[float, float]:
        """
        Calculate targets using Fibonacci extensions.
        
        T1: 1.5x risk (1:1.5 RR)
        T2: 2.5x risk (1:2.5 RR)
        """
        risk = abs(entry_price - stop_loss)
        
        if direction == TradeDirection.LONG:
            target_1 = entry_price + (risk * 1.5)
            target_2 = entry_price + (risk * 2.5)
        else:
            target_1 = entry_price - (risk * 1.5)
            target_2 = entry_price - (risk * 2.5)
        
        return target_1, target_2
    
    def _calculate_position_size(
        self,
        risk_points: float,
        instrument_type: InstrumentType,
    ) -> int:
        """
        Calculate position size based on risk.
        
        Formula: Position Size = Max Risk Amount / (Risk Points × Lot Size)
        """
        if risk_points <= 0:
            return 1
        
        # Risk per lot
        risk_per_lot = risk_points * self.lot_size
        
        # Calculate lots based on max risk
        lots = int(self.max_risk_amount / risk_per_lot)
        
        # Minimum 1 lot, maximum 5 lots for safety
        return max(1, min(lots, 5))
    
    def _validate_trade(
        self,
        risk_reward_t2: float,
        risk_amount: float,
        position_size: int,
        regime: MarketRegime,
    ) -> Tuple[bool, List[str]]:
        """
        Validate trade meets all criteria.
        
        Key rule: Reject if RR < 1:2
        """
        rejection_reasons = []
        
        # Check risk-reward (CRITICAL)
        if risk_reward_t2 < self.min_risk_reward:
            rejection_reasons.append(
                f"Risk-Reward {risk_reward_t2:.2f} below minimum {self.min_risk_reward}"
            )
        
        # Check risk amount
        if risk_amount > self.max_risk_amount:
            rejection_reasons.append(
                f"Risk amount ₹{risk_amount:,.0f} exceeds max ₹{self.max_risk_amount:,.0f}"
            )
        
        # Check regime allows trading
        if not regime.trade_allowed:
            rejection_reasons.append("Trading not allowed in current regime")
        
        # Check position size
        if position_size < 1:
            rejection_reasons.append("Invalid position size")
        
        is_valid = len(rejection_reasons) == 0
        return is_valid, rejection_reasons
    
    def _to_trade_direction(self, signal_dir: SignalDirection) -> TradeDirection:
        """Convert signal direction to trade direction."""
        if signal_dir == SignalDirection.LONG:
            return TradeDirection.LONG
        return TradeDirection.SHORT
    
    def _build_reasoning(
        self,
        signal: TradeSignal,
        regime: MarketRegime,
        confluence: ConfluenceScore,
        options_intel: OptionsIntelligence,
    ) -> List[str]:
        """Build comprehensive reasoning for the trade."""
        reasoning = []
        
        # Regime context
        reasoning.append(f"Regime: {regime.regime.value} ({regime.volatility.value} volatility)")
        reasoning.append(f"Trend: {regime.trend_direction.value}")
        
        # Confluence
        reasoning.append(f"Confluence Score: {confluence.total_score}/{confluence.max_possible_score}")
        if confluence.is_eligible:
            reasoning.append("✅ Confluence threshold met")
        
        # Options intelligence
        reasoning.append(f"Options OI Buildup: {options_intel.oi_buildup_type}")
        reasoning.append(f"PCR: {options_intel.current_pcr:.2f} ({options_intel.pcr_interpretation})")
        reasoning.append(f"IV Status: {options_intel.iv_status}")
        
        if options_intel.has_conflict:
            reasoning.append("⚠️ Options showing conflicting signals")
        else:
            reasoning.append(f"Options Direction: {options_intel.direction.value}")
        
        # Setup type
        if regime.allowed_setups:
            reasoning.append(f"Allowed Setups: {', '.join(regime.allowed_setups)}")
        
        return reasoning
