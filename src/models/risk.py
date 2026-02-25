"""
Risk Management Models.

Pydantic models for risk state and risk checks.
"""

from datetime import date as DateType, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class RiskStatus(str, Enum):
    """Risk status levels."""
    
    NORMAL = "normal"
    CAUTION = "caution"
    WARNING = "warning"
    CRITICAL = "critical"
    SHUTDOWN = "shutdown"


class DailyRiskState(BaseModel):
    """
    Daily Risk State.
    
    Tracks all risk metrics for the trading day.
    """
    
    date: DateType = Field(..., description="Trading date")
    
    # Trade Counts
    trades_taken: int = Field(default=0, ge=0, description="Number of trades taken")
    max_trades: int = Field(default=2, ge=1, description="Maximum trades allowed")
    trades_remaining: int = Field(default=2, ge=0, description="Remaining trade capacity")
    
    # P&L Tracking
    total_pnl: float = Field(default=0.0, description="Total P&L for the day")
    realized_pnl: float = Field(default=0.0, description="Realized P&L")
    unrealized_pnl: float = Field(default=0.0, description="Unrealized P&L")
    
    # Loss Tracking
    consecutive_losses: int = Field(default=0, ge=0, description="Consecutive losses")
    max_consecutive_losses: int = Field(
        default=2,
        ge=1,
        description="Max consecutive losses before shutdown"
    )
    worst_trade_pnl: float = Field(default=0.0, description="Worst single trade P&L")
    best_trade_pnl: float = Field(default=0.0, description="Best single trade P&L")
    
    # Capital & Limits
    starting_capital: float = Field(..., gt=0, description="Starting capital")
    current_capital: float = Field(..., gt=0, description="Current capital")
    max_daily_loss_pct: float = Field(
        default=1.5,
        ge=0,
        description="Max daily loss percentage"
    )
    max_daily_loss_amount: float = Field(..., ge=0, description="Max daily loss in INR")
    remaining_risk_capacity: float = Field(..., ge=0, description="Remaining risk capacity")
    
    # Status Flags
    max_loss_reached: bool = Field(
        default=False,
        description="Whether max daily loss reached"
    )
    max_trades_reached: bool = Field(
        default=False,
        description="Whether max trades reached"
    )
    hard_shutdown: bool = Field(
        default=False,
        description="Hard shutdown triggered"
    )
    status: RiskStatus = Field(
        default=RiskStatus.NORMAL,
        description="Overall risk status"
    )
    
    # Shutdown Reasons
    shutdown_reason: Optional[str] = Field(
        default=None,
        description="Reason for shutdown if applicable"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    def update_after_trade(
        self,
        pnl: float,
        is_winner: bool
    ) -> None:
        """
        Update risk state after a trade.
        
        Args:
            pnl: Trade P&L
            is_winner: Whether trade was profitable
        """
        self.trades_taken += 1
        self.trades_remaining = max(0, self.max_trades - self.trades_taken)
        self.realized_pnl += pnl
        self.total_pnl = self.realized_pnl + self.unrealized_pnl
        self.current_capital = self.starting_capital + self.total_pnl
        
        # Update best/worst
        if pnl < self.worst_trade_pnl:
            self.worst_trade_pnl = pnl
        if pnl > self.best_trade_pnl:
            self.best_trade_pnl = pnl
        
        # Track consecutive losses
        if not is_winner:
            self.consecutive_losses += 1
        else:
            self.consecutive_losses = 0
        
        # Calculate remaining capacity
        self.remaining_risk_capacity = self.max_daily_loss_amount + self.total_pnl
        
        # Check limits
        self._check_limits()
        self.updated_at = datetime.now()
    
    def _check_limits(self) -> None:
        """Check and update limit flags and status."""
        # Check max trades
        if self.trades_taken >= self.max_trades:
            self.max_trades_reached = True
        
        # Check max loss
        if self.total_pnl <= -self.max_daily_loss_amount:
            self.max_loss_reached = True
            self.hard_shutdown = True
            self.shutdown_reason = "Maximum daily loss reached"
        
        # Check consecutive losses
        if self.consecutive_losses >= self.max_consecutive_losses:
            self.hard_shutdown = True
            self.shutdown_reason = f"{self.consecutive_losses} consecutive losses"
        
        # Update status
        self._update_status()
    
    def _update_status(self) -> None:
        """Update overall risk status."""
        if self.hard_shutdown:
            self.status = RiskStatus.SHUTDOWN
        elif self.max_loss_reached or self.max_trades_reached:
            self.status = RiskStatus.CRITICAL
        elif self.consecutive_losses >= 1 or self.remaining_risk_capacity < self.max_daily_loss_amount * 0.5:
            self.status = RiskStatus.WARNING
        elif self.trades_taken >= 1 or self.total_pnl < 0:
            self.status = RiskStatus.CAUTION
        else:
            self.status = RiskStatus.NORMAL
    
    @property
    def pnl_percentage(self) -> float:
        """Get P&L as percentage of starting capital."""
        if self.starting_capital <= 0:
            return 0.0
        return (self.total_pnl / self.starting_capital) * 100
    
    @property
    def can_trade(self) -> bool:
        """Check if trading is allowed."""
        return (
            not self.hard_shutdown
            and not self.max_loss_reached
            and not self.max_trades_reached
            and self.remaining_risk_capacity > 0
        )
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        status_emoji = {
            RiskStatus.NORMAL: "🟢",
            RiskStatus.CAUTION: "🟡",
            RiskStatus.WARNING: "🟠",
            RiskStatus.CRITICAL: "🔴",
            RiskStatus.SHUTDOWN: "⛔",
        }
        return (
            f"{status_emoji.get(self.status, '⚪')} {self.status.value.upper()} | "
            f"Trades: {self.trades_taken}/{self.max_trades} | "
            f"P&L: ₹{self.total_pnl:+,.0f} ({self.pnl_percentage:+.2f}%) | "
            f"Losses: {self.consecutive_losses}"
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "date": self.date.isoformat(),
            "trades_taken": self.trades_taken,
            "total_pnl": self.total_pnl,
            "consecutive_losses": self.consecutive_losses,
            "hard_shutdown": self.hard_shutdown,
            "status": self.status.value,
            "shutdown_reason": self.shutdown_reason,
            "updated_at": self.updated_at.isoformat(),
        }


class RiskCheckResult(BaseModel):
    """
    Risk Check Result.
    
    Result of a risk evaluation for a potential trade.
    """
    
    is_allowed: bool = Field(..., description="Whether trade is allowed")
    
    # Individual Checks
    trade_count_ok: bool = Field(default=True, description="Trade count within limit")
    daily_loss_ok: bool = Field(default=True, description="Daily loss within limit")
    consecutive_loss_ok: bool = Field(default=True, description="Consecutive losses ok")
    position_size_ok: bool = Field(default=True, description="Position size acceptable")
    risk_reward_ok: bool = Field(default=True, description="Risk-reward acceptable")
    
    # Rejection Reasons
    rejection_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for rejection"
    )
    
    # Warnings
    warnings: List[str] = Field(
        default_factory=list,
        description="Risk warnings (trade still allowed)"
    )
    
    # Suggested Adjustments
    suggested_position_size: Optional[int] = Field(
        default=None,
        description="Suggested position size if adjustment needed"
    )
    suggested_stop_loss: Optional[float] = Field(
        default=None,
        description="Suggested stop loss if adjustment needed"
    )
    
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        if self.is_allowed:
            warning_str = f" ⚠️ {len(self.warnings)} warnings" if self.warnings else ""
            return f"✅ TRADE ALLOWED{warning_str}"
        else:
            return f"❌ TRADE REJECTED: {', '.join(self.rejection_reasons)}"


class PositionRisk(BaseModel):
    """
    Position Risk Metrics.
    
    Real-time risk metrics for an open position.
    """
    
    instrument: str = Field(..., description="Position instrument")
    direction: str = Field(..., description="LONG or SHORT")
    entry_price: float = Field(..., gt=0, description="Entry price")
    current_price: float = Field(..., gt=0, description="Current price")
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    quantity: int = Field(..., ge=1, description="Position quantity")
    
    # Risk Metrics
    unrealized_pnl_points: float = Field(default=0.0, description="Unrealized P&L points")
    unrealized_pnl_amount: float = Field(default=0.0, description="Unrealized P&L INR")
    distance_to_sl_points: float = Field(default=0.0, description="Distance to SL points")
    distance_to_sl_pct: float = Field(default=0.0, description="Distance to SL %")
    
    # Status
    is_profitable: bool = Field(default=False, description="Currently profitable")
    sl_hit: bool = Field(default=False, description="Stop loss hit")
    target_1_hit: bool = Field(default=False, description="Target 1 hit")
    target_2_hit: bool = Field(default=False, description="Target 2 hit")
    
    # Trailing SL
    trailing_sl_active: bool = Field(default=False, description="Trailing SL active")
    trailing_sl_price: Optional[float] = Field(default=None, description="Current trailing SL")
    
    timestamp: datetime = Field(default_factory=datetime.now)
    
    def update_metrics(self) -> None:
        """Update risk metrics based on current price."""
        if self.direction == "LONG":
            self.unrealized_pnl_points = self.current_price - self.entry_price
            self.distance_to_sl_points = self.current_price - self.stop_loss
        else:
            self.unrealized_pnl_points = self.entry_price - self.current_price
            self.distance_to_sl_points = self.stop_loss - self.current_price
        
        self.unrealized_pnl_amount = self.unrealized_pnl_points * self.quantity
        self.is_profitable = self.unrealized_pnl_points > 0
        
        if self.entry_price > 0:
            self.distance_to_sl_pct = (self.distance_to_sl_points / self.entry_price) * 100
        
        # Check SL hit
        if self.direction == "LONG":
            self.sl_hit = self.current_price <= self.stop_loss
        else:
            self.sl_hit = self.current_price >= self.stop_loss
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        status = "🟢" if self.is_profitable else "🔴"
        return (
            f"{status} {self.direction} {self.instrument} | "
            f"P&L: ₹{self.unrealized_pnl_amount:+,.0f} | "
            f"SL Distance: {self.distance_to_sl_points:+.0f} pts"
        )
