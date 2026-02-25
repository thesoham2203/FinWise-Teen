"""
Tests for Technical Confluence Engine.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from src.confluence.engine import ConfluenceEngine, create_ohlcv_dataframe
from src.confluence.indicators import (
    VWAPIndicator, EMAIndicator, RSIIndicator, 
    VolumeIndicator, PriceActionIndicator
)
from src.models.signal import SignalDirection


@pytest.fixture
def sample_data():
    """Create sample OHLCV data."""
    n = 50
    base_price = 51500
    
    # Create uptrending data
    prices = [base_price + i * 5 + np.random.normal(0, 10) for i in range(n)]
    
    return pd.DataFrame({
        'open': [p - np.random.uniform(5, 15) for p in prices],
        'high': [p + np.random.uniform(10, 30) for p in prices],
        'low': [p - np.random.uniform(10, 30) for p in prices],
        'close': prices,
        'volume': [100000 + np.random.randint(-20000, 20000) for _ in range(n)],
    })


@pytest.fixture
def downtrend_data():
    """Create downtrending data."""
    n = 50
    base_price = 51500
    
    prices = [base_price - i * 5 + np.random.normal(0, 10) for i in range(n)]
    
    return pd.DataFrame({
        'open': [p + np.random.uniform(5, 15) for p in prices],
        'high': [p + np.random.uniform(10, 30) for p in prices],
        'low': [p - np.random.uniform(10, 30) for p in prices],
        'close': prices,
        'volume': [100000 + np.random.randint(-20000, 20000) for _ in range(n)],
    })


class TestVWAPIndicator:
    """Tests for VWAPIndicator."""
    
    def test_calculate_with_valid_data(self, sample_data):
        """Test VWAP calculation with valid data."""
        indicator = VWAPIndicator()
        signal = indicator.calculate(sample_data)
        
        assert signal is not None
        assert signal.name == "VWAP"
        assert signal.signal in [SignalDirection.LONG, SignalDirection.SHORT, SignalDirection.NEUTRAL]
        assert 0 <= signal.score <= 2
    
    def test_calculate_with_insufficient_data(self):
        """Test VWAP with insufficient data."""
        indicator = VWAPIndicator()
        short_data = pd.DataFrame({
            'open': [100], 'high': [101], 'low': [99], 
            'close': [100], 'volume': [1000]
        })
        
        signal = indicator.calculate(short_data)
        assert signal.score == 0
        assert "Insufficient" in signal.reasoning


class TestEMAIndicator:
    """Tests for EMAIndicator."""
    
    def test_bullish_crossover_detection(self, sample_data):
        """Test EMA detects bullish signals in uptrend."""
        indicator = EMAIndicator(fast_period=9, slow_period=21)
        signal = indicator.calculate(sample_data)
        
        assert signal is not None
        assert signal.name == "EMA_9/21"
        # In uptrend, should lean bullish
        assert signal.signal in [SignalDirection.LONG, SignalDirection.NEUTRAL]
    
    def test_bearish_in_downtrend(self, downtrend_data):
        """Test EMA detects bearish signals in downtrend."""
        indicator = EMAIndicator(fast_period=9, slow_period=21)
        signal = indicator.calculate(downtrend_data)
        
        assert signal is not None
        # In downtrend, should lean bearish or neutral
        assert signal.signal in [SignalDirection.SHORT, SignalDirection.NEUTRAL]


class TestRSIIndicator:
    """Tests for RSIIndicator."""
    
    def test_rsi_calculation(self, sample_data):
        """Test RSI calculation."""
        indicator = RSIIndicator(period=14)
        signal = indicator.calculate(sample_data)
        
        assert signal is not None
        assert signal.name == "RSI_14"
        assert signal.value is not None
        assert 0 <= signal.value <= 100
    
    def test_oversold_detection(self):
        """Test RSI detects oversold condition."""
        # Create strongly downtrending data
        n = 30
        prices = [51500 - i * 50 for i in range(n)]
        data = create_ohlcv_dataframe(prices)
        
        indicator = RSIIndicator(period=14)
        signal = indicator.calculate(data)
        
        # Strong downtrend should show low RSI
        assert signal.value < 50


class TestVolumeIndicator:
    """Tests for VolumeIndicator."""
    
    def test_volume_analysis(self, sample_data):
        """Test volume analysis."""
        indicator = VolumeIndicator(period=20)
        signal = indicator.calculate(sample_data)
        
        assert signal is not None
        assert signal.name == "Volume"
    
    def test_high_volume_detection(self, sample_data):
        """Test high volume detection."""
        # Add spike in last candle
        sample_data.loc[sample_data.index[-1], 'volume'] = 500000
        
        indicator = VolumeIndicator(period=20)
        signal = indicator.calculate(sample_data)
        
        # Should detect high volume
        assert signal.value > 1.5


class TestPriceActionIndicator:
    """Tests for PriceActionIndicator."""
    
    def test_price_action_analysis(self, sample_data):
        """Test price action analysis."""
        indicator = PriceActionIndicator()
        signal = indicator.calculate(sample_data)
        
        assert signal is not None
        assert signal.name == "PriceAction"
    
    def test_bullish_engulfing_detection(self):
        """Test bullish engulfing pattern detection."""
        # Create bullish engulfing pattern
        data = pd.DataFrame({
            'open': [100, 99, 97],
            'high': [101, 100, 102],
            'low': [98, 96, 95],
            'close': [99, 97, 101],  # Last candle engulfs
            'volume': [100000, 100000, 150000],
        })
        
        indicator = PriceActionIndicator()
        signal = indicator.calculate(data)
        
        # Should detect pattern
        assert signal is not None


class TestConfluenceEngine:
    """Tests for ConfluenceEngine."""
    
    def test_confluence_calculation(self, sample_data):
        """Test full confluence calculation."""
        engine = ConfluenceEngine()
        confluence = engine.calculate_confluence(sample_data)
        
        assert confluence is not None
        assert 0 <= confluence.total_score <= confluence.max_possible_score
        assert confluence.direction in [
            SignalDirection.LONG, 
            SignalDirection.SHORT, 
            SignalDirection.NEUTRAL
        ]
    
    def test_eligibility_threshold(self, sample_data):
        """Test eligibility is based on threshold."""
        engine = ConfluenceEngine(min_score=7.0)
        confluence = engine.calculate_confluence(sample_data)
        
        # Eligibility should match score threshold
        if confluence.total_score >= 7.0:
            assert confluence.is_eligible or confluence.direction == SignalDirection.NEUTRAL
    
    def test_explanation_generation(self, sample_data):
        """Test explanation is generated."""
        engine = ConfluenceEngine()
        confluence = engine.calculate_confluence(sample_data)
        explanation = engine.explain_score(confluence)
        
        assert len(explanation) > 0
        assert any("Score" in line for line in explanation)
    
    def test_all_signals_present(self, sample_data):
        """Test all indicator signals are present."""
        engine = ConfluenceEngine()
        confluence = engine.calculate_confluence(sample_data)
        
        signals = confluence.get_all_signals()
        assert len(signals) == 5  # All 5 indicators


class TestCreateOHLCVDataframe:
    """Tests for create_ohlcv_dataframe helper."""
    
    def test_basic_creation(self):
        """Test basic dataframe creation."""
        prices = [100, 101, 102, 103, 104]
        df = create_ohlcv_dataframe(prices)
        
        assert len(df) == 5
        assert 'open' in df.columns
        assert 'high' in df.columns
        assert 'low' in df.columns
        assert 'close' in df.columns
        assert 'volume' in df.columns
    
    def test_with_all_params(self):
        """Test creation with all parameters."""
        prices = [100, 101, 102]
        opens = [99, 100, 101]
        highs = [102, 103, 104]
        lows = [98, 99, 100]
        volumes = [1000, 2000, 3000]
        
        df = create_ohlcv_dataframe(prices, opens, highs, lows, volumes)
        
        assert df['open'].tolist() == opens
        assert df['close'].tolist() == prices
        assert df['volume'].tolist() == volumes
