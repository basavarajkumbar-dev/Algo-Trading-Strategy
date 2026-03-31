from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from algo_trading.config.settings import SETTINGS
from algo_trading.data.kite_data import KiteDataHandler
from algo_trading.engines.backtest_engine import BacktestEngine
from algo_trading.selector.strategy_selector import StrategySelector


st.set_page_config(page_title="Nifty Options Algo Dashboard", layout="wide")
st.title("Nifty Options Algo Trading Dashboard")

col1, col2, col3 = st.columns(3)
with col1:
    run_backtest = st.button("Run Backtest")
with col2:
    st.metric("Capital", f"₹{SETTINGS.risk.capital:,.0f}")
with col3:
    st.metric("Risk Per Trade", f"{SETTINGS.risk.max_risk_per_trade_pct*100:.1f}%")

if run_backtest:
    dh = KiteDataHandler()
    selector = StrategySelector()
    be = BacktestEngine(dh, selector, {"lot_size": SETTINGS.risk.lot_size, "lots": SETTINGS.risk.lots_fixed})
    result = be.run(None, SETTINGS.engine.from_date, SETTINGS.engine.to_date)
    st.subheader("Backtest Summary")
    s1, s2, s3 = st.columns(3)
    s1.metric("Total P&L", f"₹{result.total_pnl:,.2f}")
    s2.metric("Win Rate", f"{result.win_rate:.2f}%")
    s3.metric("Max Drawdown", f"₹{result.max_drawdown:,.2f}")

    if not result.strategy_stats.empty:
        st.subheader("Strategy Comparison")
        st.dataframe(result.strategy_stats)

st.subheader("Live/Paper Trade Logs")
for log in [SETTINGS.log_dir / "trades_paper.csv", SETTINGS.log_dir / "trades_live.csv"]:
    if Path(log).exists():
        st.write(log.name)
        st.dataframe(pd.read_csv(log).tail(20))
