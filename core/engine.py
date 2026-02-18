from dataclasses import asdict
from typing import List, Optional
from core.types import RunMode, Side, Order, Signal, MarketBar
from execution.sim import SimulatedExecution
from portfolio.portfolio import Portfolio
from risk.governor import RiskGovernor
from data.calendar_nse import FORCE_SQUAREOFF


class Engine:
    def __init__(self, strategy, mode: RunMode, initial_capital: float = 100000.0):
        self.strategy = strategy
        self.mode = mode

        self.portfolio = Portfolio(initial_capital)
        self.exec = SimulatedExecution()
        self.risk = RiskGovernor()

        self.active: Optional[dict] = None  # {symbol, side, qty, entry, stop}
        self.trades: List[dict] = []
        self.signals: List[Signal] = []
        self.equity_curve: List[dict] = []

    def _enter(self, sig: Signal, ts):
        if not self.risk.allow_entry_time(ts):
            return

        qty = self.risk.size_position(self.portfolio, sig)
        if qty <= 0:
            return

        o = Order(symbol=sig.symbol, side=sig.side, quantity=qty, price=sig.entry, tag="entry")
        f = self.exec.execute(o)
        self.portfolio.update_fill(f)

        self.active = {
            "symbol": sig.symbol,
            "side": sig.side,
            "qty": qty,
            "entry": f.price,
            "stop": sig.stop,
            "reason": sig.reasoning,
        }

    def _exit(self, price: float, tag: str):
        if not self.active:
            return

        side = Side.SELL if self.active["side"] == Side.BUY else Side.BUY
        qty = int(self.active["qty"])
        sym = self.active["symbol"]

        o = Order(symbol=sym, side=side, quantity=qty, price=price, tag=tag)
        f = self.exec.execute(o)
        self.portfolio.update_fill(f)

        self.trades.append(
            {
                "symbol": sym,
                "entry": self.active["entry"],
                "exit": f.price,
                "qty": qty,
                "side": self.active["side"].value,
                "reason": self.active["reason"],
                "exit_tag": tag,
                "pnl_est": (f.price - self.active["entry"]) * (qty if self.active["side"] == Side.BUY else -qty),
                "exit_time": self.equity_curve[-1]["timestamp"] if self.equity_curve else None
            }
        )
        self.active = None

    def run(self, bars: List[MarketBar]):
        for bar in bars:
            # Update equity curve first
            self.equity_curve.append({
                "timestamp": bar.timestamp,
                "equity": self.portfolio.equity()
            })

            sig = self.strategy.on_bar(bar)

            if self.mode == RunMode.SIGNAL:
                if sig:
                    self.signals.append(sig)
                continue

            # BACKTEST mode below
            if sig and self.active is None:
                self._enter(sig, bar.timestamp)

            # Stop-loss check
            if self.active:
                stop = float(self.active["stop"])
                if self.active["side"] == Side.BUY and bar.low <= stop:
                    self._exit(stop, "stop")
                elif self.active["side"] == Side.SELL and bar.high >= stop:
                    self._exit(stop, "stop")

            # EOD squareoff safety
            if self.active and bar.timestamp.time() >= FORCE_SQUAREOFF:
                self._exit(bar.close, "eod_squareoff")

        return self.summary()

    def summary(self):
        wins = [t for t in self.trades if t['pnl_est'] > 0]
        win_rate = len(wins) / len(self.trades) if self.trades else 0.0

        return {
            "final_equity": self.portfolio.equity(),
            "realized_pnl": self.portfolio.realized_pnl,
            "daily_realized": self.portfolio.daily_realized,
            "num_trades": len(self.trades),
            "win_rate": win_rate,
            "trades": self.trades,
            "num_signals": len(self.signals),
            "equity_curve": self.equity_curve,
        }

