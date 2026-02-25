"""
FastAPI Routes Module.

Provides REST API endpoints for the trading system.
"""

from datetime import date, datetime
from typing import Dict, List, Optional
import uuid
import logging

from fastapi import FastAPI, HTTPException, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.config import settings
from src.ingestion import BrokerStub, MarketDataBuffer, DataValidator
from src.regime import MarketRegimeEngine
from src.confluence import ConfluenceEngine
from src.options import OptionsIntelligenceEngine
from src.trade import TradeBuilder
from src.risk import RiskGovernor
from src.models.signal import SignalDirection, TradeSignal
from src.models.trade import ExecutedTrade, TradeDirection
from src.persistence import (
    SignalsRepository,
    TradePlansRepository,
    ExecutedTradesRepository,
    RiskStateRepository,
)


logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Initialize components
broker = BrokerStub()
data_buffer = MarketDataBuffer()
validator = DataValidator()
regime_engine = MarketRegimeEngine()
confluence_engine = ConfluenceEngine()
options_engine = OptionsIntelligenceEngine()
trade_builder = TradeBuilder()
risk_governor = RiskGovernor()

# Initialize repositories
signals_repo = SignalsRepository()
plans_repo = TradePlansRepository()
trades_repo = ExecutedTradesRepository()
risk_repo = RiskStateRepository()


# Request/Response Models
class TradeLogRequest(BaseModel):
    """Request to log a manual trade execution."""
    plan_id: str
    entry_price: float
    quantity: int
    notes: Optional[str] = ""


class TradeExitRequest(BaseModel):
    """Request to log trade exit."""
    trade_id: str
    exit_price: float
    exit_reason: str
    notes: Optional[str] = ""


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    components: Dict[str, bool]


# Endpoints

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    System health check.
    
    Returns status of all components.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        components={
            "broker": broker.is_connected(),
            "buffer_ready": data_buffer.is_ready,
            "validator": True,
            "risk_governor": True,
        }
    )


@router.get("/market/status")
async def get_market_status():
    """Get current market status."""
    return validator.get_market_status()


@router.get("/market/data")
async def get_market_data():
    """
    Get latest market data.
    
    Returns current snapshot if available.
    """
    if not broker.is_connected():
        broker.connect()
    
    snapshot = broker.get_market_snapshot()
    if not snapshot:
        raise HTTPException(status_code=503, detail="Market data unavailable")
    
    return {
        "spot": {
            "ltp": snapshot.spot.ltp,
            "change": snapshot.spot.change,
            "change_pct": snapshot.spot.change_pct,
            "day_high": snapshot.spot.ohlcv.high,
            "day_low": snapshot.spot.ohlcv.low,
        },
        "futures": {
            "symbol": snapshot.futures.symbol,
            "ltp": snapshot.futures.ltp,
            "basis": snapshot.futures.calculate_basis(snapshot.spot.ltp),
            "oi": snapshot.futures.open_interest,
        },
        "vix": {
            "value": snapshot.vix.value,
            "change_pct": snapshot.vix.change_pct,
            "direction": snapshot.vix.direction,
            "level": snapshot.vix.level,
        },
        "options": {
            "atm_strike": snapshot.options_chain.atm_strike,
            "atm_straddle": snapshot.options_chain.atm_straddle_premium,
            "pcr": snapshot.options_chain.pcr,
        },
        "timestamp": snapshot.timestamp.isoformat(),
    }


@router.get("/market/regime")
async def get_market_regime():
    """
    Get current market regime classification.
    """
    if not broker.is_connected():
        broker.connect()
    
    snapshot = broker.get_market_snapshot()
    if not snapshot:
        raise HTTPException(status_code=503, detail="Market data unavailable")
    
    # Get historical prices for VWAP
    prices = data_buffer.get_spot_prices(20)
    volumes = [100000] * len(prices)  # Simplified
    
    regime = regime_engine.classify_regime(snapshot, prices, volumes)
    
    return {
        "regime": regime.regime.value,
        "volatility": regime.volatility.value,
        "trend": regime.trend_direction.value,
        "trade_allowed": regime.trade_allowed,
        "allowed_setups": regime.allowed_setups,
        "atr_ratio": regime.atr_ratio,
        "vwap_slope": regime.vwap_slope,
        "price_vs_vwap": regime.price_vs_vwap,
        "vix_direction": regime.vix_direction,
        "vix_level": regime.vix_level,
        "regime_reasons": regime.regime_reasons,
        "rejection_reasons": regime.trade_rejection_reasons,
        "timestamp": regime.timestamp.isoformat(),
    }


@router.get("/signals/current")
async def get_current_signal():
    """
    Get current trade signal.
    
    Runs through full analysis pipeline.
    """
    if not broker.is_connected():
        broker.connect()
    
    snapshot = broker.get_market_snapshot()
    if not snapshot:
        raise HTTPException(status_code=503, detail="Market data unavailable")
    
    # Add to buffer
    data_buffer.add_snapshot(snapshot)
    
    # Check buffer readiness
    if not data_buffer.is_ready:
        return {
            "status": "buffer_filling",
            "message": data_buffer.get_no_trade_reason(),
            "buffer_fill": data_buffer.get_metrics().fill_percentage,
        }
    
    # Get prices for analysis
    ohlcv_data = data_buffer.get_spot_ohlcv_data(50)
    import pandas as pd
    df = pd.DataFrame(ohlcv_data).rename(columns={
        "open": "open", "high": "high", "low": "low", 
        "close": "close", "volume": "volume"
    })
    
    # Regime analysis
    prices = [d["close"] for d in ohlcv_data]
    volumes = [d["volume"] for d in ohlcv_data]
    regime = regime_engine.classify_regime(snapshot, prices, volumes)
    
    # Confluence analysis
    confluence = confluence_engine.calculate_confluence(
        df, 
        SignalDirection.LONG if regime.trend_direction.value == "up" else SignalDirection.SHORT
    )
    
    # Options analysis
    options_intel = options_engine.analyze(snapshot.options_chain, snapshot.spot.ltp)
    
    # Generate signal
    signal_id = str(uuid.uuid4())
    is_valid = (
        regime.trade_allowed 
        and confluence.is_eligible 
        and not options_intel.has_conflict
    )
    
    # Determine direction
    if is_valid:
        if confluence.direction == SignalDirection.LONG and options_intel.direction == SignalDirection.LONG:
            direction = SignalDirection.LONG
        elif confluence.direction == SignalDirection.SHORT and options_intel.direction == SignalDirection.SHORT:
            direction = SignalDirection.SHORT
        else:
            direction = SignalDirection.NEUTRAL
            is_valid = False
    else:
        direction = SignalDirection.NEUTRAL
    
    signal = TradeSignal(
        signal_id=signal_id,
        timestamp=datetime.now(),
        direction=direction,
        is_valid=is_valid,
        validity_reasons=regime.trade_rejection_reasons + options_intel.conflict_reasons,
        regime_score=2.0 if regime.trade_allowed else 0.0,
        confluence_score=confluence.total_score,
        options_score=options_intel.confidence * 10,
        total_score=confluence.total_score + (options_intel.confidence * 10) + (2.0 if regime.trade_allowed else 0.0),
        regime_type=regime.regime.value,
        volatility_level=regime.volatility.value,
        confluence_details=confluence,
        options_intel=options_intel,
        suggested_setup=regime.allowed_setups[0] if regime.allowed_setups else "",
        reasoning_chain=confluence.reasoning + options_intel.reasoning,
    )
    
    return {
        "signal_id": signal.signal_id,
        "direction": signal.direction.value,
        "is_valid": signal.is_valid,
        "total_score": signal.total_score,
        "regime": {
            "type": regime.regime.value,
            "volatility": regime.volatility.value,
            "trade_allowed": regime.trade_allowed,
        },
        "confluence": {
            "score": confluence.total_score,
            "is_eligible": confluence.is_eligible,
            "direction": confluence.direction.value,
        },
        "options": {
            "direction": options_intel.direction.value,
            "confidence": options_intel.confidence,
            "has_conflict": options_intel.has_conflict,
            "pcr": options_intel.current_pcr,
        },
        "reasoning": signal.reasoning_chain[:10],  # Limit for response size
        "timestamp": signal.timestamp.isoformat(),
    }


@router.get("/signals/history")
async def get_signal_history(limit: int = 20):
    """Get signal history."""
    signals = signals_repo.get_latest(limit)
    return {"signals": signals, "count": len(signals)}


@router.get("/risk/status")
async def get_risk_status():
    """Get current risk state."""
    return risk_governor.get_risk_summary()


@router.get("/trades/plans/today")
async def get_today_plans():
    """Get today's trade plans."""
    plans = plans_repo.get_by_date(date.today())
    return {"plans": plans, "count": len(plans)}


@router.get("/trades/history")
async def get_trade_history(limit: int = 50):
    """Get trade history."""
    trades = trades_repo.get_trade_history(limit)
    return {"trades": trades, "count": len(trades)}


@router.post("/trades/log")
async def log_trade_execution(request: TradeLogRequest):
    """
    Log a manual trade execution.
    
    This records when the human trader executes a trade from a plan.
    """
    # Get the plan
    plan = plans_repo.get_by_id(request.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Trade plan not found")
    
    # Create executed trade record
    trade = ExecutedTrade(
        trade_id=str(uuid.uuid4()),
        plan_id=request.plan_id,
        instrument=plan["instrument"],
        direction=TradeDirection(plan["direction"]),
        entry_price=request.entry_price,
        entry_time=datetime.now(),
        quantity=request.quantity,
        notes=request.notes or "",
    )
    
    # Save to database
    trade_id = trades_repo.save(trade)
    if not trade_id:
        raise HTTPException(status_code=500, detail="Failed to save trade")
    
    # Update plan status
    plans_repo.update_status(request.plan_id, "executed")
    
    # Update risk governor
    # Convert dict to TradePlan would be needed here in production
    
    return {
        "trade_id": trade.trade_id,
        "status": "logged",
        "message": "Trade execution logged successfully",
    }


@router.post("/trades/exit")
async def log_trade_exit(request: TradeExitRequest):
    """
    Log a trade exit.
    
    Records when the human trader exits a position.
    """
    # Calculate P&L (simplified)
    # In production, fetch trade details and calculate properly
    
    success = trades_repo.update_exit(
        trade_id=request.trade_id,
        exit_price=request.exit_price,
        exit_time=datetime.now(),
        exit_reason=request.exit_reason,
        pnl_points=0,  # Would calculate based on entry
        pnl_amount=0,  # Would calculate based on entry and qty
        is_winner=True,  # Would determine based on P&L
    )
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update trade")
    
    return {
        "trade_id": request.trade_id,
        "status": "closed",
        "message": "Trade exit logged successfully",
    }


@router.get("/buffer/status")
async def get_buffer_status():
    """Get data buffer status."""
    metrics = data_buffer.get_metrics()
    return {
        "current_size": metrics.current_size,
        "max_size": metrics.max_size,
        "fill_percentage": metrics.fill_percentage,
        "status": metrics.status.value,
        "trade_allowed": data_buffer.trade_allowed,
        "no_trade_reason": data_buffer.get_no_trade_reason(),
    }


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Bank Nifty Decision Support System",
        description="Human-in-the-loop trading decision support for Bank Nifty F&O",
        version="1.0.0",
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include router
    app.include_router(router, prefix="/api/v1")
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize on startup."""
        logger.info("Starting Bank Nifty DSS API...")
        broker.connect()
        risk_governor.initialize_day()
        logger.info("API ready")
    
    @app.on_event("shutdown")
    async def shutdown_event():
        """Cleanup on shutdown."""
        logger.info("Shutting down...")
        broker.disconnect()
    
    return app
