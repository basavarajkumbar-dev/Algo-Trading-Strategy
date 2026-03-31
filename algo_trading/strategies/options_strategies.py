from __future__ import annotations

from typing import List

import pandas as pd

from algo_trading.models.core import OptionLeg, Signal
from algo_trading.strategies.base import BaseStrategy
from algo_trading.utils.strike_selector import select_strike


def _qty(config: dict) -> int:
    return int(config.get("lot_size", 50) * config.get("lots", 2))


class LongCallStrategy(BaseStrategy):
    name = "long_call"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        last = data.iloc[-1]
        if last["ema_fast"] <= last["ema_slow"]:
            return Signal(strategy=self.name, action="HOLD", reason="No bullish trend")
        strike = select_strike(option_chain, "CE", style="ATM")
        premium = float(option_chain[(option_chain["strike"] == strike) & (option_chain["type"] == "CE")]["premium"].iloc[0])
        sl = premium * 0.7
        target = premium + (premium - sl) * 2
        leg = OptionLeg(symbol=f"NIFTY{expiry}{int(strike)}CE", side="BUY", qty=_qty(self.config), strike=strike, option_type="CE", expiry=expiry, entry_price=premium)
        return Signal(strategy=self.name, action="ENTER", legs=[leg], stop_loss=sl, target=target, reason="EMA bullish crossover")


class LongPutStrategy(BaseStrategy):
    name = "long_put"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        last = data.iloc[-1]
        if last["ema_fast"] >= last["ema_slow"]:
            return Signal(strategy=self.name, action="HOLD", reason="No bearish trend")
        strike = select_strike(option_chain, "PE", style="ATM")
        premium = float(option_chain[(option_chain["strike"] == strike) & (option_chain["type"] == "PE")]["premium"].iloc[0])
        sl = premium * 0.7
        target = premium + (premium - sl) * 2
        leg = OptionLeg(symbol=f"NIFTY{expiry}{int(strike)}PE", side="BUY", qty=_qty(self.config), strike=strike, option_type="PE", expiry=expiry, entry_price=premium)
        return Signal(strategy=self.name, action="ENTER", legs=[leg], stop_loss=sl, target=target, reason="EMA bearish crossover")


class BullCallSpreadStrategy(BaseStrategy):
    name = "bull_call_spread"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        last = data.iloc[-1]
        if last["ema_fast"] <= last["ema_slow"]:
            return Signal(strategy=self.name, action="HOLD", reason="No bullish trend")
        buy_strike = select_strike(option_chain, "CE", style="ATM")
        sell_strike = buy_strike + 100
        buy_p = float(option_chain[(option_chain["strike"] == buy_strike) & (option_chain["type"] == "CE")]["premium"].iloc[0])
        sell_p = float(option_chain[(option_chain["strike"] == sell_strike) & (option_chain["type"] == "CE")]["premium"].iloc[0])
        net = buy_p - sell_p
        sl = net * 0.6
        target = net + (net - sl) * 2
        legs = [
            OptionLeg(symbol=f"NIFTY{expiry}{int(buy_strike)}CE", side="BUY", qty=_qty(self.config), strike=buy_strike, option_type="CE", expiry=expiry, entry_price=buy_p),
            OptionLeg(symbol=f"NIFTY{expiry}{int(sell_strike)}CE", side="SELL", qty=_qty(self.config), strike=sell_strike, option_type="CE", expiry=expiry, entry_price=sell_p),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=sl, target=target, reason="Bullish trend + debit spread")


class BearPutSpreadStrategy(BaseStrategy):
    name = "bear_put_spread"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        last = data.iloc[-1]
        if last["ema_fast"] >= last["ema_slow"]:
            return Signal(strategy=self.name, action="HOLD", reason="No bearish trend")
        buy_strike = select_strike(option_chain, "PE", style="ATM")
        sell_strike = buy_strike - 100
        buy_p = float(option_chain[(option_chain["strike"] == buy_strike) & (option_chain["type"] == "PE")]["premium"].iloc[0])
        sell_p = float(option_chain[(option_chain["strike"] == sell_strike) & (option_chain["type"] == "PE")]["premium"].iloc[0])
        net = buy_p - sell_p
        sl = net * 0.6
        target = net + (net - sl) * 2
        legs = [
            OptionLeg(symbol=f"NIFTY{expiry}{int(buy_strike)}PE", side="BUY", qty=_qty(self.config), strike=buy_strike, option_type="PE", expiry=expiry, entry_price=buy_p),
            OptionLeg(symbol=f"NIFTY{expiry}{int(sell_strike)}PE", side="SELL", qty=_qty(self.config), strike=sell_strike, option_type="PE", expiry=expiry, entry_price=sell_p),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=sl, target=target, reason="Bearish trend + debit spread")


class IronCondorStrategy(BaseStrategy):
    name = "iron_condor"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        spot = float(data["close"].iloc[-1])
        low_put = spot - 200
        short_put = spot - 100
        short_call = spot + 100
        high_call = spot + 200
        qty = _qty(self.config)
        legs: List[OptionLeg] = [
            OptionLeg(symbol=f"NIFTY{expiry}{int(short_put)}PE", side="SELL", qty=qty, strike=short_put, option_type="PE", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(low_put)}PE", side="BUY", qty=qty, strike=low_put, option_type="PE", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(short_call)}CE", side="SELL", qty=qty, strike=short_call, option_type="CE", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(high_call)}CE", side="BUY", qty=qty, strike=high_call, option_type="CE", expiry=expiry),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=120.0, target=240.0, reason="Range-bound with defined risk")


class ShortStraddleStrategy(BaseStrategy):
    name = "short_straddle"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        atm = select_strike(option_chain, "CE", style="ATM")
        qty = _qty(self.config)
        legs = [
            OptionLeg(symbol=f"NIFTY{expiry}{int(atm)}CE", side="SELL", qty=qty, strike=atm, option_type="CE", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(atm)}PE", side="SELL", qty=qty, strike=atm, option_type="PE", expiry=expiry),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=150.0, target=300.0, reason="Low movement volatility crush setup")


class ShortStrangleStrategy(BaseStrategy):
    name = "short_strangle"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        spot = float(data["close"].iloc[-1])
        qty = _qty(self.config)
        legs = [
            OptionLeg(symbol=f"NIFTY{expiry}{int(spot + 150)}CE", side="SELL", qty=qty, strike=spot + 150, option_type="CE", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(spot - 150)}PE", side="SELL", qty=qty, strike=spot - 150, option_type="PE", expiry=expiry),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=140.0, target=280.0, reason="Sideways to mild trend neutral income")


class ProtectivePutStrategy(BaseStrategy):
    name = "protective_put"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        spot = float(data["close"].iloc[-1])
        put_strike = select_strike(option_chain, "PE", style="ATM")
        qty = _qty(self.config)
        legs = [
            OptionLeg(symbol="NIFTY-FUT", side="BUY", qty=qty, strike=spot, option_type="FUT", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(put_strike)}PE", side="BUY", qty=qty, strike=put_strike, option_type="PE", expiry=expiry),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=100.0, target=200.0, reason="Hedge downside on long underlying")


class CoveredCallStrategy(BaseStrategy):
    name = "covered_call"

    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        spot = float(data["close"].iloc[-1])
        call_strike = spot + 100
        qty = _qty(self.config)
        legs = [
            OptionLeg(symbol="NIFTY-FUT", side="BUY", qty=qty, strike=spot, option_type="FUT", expiry=expiry),
            OptionLeg(symbol=f"NIFTY{expiry}{int(call_strike)}CE", side="SELL", qty=qty, strike=call_strike, option_type="CE", expiry=expiry),
        ]
        return Signal(strategy=self.name, action="ENTER", legs=legs, stop_loss=90.0, target=180.0, reason="Income on long underlying")
