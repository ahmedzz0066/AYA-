"""Volume footprint reconstruction from OHLCV, derived from first principles.

See docs/DERIVATION.md for the full derivation.  The short version: price is
continuous (A1), volume accrues in proportion to distance travelled (A2), and
upward travel is buy-initiated (A3).  Everything else follows.
"""

from .core import (
    Bar,
    BarProfile,
    FootprintConfig,
    Leg,
    Row,
    build_profile,
    buy_share,
    decompose,
    overlap_coefficient,
    path_weights,
    session_profile,
    value_area,
)
from .render import render_dashboard, render_footprint, render_profile

__version__ = "1.0.0"

__all__ = [
    "Bar",
    "BarProfile",
    "FootprintConfig",
    "Leg",
    "Row",
    "build_profile",
    "buy_share",
    "decompose",
    "overlap_coefficient",
    "path_weights",
    "render_dashboard",
    "render_footprint",
    "render_profile",
    "session_profile",
    "value_area",
]
