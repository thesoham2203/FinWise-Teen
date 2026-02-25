"""
Risk Governor Module.

Enforces strict risk controls:
- Max 2 trades per day
- Max 1-1.5% daily loss
- SL-based tightening
- Hard shutdown after 2 consecutive SL
"""

from datetime import date, datetime
from typing import Optional, Tuple

from src.config import settings
from src.models.risk import DailyRiskState, RiskCheckResult, RiskStatus
from src.models.trade import TradePlan, ExecutedTrade


class RiskGovernor:
    """
    Risk Governor.
    
    Enforces all risk controls and manages daily risk state.
    This is the final gatekeeper before any trade is allowed.
    """
    
    def __init__(
        self,
        capital: float = None,
        max_trades_per_day: int = None,
        max_daily_loss_pct: float = None,
        max_consecutive_losses: int = None,
    ):
        """
        Initialize risk governor.
        
        Args:
            capital: Trading capital (default from settings)
            max_trades_per_day: Max trades per day (default: 2)
            max_daily_loss_pct: Max daily loss % (default: 1.5)
            max_consecutive_losses: Max consecutive SL (default: 2)
        """
        self.capital = capital or settings.trading_capital
        self.max_trades = max_trades_per_day or settings.max_trades_per_day
        self.max_daily_loss_pct = max_daily_loss_pct or settings.max_daily_loss_pct
        self.max_consecutive_losses = max_consecutive_losses or settings.max_consecutive_losses
        
        # Calculate limits
        self.max_daily_loss_amount = self.capital * (self.max_daily_loss_pct / 100)
        
        # Current day state
        self._risk_state: Optional[DailyRiskState] = None
    
    def initialize_day(self, trading_date: date = None) -> DailyRiskState:
        """
        Initialize risk state for a new trading day.
        
        Args:
            trading_date: Date to initialize for (default: today)
            
        Returns:
            Initialized DailyRiskState
        """
        if trading_date is None:
            trading_date = date.today()
        
        self._risk_state = DailyRiskState(
            date=trading_date,
            trades_taken=0,
            max_trades=self.max_trades,
            trades_remaining=self.max_trades,
            total_pnl=0.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            consecutive_losses=0,
            max_consecutive_losses=self.max_consecutive_losses,
            worst_trade_pnl=0.0,
            best_trade_pnl=0.0,
            starting_capital=self.capital,
            current_capital=self.capital,
            max_daily_loss_pct=self.max_daily_loss_pct,
            max_daily_loss_amount=self.max_daily_loss_amount,
            remaining_risk_capacity=self.max_daily_loss_amount,
            max_loss_reached=False,
            max_trades_reached=False,
            hard_shutdown=False,
            status=RiskStatus.NORMAL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        
        return self._risk_state
    
    def get_current_state(self) -> Optional[DailyRiskState]:
        """Get current risk state."""
        return self._risk_state
    
    def check_trade_risk(self, plan: TradePlan) -> RiskCheckResult:
        """
        Check if a trade is allowed based on current risk state.
        
        Args:
            plan: Trade plan to evaluate
            
        Returns:
            RiskCheckResult with approval/rejection
        """
        if self._risk_state is None:
            self.initialize_day()
        
        state = self._risk_state
        rejection_reasons = []
        warnings = []
        
        # Check 1: Hard shutdown
        if state.hard_shutdown:
            rejection_reasons.append(
                f"Hard shutdown active: {state.shutdown_reason}"
            )
            return self._create_result(False, rejection_reasons, warnings, plan)
        
        # Check 2: Max trades reached
        if state.trades_taken >= state.max_trades:
            rejection_reasons.append(
                f"Max trades reached ({state.trades_taken}/{state.max_trades})"
            )
            return self._create_result(False, rejection_reasons, warnings, plan)
        
        # Check 3: Max daily loss
        if state.total_pnl <= -state.max_daily_loss_amount:
            rejection_reasons.append(
                f"Max daily loss reached (₹{abs(state.total_pnl):,.0f})"
            )
            return self._create_result(False, rejection_reasons, warnings, plan)
        
        # Check 4: Trade risk amount
        if plan.risk_amount > state.remaining_risk_capacity:
            rejection_reasons.append(
                f"Trade risk (₹{plan.risk_amount:,.0f}) exceeds remaining capacity (₹{state.remaining_risk_capacity:,.0f})"
            )
            return self._create_result(False, rejection_reasons, warnings, plan)
        
        # Check 5: Plan validity
        if not plan.is_valid:
            rejection_reasons.extend(plan.rejection_reasons)
            return self._create_result(False, rejection_reasons, warnings, plan)
        
        # Check 6: Risk-Reward
        if plan.risk_reward_t2 < settings.min_risk_reward:
            rejection_reasons.append(
                f"RR {plan.risk_reward_t2:.2f} below minimum {settings.min_risk_reward}"
            )
            return self._create_result(False, rejection_reasons, warnings, plan)
        
        # Warnings (trade still allowed)
        if state.consecutive_losses >= 1:
            warnings.append(
                f"Caution: {state.consecutive_losses} consecutive loss(es)"
            )
        
        if state.trades_taken >= state.max_trades - 1:
            warnings.append("This would be your last trade for the day")
        
        if plan.risk_amount > state.remaining_risk_capacity * 0.5:
            warnings.append("Trade uses significant risk capacity")
        
        return self._create_result(True, rejection_reasons, warnings, plan)
    
    def _create_result(
        self,
        is_allowed: bool,
        rejections: list,
        warnings: list,
        plan: TradePlan,
    ) -> RiskCheckResult:
        """Create risk check result."""
        return RiskCheckResult(
            is_allowed=is_allowed,
            trade_count_ok=not any("Max trades" in r for r in rejections),
            daily_loss_ok=not any("daily loss" in r.lower() for r in rejections),
            consecutive_loss_ok=not any("consecutive" in r.lower() for r in rejections),
            position_size_ok=not any("position size" in r.lower() for r in rejections),
            risk_reward_ok=not any("RR" in r for r in rejections),
            rejection_reasons=rejections,
            warnings=warnings,
            suggested_position_size=self._suggest_position_size(plan) if not is_allowed else None,
            suggested_stop_loss=None,
            timestamp=datetime.now(),
        )
    
    def _suggest_position_size(self, plan: TradePlan) -> Optional[int]:
        """Suggest a reduced position size if original is too large."""
        if self._risk_state is None:
            return None
        
        remaining = self._risk_state.remaining_risk_capacity
        if remaining <= 0:
            return None
        
        # Calculate max lots based on remaining capacity
        risk_per_lot = plan.risk_points * plan.lot_size
        if risk_per_lot <= 0:
            return None
        
        max_lots = int(remaining / risk_per_lot)
        return max(1, max_lots) if max_lots > 0 else None
    
    def record_trade_entry(self, plan: TradePlan) -> None:
        """
        Record a trade entry (position opened).
        
        Args:
            plan: Trade plan that was executed
        """
        if self._risk_state is None:
            self.initialize_day()
        
        state = self._risk_state
        state.trades_taken += 1
        state.trades_remaining = max(0, state.max_trades - state.trades_taken)
        
        # Update status
        if state.trades_taken >= state.max_trades:
            state.max_trades_reached = True
        
        state._update_status()
        state.updated_at = datetime.now()
    
    def record_trade_exit(self, trade: ExecutedTrade) -> None:
        """
        Record a trade exit and update risk state.
        
        Args:
            trade: Completed trade record
        """
        if self._risk_state is None:
            self.initialize_day()
        
        state = self._risk_state
        
        # Update P&L
        state.realized_pnl += trade.pnl_amount
        state.total_pnl = state.realized_pnl + state.unrealized_pnl
        state.current_capital = state.starting_capital + state.total_pnl
        
        # Track best/worst
        if trade.pnl_amount < state.worst_trade_pnl:
            state.worst_trade_pnl = trade.pnl_amount
        if trade.pnl_amount > state.best_trade_pnl:
            state.best_trade_pnl = trade.pnl_amount
        
        # Track consecutive losses
        if trade.is_winner:
            state.consecutive_losses = 0
        else:
            state.consecutive_losses += 1
        
        # Update remaining capacity
        state.remaining_risk_capacity = state.max_daily_loss_amount + state.total_pnl
        
        # Check limits
        self._check_limits()
        state.updated_at = datetime.now()
    
    def _check_limits(self) -> None:
        """Check and enforce risk limits."""
        if self._risk_state is None:
            return
        
        state = self._risk_state
        
        # Check max daily loss
        if state.total_pnl <= -state.max_daily_loss_amount:
            state.max_loss_reached = True
            state.hard_shutdown = True
            state.shutdown_reason = "Maximum daily loss reached"
        
        # Check consecutive losses
        if state.consecutive_losses >= state.max_consecutive_losses:
            state.hard_shutdown = True
            state.shutdown_reason = f"{state.consecutive_losses} consecutive losses"
        
        # Update status
        state._update_status()
    
    def update_unrealized_pnl(self, unrealized: float) -> None:
        """
        Update unrealized P&L for open position.
        
        Args:
            unrealized: Current unrealized P&L
        """
        if self._risk_state is None:
            return
        
        self._risk_state.unrealized_pnl = unrealized
        self._risk_state.total_pnl = (
            self._risk_state.realized_pnl + unrealized
        )
        self._risk_state.current_capital = (
            self._risk_state.starting_capital + self._risk_state.total_pnl
        )
    
    def should_tighten_sl(self, unrealized_pnl: float, target_1: float) -> Tuple[bool, str]:
        """
        Check if stop loss should be tightened.
        
        Rule: Move SL to breakeven after 50% of target reached.
        
        Args:
            unrealized_pnl: Current unrealized P&L points
            target_1: Target 1 in points
            
        Returns:
            (should_tighten, reason)
        """
        if target_1 <= 0:
            return False, ""
        
        progress = unrealized_pnl / target_1
        
        if progress >= 0.5:
            return True, f"Target {progress*100:.0f}% reached - move SL to breakeven"
        
        return False, ""
    
    def can_trade(self) -> Tuple[bool, str]:
        """
        Quick check if trading is currently allowed.
        
        Returns:
            (can_trade, reason)
        """
        if self._risk_state is None:
            return True, "Risk state not initialized - will initialize on first trade"
        
        state = self._risk_state
        
        if state.hard_shutdown:
            return False, f"Hard shutdown: {state.shutdown_reason}"
        
        if state.max_trades_reached:
            return False, f"Max trades reached ({state.trades_taken}/{state.max_trades})"
        
        if state.max_loss_reached:
            return False, f"Max daily loss reached (₹{abs(state.total_pnl):,.0f})"
        
        return True, "Trading allowed"
    
    def get_risk_summary(self) -> dict:
        """Get current risk state summary."""
        if self._risk_state is None:
            return {
                "status": "not_initialized",
                "can_trade": True,
                "message": "Risk state not initialized",
            }
        
        state = self._risk_state
        can_trade, reason = self.can_trade()
        
        return {
            "status": state.status.value,
            "can_trade": can_trade,
            "reason": reason,
            "trades_taken": state.trades_taken,
            "trades_remaining": state.trades_remaining,
            "total_pnl": state.total_pnl,
            "pnl_percentage": state.pnl_percentage,
            "consecutive_losses": state.consecutive_losses,
            "remaining_risk_capacity": state.remaining_risk_capacity,
            "hard_shutdown": state.hard_shutdown,
        }
