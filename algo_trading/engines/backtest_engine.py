from __future__ import annotations

from dataclasses import dataclass

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

    @staticmethod
    def _direction_bias(strategy_name: str) -> int:
        bullish = {"long_call", "bull_call_spread", "covered_call", "protective_put"}
        bearish = {"long_put", "bear_put_spread"}
        neutral = {"iron_condor", "short_straddle", "short_strangle"}
        if strategy_name in bullish:
            return 1
        if strategy_name in bearish:
            return -1
        if strategy_name in neutral:
            return 0
        return 0

    def _evaluate_trade(self, strategy_name: str, signal_stop: float, price_now: float, price_next: float) -> float:
        risk = max(signal_stop, 1.0)
        bias = self._direction_bias(strategy_name)
        if bias == 0:
            moved = abs(price_next - price_now)
            return risk * 2 if moved <= price_now * 0.002 else -risk
        price_move = price_next - price_now
        is_win = (price_move > 0 and bias > 0) or (price_move < 0 and bias < 0)
        return risk * 2 if is_win else -risk

    def run(self, instrument_token: int | None, from_date: str, to_date: str) -> BacktestResult:
        data = self.data_handler.get_historical_data(instrument_token, from_date, to_date)
        data = add_indicators(data)
        expiry = self.data_handler.nearest_expiry()
        logs = []

        step = 30
        for i in range(step, len(data) - step, step):
            window = data.iloc[: i + 1]
            state = self.selector.detect_market_state(window)
            picked = self.selector.choose(state)
            strategy_cls = STRATEGY_REGISTRY[picked.strategy]
            strategy = strategy_cls(self.strategy_config)
            option_chain = self.data_handler.get_option_chain_snapshot(float(window["close"].iloc[-1]), expiry)
            signal = strategy.generate_signal(window, option_chain, expiry)
            if signal.action != "ENTER":
                continue

            price_now = float(window["close"].iloc[-1])
            price_next = float(data["close"].iloc[i + step])
            pnl = self._evaluate_trade(picked.strategy, float(signal.stop_loss or 0), price_now, price_next)
            logs.append({"strategy": picked.strategy, "pnl": pnl, "probability": picked.probability})

        if not logs:
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
