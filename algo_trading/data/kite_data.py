from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

import numpy as np
import pandas as pd

try:
    from kiteconnect import KiteConnect
except Exception:  # pragma: no cover
    KiteConnect = None

from algo_trading.config.settings import SETTINGS


class KiteDataHandler:
    """Wrapper for Kite Connect historical/live/options data APIs."""

    def __init__(self) -> None:
        self.kite = None
        if KiteConnect and SETTINGS.kite.api_key:
            self.kite = KiteConnect(api_key=SETTINGS.kite.api_key)
            if SETTINGS.kite.access_token:
                self.kite.set_access_token(SETTINGS.kite.access_token)

    def _synthetic_ohlc(self, from_date: str, to_date: str, timeframe: str = "5min") -> pd.DataFrame:
        idx = pd.date_range(from_date, to_date, freq="5min")
        base = 22000 + np.cumsum(np.random.normal(0, 4, len(idx)))
        df = pd.DataFrame(index=idx)
        df["open"] = base
        df["high"] = base + np.abs(np.random.normal(3, 2, len(idx)))
        df["low"] = base - np.abs(np.random.normal(3, 2, len(idx)))
        df["close"] = base + np.random.normal(0, 2, len(idx))
        df["volume"] = np.random.randint(1000, 5000, len(idx))
        return df

    def get_historical_data(
        self,
        instrument_token: int | None,
        from_date: str,
        to_date: str,
        interval: str = "5minute",
    ) -> pd.DataFrame:
        if self.kite and instrument_token:
            candles = self.kite.historical_data(instrument_token, from_date, to_date, interval)
            df = pd.DataFrame(candles)
            if not df.empty:
                df["date"] = pd.to_datetime(df["date"])
                df = df.set_index("date")
                return df
        return self._synthetic_ohlc(from_date, to_date)

    def get_ltp(self, symbols: List[str]) -> Dict[str, Any]:
        if self.kite:
            return self.kite.ltp(symbols)
        return {s: {"last_price": 100 + np.random.random() * 20} for s in symbols}

    def get_option_chain_snapshot(self, spot: float, expiry: str) -> pd.DataFrame:
        strikes = np.arange(round(spot / 50) * 50 - 500, round(spot / 50) * 50 + 550, 50)
        rows = []
        for strike in strikes:
            moneyness = abs(spot - strike)
            iv = max(8, 18 + np.random.normal(0, 2))
            ce_price = max(5.0, max(spot - strike, 0) + 40 - moneyness * 0.06)
            pe_price = max(5.0, max(strike - spot, 0) + 40 - moneyness * 0.06)
            rows.extend(
                [
                    {"strike": strike, "type": "CE", "expiry": expiry, "premium": ce_price, "iv": iv, "delta": 0.5 - (strike - spot) / 1000},
                    {"strike": strike, "type": "PE", "expiry": expiry, "premium": pe_price, "iv": iv, "delta": -0.5 - (strike - spot) / 1000},
                ]
            )
        return pd.DataFrame(rows)

    def nearest_expiry(self) -> str:
        today = datetime.utcnow().date()
        days_ahead = (3 - today.weekday()) % 7
        if days_ahead == 0:
            days_ahead = 7
        return str(today + timedelta(days=days_ahead))
