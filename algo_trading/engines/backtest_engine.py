from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from algo_trading.data.kite_data import KiteDataHandler
from algo_trading.selector.strategy_selector import StrategySelector
from algo_trading.strategies import STRATEGY_REGISTRY
from algo_trading.utils.indicators import add_indicators


@dataclass
class BacktestResult:
    total_pnl: float
    win_rate: float
    max_drawdown: float
    strategy_stats: pd.DataFrame


class BacktestEngine:
    def __init__(self, data_handler: KiteDataHandler, selector: StrategySelector, strategy_config: dict):
        self.data_handler = data_handler
        self.selector = selector
        self.strategy_config = strategy_config

    def run(self, instrument_token: int | None, from_date: str, to_date: str) -> BacktestResult:
        data = self.data_handler.get_historical_data(instrument_token, from_date, to_date)
        data = add_indicators(data)
        expiry = self.data_handler.nearest_expiry()
        pnl_series = []
        logs = []

        step = 30
        for i in range(step, len(data), step):
            window = data.iloc[: i + 1]
            state = self.selector.detect_market_state(window)
            picked = self.selector.choose(state)
            strategy_cls = STRATEGY_REGISTRY[picked.strategy]
            strategy = strategy_cls(self.strategy_config)
            option_chain = self.data_handler.get_option_chain_snapshot(float(window["close"].iloc[-1]), expiry)
            signal = strategy.generate_signal(window, option_chain, expiry)
            if signal.action != "ENTER":
                continue
            outcome = np.random.choice([1, -1], p=[picked.probability / 100, 1 - picked.probability / 100])
            risk = max(signal.stop_loss or 50, 1)
            pnl = risk * 2 if outcome > 0 else -risk
            pnl_series.append(pnl)
            logs.append({"strategy": picked.strategy, "pnl": pnl, "probability": picked.probability})

        if not pnl_series:
            return BacktestResult(0.0, 0.0, 0.0, pd.DataFrame())

        trades = pd.DataFrame(logs)
        cum = trades["pnl"].cumsum()
        drawdown = (cum - cum.cummax()).min()
        stats = trades.groupby("strategy").agg(
            trades=("pnl", "count"),
            pnl=("pnl", "sum"),
            win_rate=("pnl", lambda s: (s > 0).mean() * 100),
            avg_probability=("probability", "mean"),
        ).sort_values("pnl", ascending=False)
        return BacktestResult(
            total_pnl=float(trades["pnl"].sum()),
            win_rate=float((trades["pnl"] > 0).mean() * 100),
            max_drawdown=float(drawdown),
            strategy_stats=stats,
        )
