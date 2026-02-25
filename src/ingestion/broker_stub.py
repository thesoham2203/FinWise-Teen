"""
Broker API Abstraction Layer.

Provides abstract broker interface and stubbed implementation.
TODO: Implement actual broker connectivity (Zerodha, Angel One, etc.)
"""

import random
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Optional

from src.models.market_data import (
    FuturesData,
    MarketSnapshot,
    OHLCV,
    OptionData,
    OptionGreeks,
    OptionsChain,
    SpotData,
    VIXData,
)


class BrokerInterface(ABC):
    """
    Abstract Broker Interface.
    
    Defines the contract for broker implementations.
    All broker integrations must implement this interface.
    """
    
    @abstractmethod
    def connect(self) -> bool:
        """
        Establish connection to broker.
        
        Returns:
            True if connection successful
        """
        pass
    
    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from broker."""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to broker."""
        pass
    
    @abstractmethod
    def get_spot_data(self, symbol: str = "BANKNIFTY") -> Optional[SpotData]:
        """
        Get spot index data.
        
        Args:
            symbol: Index symbol
            
        Returns:
            SpotData or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_futures_data(self, symbol: str = "BANKNIFTY") -> Optional[FuturesData]:
        """
        Get futures data for current month.
        
        Args:
            symbol: Underlying symbol
            
        Returns:
            FuturesData or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_options_chain(
        self,
        symbol: str = "BANKNIFTY",
        strikes_around_atm: int = 5
    ) -> Optional[OptionsChain]:
        """
        Get options chain (ATM ± specified strikes).
        
        Args:
            symbol: Underlying symbol
            strikes_around_atm: Number of strikes above and below ATM
            
        Returns:
            OptionsChain or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_vix(self) -> Optional[VIXData]:
        """
        Get India VIX data.
        
        Returns:
            VIXData or None if unavailable
        """
        pass
    
    @abstractmethod
    def get_market_snapshot(self) -> Optional[MarketSnapshot]:
        """
        Get complete market snapshot.
        
        Returns:
            MarketSnapshot with all data or None
        """
        pass


class BrokerStub(BrokerInterface):
    """
    Stubbed Broker Implementation.
    
    Generates simulated market data for testing and development.
    
    TODO: Replace with actual broker implementation:
        - Zerodha Kite Connect
        - Angel One SmartAPI
        - Upstox API
        - IIFL Markets API
    """
    
    def __init__(self):
        """Initialize the stub broker."""
        self._connected = False
        self._base_price = 51500.0  # Base Bank Nifty price
        self._vix_base = 13.5
        self._strike_interval = 100  # Bank Nifty strike interval
        
        # Simulated daily data
        self._day_open = self._base_price + random.uniform(-100, 100)
        self._prev_close = self._base_price - random.uniform(-50, 50)
        self._prev_high = self._prev_close + random.uniform(200, 400)
        self._prev_low = self._prev_close - random.uniform(200, 400)
    
    def connect(self) -> bool:
        """
        Simulate connection to broker.
        
        Returns:
            Always True for stub
        """
        # TODO: Implement actual broker authentication
        # Example for Kite Connect:
        # self._kite = KiteConnect(api_key=API_KEY)
        # login_url = self._kite.login_url()
        # ... handle OAuth flow ...
        # self._kite.set_access_token(access_token)
        
        self._connected = True
        return True
    
    def disconnect(self) -> None:
        """Disconnect from broker."""
        self._connected = False
    
    def is_connected(self) -> bool:
        """Check connection status."""
        return self._connected
    
    def _get_simulated_price(self) -> float:
        """Generate simulated price with random walk."""
        # Random walk around base price
        change = random.gauss(0, 20)  # Mean 0, std dev 20 points
        self._base_price += change
        # Mean reversion
        if abs(self._base_price - 51500) > 500:
            self._base_price -= change * 0.5
        return round(self._base_price, 2)
    
    def _get_atm_strike(self, spot_price: float) -> float:
        """Calculate ATM strike for given spot price."""
        return round(spot_price / self._strike_interval) * self._strike_interval
    
    def get_spot_data(self, symbol: str = "BANKNIFTY") -> Optional[SpotData]:
        """
        Get simulated spot data.
        
        Args:
            symbol: Index symbol
            
        Returns:
            Simulated SpotData
        """
        if not self._connected:
            return None
        
        ltp = self._get_simulated_price()
        
        # Calculate day's OHLC
        day_high = max(self._day_open, ltp) + random.uniform(0, 50)
        day_low = min(self._day_open, ltp) - random.uniform(0, 50)
        
        ohlcv = OHLCV(
            open=self._day_open,
            high=day_high,
            low=day_low,
            close=ltp,
            volume=random.randint(100000, 500000),
        )
        
        return SpotData(
            symbol=symbol,
            ltp=ltp,
            ohlcv=ohlcv,
            prev_close=self._prev_close,
            timestamp=datetime.now(),
        )
    
    def get_futures_data(self, symbol: str = "BANKNIFTY") -> Optional[FuturesData]:
        """
        Get simulated futures data.
        
        Args:
            symbol: Underlying symbol
            
        Returns:
            Simulated FuturesData
        """
        if not self._connected:
            return None
        
        spot_ltp = self._get_simulated_price()
        # Futures typically trade at premium
        futures_premium = random.uniform(20, 80)
        futures_ltp = spot_ltp + futures_premium
        
        # Calculate expiry (current month last Thursday)
        now = datetime.now()
        # Simplified: use last day of current month
        if now.month == 12:
            expiry = datetime(now.year + 1, 1, 1) - timedelta(days=1)
        else:
            expiry = datetime(now.year, now.month + 1, 1) - timedelta(days=1)
        
        # Generate symbol like BANKNIFTY24JANFUT
        month_code = now.strftime("%b").upper()
        year_code = now.strftime("%y")
        fut_symbol = f"{symbol}{year_code}{month_code}FUT"
        
        ohlcv = OHLCV(
            open=self._day_open + futures_premium,
            high=max(self._day_open, futures_ltp) + random.uniform(10, 60),
            low=min(self._day_open, futures_ltp) - random.uniform(10, 60),
            close=futures_ltp,
            volume=random.randint(50000, 200000),
        )
        
        return FuturesData(
            symbol=fut_symbol,
            ltp=round(futures_ltp, 2),
            ohlcv=ohlcv,
            open_interest=random.randint(100000, 500000),
            oi_change=random.randint(-50000, 50000),
            expiry=expiry,
            timestamp=datetime.now(),
        )
    
    def get_options_chain(
        self,
        symbol: str = "BANKNIFTY",
        strikes_around_atm: int = 5
    ) -> Optional[OptionsChain]:
        """
        Get simulated options chain.
        
        Args:
            symbol: Underlying symbol
            strikes_around_atm: Strikes above/below ATM
            
        Returns:
            Simulated OptionsChain
        """
        if not self._connected:
            return None
        
        spot_price = self._get_simulated_price()
        atm_strike = self._get_atm_strike(spot_price)
        
        # Calculate expiry
        now = datetime.now()
        # Weekly expiry (next Wednesday)
        days_until_wednesday = (2 - now.weekday()) % 7
        if days_until_wednesday == 0 and now.hour >= 15:
            days_until_wednesday = 7
        expiry = now + timedelta(days=days_until_wednesday)
        
        calls = []
        puts = []
        
        for i in range(-strikes_around_atm, strikes_around_atm + 1):
            strike = atm_strike + (i * self._strike_interval)
            
            # Distance from ATM
            distance = abs(strike - spot_price)
            
            # Simplified option pricing
            # ATM options have highest premium, decreasing as we go OTM
            atm_premium = spot_price * 0.02  # ~2% of spot
            
            # Call pricing
            if strike <= spot_price:  # ITM call
                call_intrinsic = spot_price - strike
                call_time_value = atm_premium * (1 - distance / 1000)
                call_premium = call_intrinsic + max(call_time_value, 10)
            else:  # OTM call
                call_premium = max(atm_premium * (1 - distance / 500), 5)
            
            # Put pricing
            if strike >= spot_price:  # ITM put
                put_intrinsic = strike - spot_price
                put_time_value = atm_premium * (1 - distance / 1000)
                put_premium = put_intrinsic + max(put_time_value, 10)
            else:  # OTM put
                put_premium = max(atm_premium * (1 - distance / 500), 5)
            
            # Generate Greeks
            call_delta = max(0.1, min(0.9, 0.5 + (spot_price - strike) / 500))
            put_delta = call_delta - 1
            
            # Call option
            call_symbol = f"{symbol}{now.strftime('%y%b%d').upper()}{int(strike)}CE"
            calls.append(OptionData(
                symbol=call_symbol,
                strike=strike,
                option_type="CE",
                ltp=round(call_premium, 2),
                bid=round(call_premium - random.uniform(0.5, 2), 2),
                ask=round(call_premium + random.uniform(0.5, 2), 2),
                open_interest=random.randint(10000, 200000),
                oi_change=random.randint(-20000, 20000),
                volume=random.randint(1000, 50000),
                greeks=OptionGreeks(
                    delta=round(call_delta, 3),
                    gamma=round(random.uniform(0.001, 0.01), 4),
                    theta=round(-random.uniform(10, 50), 2),
                    vega=round(random.uniform(5, 20), 2),
                    iv=round(self._vix_base + random.uniform(-2, 5), 2),
                ),
                expiry=expiry,
                timestamp=datetime.now(),
            ))
            
            # Put option
            put_symbol = f"{symbol}{now.strftime('%y%b%d').upper()}{int(strike)}PE"
            puts.append(OptionData(
                symbol=put_symbol,
                strike=strike,
                option_type="PE",
                ltp=round(put_premium, 2),
                bid=round(put_premium - random.uniform(0.5, 2), 2),
                ask=round(put_premium + random.uniform(0.5, 2), 2),
                open_interest=random.randint(10000, 200000),
                oi_change=random.randint(-20000, 20000),
                volume=random.randint(1000, 50000),
                greeks=OptionGreeks(
                    delta=round(put_delta, 3),
                    gamma=round(random.uniform(0.001, 0.01), 4),
                    theta=round(-random.uniform(10, 50), 2),
                    vega=round(random.uniform(5, 20), 2),
                    iv=round(self._vix_base + random.uniform(-2, 5), 2),
                ),
                expiry=expiry,
                timestamp=datetime.now(),
            ))
        
        return OptionsChain(
            underlying=symbol,
            spot_price=spot_price,
            atm_strike=atm_strike,
            expiry=expiry,
            calls=sorted(calls, key=lambda x: x.strike),
            puts=sorted(puts, key=lambda x: x.strike),
            timestamp=datetime.now(),
        )
    
    def get_vix(self) -> Optional[VIXData]:
        """
        Get simulated VIX data.
        
        Returns:
            Simulated VIXData
        """
        if not self._connected:
            return None
        
        # Random walk for VIX
        self._vix_base += random.gauss(0, 0.3)
        self._vix_base = max(10, min(30, self._vix_base))  # Clamp between 10-30
        
        vix_value = round(self._vix_base, 2)
        prev_vix = vix_value - random.uniform(-1, 1)
        
        return VIXData(
            symbol="INDIAVIX",
            value=vix_value,
            prev_close=round(prev_vix, 2),
            ohlcv=OHLCV(
                open=round(prev_vix + random.uniform(-0.5, 0.5), 2),
                high=round(max(vix_value, prev_vix) + random.uniform(0.2, 0.8), 2),
                low=round(min(vix_value, prev_vix) - random.uniform(0.2, 0.8), 2),
                close=vix_value,
                volume=0,
            ),
            timestamp=datetime.now(),
        )
    
    def get_market_snapshot(self) -> Optional[MarketSnapshot]:
        """
        Get complete market snapshot.
        
        Returns:
            MarketSnapshot with all data
        """
        if not self._connected:
            return None
        
        spot = self.get_spot_data()
        futures = self.get_futures_data()
        options_chain = self.get_options_chain()
        vix = self.get_vix()
        
        if not all([spot, futures, options_chain, vix]):
            return None
        
        return MarketSnapshot(
            spot=spot,
            futures=futures,
            options_chain=options_chain,
            vix=vix,
            timestamp=datetime.now(),
        )


# Factory function for creating broker instances
def create_broker(broker_type: str = "stub") -> BrokerInterface:
    """
    Factory function to create broker instances.
    
    Args:
        broker_type: Type of broker ('stub', 'kite', 'angel', etc.)
        
    Returns:
        BrokerInterface implementation
    """
    if broker_type == "stub":
        return BrokerStub()
    # TODO: Add other broker implementations
    # elif broker_type == "kite":
    #     return KiteBroker()
    # elif broker_type == "angel":
    #     return AngelBroker()
    else:
        raise ValueError(f"Unknown broker type: {broker_type}")
