from __future__ import annotations

from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import os


load_dotenv()


class KiteSettings(BaseModel):
    api_key: str = Field(default_factory=lambda: os.getenv("KITE_API_KEY", ""))
    api_secret: str = Field(default_factory=lambda: os.getenv("KITE_API_SECRET", ""))
    access_token: str = Field(default_factory=lambda: os.getenv("KITE_ACCESS_TOKEN", ""))


class RiskSettings(BaseModel):
    capital: float = 1_000_000
    lot_size: int = 50
    lots_fixed: int = 2
    max_risk_per_trade_pct: float = 0.02
    reward_to_risk: float = 2.0
    daily_loss_limit_pct: float = 0.05
    max_trades_per_day: int = 6


class EngineSettings(BaseModel):
    mode: str = "backtest"  # backtest | paper | live
    symbol: str = "NIFTY 50"
    timeframe: str = "5minute"
    from_date: str = "2024-01-01"
    to_date: str = "2024-12-31"


class AppSettings(BaseModel):
    kite: KiteSettings = Field(default_factory=KiteSettings)
    risk: RiskSettings = Field(default_factory=RiskSettings)
    engine: EngineSettings = Field(default_factory=EngineSettings)
    log_dir: Path = Path("logs")
    report_dir: Path = Path("reports")


SETTINGS = AppSettings()
