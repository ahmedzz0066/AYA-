#!/usr/bin/env python3
"""Run the footprint reconstruction on synthetic bars and print the result.

    python3 demo.py                 # default window
    python3 demo.py --engine close  # compare against the naive split
    python3 demo.py --bars 8 --row-size 0.5 --concentration 6
"""

from __future__ import annotations

import argparse
import math
import random

from vfootprint import (
    Bar,
    FootprintConfig,
    build_profile,
    render_dashboard,
    render_footprint,
    render_profile,
    session_profile,
)


def synth(n: int, seed: int = 7, start: float = 100.0) -> list[Bar]:
    """A random walk with drift and volume clustered on range expansion."""
    rng = random.Random(seed)
    bars: list[Bar] = []
    price = start
    for i in range(n):
        drift = 0.12 * math.sin(i / 2.0)
        o = price
        c = o + drift + rng.gauss(0, 0.35)
        span = abs(c - o) + abs(rng.gauss(0, 0.3)) + 0.05
        h = max(o, c) + abs(rng.gauss(0, span * 0.5))
        l = min(o, c) - abs(rng.gauss(0, span * 0.5))
        v = round(800 + 2200 * (h - l) + rng.random() * 400)
        bars.append(Bar(o=o, h=h, l=l, c=c, v=float(v), t=i + 1))
        price = c
    return bars


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bars", type=int, default=5)
    ap.add_argument("--row-size", type=float, default=0.25)
    ap.add_argument("--concentration", type=float, default=6.0)
    ap.add_argument("--action-exponent", type=float, default=1.0)
    ap.add_argument("--value-area", type=float, default=70.0)
    ap.add_argument("--imbalance", type=float, default=3.0)
    ap.add_argument("--engine", default="path", choices=["path", "close", "ltf"])
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()

    cfg = FootprintConfig(
        row_size=args.row_size,
        concentration=args.concentration,
        action_exponent=args.action_exponent,
        value_area_pct=args.value_area,
        imbalance_threshold=args.imbalance,
        engine=args.engine,
    )

    bars = synth(args.bars, seed=args.seed)
    profiles = [build_profile(b, cfg) for b in bars]

    print("FOOTPRINT   sell x buy    ◄ POC   │ value area   ↑↓ diagonal imbalance")
    print()
    print(render_footprint(profiles, cfg))
    print()
    print("COMPOSITE PROFILE   sell │ buy, shared scale")
    print()
    rows, poc_i, val_i, vah_i = session_profile(profiles, cfg.row_size)
    print(render_profile(rows, poc_i, val_i, vah_i))
    print()
    print("DASHBOARD")
    print()
    print(render_dashboard(profiles, cfg))


if __name__ == "__main__":
    main()
