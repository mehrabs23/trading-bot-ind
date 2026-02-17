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

    @abstractmethod
    def generate_signal(self) -> Optional[Signal]:
        raise NotImplementedError

