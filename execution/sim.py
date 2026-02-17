from core.types import Fill, Side
from portfolio.costs_india import estimate_cost


class SimulatedExecution:
    def __init__(self, slippage_bps: float = 5.0):
        self.slippage_bps = slippage_bps

    def execute(self, order) -> Fill:
        px = float(order.price) if order.price is not None else 0.0
        slip = px * (self.slippage_bps / 10000.0)

        exec_px = px + slip if order.side == Side.BUY else px - slip
        fee = estimate_cost(order.quantity, exec_px)

        return Fill(
            symbol=order.symbol,
            side=order.side,
            quantity=order.quantity,
            price=exec_px,
            fee=fee,
            tag=order.tag,
        )

