# AYA — Volumetric Supply & Demand Zones v6

A math-first **Supply & Demand zone** indicator for TradingView (**Pine Script v6**),
grounded in auction-market theory and volume profiling rather than subjective swing
drawing.

## Contents

- **[`VolumetricSupplyDemandZones_v6.pine`](./VolumetricSupplyDemandZones_v6.pine)** —
  the full Pine Script v6 indicator (drop into TradingView → Pine Editor → Add to chart).
- **[`DOCUMENTATION.md`](./DOCUMENTATION.md)** — first-principles rationale, the
  mathematics behind every rule, logic/pseudocode, usage & risk rules, and a
  backtesting/validation plan.

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
