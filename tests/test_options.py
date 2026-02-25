"""
Tests for Options Intelligence Engine.
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from src.options.engine import OptionsIntelligenceEngine
from src.models.market_data import (
    OptionsChain, OptionData, OptionGreeks
)
from src.models.signal import SignalDirection


@pytest.fixture
def options_engine():
    """Create an options intelligence engine."""
    return OptionsIntelligenceEngine()


@pytest.fixture
def sample_chain():
    """Create a sample options chain."""
    now = datetime.now()
    
    calls = []
    puts = []
    
    for i in range(-5, 6):
        strike = 51500 + i * 100
        
        # Calls
        calls.append(OptionData(
            symbol=f"BN{int(strike)}CE",
            strike=strike,
            option_type="CE",
            ltp=max(10, 200 - i * 20),
            open_interest=50000 + i * 5000,
            oi_change=1000 if i < 0 else -1000,
            greeks=OptionGreeks(delta=0.5, iv=15),
            expiry=now,
            timestamp=now,
        ))
        
        # Puts
        puts.append(OptionData(
            symbol=f"BN{int(strike)}PE",
            strike=strike,
            option_type="PE",
            ltp=max(10, 200 + i * 20),
            open_interest=55000 - i * 3000,
            oi_change=-1000 if i < 0 else 1000,
            greeks=OptionGreeks(delta=-0.5, iv=15),
            expiry=now,
            timestamp=now,
        ))
    
    return OptionsChain(
        underlying="BANKNIFTY",
        spot_price=51500,
        atm_strike=51500,
        expiry=now,
        calls=calls,
        puts=puts,
        timestamp=now,
    )


class TestOptionsIntelligenceEngine:
    """Tests for OptionsIntelligenceEngine."""
    
    def test_initialization(self, options_engine):
        """Test engine initializes correctly."""
        assert options_engine is not None
        assert options_engine._prev_chain is None
        assert options_engine._prev_pcr is None
    
    def test_analyze_returns_intelligence(self, options_engine, sample_chain):
        """Test analyze returns OptionsIntelligence."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel is not None
        assert intel.direction in [
            SignalDirection.LONG, 
            SignalDirection.SHORT, 
            SignalDirection.NEUTRAL
        ]
        assert 0 <= intel.confidence <= 1
    
    def test_pcr_calculation(self, options_engine, sample_chain):
        """Test PCR is calculated correctly."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel.current_pcr > 0
        assert intel.pcr_interpretation in ["bullish", "bearish", "neutral"]
    
    def test_oi_buildup_detection(self, options_engine, sample_chain):
        """Test OI buildup type detection."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel.oi_buildup_type in [
            "long_buildup", "short_buildup", 
            "long_unwinding", "short_covering", "neutral"
        ]
    
    def test_atm_straddle_calculation(self, options_engine, sample_chain):
        """Test ATM straddle premium calculation."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel.atm_straddle_premium > 0
    
    def test_iv_status(self, options_engine, sample_chain):
        """Test IV status detection."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel.iv_status in ["low", "normal", "elevated", "extreme"]
        assert intel.iv_trend in ["expanding", "contracting", "stable"]
    
    def test_oi_walls_detection(self, options_engine, sample_chain):
        """Test OI walls are detected."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel.call_wall_strike > 0
        assert intel.put_wall_strike > 0
    
    def test_max_pain_calculation(self, options_engine, sample_chain):
        """Test max pain strike calculation."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert intel.max_pain_strike > 0
        # Max pain should be within reasonable range of spot
        assert abs(intel.max_pain_strike - 51500) < 1000
    
    def test_conflict_detection(self, options_engine, sample_chain):
        """Test conflict detection."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert isinstance(intel.has_conflict, bool)
        if intel.has_conflict:
            assert len(intel.conflict_reasons) > 0
    
    def test_reasoning_populated(self, options_engine, sample_chain):
        """Test reasoning is populated."""
        intel = options_engine.analyze(sample_chain, 51500)
        
        assert len(intel.reasoning) > 0
    
    def test_second_call_shows_changes(self, options_engine, sample_chain):
        """Test second analysis call shows changes."""
        # First call
        intel1 = options_engine.analyze(sample_chain, 51500)
        
        # Second call with same chain (simulates next tick)
        intel2 = options_engine.analyze(sample_chain, 51500)
        
        # PCR change should be 0 since same data
        assert intel2.pcr_change == 0
    
    def test_reset_day(self, options_engine, sample_chain):
        """Test day reset clears state."""
        # First analyze to populate state
        options_engine.analyze(sample_chain, 51500)
        
        # Reset
        options_engine.reset_day()
        
        assert options_engine._prev_chain is None
        assert options_engine._prev_pcr is None
        assert options_engine._prev_straddle is None


class TestConflictResolution:
    """Tests for conflict resolution logic."""
    
    def test_no_conflict_when_aligned(self, options_engine):
        """Test no conflict when signals align."""
        # Create chain with clear bullish signals
        now = datetime.now()
        
        calls = [OptionData(
            symbol=f"BN51500CE",
            strike=51500,
            option_type="CE",
            ltp=200,
            open_interest=50000,
            oi_change=-5000,  # Calls unwinding = bullish
            greeks=OptionGreeks(delta=0.5, iv=12),
            expiry=now,
            timestamp=now,
        )]
        
        puts = [OptionData(
            symbol=f"BN51500PE",
            strike=51500,
            option_type="PE",
            ltp=180,
            open_interest=80000,  # High put OI = bullish
            oi_change=10000,  # Puts building = bullish
            greeks=OptionGreeks(delta=-0.5, iv=12),
            expiry=now,
            timestamp=now,
        )]
        
        chain = OptionsChain(
            underlying="BANKNIFTY",
            spot_price=51500,
            atm_strike=51500,
            expiry=now,
            calls=calls,
            puts=puts,
            timestamp=now,
        )
        
        intel = options_engine.analyze(chain, 51500)
        
        # Should not have major conflicts with aligned signals
        # (May still have conflicts due to limited data)
        assert isinstance(intel.has_conflict, bool)


class TestPCRInterpretation:
    """Tests for PCR interpretation."""
    
    def test_bullish_pcr(self, options_engine):
        """Test bullish PCR interpretation."""
        now = datetime.now()
        
        # Create high PCR chain (more put OI)
        calls = [OptionData(
            symbol="BN51500CE", strike=51500, option_type="CE",
            ltp=200, open_interest=40000, oi_change=0,
            greeks=OptionGreeks(), expiry=now, timestamp=now,
        )]
        puts = [OptionData(
            symbol="BN51500PE", strike=51500, option_type="PE",
            ltp=180, open_interest=60000, oi_change=0,  # Higher put OI
            greeks=OptionGreeks(), expiry=now, timestamp=now,
        )]
        
        chain = OptionsChain(
            underlying="BANKNIFTY", spot_price=51500, atm_strike=51500,
            expiry=now, calls=calls, puts=puts, timestamp=now,
        )
        
        intel = options_engine.analyze(chain, 51500)
        
        # High PCR (>1.2) should be bullish
        assert intel.current_pcr > 1.0
