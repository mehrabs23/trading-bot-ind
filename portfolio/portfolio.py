from dataclasses import dataclass


@dataclass
class Position:
    qty: int = 0
    avg: float = 0.0


class Portfolio:
    def __init__(self, initial_capital: float):
        self.initial_capital = initial_capital
        self.realized_pnl = 0.0
        self.daily_realized = 0.0
        self.pos = {}  # symbol -> Position

    def get_pos(self, symbol: str) -> Position:
        if symbol not in self.pos:
            self.pos[symbol] = Position()
        return self.pos[symbol]

    def update_fill(self, fill):
        p = self.get_pos(fill.symbol)
        q = fill.quantity if fill.side == "BUY" else -fill.quantity

        # If position flips or closes, realize pnl on the closing part.
        if p.qty != 0 and (p.qty > 0) != (q > 0):
            # close entire position (we’ll support partial later)
            pnl = (fill.price - p.avg) * p.qty
            self.realized_pnl += pnl
            self.daily_realized += pnl
            p.qty = 0
            p.avg = 0.0
        else:
            p.qty += q
            p.avg = fill.price

    def equity(self) -> float:
        return self.initial_capital + self.realized_pnl

