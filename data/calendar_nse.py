from datetime import time

MARKET_OPEN = time(9, 15)
MARKET_CLOSE = time(15, 30)

# For intraday safety; configurable later.
ENTRY_CUTOFF = time(15, 10)
FORCE_SQUAREOFF = time(15, 20)

