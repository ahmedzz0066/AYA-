"""XAUUSD M5 3:1 limit-order strategy engine.

Zero third-party dependencies on purpose: the fewer moving parts, the fewer
ways a backtest can lie to you.
"""

__all__ = [
    "data",
    "indicators",
    "strategy",
    "broker",
    "backtest",
    "metrics",
    "walkforward",
]
