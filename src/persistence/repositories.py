"""
Repository Pattern for Database Operations.

Provides CRUD operations for all entities.
"""

from datetime import date, datetime
from typing import Dict, List, Optional
import logging
import json

from src.persistence.client import get_supabase_client
from src.models.signal import TradeSignal
from src.models.trade import TradePlan, ExecutedTrade
from src.models.risk import DailyRiskState


logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository with common operations."""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self._client = get_supabase_client()
    
    @property
    def table(self):
        """Get table reference."""
        if not self._client.is_connected():
            self._client.connect()
        return self._client.client.table(self.table_name)
    
    def _safe_execute(self, operation, default=None):
        """Safely execute database operation with error handling."""
        try:
            return operation()
        except Exception as e:
            logger.error(f"Database error on {self.table_name}: {e}")
            return default


class SignalsRepository(BaseRepository):
    """Repository for trade signals."""
    
    def __init__(self):
        super().__init__("signals")
    
    def save(self, signal: TradeSignal) -> Optional[str]:
        """
        Save a trade signal.
        
        Args:
            signal: TradeSignal to save
            
        Returns:
            Signal ID if successful
        """
        data = {
            "timestamp": signal.timestamp.isoformat(),
            "direction": signal.direction.value,
            "is_valid": signal.is_valid,
            "regime_type": signal.regime_type,
            "volatility_level": signal.volatility_level,
            "confluence_score": signal.confluence_score,
            "options_score": signal.options_score,
            "total_score": signal.total_score,
            "reasoning": signal.reasoning_chain,
        }
        
        # Add detailed data as JSON if available
        if signal.confluence_details:
            data["confluence_data"] = {
                "total_score": signal.confluence_details.total_score,
                "direction": signal.confluence_details.direction.value,
                "is_eligible": signal.confluence_details.is_eligible,
            }
        
        if signal.options_intel:
            data["options_data"] = {
                "direction": signal.options_intel.direction.value,
                "pcr": signal.options_intel.current_pcr,
                "iv_status": signal.options_intel.iv_status,
                "has_conflict": signal.options_intel.has_conflict,
            }
        
        def _insert():
            result = self.table.insert(data).execute()
            if result.data:
                return result.data[0].get("id")
            return None
        
        return self._safe_execute(_insert)
    
    def get_latest(self, limit: int = 10) -> List[Dict]:
        """Get latest signals."""
        def _query():
            result = self.table.select("*").order(
                "timestamp", desc=True
            ).limit(limit).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])
    
    def get_by_date(self, target_date: date) -> List[Dict]:
        """Get signals for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        def _query():
            result = self.table.select("*").gte(
                "timestamp", start.isoformat()
            ).lte(
                "timestamp", end.isoformat()
            ).order("timestamp", desc=True).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])


class TradePlansRepository(BaseRepository):
    """Repository for trade plans."""
    
    def __init__(self):
        super().__init__("trade_plans")
    
    def save(self, plan: TradePlan, signal_db_id: str = None) -> Optional[str]:
        """
        Save a trade plan.
        
        Args:
            plan: TradePlan to save
            signal_db_id: Database ID of associated signal
            
        Returns:
            Plan ID if successful
        """
        data = {
            "plan_id": plan.plan_id,
            "signal_id": signal_db_id,
            "instrument": plan.instrument,
            "instrument_type": plan.instrument_type.value,
            "direction": plan.direction.value,
            "entry_zone": {
                "lower": plan.entry_zone.lower,
                "upper": plan.entry_zone.upper,
                "optimal": plan.entry_zone.optimal,
            },
            "stop_loss": plan.stop_loss,
            "target_1": plan.target_1,
            "target_2": plan.target_2,
            "risk_reward": plan.risk_reward_t2,
            "position_size": plan.position_size,
            "risk_amount": plan.risk_amount,
            "status": plan.status.value,
            "is_valid": plan.is_valid,
            "rejection_reasons": plan.rejection_reasons,
            "reasoning": plan.reasoning,
        }
        
        def _insert():
            result = self.table.insert(data).execute()
            if result.data:
                return result.data[0].get("id")
            return None
        
        return self._safe_execute(_insert)
    
    def update_status(self, plan_id: str, status: str) -> bool:
        """Update plan status."""
        def _update():
            self.table.update({"status": status}).eq("plan_id", plan_id).execute()
            return True
        
        return self._safe_execute(_update, False)
    
    def get_by_id(self, plan_id: str) -> Optional[Dict]:
        """Get plan by ID."""
        def _query():
            result = self.table.select("*").eq("plan_id", plan_id).limit(1).execute()
            return result.data[0] if result.data else None
        
        return self._safe_execute(_query)
    
    def get_pending(self) -> List[Dict]:
        """Get all pending plans."""
        def _query():
            result = self.table.select("*").eq("status", "pending").execute()
            return result.data or []
        
        return self._safe_execute(_query, [])
    
    def get_by_date(self, target_date: date) -> List[Dict]:
        """Get plans for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        def _query():
            result = self.table.select("*").gte(
                "created_at", start.isoformat()
            ).lte(
                "created_at", end.isoformat()
            ).order("created_at", desc=True).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])


class ExecutedTradesRepository(BaseRepository):
    """Repository for executed trades."""
    
    def __init__(self):
        super().__init__("executed_trades")
    
    def save(self, trade: ExecutedTrade) -> Optional[str]:
        """
        Save an executed trade.
        
        Args:
            trade: ExecutedTrade to save
            
        Returns:
            Trade ID if successful
        """
        data = {
            "trade_id": trade.trade_id,
            "plan_id": trade.plan_id,
            "instrument": trade.instrument,
            "direction": trade.direction.value,
            "entry_price": trade.entry_price,
            "entry_time": trade.entry_time.isoformat(),
            "quantity": trade.quantity,
            "exit_price": trade.exit_price,
            "exit_time": trade.exit_time.isoformat() if trade.exit_time else None,
            "exit_reason": trade.exit_reason,
            "pnl_points": trade.pnl_points,
            "pnl_amount": trade.pnl_amount,
            "is_closed": trade.is_closed,
            "is_winner": trade.is_winner,
            "notes": trade.notes,
        }
        
        def _insert():
            result = self.table.insert(data).execute()
            if result.data:
                return result.data[0].get("id")
            return None
        
        return self._safe_execute(_insert)
    
    def update_exit(
        self,
        trade_id: str,
        exit_price: float,
        exit_time: datetime,
        exit_reason: str,
        pnl_points: float,
        pnl_amount: float,
        is_winner: bool,
    ) -> bool:
        """Update trade with exit details."""
        data = {
            "exit_price": exit_price,
            "exit_time": exit_time.isoformat(),
            "exit_reason": exit_reason,
            "pnl_points": pnl_points,
            "pnl_amount": pnl_amount,
            "is_closed": True,
            "is_winner": is_winner,
        }
        
        def _update():
            self.table.update(data).eq("trade_id", trade_id).execute()
            return True
        
        return self._safe_execute(_update, False)
    
    def get_open_trades(self) -> List[Dict]:
        """Get all open trades."""
        def _query():
            result = self.table.select("*").eq("is_closed", False).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])
    
    def get_by_date(self, target_date: date) -> List[Dict]:
        """Get trades for a specific date."""
        start = datetime.combine(target_date, datetime.min.time())
        end = datetime.combine(target_date, datetime.max.time())
        
        def _query():
            result = self.table.select("*").gte(
                "entry_time", start.isoformat()
            ).lte(
                "entry_time", end.isoformat()
            ).order("entry_time", desc=True).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])
    
    def get_trade_history(self, limit: int = 50) -> List[Dict]:
        """Get trade history."""
        def _query():
            result = self.table.select("*").eq("is_closed", True).order(
                "exit_time", desc=True
            ).limit(limit).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])


class RiskStateRepository(BaseRepository):
    """Repository for daily risk state."""
    
    def __init__(self):
        super().__init__("daily_risk_state")
    
    def save(self, state: DailyRiskState) -> Optional[str]:
        """
        Save or update daily risk state.
        
        Uses upsert to handle both insert and update.
        
        Args:
            state: DailyRiskState to save
            
        Returns:
            State ID if successful
        """
        data = {
            "date": state.date.isoformat(),
            "trades_taken": state.trades_taken,
            "max_trades": state.max_trades,
            "total_pnl": state.total_pnl,
            "realized_pnl": state.realized_pnl,
            "consecutive_losses": state.consecutive_losses,
            "starting_capital": state.starting_capital,
            "current_capital": state.current_capital,
            "max_daily_loss_amount": state.max_daily_loss_amount,
            "remaining_risk_capacity": state.remaining_risk_capacity,
            "hard_shutdown": state.hard_shutdown,
            "shutdown_reason": state.shutdown_reason,
            "status": state.status.value,
            "updated_at": datetime.now().isoformat(),
        }
        
        def _upsert():
            result = self.table.upsert(
                data,
                on_conflict="date"
            ).execute()
            if result.data:
                return result.data[0].get("id")
            return None
        
        return self._safe_execute(_upsert)
    
    def get_by_date(self, target_date: date) -> Optional[Dict]:
        """Get risk state for a specific date."""
        def _query():
            result = self.table.select("*").eq(
                "date", target_date.isoformat()
            ).limit(1).execute()
            return result.data[0] if result.data else None
        
        return self._safe_execute(_query)
    
    def get_today(self) -> Optional[Dict]:
        """Get today's risk state."""
        return self.get_by_date(date.today())
    
    def get_history(self, days: int = 30) -> List[Dict]:
        """Get risk state history."""
        def _query():
            result = self.table.select("*").order(
                "date", desc=True
            ).limit(days).execute()
            return result.data or []
        
        return self._safe_execute(_query, [])
