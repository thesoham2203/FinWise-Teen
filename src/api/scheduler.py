"""
APScheduler Module.

Manages scheduled tasks for market data and signal generation.
"""

from datetime import datetime, time
from typing import Optional
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.config import settings
from src.ingestion import BrokerStub, MarketDataBuffer, DataValidator
from src.regime import MarketRegimeEngine
from src.risk import RiskGovernor


logger = logging.getLogger(__name__)


class SignalScheduler:
    """
    Scheduler for automated tasks.
    
    Jobs:
    - Market data fetch (every 1 second during market hours)
    - Signal generation (every 5 seconds)
    - Risk state update (every 30 seconds)
    - EOD cleanup (at 15:35)
    """
    
    def __init__(
        self,
        broker: BrokerStub,
        buffer: MarketDataBuffer,
        validator: DataValidator,
        regime_engine: MarketRegimeEngine,
        risk_governor: RiskGovernor,
    ):
        """
        Initialize scheduler.
        
        Args:
            broker: Broker instance
            buffer: Data buffer
            validator: Data validator
            regime_engine: Regime engine
            risk_governor: Risk governor
        """
        self.broker = broker
        self.buffer = buffer
        self.validator = validator
        self.regime_engine = regime_engine
        self.risk_governor = risk_governor
        
        self.scheduler: Optional[AsyncIOScheduler] = None
        self._is_running = False
    
    def start(self) -> None:
        """Start the scheduler."""
        if self._is_running:
            logger.warning("Scheduler already running")
            return
        
        self.scheduler = AsyncIOScheduler()
        
        # Market data fetch job - every 1 second during market hours
        self.scheduler.add_job(
            self._fetch_market_data,
            IntervalTrigger(seconds=1),
            id="fetch_market_data",
            name="Fetch Market Data",
            max_instances=1,
        )
        
        # Signal generation job - every 5 seconds
        self.scheduler.add_job(
            self._generate_signal,
            IntervalTrigger(seconds=5),
            id="generate_signal",
            name="Generate Signal",
            max_instances=1,
        )
        
        # Risk state update - every 30 seconds
        self.scheduler.add_job(
            self._update_risk_state,
            IntervalTrigger(seconds=30),
            id="update_risk_state",
            name="Update Risk State",
            max_instances=1,
        )
        
        # EOD cleanup - at 15:35 IST on weekdays
        self.scheduler.add_job(
            self._eod_cleanup,
            CronTrigger(
                hour=15,
                minute=35,
                day_of_week="mon-fri",
            ),
            id="eod_cleanup",
            name="EOD Cleanup",
            max_instances=1,
        )
        
        # Day start initialization - at 9:10 IST on weekdays
        self.scheduler.add_job(
            self._day_start,
            CronTrigger(
                hour=9,
                minute=10,
                day_of_week="mon-fri",
            ),
            id="day_start",
            name="Day Start Init",
            max_instances=1,
        )
        
        self.scheduler.start()
        self._is_running = True
        logger.info("Scheduler started with all jobs")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        if self.scheduler:
            self.scheduler.shutdown()
            self._is_running = False
            logger.info("Scheduler stopped")
    
    async def _fetch_market_data(self) -> None:
        """Fetch market data job."""
        # Only run during market hours
        if not self.validator.is_market_open():
            return
        
        try:
            if not self.broker.is_connected():
                self.broker.connect()
            
            snapshot = self.broker.get_market_snapshot()
            if snapshot:
                # Validate data
                validation = self.validator.validate_snapshot(snapshot)
                if validation.is_valid:
                    self.buffer.add_snapshot(snapshot)
                    logger.debug(f"Added snapshot: {snapshot.spot.ltp}")
                else:
                    logger.warning(f"Invalid data: {validation.errors}")
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
    
    async def _generate_signal(self) -> None:
        """Generate trading signal job."""
        # Only run during market hours and when buffer is ready
        if not self.validator.is_market_open():
            return
        
        if not self.buffer.is_ready:
            logger.debug("Buffer not ready for signal generation")
            return
        
        # Check if in opening range period
        if self.validator.is_opening_range_period():
            logger.debug("In opening range period - capturing OR")
            return
        
        try:
            snapshot = self.buffer.get_latest_snapshot()
            if not snapshot:
                return
            
            # Classify regime
            prices = self.buffer.get_spot_prices(50)
            volumes = [100000] * len(prices)  # Simplified
            regime = self.regime_engine.classify_regime(snapshot, prices, volumes)
            
            logger.debug(
                f"Regime: {regime.regime.value}, "
                f"Trade allowed: {regime.trade_allowed}"
            )
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}")
    
    async def _update_risk_state(self) -> None:
        """Update risk state job."""
        try:
            state = self.risk_governor.get_current_state()
            if state:
                logger.debug(
                    f"Risk state: {state.status.value}, "
                    f"Trades: {state.trades_taken}/{state.max_trades}, "
                    f"P&L: {state.total_pnl}"
                )
        except Exception as e:
            logger.error(f"Error updating risk state: {e}")
    
    async def _eod_cleanup(self) -> None:
        """End of day cleanup job."""
        logger.info("Running EOD cleanup...")
        try:
            # Save final risk state
            state = self.risk_governor.get_current_state()
            if state:
                from src.persistence import RiskStateRepository
                repo = RiskStateRepository()
                repo.save(state)
                logger.info(f"Saved EOD risk state: P&L {state.total_pnl}")
            
            # Clear buffers
            # (Don't clear in case of issues, just log)
            logger.info("EOD cleanup completed")
            
        except Exception as e:
            logger.error(f"Error in EOD cleanup: {e}")
    
    async def _day_start(self) -> None:
        """Day start initialization job."""
        logger.info("Running day start initialization...")
        try:
            # Initialize risk governor for new day
            self.risk_governor.initialize_day()
            
            # Reset regime engine
            self.regime_engine.reset_day()
            
            # Connect broker
            if not self.broker.is_connected():
                self.broker.connect()
            
            logger.info("Day start initialization completed")
            
        except Exception as e:
            logger.error(f"Error in day start: {e}")
    
    def get_status(self) -> dict:
        """Get scheduler status."""
        if not self.scheduler:
            return {"status": "not_initialized"}
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
            })
        
        return {
            "status": "running" if self._is_running else "stopped",
            "jobs": jobs,
        }
