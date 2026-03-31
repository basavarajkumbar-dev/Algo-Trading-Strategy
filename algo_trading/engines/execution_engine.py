from __future__ import annotations

import logging
import time
from typing import List

from algo_trading.models.core import Signal, Trade


class ExecutionEngine:
    def __init__(self, kite_client=None):
        self.kite = kite_client
        self.logger = logging.getLogger(self.__class__.__name__)

    def execute_signal(self, signal: Signal) -> List[str]:
        order_ids = []
        for leg in signal.legs:
            order_ids.append(self._place_order_with_retry(leg.symbol, leg.side, leg.qty))
        return order_ids

    def _place_order_with_retry(self, symbol: str, side: str, qty: int, retries: int = 3) -> str:
        for attempt in range(1, retries + 1):
            try:
                if self.kite:
                    order_id = self.kite.place_order(
                        variety="regular",
                        exchange="NFO",
                        tradingsymbol=symbol,
                        transaction_type=side,
                        quantity=qty,
                        order_type="MARKET",
                        product="NRML",
                    )
                    return str(order_id)
                return f"SIM-{symbol}-{int(time.time())}"
            except Exception as exc:  # pragma: no cover
                self.logger.warning("Order failed %s/%s for %s: %s", attempt, retries, symbol, exc)
                time.sleep(0.5)
        raise RuntimeError(f"Could not place order for {symbol}")

    def close_trade(self, trade: Trade) -> None:
        trade.status = "CLOSED"
