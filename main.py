from __future__ import annotations

import argparse

from algo_trading.config.settings import SETTINGS
from algo_trading.data.kite_data import KiteDataHandler
from algo_trading.engines.backtest_engine import BacktestEngine
from algo_trading.engines.trading_engines import LiveTradingEngine, PaperTradingEngine
from algo_trading.selector.strategy_selector import StrategySelector
from algo_trading.utils.reporting import save_backtest_report


def run_backtest() -> None:
    data_handler = KiteDataHandler()
    selector = StrategySelector()
    strategy_config = {"lot_size": SETTINGS.risk.lot_size, "lots": SETTINGS.risk.lots_fixed}
    engine = BacktestEngine(data_handler, selector, strategy_config)
    result = engine.run(None, SETTINGS.engine.from_date, SETTINGS.engine.to_date)
    report_path = save_backtest_report(result)
    print("Backtest complete")
    print(f"Total PnL: {result.total_pnl:.2f}, Win rate: {result.win_rate:.2f}% Drawdown: {result.max_drawdown:.2f}")
    print(f"Report: {report_path}")


def run_paper() -> None:
    engine = PaperTradingEngine()
    trade = engine.evaluate_and_trade()
    print("Paper trade executed" if trade else "No paper trade (risk/conditions not met)")


def run_live() -> None:
    if not SETTINGS.kite.api_key or not SETTINGS.kite.access_token:
        raise ValueError("Set KITE_API_KEY and KITE_ACCESS_TOKEN for live trading")
    engine = LiveTradingEngine()
    trade = engine.evaluate_and_trade()
    print("Live trade executed" if trade else "No live trade (risk/conditions not met)")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Nifty Options Algo Trading")
    p.add_argument("--mode", choices=["backtest", "paper", "live"], default="backtest")
    return p


if __name__ == "__main__":
    args = build_parser().parse_args()
    if args.mode == "backtest":
        run_backtest()
    elif args.mode == "paper":
        run_paper()
    else:
        run_live()
