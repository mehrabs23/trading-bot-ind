from typing import Optional
from core.types import Signal, Side
from strategies.base import Strategy


class VWAPStrategy(Strategy):
    def __init__(self, symbol: str):
        super().__init__(symbol)
        self.current_date = None
        self.cum_vol = 0.0
        self.cum_pv = 0.0
        self.prev_vwap = None

    def generate_signal(self) -> Optional[Signal]:
        bar = self.history[-1]
        
        # Reset on new day
        if self.current_date != bar.timestamp.date():
            self.current_date = bar.timestamp.date()
            self.cum_vol = 0.0
            self.cum_pv = 0.0
            self.prev_vwap = None

        # Update VWAP
        current_pv = (bar.high + bar.low + bar.close) / 3 * bar.volume
        self.cum_pv += current_pv
        self.cum_vol += bar.volume
        
        if self.cum_vol == 0:
            return None
            
        vwap = self.cum_pv / self.cum_vol
        
        # Need at least 2 bars of data/vwap to detect crossover
        # We need the PREVIOUS bar's VWAP and Close to detect crossover
        if len(self.history) < 2 or self.prev_vwap is None:
            self.prev_vwap = vwap
            return None

        # Check Crossover
        prev_bar = self.history[-2]
        # Ensure previous bar was same day (sanity check, though reset handled above)
        if prev_bar.timestamp.date() != self.current_date:
            self.prev_vwap = vwap
            return None

        signal = None
        px = bar.close
        
        # Metrics
        atr = self._atr()
        avg_vol = self._avg_volume()
        avg_val = avg_vol * px
        
        meta = {
            "vwap": vwap,
            "atr": atr,
            "avg_volume": avg_vol,
            "avg_value": avg_val
        }

        # Logic: 
        # Buy: Prev Close < Prev VWAP AND Curr Close > Curr VWAP (Reclaim from below)
        # Sell: Prev Close > Prev VWAP AND Curr Close < Curr VWAP (Breakdown)
        
        # Stop loss: For now fixed % (0.5%) or ATR based. Let's use 1*ATR if available, else 0.5%
        risk_pct = 0.005
        if atr > 0:
            risk_amt = atr
        else:
            risk_amt = px * risk_pct

        if prev_bar.close < self.prev_vwap and px > vwap:
            # Bullish Crossover
            stop = px - risk_amt
            target = px + 1.5 * risk_amt
            signal = Signal(
                symbol=self.symbol,
                timestamp=bar.timestamp,
                side=Side.BUY,
                entry=px,
                stop=stop,
                targets=[target],
                confidence=0.6,
                reasoning=f"VWAP Reclaim: Close {px:.2f} crossed above VWAP {vwap:.2f}",
                meta=meta
            )

        elif prev_bar.close > self.prev_vwap and px < vwap:
            # Bearish Breakdown
            stop = px + risk_amt
            target = px - 1.5 * risk_amt
            signal = Signal(
                symbol=self.symbol,
                timestamp=bar.timestamp,
                side=Side.SELL,
                entry=px,
                stop=stop,
                targets=[target],
                confidence=0.6,
                reasoning=f"VWAP Breakdown: Close {px:.2f} crossed below VWAP {vwap:.2f}",
                meta=meta
            )

        # Update prev state
        self.prev_vwap = vwap
        
        return signal
