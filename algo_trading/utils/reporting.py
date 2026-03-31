from __future__ import annotations

from pathlib import Path

import pandas as pd

from algo_trading.config.settings import SETTINGS
from algo_trading.engines.backtest_engine import BacktestResult


def save_backtest_report(result: BacktestResult, name: str = "backtest_report") -> Path:
    SETTINGS.report_dir.mkdir(parents=True, exist_ok=True)
    summary_path = SETTINGS.report_dir / f"{name}_summary.csv"
    strat_path = SETTINGS.report_dir / f"{name}_strategy_stats.csv"

    pd.DataFrame(
        [
            {
                "total_pnl": result.total_pnl,
                "win_rate": result.win_rate,
                "max_drawdown": result.max_drawdown,
            }
        ]
    ).to_csv(summary_path, index=False)
    result.strategy_stats.to_csv(strat_path)
    return summary_path
