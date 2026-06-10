# AYA-

## Aether Supply & Demand — Quantum Resonance [Ω v9]

`aether-supply-demand-omega.pine` — a Pine Script v6 supply & demand engine for TradingView,
evolved from "Volumetric Supply and Demand [BOSWaves]" (MPL 2.0).

### Features

- **Zone Quality Score (0–100) with S/A/B/C grades** — combines impulse strength,
  relative volume participation, delta alignment, base compression, and
  premium/discount location. A minimum-grade filter keeps only the best zones.
- **Higher-timeframe bias** — zones fighting the HTF EMA trend are penalized.
- **Volume + delta profiles inside every zone**, with POC and configurable
  Value Area (default 70%) lines.
- **Liquidity sweep detection** — a wick through the far edge of a zone that
  closes back inside is flagged as a stop-run (diamond marker + alert).
- **Breaker flips** — a quality zone broken by a closing candle inverts into
  the opposite zone type instead of being discarded.
- **Partial mitigation** — zones shrink as price consumes them, leaving only
  the fresh untraded portion.
- **Retest confirmation signals** — wick into a zone with a close back outside
  in the reactive direction plots an arrow and can fire an alert.
- **Zone lifecycle management** — merging of overlapping zones, aging/expiry,
  touch counting, and a per-zone info box (grade, volume, delta, touches, status).
- **Live dashboard** — HTF bias, range position (premium/discount), zone census,
  and distance to the nearest demand/supply zone.
- **8 alert conditions** covering zone formation, tests, mitigation, sweeps,
  breakers, and confirmed retests.

### Usage

Paste the script into TradingView's Pine Editor and add it to a chart.
Defaults are a reasonable starting point; the most impactful inputs are
`Swing Length`, `Impulse Size (ATR)`, `Minimum Zone Grade`, and the
`Higher Timeframe Bias` settings.

> **Disclaimer:** This is an analysis tool, not financial advice. No indicator
> predicts markets; delta here is approximated from candle direction, and all
> scoring is heuristic. Backtest and forward-test before risking capital.

Licensed under the Mozilla Public License 2.0.
