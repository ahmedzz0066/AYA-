"""Kairometric Field Theory (KFT) — an original smart-money trading framework.

See METHODOLOGY.md for the full mathematical specification.
"""

from .strategy import KFTParams, build_features  # noqa: F401
from .backtest import Backtester, metrics  # noqa: F401
