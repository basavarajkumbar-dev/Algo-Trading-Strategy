from __future__ import annotations

import pandas as pd


try:
    import pandas_ta as ta
except Exception:  # pragma: no cover
    ta = None


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["ema_fast"] = out["close"].ewm(span=20).mean()
    out["ema_slow"] = out["close"].ewm(span=50).mean()
    if ta is not None:
        out["atr"] = ta.atr(out["high"], out["low"], out["close"], length=14)
    else:
        tr = (out["high"] - out["low"]).rolling(14).mean()
        out["atr"] = tr
    out["range_pct"] = (out["high"].rolling(20).max() - out["low"].rolling(20).min()) / out["close"]
    return out.dropna()
