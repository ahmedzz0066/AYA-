# AYA — Volumetric Supply & Demand Zones

Math-first **Supply & Demand zone** indicators for TradingView (**Pine Script v6**),
grounded in auction-market theory and volume profiling rather than subjective swing
drawing. Three generations are included.

## 🧠 Latest: VolSD v8 — Self-Learning

The v6 engine upgraded into a **self-calibrating probability system**: an online
logistic-regression model learns per symbol/timeframe which confluence factors
actually predict bounces (walk-forward, non-repainting), every zone shows
**P(bounce) + the historical bounce rate of similar zones** ("P:72% | hist 68%
(n=23)"), retests are graded by an **absorption model** (defended vs consumed)
instead of blind decay, plus **true intrabar delta** (lower-TF), **time-of-day
relative volume**, and a **news-shock filter**.

- **[`VolSD_v8_SelfLearning.pine`](./VolSD_v8_SelfLearning.pine)** — the indicator.
- **[`DOCUMENTATION_v8.md`](./DOCUMENTATION_v8.md)** — the learning math, lifecycle,
  usage, calibration-based validation, and honest limitations.

## VolSD Quantum v7 (Elite)

Next-generation engine that fuses Auction Market Theory with **Smart Money Concepts** —
market structure (**BOS/CHoCH**), **Order Blocks**, **Fair Value Gaps**, **liquidity
sweeps**, **premium/discount + OTE**, **HVN alignment**, adaptive **volume z-score**
gating, and projected **targets + R:R** — scored across **10 orthogonal confluence
channels** (0–10). Non-repainting.

- **[`VolSD_Quantum_v7.pine`](./VolSD_Quantum_v7.pine)** — the indicator.
- **[`DOCUMENTATION_v7.md`](./DOCUMENTATION_v7.md)** — full derivation, engines,
  pseudocode, usage/risk, validation plan, and a v6→v7 comparison.

## Contents

- **[`VolSD_v8_SelfLearning.pine`](./VolSD_v8_SelfLearning.pine)** + **[`DOCUMENTATION_v8.md`](./DOCUMENTATION_v8.md)** — v8 Self-Learning (recommended).
- **[`VolSD_Quantum_v7.pine`](./VolSD_Quantum_v7.pine)** + **[`DOCUMENTATION_v7.md`](./DOCUMENTATION_v7.md)** — v7 Elite (SMC + auction confluence).
- **[`VolumetricSupplyDemandZones_v6.pine`](./VolumetricSupplyDemandZones_v6.pine)** +
  **[`DOCUMENTATION.md`](./DOCUMENTATION.md)** — v6 (base→impulse + volume profile),
  retained for reference and comparison.

Drop either `.pine` file into TradingView → Pine Editor → Add to chart.

## What it does

1. Detects **base → impulse** structure objectively (tight consolidation that resolves
   with a high-volume, one-sided imbalance candle).
2. Builds a rolling **Volume Profile** (POC / VAH / VAL / histogram) for auction context.
3. Scores each zone **0–10** from five orthogonal, ATR/volume-normalized factors:
   volume percentile, impulse ratio, delta imbalance, width efficiency, and HTF
   confluence.
4. Applies **freshness** (exponential time decay) and **consumption** (per-touch +
   mitigation) so live strength reflects how spent a zone is.
5. **Filters** by strength threshold and market regime (ADX), and **alerts** on
   strong-zone retest + rejection + volume spike.

Designed to be **non-repainting** (confirmed bars + `lookahead_off`) and instrument-/
timeframe-agnostic.

See **[DOCUMENTATION.md](./DOCUMENTATION.md)** for the full derivation and usage guide.
