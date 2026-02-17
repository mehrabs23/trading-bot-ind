from datetime import time
from data.calendar_nse import ENTRY_CUTOFF


class RiskGovernor:
    def __init__(
        self,
        max_daily_loss_pct: float = 0.01,       # 1% equity
        max_risk_per_trade_pct: float = 0.005,  # 0.5% equity
        cutoff_time: time = ENTRY_CUTOFF,
    ):
        self.max_daily_loss_pct = max_daily_loss_pct
        self.max_risk_per_trade_pct = max_risk_per_trade_pct
        self.cutoff_time = cutoff_time

    def allow_entry_time(self, ts) -> bool:
        return ts.time() < self.cutoff_time

    def size_position(self, portfolio, signal) -> int:
        eq = portfolio.equity()

        # daily stop
        if portfolio.daily_realized <= -eq * self.max_daily_loss_pct:
            return 0

        rps = abs(signal.entry - signal.stop)
        if rps <= 0:
            return 0

        capital_risk = eq * self.max_risk_per_trade_pct
        qty = int(capital_risk / rps)
        return max(qty, 0)

