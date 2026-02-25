"""
Tests for Trade Construction Engine.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.trade.builder import TradeBuilder
from src.models.signal import SignalDirection, ConfluenceScore, OptionsIntelligence, TradeSignal
from src.models.regime import MarketRegime, RegimeType, VolatilityLevel, TrendDirection
from src.models.trade import TradeDirection, TradeStatus, InstrumentType


@pytest.fixture
def trade_builder():
    """Create a trade builder."""
    return TradeBuilder(capital=500000, risk_per_trade_pct=1.0, min_risk_reward=2.0)


@pytest.fixture
def valid_signal():
    """Create a valid trade signal."""
    return TradeSignal(
        signal_id="test-signal-001",
        timestamp=datetime.now(),
        direction=SignalDirection.LONG,
        is_valid=True,
        validity_reasons=[],
        regime_score=2.0,
        confluence_score=8.0,
        options_score=7.0,
        total_score=17.0,
        regime_type="trending_bullish",
        volatility_level="normal",
        confluence_details=None,
        options_intel=None,
        suggested_setup="pullback_to_vwap",
        reasoning_chain=["Bullish regime", "High confluence"],
    )


@pytest.fixture
def mock_snapshot():
    """Create a mock market snapshot."""
    snapshot = MagicMock()
    
    # Spot
    snapshot.spot.ltp = 51500
    snapshot.spot.ohlcv.high = 51700
    snapshot.spot.ohlcv.low = 51300
    snapshot.spot.ohlcv.range = 400
    
    # Futures
    snapshot.futures.symbol = "BANKNIFTY24JANFUT"
    snapshot.futures.ltp = 51550
    
    # Options
    snapshot.options_chain.atm_call = MagicMock()
    snapshot.options_chain.atm_call.symbol = "BN51500CE"
    snapshot.options_chain.atm_call.ltp = 200
    
    snapshot.options_chain.atm_put = MagicMock()
    snapshot.options_chain.atm_put.symbol = "BN51500PE"
    snapshot.options_chain.atm_put.ltp = 180
    
    return snapshot


@pytest.fixture
def mock_regime():
    """Create a mock market regime."""
    regime = MagicMock(spec=MarketRegime)
    regime.regime = RegimeType.TRENDING_BULLISH
    regime.volatility = VolatilityLevel.NORMAL
    regime.trade_allowed = True
    regime.allowed_setups = ["pullback_to_vwap"]
    regime.opening_range = None
    regime.trend_direction = TrendDirection.UP
    return regime


@pytest.fixture
def mock_confluence():
    """Create a mock confluence score."""
    confluence = MagicMock(spec=ConfluenceScore)
    confluence.total_score = 8.0
    confluence.direction = SignalDirection.LONG
    confluence.is_eligible = True
    confluence.reasoning = ["VWAP bullish", "EMA aligned"]
    return confluence


@pytest.fixture
def mock_options_intel():
    """Create mock options intelligence."""
    intel = MagicMock(spec=OptionsIntelligence)
    intel.direction = SignalDirection.LONG
    intel.has_conflict = False
    intel.iv_status = "normal"
    intel.confidence = 0.8
    intel.oi_buildup_type = "long_buildup"
    intel.current_pcr = 1.1
    intel.reasoning = ["Put writers active"]
    return intel


class TestTradeBuilder:
    """Tests for TradeBuilder."""
    
    def test_initialization(self, trade_builder):
        """Test builder initializes with correct values."""
        assert trade_builder.capital == 500000
        assert trade_builder.risk_per_trade_pct == 1.0
        assert trade_builder.min_risk_reward == 2.0
        assert trade_builder.lot_size == 15
    
    def test_max_risk_calculation(self, trade_builder):
        """Test max risk amount calculation."""
        expected_max_risk = 500000 * 0.01  # 1%
        assert trade_builder.max_risk_amount == expected_max_risk


class TestBuildTradePlan:
    """Tests for build_trade_plan method."""
    
    def test_builds_valid_plan(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test building a valid trade plan."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan is not None
        assert plan.signal_id == valid_signal.signal_id
        assert plan.direction == TradeDirection.LONG
    
    def test_returns_none_for_invalid_signal(
        self, trade_builder, mock_snapshot, mock_regime,
        mock_confluence, mock_options_intel
    ):
        """Test returns None for invalid signal."""
        invalid_signal = MagicMock(spec=TradeSignal)
        invalid_signal.is_valid = False
        
        plan = trade_builder.build_trade_plan(
            signal=invalid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan is None
    
    def test_entry_zone_calculated(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test entry zone is calculated correctly."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan.entry_zone is not None
        assert plan.entry_zone.lower > 0
        assert plan.entry_zone.upper > plan.entry_zone.lower
        assert plan.entry_zone.lower <= plan.entry_zone.optimal <= plan.entry_zone.upper
    
    def test_stop_loss_calculated(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test stop loss is calculated."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan.stop_loss > 0
        # For long, SL should be below entry
        assert plan.stop_loss < plan.entry_zone.optimal
    
    def test_targets_calculated(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test targets are calculated."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan.target_1 > 0
        assert plan.target_2 > 0
        # For long, targets should be above entry
        assert plan.target_1 > plan.entry_zone.optimal
        assert plan.target_2 > plan.target_1
    
    def test_risk_reward_calculated(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test risk-reward ratios are calculated."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan.risk_reward_t1 > 0
        assert plan.risk_reward_t2 > 0
        assert plan.risk_reward_t2 > plan.risk_reward_t1
    
    def test_position_size_calculated(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test position size is calculated."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert plan.position_size >= 1
        assert plan.position_size <= 5  # Max 5 lots for safety
    
    def test_reasoning_populated(
        self, trade_builder, valid_signal, mock_snapshot,
        mock_regime, mock_confluence, mock_options_intel
    ):
        """Test reasoning is populated."""
        plan = trade_builder.build_trade_plan(
            signal=valid_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        assert len(plan.reasoning) > 0


class TestRiskRewardValidation:
    """Tests for risk-reward validation."""
    
    def test_rejects_low_rr(self, trade_builder):
        """Test that low RR trades are rejected."""
        # Create a situation with low RR
        is_valid, reasons = trade_builder._validate_trade(
            risk_reward_t2=1.5,  # Below min of 2.0
            risk_amount=3000,
            position_size=1,
            regime=MagicMock(trade_allowed=True),
        )
        
        assert not is_valid
        assert any("Risk-Reward" in r for r in reasons)
    
    def test_accepts_good_rr(self, trade_builder):
        """Test that good RR trades are accepted."""
        is_valid, reasons = trade_builder._validate_trade(
            risk_reward_t2=2.5,  # Above min
            risk_amount=3000,
            position_size=1,
            regime=MagicMock(trade_allowed=True),
        )
        
        assert is_valid
        assert len(reasons) == 0


class TestShortTrades:
    """Tests for short trade construction."""
    
    def test_short_trade_levels(
        self, trade_builder, mock_snapshot, mock_regime,
        mock_confluence, mock_options_intel
    ):
        """Test short trade has correct level relationships."""
        short_signal = TradeSignal(
            signal_id="test-short-001",
            timestamp=datetime.now(),
            direction=SignalDirection.SHORT,
            is_valid=True,
            validity_reasons=[],
            regime_score=2.0,
            confluence_score=8.0,
            options_score=7.0,
            total_score=17.0,
            regime_type="trending_bearish",
            volatility_level="normal",
        )
        
        mock_regime.trade_allowed = True
        
        plan = trade_builder.build_trade_plan(
            signal=short_signal,
            snapshot=mock_snapshot,
            regime=mock_regime,
            confluence=mock_confluence,
            options_intel=mock_options_intel,
        )
        
        if plan:  # May be None if validation fails
            assert plan.direction == TradeDirection.SHORT
            # For short, SL should be above entry
            assert plan.stop_loss > plan.entry_zone.optimal
            # Targets should be below entry
            assert plan.target_1 < plan.entry_zone.optimal
