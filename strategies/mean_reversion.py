import statistics
from typing import Optional
from core.types import Signal, Side
from strategies.base import Strategy


class MeanReversionStrategy(Strategy):
    def __init__(self, symbol: str, lookback: int = 20, threshold: float = 0.02):
        super().__init__(symbol)
        self.lookback = lookback
        self.threshold = threshold

    def generate_signal(self) -> Optional[Signal]:
        if len(self.history) < self.lookback + 1:
            return None

        closes = [b.close for b in self.history[-self.lookback:]]
        sma = statistics.mean(closes)
        last = self.history[-1]
        px = last.close

        dev = (px - sma) / sma

        # 1R stop default: 1% away (placeholder). We’ll later use ATR.
        if dev > self.threshold:
            stop = px * 1.01
            return Signal(
                symbol=self.symbol,
                side=Side.SELL,
                entry=px,
                stop=stop,
                targets=[sma],
                confidence=min(abs(dev) * 10, 1.0),
                reasoning=f"Mean-reversion SELL: close {px:.2f} is {dev*100:.2f}% above {self.lookback}SMA {sma:.2f}",
                meta={"sma": sma, "deviation": dev},
            )

        if dev < -self.threshold:
            stop = px * 0.99
            return Signal(
                symbol=self.symbol,
                side=Side.BUY,
                entry=px,
                stop=stop,
                targets=[sma],
                confidence=min(abs(dev) * 10, 1.0),
                reasoning=f"Mean-reversion BUY: close {px:.2f} is {abs(dev)*100:.2f}% below {self.lookback}SMA {sma:.2f}",
                meta={"sma": sma, "deviation": dev},
            )

        return None

