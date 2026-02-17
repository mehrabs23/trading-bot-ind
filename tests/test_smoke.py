from datetime import datetime
from core.types import MarketBar, RunMode
from strategies.mean_reversion import MeanReversionStrategy
from core.engine import Engine


def test_smoke_runs():
    bars = []
    t0 = datetime.fromisoformat("2026-02-17T09:15:00")
    px = 100.0
    for i in range(40):
        bars.append(MarketBar("X", t0, px, px+1, px-1, px, 1000))
        px += 0.2

    eng = Engine(MeanReversionStrategy("X"), RunMode.SIGNAL)
    res = eng.run(bars)
    assert "num_signals" in res

