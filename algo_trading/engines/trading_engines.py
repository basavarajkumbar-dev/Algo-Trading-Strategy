from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import uuid

import pandas as pd

from algo_trading.config.settings import SETTINGS
from algo_trading.data.kite_data import KiteDataHandler
from algo_trading.engines.execution_engine import ExecutionEngine
from algo_trading.models.core import Trade
from algo_trading.risk.risk_manager import RiskManager
from algo_trading.selector.strategy_selector import StrategySelector
from algo_trading.strategies import STRATEGY_REGISTRY
from algo_trading.utils.indicators import add_indicators


class BaseTradingEngine:
    def __init__(self, live: bool = False):
        self.data_handler = KiteDataHandler()
        self.selector = StrategySelector()
        self.risk = RiskManager(SETTINGS.risk)
        self.executor = ExecutionEngine(self.data_handler.kite if live else None)
        self.trades: list[Trade] = []
        self.log_path = SETTINGS.log_dir / f"trades_{'live' if live else 'paper'}.csv"
        Path(SETTINGS.log_dir).mkdir(parents=True, exist_ok=True)

    def evaluate_and_trade(self, instrument_token: int | None = None) -> Trade | None:
        data = self.data_handler.get_historical_data(instrument_token, SETTINGS.engine.from_date, SETTINGS.engine.to_date)
        data = add_indicators(data)
        state = self.selector.detect_market_state(data)
        picked = self.selector.choose(state)

        expiry = self.data_handler.nearest_expiry()
        option_chain = self.data_handler.get_option_chain_snapshot(state.price, expiry)
        strategy = STRATEGY_REGISTRY[picked.strategy]({"lot_size": SETTINGS.risk.lot_size, "lots": SETTINGS.risk.lots_fixed})
        signal = strategy.generate_signal(data, option_chain, expiry)

        ok, reason = self.risk.can_take_trade(signal)
        if not ok:
            return None

        self.executor.execute_signal(signal)
        trade = Trade(trade_id=str(uuid.uuid4()), strategy=signal.strategy, timestamp=datetime.utcnow(), legs=signal.legs)
        self.trades.append(trade)
        self.risk.register_trade()
        self._log_trade(trade, picked.probability, reason)
        return trade

    def _log_trade(self, trade: Trade, probability: float, reason: str) -> None:
        rows = []
        for leg in trade.legs:
            r = asdict(leg)
            r.update({"trade_id": trade.trade_id, "strategy": trade.strategy, "ts": trade.timestamp.isoformat(), "probability": probability, "risk_check": reason})
            rows.append(r)
        df = pd.DataFrame(rows)
        write_header = not self.log_path.exists()
        df.to_csv(self.log_path, mode="a", header=write_header, index=False)


class PaperTradingEngine(BaseTradingEngine):
    def __init__(self):
        super().__init__(live=False)


class LiveTradingEngine(BaseTradingEngine):
    def __init__(self):
        super().__init__(live=True)
