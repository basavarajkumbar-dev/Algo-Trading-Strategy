# Nifty Options Algo Trading System (Kite Connect)

Production-style modular Python system for **Nifty options** that supports:

- Strategy selection with market regime detection
- Backtesting on historical data
- Paper trading (live simulation)
- Live trading with Kite Connect order execution
- Streamlit monitoring dashboard

## 1) Features

### Supported strategies
- Directional: Long Call, Long Put, Bull Call Spread, Bear Put Spread
- Neutral/Income: Iron Condor, Short Straddle, Short Strangle
- Hedged: Protective Put, Covered Call

Each strategy supports configurable entry, stop-loss, target (1:2 risk-reward), and multi-leg orders.

### Strategy selection engine
- Market state classification: bullish / bearish / sideways
- Inputs: EMA trend, ATR volatility/range context
- Selection logic maps market state to suitable strategies
- Uses historical win rate + risk-reward consistency to choose highest probability strategy

### Risk controls (strict)
- Fixed lot size: 2 lots (`lots_fixed`)
- Reward:Risk = 2:1
- Max risk/trade (default 2% capital)
- Daily loss limit
- Max trades per day

## 2) Project structure

```text
algo_trading/
  config/settings.py
  data/kite_data.py
  dashboard/streamlit_app.py
  engines/
    backtest_engine.py
    execution_engine.py
    trading_engines.py
  models/core.py
  risk/risk_manager.py
  selector/strategy_selector.py
  strategies/
    base.py
    options_strategies.py
  utils/
    indicators.py
    strike_selector.py
    reporting.py
main.py
tests/
```

## 3) Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 4) Where to add API keys

Create a `.env` file in project root:

```env
KITE_API_KEY=your_api_key
KITE_API_SECRET=your_api_secret
KITE_ACCESS_TOKEN=your_access_token
```

The app reads these variables through `python-dotenv` in `algo_trading/config/settings.py`.

> Live trading requires valid `KITE_API_KEY` + `KITE_ACCESS_TOKEN`.

## 5) Run modes

### Backtest
```bash
python main.py --mode backtest
```
Outputs summary and CSV reports under `reports/`.

### Paper trading (live simulation)
```bash
python main.py --mode paper
```
Writes paper trade logs into `logs/trades_paper.csv`.

### Live trading
```bash
python main.py --mode live
```
Places live orders through Kite (`NFO`, `NRML`, `MARKET`) and logs into `logs/trades_live.csv`.

## 6) Streamlit dashboard

```bash
streamlit run algo_trading/dashboard/streamlit_app.py
```

Dashboard shows:
- Running backtest summary
- Strategy comparison table
- Paper/live trade logs

## 7) Configuration

Tune in `algo_trading/config/settings.py`:
- Capital and risk limits
- Lot size and fixed lots
- Backtest date range
- Symbol/timeframe defaults

## 8) Testing

```bash
pytest -q
```

Includes unit tests for:
- Strategy selection
- Risk manager constraints
- Strategy signal generation

## 9) Production hardening checklist

- Replace synthetic option-chain fallback with broker chain snapshot source
- Add persistent DB (PostgreSQL) for trades, metrics, and audit trail
- Add websocket feed + event-driven execution loop
- Add secrets manager and token refresh workflow
- Add slippage/transaction cost model and realistic fill simulation
- Add ML selector model retraining job + model registry
- Add alerting (Telegram/Slack) and circuit-breakers

