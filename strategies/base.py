from abc import ABC, abstractmethod
from typing import List, Optional
from core.types import MarketBar, Signal


class Strategy(ABC):
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.history: List[MarketBar] = []

    def on_bar(self, bar: MarketBar) -> Optional[Signal]:
        self.history.append(bar)
        return self.generate_signal()

    def _atr(self, period: int = 14) -> float:
        if len(self.history) < period + 1:
            return 0.0

        tr_sum = 0.0
        # simple ATR calculation for now
        for i in range(1, period + 1):
            curr = self.history[-i]
            prev = self.history[-i - 1]
            tr = max(
                curr.high - curr.low,
                abs(curr.high - prev.close),
                abs(curr.low - prev.close),
            )
            tr_sum += tr

        return tr_sum / period

    def _avg_volume(self, period: int = 20) -> float:
        if len(self.history) < period:
            return 0.0
        
        vols = [b.volume for b in self.history[-period:]]
        import statistics
        return statistics.mean(vols)

    @abstractmethod
    def generate_signal(self) -> Optional[Signal]:
        raise NotImplementedError

