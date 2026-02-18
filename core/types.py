from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from typing import Optional, List, Dict, Any


class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class RunMode(str, Enum):
    SIGNAL = "SIGNAL"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    LIVE = "LIVE"


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    timestamp: datetime
    side: Side
    entry: float
    stop: float
    targets: List[float]
    confidence: float
    reasoning: str
    meta: Dict[str, Any] | None = None


@dataclass(frozen=True)
class Order:
    symbol: str
    side: Side
    quantity: int
    price: Optional[float]  # None means market in live mode, kept for future
    tag: str


@dataclass(frozen=True)
class Fill:
    symbol: str
    side: Side
    quantity: int
    price: float
    fee: float
    tag: str

