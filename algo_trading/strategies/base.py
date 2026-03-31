from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict

import pandas as pd

from algo_trading.models.core import Signal


class BaseStrategy(ABC):
    name: str = "base"

    def __init__(self, config: Dict):
        self.config = config

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame, option_chain: pd.DataFrame, expiry: str) -> Signal:
        ...
