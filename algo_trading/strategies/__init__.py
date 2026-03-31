from algo_trading.strategies.options_strategies import (
    BearPutSpreadStrategy,
    BullCallSpreadStrategy,
    CoveredCallStrategy,
    IronCondorStrategy,
    LongCallStrategy,
    LongPutStrategy,
    ProtectivePutStrategy,
    ShortStraddleStrategy,
    ShortStrangleStrategy,
)


STRATEGY_REGISTRY = {
    "long_call": LongCallStrategy,
    "long_put": LongPutStrategy,
    "bull_call_spread": BullCallSpreadStrategy,
    "bear_put_spread": BearPutSpreadStrategy,
    "iron_condor": IronCondorStrategy,
    "short_straddle": ShortStraddleStrategy,
    "short_strangle": ShortStrangleStrategy,
    "protective_put": ProtectivePutStrategy,
    "covered_call": CoveredCallStrategy,
}
