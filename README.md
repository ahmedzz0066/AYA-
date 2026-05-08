# AYA Line — Volume Engine

Institutional-style intraday decision-support model — **100 % volume-driven**.

> "Less is better. Precision over frequency. Protect capital first."

## Files

| File                | Purpose                                                                                |
|---------------------|----------------------------------------------------------------------------------------|
| `ROADMAP.md`        | Volume-engine roadmap, logic, build order                                              |
| `AYA_Line.pine`     | Pine Script **v6** — the volume engine (aVWAP, VP, CVD, HVN, S/D, bias, TPs)           |
| `Volumatic_SR.pine` | Pine Script **v5** — BigBeluga's *Volumatic S/R Levels* (companion confluence layer)   |

## Inputs (volume only)

1. **Anchored Session VWAP** + ±1σ bands.
2. **Volume Profile** — POC, VAH, VAL over a rolling lookback.
3. **Cumulative Volume Delta** (CVD) — three selectable proxies, session-reset.
4. **HVN Levels** — BigBeluga z-score detector (signed-volume × body z).
5. **Supply / Demand Zones** — last opposing bar before a volume impulse.

No EMAs, no ATR, no daily pivots. Every gate in the model is built from
the order book.

## Quick start (TradingView)

1. Open TradingView → Pine Editor.
2. Paste the contents of `AYA_Line.pine`.
3. Save → "Add to chart".
4. Recommended chart timeframe: **5m** or **15m**. The script pulls 1H
   internally via `request.security` for invalidation control.

## What it draws

- **AYA Line** — anchored session VWAP / volume POC / manual override.
- **aVWAP ±1σ bands** — fair-value envelope.
- **POC / VAH / VAL** — auction value-area edges from the rolling profile.
- **HVN levels** — bull (green) / bear (orange) horizontal lines.
- **Supply / demand boxes** — last opposing bar before a volume impulse.
- **Invalidation** — dashed line at VAL/VAH (or HVN/POC); only a 1H
  *full-body* close beyond it triggers.
- **TP1 / TP2 / TP3** — R-multiple targets; TP3 enforces ≥ 1:4 RR.
- **Dashboard** — bias + score, AYA, POC/VAH/VAL, CVD, invalidation, TPs,
  HVN count, S/D zone count, do-not-trade reason.

## Pairing with Volumatic S/R Levels

`Volumatic_SR.pine` is BigBeluga's open-source v5 indicator (MPL-2.0). The
HVN logic from it is already replicated inside `AYA_Line.pine`; the
standalone version is kept for users who want the full BigBeluga visual
(boxes, percent labels, max/min table). Layer either or both.

See `ROADMAP.md` for the full logical specification.
