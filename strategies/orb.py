from datetime import datetime, timedelta
from typing import Optional
from core.types import Signal, Side
from strategies.base import Strategy
from data.calendar_nse import MARKET_OPEN


class ORBStrategy(Strategy):
    def __init__(self, symbol: str, orb_minutes: int = 15):
        super().__init__(symbol)
        self.orb_minutes = orb_minutes
        self.current_date = None
        self.orb_high = -float('inf')
        self.orb_low = float('inf')
        self.orb_complete = False
        self.entry_taken = False

    def generate_signal(self) -> Optional[Signal]:
        bar = self.history[-1]
        
        # Reset on new day
        if self.current_date != bar.timestamp.date():
            self.current_date = bar.timestamp.date()
            self.orb_high = -float('inf')
            self.orb_low = float('inf')
            self.orb_complete = False
            self.entry_taken = False

        if self.entry_taken:
            return None

        # Calculate ORB end time
        orb_start_dt = datetime.combine(self.current_date, MARKET_OPEN)
        orb_end_dt = orb_start_dt + timedelta(minutes=self.orb_minutes)
        
        # If inside ORB period, update high/low
        if bar.timestamp < orb_end_dt:
            # If pre-market data exists (before 9:15), ignore it or assume it's part of opening? 
            # Usually data starts at 9:15.
            if bar.timestamp >= orb_start_dt:
                self.orb_high = max(self.orb_high, bar.high)
                self.orb_low = min(self.orb_low, bar.low)
            return None
        
        # Range complete
        self.orb_complete = True
        
        # Check breakout
        px = bar.close
        
        # Calculate common metrics
        atr = self._atr()
        avg_vol = self._avg_volume()
        avg_val = avg_vol * px
        
        meta = {
            "orb_high": self.orb_high,
            "orb_low": self.orb_low,
            "atr": atr,
            "avg_volume": avg_vol,
            "avg_value": avg_val
        }

        # Need valid range
        if self.orb_high == -float('inf') or self.orb_low == float('inf'):
            return None

        signal = None
        
        if px > self.orb_high:
            # ORB Buy
            stop = self.orb_low
            risk = px - stop
            
            # Sanity check risk (if range is huge)
            # For now, raw ORB validation
            
            if risk > 0:
                target = px + 1.5 * risk
                signal = Signal(
                    symbol=self.symbol,
                    timestamp=bar.timestamp,
                    side=Side.BUY,
                    entry=px,
                    stop=stop,
                    targets=[target],
                    confidence=0.7,
                    reasoning=f"ORB Buy: Close {px} > Range High {self.orb_high}",
                    meta=meta
                )

        elif px < self.orb_low:
            # ORB Sell
            stop = self.orb_high
            risk = stop - px
            if risk > 0:
                target = px - 1.5 * risk
                signal = Signal(
                    symbol=self.symbol,
                    timestamp=bar.timestamp,
                    side=Side.SELL,
                    entry=px,
                    stop=stop,
                    targets=[target],
                    confidence=0.7,
                    reasoning=f"ORB Sell: Close {px} < Range Low {self.orb_low}",
                    meta=meta
                )
        
        if signal:
            self.entry_taken = True
            return signal
            
        return None
