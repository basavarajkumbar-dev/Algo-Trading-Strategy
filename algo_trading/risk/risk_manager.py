from __future__ import annotations

from dataclasses import dataclass

from algo_trading.config.settings import RiskSettings
from algo_trading.models.core import Signal


@dataclass
class RiskState:
    day_loss: float = 0.0
    trades_taken: int = 0


class RiskManager:
    def __init__(self, settings: RiskSettings):
        self.settings = settings
        self.state = RiskState()

    def can_take_trade(self, signal: Signal) -> tuple[bool, str]:
        if signal.action != "ENTER":
            return False, "No entry signal"
        if self.state.trades_taken >= self.settings.max_trades_per_day:
            return False, "Max trades hit"
        if abs(self.state.day_loss) >= self.settings.capital * self.settings.daily_loss_limit_pct:
            return False, "Daily loss limit reached"
        if not self._is_valid_rr(signal):
            return False, "Risk:Reward validation failed"

        trade_risk = self.estimate_trade_risk(signal)
        if trade_risk > self.settings.capital * self.settings.max_risk_per_trade_pct:
            return False, "Risk per trade exceeded"
        return True, "OK"

    def _is_valid_rr(self, signal: Signal) -> bool:
        if signal.stop_loss is None or signal.target is None:
            return False
        risk = signal.stop_loss
        reward = signal.target - signal.stop_loss
        if risk <= 0:
            return False
        rr = reward / risk
        return rr >= self.settings.reward_to_risk - 1e-6

    def estimate_trade_risk(self, signal: Signal) -> float:
        if signal.stop_loss is None:
            return 0.0
        qty = max(sum(leg.qty for leg in signal.legs), 1)
        return float(signal.stop_loss * qty)

    def register_trade(self) -> None:
        self.state.trades_taken += 1

    def register_pnl(self, pnl: float) -> None:
        self.state.day_loss += min(pnl, 0)
