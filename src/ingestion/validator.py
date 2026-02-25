"""
Data Validation Module.

Validates market data for freshness, completeness, and trading hours.
"""

from dataclasses import dataclass
from datetime import datetime, time
from enum import Enum
from typing import List, Optional

import pytz

from src.config import settings
from src.models.market_data import MarketSnapshot, SpotData


class ValidationStatus(str, Enum):
    """Validation result status."""
    
    VALID = "valid"
    STALE = "stale"
    INCOMPLETE = "incomplete"
    OUTSIDE_HOURS = "outside_hours"
    INVALID = "invalid"


@dataclass
class ValidationResult:
    """
    Data validation result.
    
    Contains validation status and all check results.
    """
    
    is_valid: bool
    status: ValidationStatus
    timestamp_valid: bool = True
    data_complete: bool = True
    within_trading_hours: bool = True
    latency_ok: bool = True
    
    latency_ms: float = 0.0
    staleness_seconds: float = 0.0
    
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def to_summary(self) -> str:
        """Generate summary string."""
        if self.is_valid:
            return f"✅ VALID (latency: {self.latency_ms:.0f}ms)"
        return f"❌ {self.status.value.upper()}: {', '.join(self.errors)}"


class DataValidator:
    """
    Market Data Validator.
    
    Validates data for:
    - Timestamp freshness (max staleness)
    - Latency (max acceptable latency)
    - Data completeness
    - Trading hours
    """
    
    def __init__(
        self,
        max_staleness_seconds: int = None,
        max_latency_ms: int = None,
    ):
        """
        Initialize validator.
        
        Args:
            max_staleness_seconds: Maximum data staleness (default from settings)
            max_latency_ms: Maximum latency (default from settings)
        """
        self._max_staleness = max_staleness_seconds or settings.max_data_staleness_seconds
        self._max_latency = max_latency_ms or settings.max_latency_ms
        
        # Trading hours
        self._market_open = settings.market_open_time
        self._market_close = settings.market_close_time
        
        # IST timezone
        self._ist = pytz.timezone('Asia/Kolkata')
    
    def validate_snapshot(
        self,
        snapshot: MarketSnapshot,
        check_trading_hours: bool = True
    ) -> ValidationResult:
        """
        Validate a complete market snapshot.
        
        Args:
            snapshot: Market snapshot to validate
            check_trading_hours: Whether to check trading hours
            
        Returns:
            ValidationResult with all checks
        """
        errors = []
        warnings = []
        
        now = datetime.now()
        
        # Calculate latency
        latency_ms = (now - snapshot.timestamp).total_seconds() * 1000
        staleness = (now - snapshot.timestamp).total_seconds()
        
        # Check timestamp freshness
        timestamp_valid = staleness <= self._max_staleness
        if not timestamp_valid:
            errors.append(f"Data stale by {staleness:.1f}s (max: {self._max_staleness}s)")
        
        # Check latency
        latency_ok = latency_ms <= self._max_latency
        if not latency_ok:
            warnings.append(f"High latency: {latency_ms:.0f}ms (max: {self._max_latency}ms)")
        
        # Check data completeness
        data_complete = self._check_completeness(snapshot, errors)
        
        # Check trading hours
        within_hours = True
        if check_trading_hours:
            within_hours = self._is_within_trading_hours(now)
            if not within_hours:
                errors.append("Outside trading hours")
        
        # Determine overall status
        is_valid = timestamp_valid and data_complete and (within_hours or not check_trading_hours)
        
        if not is_valid:
            if not within_hours:
                status = ValidationStatus.OUTSIDE_HOURS
            elif not timestamp_valid:
                status = ValidationStatus.STALE
            elif not data_complete:
                status = ValidationStatus.INCOMPLETE
            else:
                status = ValidationStatus.INVALID
        else:
            status = ValidationStatus.VALID
        
        return ValidationResult(
            is_valid=is_valid,
            status=status,
            timestamp_valid=timestamp_valid,
            data_complete=data_complete,
            within_trading_hours=within_hours,
            latency_ok=latency_ok,
            latency_ms=latency_ms,
            staleness_seconds=staleness,
            errors=errors,
            warnings=warnings,
        )
    
    def validate_spot_data(self, spot: SpotData) -> ValidationResult:
        """
        Validate spot data only.
        
        Args:
            spot: Spot data to validate
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        
        now = datetime.now()
        
        # Calculate staleness
        staleness = (now - spot.timestamp).total_seconds()
        latency_ms = staleness * 1000
        
        timestamp_valid = staleness <= self._max_staleness
        if not timestamp_valid:
            errors.append(f"Spot data stale by {staleness:.1f}s")
        
        # Check data validity
        data_complete = True
        if spot.ltp <= 0:
            data_complete = False
            errors.append("Invalid LTP (zero or negative)")
        
        if spot.prev_close <= 0:
            data_complete = False
            errors.append("Invalid previous close")
        
        is_valid = timestamp_valid and data_complete
        status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID
        
        return ValidationResult(
            is_valid=is_valid,
            status=status,
            timestamp_valid=timestamp_valid,
            data_complete=data_complete,
            latency_ms=latency_ms,
            staleness_seconds=staleness,
            errors=errors,
            warnings=warnings,
        )
    
    def _check_completeness(
        self,
        snapshot: MarketSnapshot,
        errors: List[str]
    ) -> bool:
        """
        Check if all required data is present.
        
        Args:
            snapshot: Snapshot to check
            errors: List to append errors to
            
        Returns:
            True if data is complete
        """
        is_complete = True
        
        # Check spot data
        if not snapshot.spot or snapshot.spot.ltp <= 0:
            is_complete = False
            errors.append("Missing or invalid spot data")
        
        # Check futures data
        if not snapshot.futures or snapshot.futures.ltp <= 0:
            is_complete = False
            errors.append("Missing or invalid futures data")
        
        # Check options chain
        if not snapshot.options_chain:
            is_complete = False
            errors.append("Missing options chain")
        elif len(snapshot.options_chain.calls) == 0 or len(snapshot.options_chain.puts) == 0:
            is_complete = False
            errors.append("Incomplete options chain")
        
        # Check VIX
        if not snapshot.vix or snapshot.vix.value <= 0:
            is_complete = False
            errors.append("Missing or invalid VIX data")
        
        return is_complete
    
    def _is_within_trading_hours(self, dt: datetime) -> bool:
        """
        Check if given datetime is within trading hours.
        
        Args:
            dt: Datetime to check
            
        Returns:
            True if within trading hours
        """
        # Convert to IST if needed
        if dt.tzinfo is None:
            current_time = dt.time()
        else:
            ist_dt = dt.astimezone(self._ist)
            current_time = ist_dt.time()
        
        # Check if weekday (Monday = 0, Sunday = 6)
        weekday = dt.weekday()
        if weekday >= 5:  # Saturday or Sunday
            return False
        
        # Check time
        return self._market_open <= current_time <= self._market_close
    
    def is_market_open(self) -> bool:
        """
        Check if market is currently open.
        
        Returns:
            True if market is open
        """
        now = datetime.now()
        return self._is_within_trading_hours(now)
    
    def is_opening_range_period(self) -> bool:
        """
        Check if currently in opening range period (9:15-9:30).
        
        Returns:
            True if in opening range period
        """
        now = datetime.now()
        current_time = now.time()
        
        # Check weekday
        if now.weekday() >= 5:
            return False
        
        or_start = self._market_open
        or_end = settings.opening_range_end_time
        
        return or_start <= current_time <= or_end
    
    def get_market_status(self) -> dict:
        """
        Get current market status.
        
        Returns:
            Dict with market status information
        """
        now = datetime.now()
        is_open = self.is_market_open()
        is_or = self.is_opening_range_period()
        
        status = "closed"
        if is_open:
            if is_or:
                status = "opening_range"
            else:
                status = "open"
        
        return {
            "status": status,
            "is_open": is_open,
            "is_opening_range": is_or,
            "market_open": self._market_open.strftime("%H:%M"),
            "market_close": self._market_close.strftime("%H:%M"),
            "current_time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
        }
