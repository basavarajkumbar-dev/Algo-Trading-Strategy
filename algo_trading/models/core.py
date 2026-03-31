from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class OptionLeg:
    symbol: str
    side: str  # BUY | SELL
    qty: int
    strike: float
    option_type: str  # CE | PE
    expiry: str
    entry_price: float = 0.0
    exit_price: Optional[float] = None


@dataclass
class Signal:
    strategy: str
    action: str  # ENTER | EXIT | HOLD
    legs: List[OptionLeg] = field(default_factory=list)
    stop_loss: Optional[float] = None
    target: Optional[float] = None
    reason: str = ""


@dataclass
class Trade:
    trade_id: str
    strategy: str
    timestamp: datetime
    legs: List[OptionLeg]
    status: str = "OPEN"
    pnl: float = 0.0


@dataclass
class MarketState:
    trend: str  # bullish | bearish | sideways
    volatility: str  # low | medium | high
    atr: float
    vix: float
    price: float
