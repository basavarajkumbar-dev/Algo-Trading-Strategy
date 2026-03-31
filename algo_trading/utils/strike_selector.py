from __future__ import annotations

import pandas as pd


def select_strike(option_chain: pd.DataFrame, option_type: str, style: str = "ATM", delta_target: float | None = None) -> float:
    chain = option_chain[option_chain["type"] == option_type].copy()
    if delta_target is not None:
        idx = (chain["delta"] - delta_target).abs().idxmin()
        return float(chain.loc[idx, "strike"])

    spot = chain["strike"].median()
    if style == "ATM":
        idx = (chain["strike"] - spot).abs().idxmin()
    elif style == "ITM":
        if option_type == "CE":
            idx = chain[chain["strike"] <= spot]["strike"].idxmax()
        else:
            idx = chain[chain["strike"] >= spot]["strike"].idxmin()
    else:  # OTM
        if option_type == "CE":
            idx = chain[chain["strike"] >= spot]["strike"].idxmin()
        else:
            idx = chain[chain["strike"] <= spot]["strike"].idxmax()
    return float(chain.loc[idx, "strike"])
