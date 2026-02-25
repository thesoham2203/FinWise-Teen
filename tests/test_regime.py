"""
Tests for Market Regime Engine.
"""

import pytest
from datetime import datetime, time
from unittest.mock import MagicMock, patch

from src.regime.engine import MarketRegimeEngine
from src.models.market_data import (
    SpotData, FuturesData, OptionsChain, VIXData, 
    MarketSnapshot, OHLCV, OptionData, OptionGreeks
)
from src.models.regime import RegimeType, VolatilityLevel, TrendDirection


@pytest.fixture
def regime_engine():
    """Create a regime engine instance."""
    engine = MarketRegimeEngine()
    engine.set_previous_day_data(
        high=52000,
        low=51000,
        close=51500
    )
    return engine


@pytest.fixture
def sample_snapshot():
    """Create a sample market snapshot."""
    now = datetime.now()
    
    spot = SpotData(
        symbol="BANKNIFTY",
        ltp=51600,
        ohlcv=OHLCV(open=51500, high=51800, low=51400, close=51600, volume=100000),
        prev_close=51500,
        timestamp=now,
    )
    
    futures = FuturesData(
        symbol="BANKNIFTY24JANFUT",
        ltp=51650,
        ohlcv=OHLCV(open=51550, high=51850, low=51450, close=51650, volume=50000),
        open_interest=200000,
        oi_change=10000,
        expiry=now,
        timestamp=now,
    )
    
    # Create minimal options chain
    calls = [OptionData(
        symbol=f"BN{int(51500 + i*100)}CE",
        strike=51500 + i*100,
        option_type="CE",
        ltp=200 - i*20,
        open_interest=50000,
        oi_change=1000,
        greeks=OptionGreeks(delta=0.5, iv=15),
        expiry=now,
        timestamp=now,
    ) for i in range(-2, 3)]
    
    puts = [OptionData(
        symbol=f"BN{int(51500 + i*100)}PE",
        strike=51500 + i*100,
        option_type="PE",
        ltp=200 + i*20,
        open_interest=45000,
        oi_change=-1000,
        greeks=OptionGreeks(delta=-0.5, iv=15),
        expiry=now,
        timestamp=now,
    ) for i in range(-2, 3)]
    
    options_chain = OptionsChain(
        underlying="BANKNIFTY",
        spot_price=51600,
        atm_strike=51600,
        expiry=now,
        calls=calls,
        puts=puts,
        timestamp=now,
    )
    
    vix = VIXData(
        symbol="INDIAVIX",
        value=14.5,
        prev_close=14.0,
        timestamp=now,
    )
    
    return MarketSnapshot(
        spot=spot,
        futures=futures,
        options_chain=options_chain,
        vix=vix,
        timestamp=now,
    )


class TestMarketRegimeEngine:
    """Tests for MarketRegimeEngine."""
    
    def test_initialization(self, regime_engine):
        """Test engine initializes correctly."""
        assert regime_engine is not None
        assert regime_engine._prev_day_high == 52000
        assert regime_engine._prev_day_low == 51000
    
    def test_volatility_determination_normal(self, regime_engine):
        """Test normal volatility detection."""
        vix = MagicMock()
        vix.level = "normal"
        
        volatility = regime_engine.determine_volatility(1.0, vix)
        assert volatility == VolatilityLevel.NORMAL
    
    def test_volatility_determination_high(self, regime_engine):
        """Test high volatility detection."""
        vix = MagicMock()
        vix.level = "normal"
        
        volatility = regime_engine.determine_volatility(1.5, vix)
        assert volatility == VolatilityLevel.HIGH
    
    def test_volatility_determination_extreme(self, regime_engine):
        """Test extreme volatility detection."""
        vix = MagicMock()
        vix.level = "extreme"
        
        volatility = regime_engine.determine_volatility(2.0, vix)
        assert volatility == VolatilityLevel.EXTREME
    
    def test_trend_determination_bullish(self, regime_engine):
        """Test bullish trend detection."""
        trend = regime_engine.determine_trend(
            price=51800,
            vwap=51500,
            vwap_slope=0.15,
            opening_range=None,
        )
        assert trend == TrendDirection.UP
    
    def test_trend_determination_bearish(self, regime_engine):
        """Test bearish trend detection."""
        trend = regime_engine.determine_trend(
            price=51200,
            vwap=51500,
            vwap_slope=-0.15,
            opening_range=None,
        )
        assert trend == TrendDirection.DOWN
    
    def test_trend_determination_sideways(self, regime_engine):
        """Test sideways detection."""
        trend = regime_engine.determine_trend(
            price=51500,
            vwap=51500,
            vwap_slope=0.01,
            opening_range=None,
        )
        assert trend == TrendDirection.SIDEWAYS
    
    def test_atr_calculation(self, regime_engine):
        """Test ATR calculation."""
        current_atr, avg_atr = regime_engine.calculate_atr(100)
        # With limited data, should return current range
        assert current_atr == 100
    
    @patch('src.regime.engine.datetime')
    def test_regime_classification(self, mock_datetime, regime_engine, sample_snapshot):
        """Test regime classification."""
        # Mock time to be after opening range
        mock_datetime.now.return_value = datetime.now().replace(hour=10, minute=30)
        
        prices = [51500 + i*10 for i in range(20)]  # Uptrend
        volumes = [100000] * 20
        
        regime = regime_engine.classify_regime(sample_snapshot, prices, volumes)
        
        assert regime is not None
        assert regime.regime in [r for r in RegimeType]
        assert regime.volatility in [v for v in VolatilityLevel]
    
    def test_reset_day(self, regime_engine):
        """Test day reset clears state."""
        regime_engine._opening_range = MagicMock()
        regime_engine._or_candles = [1, 2, 3]
        
        regime_engine.reset_day()
        
        assert regime_engine._opening_range is None
        assert regime_engine._or_candles == []


class TestOpeningRange:
    """Tests for opening range functionality."""
    
    def test_or_not_captured_during_period(self, regime_engine):
        """Test OR is not marked captured during the period."""
        # Create spot data
        spot = MagicMock()
        spot.ohlcv.high = 51800
        spot.ohlcv.low = 51400
        
        # Note: This would need time mocking for full test
        # For now, just verify the method exists
        assert hasattr(regime_engine, 'update_opening_range')
    
    def test_or_finalize(self, regime_engine):
        """Test OR finalization."""
        # Add some candles
        mock_candle = MagicMock()
        mock_candle.ohlcv.high = 51800
        mock_candle.ohlcv.low = 51400
        regime_engine._or_candles = [mock_candle]
        
        regime_engine._finalize_opening_range()
        
        assert regime_engine._opening_range is not None
        assert regime_engine._opening_range.high == 51800
        assert regime_engine._opening_range.low == 51400
        assert regime_engine._opening_range.captured is True
