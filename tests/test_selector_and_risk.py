import pandas as pd

from algo_trading.config.settings import RiskSettings
from algo_trading.data.kite_data import KiteDataHandler
from algo_trading.engines.backtest_engine import BacktestEngine
from algo_trading.models.core import Signal
from algo_trading.risk.risk_manager import RiskManager
from algo_trading.selector.strategy_selector import StrategySelector
from algo_trading.strategies.options_strategies import LongCallStrategy


def test_selector_picks_bullish_strategy():
    data = pd.DataFrame(
        {
            "close": [100, 105, 110],
            "ema_fast": [101, 106, 111],
            "ema_slow": [99, 102, 108],
            "atr": [1.2, 1.1, 1.0],
        }
    )
    selector = StrategySelector()
    state = selector.detect_market_state(data)
    choice = selector.choose(state)
    assert choice.strategy in {"bull_call_spread", "long_call", "covered_call", "protective_put"}


def test_risk_manager_blocks_invalid_rr():
    rm = RiskManager(RiskSettings(capital=100000, reward_to_risk=2.0))
    sig = Signal(strategy="x", action="ENTER", stop_loss=100, target=250, legs=[])
    ok, reason = rm.can_take_trade(sig)
    assert not ok
    assert "Risk:Reward" in reason


def test_long_call_generates_entry_and_valid_rr():
    stg = LongCallStrategy({"lot_size": 50, "lots": 2})
    data = pd.DataFrame([{"ema_fast": 110, "ema_slow": 100, "close": 22000}])
    chain = pd.DataFrame([
        {"strike": 22000, "type": "CE", "premium": 100, "delta": 0.5},
        {"strike": 22000, "type": "PE", "premium": 95, "delta": -0.5},
    ])
    signal = stg.generate_signal(data, chain, "2026-04-02")
    assert signal.action == "ENTER"
    assert (signal.target - signal.stop_loss) / signal.stop_loss >= 2


def test_backtest_runs_and_produces_metrics():
    engine = BacktestEngine(KiteDataHandler(), StrategySelector(), {"lot_size": 50, "lots": 2})
    result = engine.run(None, "2024-01-01", "2024-01-10")
    assert isinstance(result.total_pnl, float)
    assert isinstance(result.win_rate, float)
