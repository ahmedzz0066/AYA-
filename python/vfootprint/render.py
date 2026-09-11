"""Terminal rendering of reconstructed footprints.

A footprint is a table, not a chart: one column per bar, one row per price level,
buy volume on the right of the split and sell volume on the left.  That layout is
the whole reason the format exists -- it puts the two sides of the same price
next to each other so the diagonal comparison is a glance rather than a
calculation.
"""

from __future__ import annotations

from typing import Sequence

from .core import BarProfile, FootprintConfig, Row, session_profile

__all__ = ["render_footprint", "render_profile", "render_dashboard"]

# Markers annotate rows without needing colour, so output stays readable when
# piped to a file.
_POC = "◄"      # pointing at the point of control
_BUY_IMB = "↑"
_SELL_IMB = "↓"
_VA = "│"


def _fmt(v: float) -> str:
    if v >= 1_000_000:
        return f"{v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"{v / 1_000:.1f}k"
    if v >= 10:
        return f"{v:.0f}"
    return f"{v:.1f}"


def render_footprint(
    profiles: Sequence[BarProfile],
    cfg: FootprintConfig,
    price_fmt: str = "{:.2f}",
) -> str:
    """Render bars side by side on a shared price ladder."""
    if not profiles:
        return "(no bars)"

    lo = min(r.index for p in profiles for r in p.rows)
    hi = max(r.index for p in profiles for r in p.rows)

    cell_w = 15
    price_w = max(len(price_fmt.format(hi * cfg.row_size)), 8)

    header = " " * (price_w + 1) + "".join(
        f"{('bar ' + str(p.bar.t)):^{cell_w}}" for p in profiles
    )
    rule = "-" * len(header)
    lines = [header, rule]

    for k in range(hi, lo - 1, -1):  # price descends down the page
        price = price_fmt.format(k * cfg.row_size)
        cells = []
        for prof in profiles:
            row = prof.row(k)
            if row is None or row.total <= 0:
                cells.append(" " * cell_w)
                continue
            i = prof.rows.index(row)
            mark = _POC if i == prof.poc_index else (
                _VA if prof.val_index <= i <= prof.vah_index else " "
            )
            imb = (
                _BUY_IMB if i in prof.buy_imbalances
                else _SELL_IMB if i in prof.sell_imbalances
                else " "
            )
            cells.append(f"{_fmt(row.sell):>5} x {_fmt(row.buy):<5}{imb}{mark}")
        lines.append(f"{price:>{price_w}} " + "".join(cells))

    lines.append(rule)
    for label, get in (
        ("delta", lambda p: f"{p.delta:+.0f}"),
        ("vol", lambda p: _fmt(p.total_volume)),
        ("tilt", lambda p: f"{p.tilt_pct:+.1f}%"),
        ("OVL", lambda p: f"{p.ovl:.2f}"),
    ):
        lines.append(
            f"{label:>{price_w}} " + "".join(f"{get(p):^{cell_w}}" for p in profiles)
        )
    return "\n".join(lines)


def render_profile(
    rows: Sequence[Row],
    poc_i: int,
    val_i: int,
    vah_i: int,
    width: int = 46,
    price_fmt: str = "{:.2f}",
) -> str:
    """Render a composite profile as opposed bars: sell left, buy right.

    Buy and sell share one horizontal scale so their widths are directly
    comparable -- the visual form of the overlap coefficient.
    """
    if not rows:
        return "(empty profile)"
    peak = max(max(r.buy, r.sell) for r in rows) or 1.0
    half = width // 2
    price_w = max(len(price_fmt.format(r.price_low)) for r in rows)

    lines = []
    for i in range(len(rows) - 1, -1, -1):
        r = rows[i]
        sell_bar = "█" * int(round(half * r.sell / peak))
        buy_bar = "█" * int(round(half * r.buy / peak))
        mark = _POC if i == poc_i else (_VA if val_i <= i <= vah_i else " ")
        lines.append(
            f"{price_fmt.format(r.price_low):>{price_w}} "
            f"{sell_bar:>{half}}|{buy_bar:<{half}} {mark} {_fmt(r.total):>7}"
        )
    return "\n".join(lines)


def render_dashboard(profiles: Sequence[BarProfile], cfg: FootprintConfig) -> str:
    """Scalar read-outs for the whole window."""
    if not profiles:
        return "(no data)"

    rows, poc_i, val_i, vah_i = session_profile(profiles, cfg.row_size)
    buy = sum(p.buy_volume for p in profiles)
    sell = sum(p.sell_volume for p in profiles)
    total = buy + sell
    tilt = 0.0 if total <= 0 else 100.0 * (buy - sell) / total
    lead = abs(tilt)

    worst_res = max(p.residual_ppm for p in profiles)
    stacks = [(p.bar.t, side, run) for p in profiles for side, run in p.stacked_imbalances()]

    out = [
        f"window          {len(profiles)} bars, row size {cfg.row_size:g}, engine {cfg.engine}",
        f"total volume    {_fmt(total)}   buy {_fmt(buy)}  sell {_fmt(sell)}",
        f"delta           {buy - sell:+,.0f}",
        f"balance         {'balanced' if lead < cfg.balance_tilt_pct else ('buyers' if tilt > 0 else 'sellers')}"
        f"  (tilt {tilt:+.2f}%, lead {lead:.2f}%)",
        f"chart POC       {rows[poc_i].price_low:.2f}",
        f"value area      {rows[val_i].price_low:.2f} .. {rows[vah_i].price_high:.2f}"
        f"  ({cfg.value_area_pct:g}%)",
        f"mean OVL        {sum(p.ovl for p in profiles) / len(profiles):.3f}",
        f"residual        {worst_res:.3g} ppm  "
        f"({'EXACT' if worst_res <= 1.0 else 'CHECK'})",
    ]
    if stacks:
        out.append("stacked imb.    " + ", ".join(
            f"bar {t} {side} x{len(run)}" for t, side, run in stacks
        ))
    return "\n".join(out)
