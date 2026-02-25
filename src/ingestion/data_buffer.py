"""
Market Data Buffer.

Thread-safe sliding window buffer for market data using deque.
Implements NO TRADE mode until buffer is sufficiently filled.
"""

import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Deque, Generic, List, Optional, TypeVar

from src.config import settings
from src.models.market_data import MarketSnapshot, SpotData


T = TypeVar('T')


class BufferStatus(str, Enum):
    """Buffer fill status."""
    
    EMPTY = "empty"
    FILLING = "filling"
    READY = "ready"
    STALE = "stale"


@dataclass
class BufferMetrics:
    """Metrics for buffer monitoring."""
    
    current_size: int = 0
    max_size: int = 100
    fill_percentage: float = 0.0
    status: BufferStatus = BufferStatus.EMPTY
    oldest_timestamp: Optional[datetime] = None
    newest_timestamp: Optional[datetime] = None
    last_update: Optional[datetime] = None
    updates_per_second: float = 0.0


class DataBuffer(Generic[T]):
    """
    Thread-safe sliding window buffer for market data.
    
    Uses collections.deque for O(1) append and pop operations.
    Implements NO TRADE mode until buffer reaches minimum fill level.
    
    Attributes:
        max_size: Maximum buffer size
        min_fill_pct: Minimum fill percentage for trade readiness
    """
    
    def __init__(
        self,
        max_size: int = None,
        min_fill_pct: float = None,
    ):
        """
        Initialize the buffer.
        
        Args:
            max_size: Maximum items in buffer (default from settings)
            min_fill_pct: Minimum fill % for ready status (default from settings)
        """
        self._max_size = max_size or settings.data_buffer_size
        self._min_fill_pct = min_fill_pct or settings.min_buffer_fill_pct
        self._min_fill_count = int(self._max_size * (self._min_fill_pct / 100))
        
        self._buffer: Deque[T] = deque(maxlen=self._max_size)
        self._lock = threading.RLock()
        
        # Metrics tracking
        self._update_count = 0
        self._first_update_time: Optional[datetime] = None
        self._last_update_time: Optional[datetime] = None
    
    def append(self, item: T) -> None:
        """
        Append item to buffer (thread-safe).
        
        If buffer is full, oldest item is automatically dropped.
        
        Args:
            item: Item to append
        """
        with self._lock:
            self._buffer.append(item)
            self._update_count += 1
            
            now = datetime.now()
            if self._first_update_time is None:
                self._first_update_time = now
            self._last_update_time = now
    
    def get_latest(self) -> Optional[T]:
        """
        Get the most recent item (thread-safe).
        
        Returns:
            Most recent item or None if empty
        """
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1]
    
    def get_oldest(self) -> Optional[T]:
        """
        Get the oldest item in buffer (thread-safe).
        
        Returns:
            Oldest item or None if empty
        """
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[0]
    
    def get_all(self) -> List[T]:
        """
        Get all items as a list (thread-safe).
        
        Returns:
            List of all items (oldest first)
        """
        with self._lock:
            return list(self._buffer)
    
    def get_last_n(self, n: int) -> List[T]:
        """
        Get last n items (thread-safe).
        
        Args:
            n: Number of items to retrieve
            
        Returns:
            List of last n items
        """
        with self._lock:
            if n >= len(self._buffer):
                return list(self._buffer)
            return list(self._buffer)[-n:]
    
    def clear(self) -> None:
        """Clear the buffer (thread-safe)."""
        with self._lock:
            self._buffer.clear()
            self._update_count = 0
            self._first_update_time = None
            self._last_update_time = None
    
    @property
    def size(self) -> int:
        """Get current buffer size."""
        with self._lock:
            return len(self._buffer)
    
    @property
    def is_empty(self) -> bool:
        """Check if buffer is empty."""
        return self.size == 0
    
    @property
    def is_full(self) -> bool:
        """Check if buffer is at max capacity."""
        return self.size >= self._max_size
    
    @property
    def fill_percentage(self) -> float:
        """Get buffer fill percentage."""
        return (self.size / self._max_size) * 100 if self._max_size > 0 else 0.0
    
    @property
    def is_ready(self) -> bool:
        """
        Check if buffer is ready for trading.
        
        Returns True only if buffer has reached minimum fill level.
        This implements the NO TRADE mode until buffer fills.
        """
        return self.size >= self._min_fill_count
    
    @property
    def status(self) -> BufferStatus:
        """Get current buffer status."""
        if self.is_empty:
            return BufferStatus.EMPTY
        elif not self.is_ready:
            return BufferStatus.FILLING
        else:
            # Check for staleness
            if self._last_update_time:
                staleness = (datetime.now() - self._last_update_time).total_seconds()
                if staleness > settings.max_data_staleness_seconds * 2:
                    return BufferStatus.STALE
            return BufferStatus.READY
    
    @property
    def trade_allowed(self) -> bool:
        """
        Check if trading is allowed based on buffer state.
        
        Implements restart-safe NO TRADE mode.
        """
        return self.status == BufferStatus.READY
    
    def get_metrics(self) -> BufferMetrics:
        """
        Get buffer metrics for monitoring.
        
        Returns:
            BufferMetrics with current state
        """
        with self._lock:
            oldest_ts = None
            newest_ts = None
            
            # Extract timestamps if items have them
            if self._buffer:
                oldest = self._buffer[0]
                newest = self._buffer[-1]
                
                if hasattr(oldest, 'timestamp'):
                    oldest_ts = oldest.timestamp
                if hasattr(newest, 'timestamp'):
                    newest_ts = newest.timestamp
            
            # Calculate update rate
            updates_per_second = 0.0
            if self._first_update_time and self._last_update_time:
                duration = (self._last_update_time - self._first_update_time).total_seconds()
                if duration > 0:
                    updates_per_second = self._update_count / duration
            
            return BufferMetrics(
                current_size=len(self._buffer),
                max_size=self._max_size,
                fill_percentage=self.fill_percentage,
                status=self.status,
                oldest_timestamp=oldest_ts,
                newest_timestamp=newest_ts,
                last_update=self._last_update_time,
                updates_per_second=updates_per_second,
            )
    
    def get_no_trade_reason(self) -> Optional[str]:
        """
        Get reason why trading is not allowed.
        
        Returns:
            Reason string or None if trading is allowed
        """
        if self.is_empty:
            return "Buffer is empty - waiting for initial data"
        elif not self.is_ready:
            needed = self._min_fill_count - self.size
            return f"Buffer filling - need {needed} more data points ({self.fill_percentage:.1f}% full)"
        elif self.status == BufferStatus.STALE:
            return "Buffer data is stale - no recent updates"
        return None


class MarketDataBuffer:
    """
    Specialized buffer for market data snapshots.
    
    Provides convenience methods for accessing market data.
    """
    
    def __init__(self):
        """Initialize market data buffer."""
        self._snapshot_buffer: DataBuffer[MarketSnapshot] = DataBuffer()
        self._spot_buffer: DataBuffer[SpotData] = DataBuffer()
    
    def add_snapshot(self, snapshot: MarketSnapshot) -> None:
        """Add a market snapshot to the buffer."""
        self._snapshot_buffer.append(snapshot)
        self._spot_buffer.append(snapshot.spot)
    
    def get_latest_snapshot(self) -> Optional[MarketSnapshot]:
        """Get the latest market snapshot."""
        return self._snapshot_buffer.get_latest()
    
    def get_spot_prices(self, n: int = 20) -> List[float]:
        """
        Get last n spot prices.
        
        Args:
            n: Number of prices to retrieve
            
        Returns:
            List of LTP values
        """
        spots = self._spot_buffer.get_last_n(n)
        return [s.ltp for s in spots]
    
    def get_spot_ohlcv_data(self, n: int = 20) -> List[dict]:
        """
        Get last n spot OHLCV data as dictionaries.
        
        Args:
            n: Number of data points
            
        Returns:
            List of OHLCV dictionaries
        """
        spots = self._spot_buffer.get_last_n(n)
        return [
            {
                "open": s.ohlcv.open,
                "high": s.ohlcv.high,
                "low": s.ohlcv.low,
                "close": s.ohlcv.close,
                "volume": s.ohlcv.volume,
                "timestamp": s.timestamp,
            }
            for s in spots
        ]
    
    @property
    def is_ready(self) -> bool:
        """Check if buffer is ready for trading."""
        return self._snapshot_buffer.is_ready
    
    @property
    def trade_allowed(self) -> bool:
        """Check if trading is allowed."""
        return self._snapshot_buffer.trade_allowed
    
    def get_no_trade_reason(self) -> Optional[str]:
        """Get reason why trading is not allowed."""
        return self._snapshot_buffer.get_no_trade_reason()
    
    def get_metrics(self) -> BufferMetrics:
        """Get buffer metrics."""
        return self._snapshot_buffer.get_metrics()
