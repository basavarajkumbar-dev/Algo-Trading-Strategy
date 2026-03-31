from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from algo_trading.models.core import MarketState


@dataclass
class StrategyScore:
    strategy: str
    probability: float


class StrategySelector:
    def __init__(self, historical_metrics: pd.DataFrame | None = None):
        self.metrics = historical_metrics if historical_metrics is not None else pd.DataFrame(
            [
                {"strategy": "bull_call_spread", "win_rate": 0.62, "rr_consistency": 0.71},
                {"strategy": "long_call", "win_rate": 0.55, "rr_consistency": 0.64},
                {"strategy": "bear_put_spread", "win_rate": 0.61, "rr_consistency": 0.69},
                {"strategy": "long_put", "win_rate": 0.54, "rr_consistency": 0.63},
                {"strategy": "iron_condor", "win_rate": 0.66, "rr_consistency": 0.72},
                {"strategy": "short_straddle", "win_rate": 0.58, "rr_consistency": 0.60},
                {"strategy": "short_strangle", "win_rate": 0.60, "rr_consistency": 0.64},
            ]
        )

    def detect_market_state(self, data: pd.DataFrame) -> MarketState:
        last = data.iloc[-1]
        trend = "bullish" if last["ema_fast"] > last["ema_slow"] else "bearish"
        if abs(last["ema_fast"] - last["ema_slow"]) < last["atr"] * 0.1:
            trend = "sideways"
        vol = "high" if last["atr"] / last["close"] > 0.006 else "medium"
        return MarketState(trend=trend, volatility=vol, atr=float(last["atr"]), vix=15.0, price=float(last["close"]))

    def shortlist(self, state: MarketState) -> list[str]:
        if state.trend == "bullish":
            return ["bull_call_spread", "long_call", "covered_call", "protective_put"]
        if state.trend == "bearish":
            return ["bear_put_spread", "long_put", "protective_put"]
        return ["iron_condor", "short_straddle", "short_strangle"]

    def choose(self, state: MarketState) -> StrategyScore:
        candidates = self.shortlist(state)
        df = self.metrics[self.metrics["strategy"].isin(candidates)].copy()
        df["probability"] = (0.7 * df["win_rate"] + 0.3 * df["rr_consistency"]) * 100
        best = df.sort_values("probability", ascending=False).iloc[0]
        return StrategyScore(strategy=str(best["strategy"]), probability=float(best["probability"]))
