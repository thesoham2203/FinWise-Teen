"""
Trade Plan Models.

Pydantic models for trade plans and executed trades.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class TradeDirection(str, Enum):
    """Trade direction."""
    
    LONG = "LONG"
    SHORT = "SHORT"


class TradeStatus(str, Enum):
    """Trade plan status."""
    
    PENDING = "pending"
    ACTIVE = "active"
    EXECUTED = "executed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    REJECTED = "rejected"


class InstrumentType(str, Enum):
    """Trading instrument type."""
    
    FUTURES = "FUT"
    CALL_OPTION = "CE"
    PUT_OPTION = "PE"


class EntryZone(BaseModel):
    """
    Entry Zone Specification.
    
    Defines the price range for optimal entry.
    """
    
    lower: float = Field(..., gt=0, description="Lower bound of entry zone")
    upper: float = Field(..., gt=0, description="Upper bound of entry zone")
    optimal: float = Field(..., gt=0, description="Optimal entry price")
    
    @field_validator('upper')
    @classmethod
    def upper_must_be_greater(cls, v: float, info) -> float:
        """Ensure upper is greater than or equal to lower."""
        if 'lower' in info.data and v < info.data['lower']:
            raise ValueError('upper must be >= lower')
        return v
    
    @property
    def range(self) -> float:
        """Get entry zone range."""
        return self.upper - self.lower
    
    def is_in_zone(self, price: float) -> bool:
        """Check if price is within entry zone."""
        return self.lower <= price <= self.upper
    
    def distance_to_zone(self, price: float) -> float:
        """Get distance to nearest zone boundary."""
        if price < self.lower:
            return self.lower - price
        elif price > self.upper:
            return price - self.upper
        return 0.0


class TradePlan(BaseModel):
    """
    Trade Plan.
    
    Complete trade plan with entry, SL, targets, and risk calculations.
    """
    
    plan_id: str = Field(..., description="Unique plan ID")
    signal_id: str = Field(..., description="Associated signal ID")
    
    # Instrument
    instrument: str = Field(..., description="Trading instrument symbol")
    instrument_type: InstrumentType = Field(..., description="Instrument type")
    direction: TradeDirection = Field(..., description="Trade direction")
    
    # Entry
    entry_zone: EntryZone = Field(..., description="Entry zone")
    
    # Stop Loss
    stop_loss: float = Field(..., gt=0, description="Stop loss price")
    sl_type: str = Field(
        default="fixed",
        description="SL type: fixed, trailing, breakeven"
    )
    
    # Targets
    target_1: float = Field(..., gt=0, description="First target")
    target_2: float = Field(..., gt=0, description="Second target")
    target_1_pct: float = Field(
        default=50.0,
        ge=0,
        le=100,
        description="Percentage to exit at T1"
    )
    
    # Risk Calculations
    risk_points: float = Field(..., ge=0, description="Risk in points")
    reward_t1_points: float = Field(..., ge=0, description="Reward at T1 in points")
    reward_t2_points: float = Field(..., ge=0, description="Reward at T2 in points")
    risk_reward_t1: float = Field(..., ge=0, description="RR ratio at T1")
    risk_reward_t2: float = Field(..., ge=0, description="RR ratio at T2")
    
    # Position Sizing
    position_size: int = Field(..., ge=1, description="Position size (lots/qty)")
    lot_size: int = Field(default=15, ge=1, description="Lot size")
    risk_amount: float = Field(..., ge=0, description="Risk amount in INR")
    
    # Status
    status: TradeStatus = Field(default=TradeStatus.PENDING)
    
    # Validity
    is_valid: bool = Field(default=False, description="Meets all criteria")
    rejection_reasons: List[str] = Field(
        default_factory=list,
        description="Reasons for rejection if invalid"
    )
    
    # Reasoning
    reasoning: List[str] = Field(
        default_factory=list,
        description="Trade plan reasoning"
    )
    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Confidence score (0-1)"
    )
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    expires_at: Optional[datetime] = Field(
        default=None,
        description="Plan expiry time"
    )
    
    @property
    def total_quantity(self) -> int:
        """Get total quantity."""
        return self.position_size * self.lot_size
    
    @property
    def max_profit_t2(self) -> float:
        """Calculate max profit at T2."""
        return self.reward_t2_points * self.total_quantity
    
    @property
    def max_loss(self) -> float:
        """Calculate max loss."""
        return self.risk_points * self.total_quantity
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        status = "✅ VALID" if self.is_valid else "❌ INVALID"
        return (
            f"{self.direction.value} {self.instrument} | "
            f"Entry: {self.entry_zone.optimal:.2f} | "
            f"SL: {self.stop_loss:.2f} | "
            f"T1: {self.target_1:.2f} | T2: {self.target_2:.2f} | "
            f"RR: 1:{self.risk_reward_t2:.1f} | "
            f"{status}"
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "plan_id": self.plan_id,
            "signal_id": self.signal_id,
            "instrument": self.instrument,
            "direction": self.direction.value,
            "entry_zone": {
                "lower": self.entry_zone.lower,
                "upper": self.entry_zone.upper,
                "optimal": self.entry_zone.optimal,
            },
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "risk_reward": self.risk_reward_t2,
            "position_size": self.position_size,
            "status": self.status.value,
            "is_valid": self.is_valid,
            "reasoning": self.reasoning,
            "created_at": self.created_at.isoformat(),
        }


class ExecutedTrade(BaseModel):
    """
    Executed Trade Record.
    
    Records details of a manually executed trade.
    """
    
    trade_id: str = Field(..., description="Unique trade ID")
    plan_id: str = Field(..., description="Associated plan ID")
    
    # Instrument
    instrument: str = Field(..., description="Traded instrument")
    direction: TradeDirection = Field(..., description="Trade direction")
    
    # Execution Details
    entry_price: float = Field(..., gt=0, description="Actual entry price")
    entry_time: datetime = Field(..., description="Entry timestamp")
    quantity: int = Field(..., ge=1, description="Quantity traded")
    
    # Exit Details
    exit_price: Optional[float] = Field(default=None, description="Exit price")
    exit_time: Optional[datetime] = Field(default=None, description="Exit timestamp")
    exit_reason: Optional[str] = Field(
        default=None,
        description="Exit reason: target_1, target_2, stop_loss, manual, trailing_sl"
    )
    
    # P&L
    pnl_points: float = Field(default=0.0, description="P&L in points")
    pnl_amount: float = Field(default=0.0, description="P&L in INR")
    pnl_percentage: float = Field(default=0.0, description="P&L as % of capital")
    
    # Status
    is_closed: bool = Field(default=False, description="Whether trade is closed")
    is_winner: Optional[bool] = Field(default=None, description="Whether trade was profitable")
    
    # Notes
    notes: str = Field(default="", description="Trade notes")
    
    created_at: datetime = Field(default_factory=datetime.now)
    
    def calculate_pnl(self) -> None:
        """Calculate P&L when trade is closed."""
        if self.exit_price is not None:
            if self.direction == TradeDirection.LONG:
                self.pnl_points = self.exit_price - self.entry_price
            else:
                self.pnl_points = self.entry_price - self.exit_price
            
            self.pnl_amount = self.pnl_points * self.quantity
            self.is_winner = self.pnl_amount > 0
            self.is_closed = True
    
    def to_summary(self) -> str:
        """Generate human-readable summary."""
        status = "OPEN" if not self.is_closed else ("WIN ✅" if self.is_winner else "LOSS ❌")
        pnl_str = f"{self.pnl_amount:+,.0f}" if self.is_closed else "N/A"
        return (
            f"{self.direction.value} {self.instrument} @ {self.entry_price:.2f} | "
            f"Qty: {self.quantity} | "
            f"P&L: {pnl_str} | {status}"
        )
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage."""
        return {
            "trade_id": self.trade_id,
            "plan_id": self.plan_id,
            "instrument": self.instrument,
            "direction": self.direction.value,
            "entry_price": self.entry_price,
            "entry_time": self.entry_time.isoformat(),
            "exit_price": self.exit_price,
            "exit_time": self.exit_time.isoformat() if self.exit_time else None,
            "exit_reason": self.exit_reason,
            "pnl_points": self.pnl_points,
            "pnl_amount": self.pnl_amount,
            "is_closed": self.is_closed,
            "is_winner": self.is_winner,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }
