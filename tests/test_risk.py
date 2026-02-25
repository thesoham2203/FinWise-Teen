"""
Tests for Risk Governor.
"""

import pytest
from datetime import date, datetime
from unittest.mock import MagicMock

from src.risk.governor import RiskGovernor
from src.models.risk import RiskStatus, DailyRiskState
from src.models.trade import TradePlan, TradeDirection, TradeStatus, EntryZone, InstrumentType


@pytest.fixture
def risk_governor():
    """Create a risk governor."""
    return RiskGovernor(
        capital=500000,
        max_trades_per_day=2,
        max_daily_loss_pct=1.5,
        max_consecutive_losses=2,
    )


@pytest.fixture
def valid_plan():
    """Create a valid trade plan."""
    return TradePlan(
        plan_id="test-plan-001",
        signal_id="test-signal-001",
        instrument="BANKNIFTY24JANFUT",
        instrument_type=InstrumentType.FUTURES,
        direction=TradeDirection.LONG,
        entry_zone=EntryZone(lower=51400, upper=51500, optimal=51450),
        stop_loss=51200,
        target_1=51700,
        target_2=51900,
        risk_points=250,
        reward_t1_points=250,
        reward_t2_points=450,
        risk_reward_t1=1.0,
        risk_reward_t2=1.8,
        position_size=1,
        lot_size=15,
        risk_amount=3750,
        status=TradeStatus.PENDING,
        is_valid=True,
    )


class TestRiskGovernor:
    """Tests for RiskGovernor."""
    
    def test_initialization(self, risk_governor):
        """Test governor initializes correctly."""
        assert risk_governor.capital == 500000
        assert risk_governor.max_trades == 2
        assert risk_governor.max_daily_loss_pct == 1.5
        assert risk_governor.max_consecutive_losses == 2
    
    def test_max_daily_loss_calculation(self, risk_governor):
        """Test max daily loss amount calculation."""
        expected = 500000 * 0.015  # 1.5%
        assert risk_governor.max_daily_loss_amount == expected
    
    def test_initialize_day(self, risk_governor):
        """Test day initialization."""
        state = risk_governor.initialize_day()
        
        assert state is not None
        assert state.date == date.today()
        assert state.trades_taken == 0
        assert state.trades_remaining == 2
        assert state.total_pnl == 0
        assert state.status == RiskStatus.NORMAL


class TestTradeRiskCheck:
    """Tests for check_trade_risk method."""
    
    def test_allows_valid_trade(self, risk_governor, valid_plan):
        """Test allows valid first trade."""
        valid_plan.risk_reward_t2 = 2.5  # Good RR
        valid_plan.risk_amount = 3000
        
        risk_governor.initialize_day()
        result = risk_governor.check_trade_risk(valid_plan)
        
        assert result.is_allowed
        assert len(result.rejection_reasons) == 0
    
    def test_rejects_after_max_trades(self, risk_governor, valid_plan):
        """Test rejects trade after max trades reached."""
        risk_governor.initialize_day()
        state = risk_governor.get_current_state()
        state.trades_taken = 2
        state.max_trades_reached = True
        
        result = risk_governor.check_trade_risk(valid_plan)
        
        assert not result.is_allowed
        assert any("Max trades" in r for r in result.rejection_reasons)
    
    def test_rejects_after_hard_shutdown(self, risk_governor, valid_plan):
        """Test rejects trade after hard shutdown."""
        risk_governor.initialize_day()
        state = risk_governor.get_current_state()
        state.hard_shutdown = True
        state.shutdown_reason = "2 consecutive losses"
        
        result = risk_governor.check_trade_risk(valid_plan)
        
        assert not result.is_allowed
        assert any("shutdown" in r.lower() for r in result.rejection_reasons)
    
    def test_rejects_excessive_risk(self, risk_governor, valid_plan):
        """Test rejects trade with excessive risk amount."""
        risk_governor.initialize_day()
        
        # Set risk higher than remaining capacity
        valid_plan.risk_amount = 10000  # Higher than max
        state = risk_governor.get_current_state()
        state.remaining_risk_capacity = 5000
        
        result = risk_governor.check_trade_risk(valid_plan)
        
        assert not result.is_allowed
        assert any("risk" in r.lower() for r in result.rejection_reasons)
    
    def test_rejects_invalid_plan(self, risk_governor, valid_plan):
        """Test rejects invalid trade plan."""
        risk_governor.initialize_day()
        valid_plan.is_valid = False
        valid_plan.rejection_reasons = ["RR too low"]
        
        result = risk_governor.check_trade_risk(valid_plan)
        
        assert not result.is_allowed
    
    def test_warns_on_consecutive_losses(self, risk_governor, valid_plan):
        """Test warns when consecutive losses exist."""
        valid_plan.risk_reward_t2 = 2.5
        risk_governor.initialize_day()
        state = risk_governor.get_current_state()
        state.consecutive_losses = 1
        
        result = risk_governor.check_trade_risk(valid_plan)
        
        assert len(result.warnings) > 0
        assert any("consecutive" in w.lower() for w in result.warnings)


class TestTradeRecording:
    """Tests for trade recording methods."""
    
    def test_record_trade_entry(self, risk_governor, valid_plan):
        """Test recording trade entry."""
        risk_governor.initialize_day()
        initial_trades = risk_governor.get_current_state().trades_taken
        
        risk_governor.record_trade_entry(valid_plan)
        
        state = risk_governor.get_current_state()
        assert state.trades_taken == initial_trades + 1
        assert state.trades_remaining == 1
    
    def test_record_winning_trade(self, risk_governor):
        """Test recording a winning trade."""
        risk_governor.initialize_day()
        
        from src.models.trade import ExecutedTrade
        trade = MagicMock(spec=ExecutedTrade)
        trade.pnl_amount = 5000
        trade.is_winner = True
        
        risk_governor.record_trade_exit(trade)
        
        state = risk_governor.get_current_state()
        assert state.realized_pnl == 5000
        assert state.consecutive_losses == 0
    
    def test_record_losing_trade(self, risk_governor):
        """Test recording a losing trade."""
        risk_governor.initialize_day()
        
        from src.models.trade import ExecutedTrade
        trade = MagicMock(spec=ExecutedTrade)
        trade.pnl_amount = -3000
        trade.is_winner = False
        
        risk_governor.record_trade_exit(trade)
        
        state = risk_governor.get_current_state()
        assert state.realized_pnl == -3000
        assert state.consecutive_losses == 1
    
    def test_hard_shutdown_on_consecutive_losses(self, risk_governor):
        """Test hard shutdown after consecutive losses."""
        risk_governor.initialize_day()
        
        from src.models.trade import ExecutedTrade
        
        # Record first loss
        trade1 = MagicMock(spec=ExecutedTrade)
        trade1.pnl_amount = -3000
        trade1.is_winner = False
        risk_governor.record_trade_exit(trade1)
        
        # Record second loss
        trade2 = MagicMock(spec=ExecutedTrade)
        trade2.pnl_amount = -3000
        trade2.is_winner = False
        risk_governor.record_trade_exit(trade2)
        
        state = risk_governor.get_current_state()
        assert state.hard_shutdown
        assert state.consecutive_losses == 2


class TestCanTrade:
    """Tests for can_trade method."""
    
    def test_can_trade_initially(self, risk_governor):
        """Test can trade at start of day."""
        risk_governor.initialize_day()
        
        can_trade, reason = risk_governor.can_trade()
        
        assert can_trade
    
    def test_cannot_trade_after_shutdown(self, risk_governor):
        """Test cannot trade after shutdown."""
        risk_governor.initialize_day()
        state = risk_governor.get_current_state()
        state.hard_shutdown = True
        state.shutdown_reason = "Max loss"
        
        can_trade, reason = risk_governor.can_trade()
        
        assert not can_trade
        assert "shutdown" in reason.lower()


class TestSLTightening:
    """Tests for stop loss tightening logic."""
    
    def test_tighten_sl_at_50pct(self, risk_governor):
        """Test SL tightened at 50% of target."""
        should_tighten, reason = risk_governor.should_tighten_sl(
            unrealized_pnl=150,  # 50% of target
            target_1=300,
        )
        
        assert should_tighten
        assert "breakeven" in reason.lower()
    
    def test_no_tighten_before_50pct(self, risk_governor):
        """Test SL not tightened before 50%."""
        should_tighten, reason = risk_governor.should_tighten_sl(
            unrealized_pnl=100,  # 33% of target
            target_1=300,
        )
        
        assert not should_tighten


class TestRiskSummary:
    """Tests for risk summary generation."""
    
    def test_get_risk_summary(self, risk_governor):
        """Test risk summary generation."""
        risk_governor.initialize_day()
        
        summary = risk_governor.get_risk_summary()
        
        assert "status" in summary
        assert "can_trade" in summary
        assert "trades_taken" in summary
        assert "total_pnl" in summary
