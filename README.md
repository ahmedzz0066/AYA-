# AYA Line

Institutional-style intraday decision-support model.

> "Less is better. Precision over frequency. Protect capital first."

## Files

| File                | Purpose                                                                                       |
|---------------------|-----------------------------------------------------------------------------------------------|
| `ROADMAP.md`        | Full trading-model roadmap, logic, and build order                                            |
| `AYA_Line.pine`     | Pine Script **v6** indicator implementing every component of the AYA framework                |
| `Volumatic_SR.pine` | Pine Script **v5** — BigBeluga's *Volumatic S/R Levels* (volume-weighted S/R confluence layer) |

## Quick start (TradingView)

1. Open TradingView → Pine Editor.
2. Paste the contents of `AYA_Line.pine`.
3. Save → "Add to chart".
4. Recommended chart timeframe: **5m** or **15m** (the indicator pulls D / 1H / 15m
   internally via `request.security`).

## What it draws

- **AYA Line** — single anchor level (pivot / aVWAP / prior-day mid / manual).
- **Invalidation** — dashed line; only a 1H *full-body* close beyond it matters.
- **TP1 / TP2 / TP3 / Extended** — R-multiple targets (TP3 enforces ≥ 1:4 RR).
- **OTE pullback zone** — 50 %–79 % discount/premium of the last 15m impulse leg
  with a 70.5 % sweet-spot.
- **Risk / reward boxes** — flagged when geometry can't satisfy 1:4.
- **Liquidity sweeps** + **MSS** markers + **reclaim sequencer**.
- **Dashboard table** mirroring `[ DAILY BIAS ] [ CORE AYA LINE ] [ MODEL TARGETS ]
  [ TRADE PLAN ] [ MARKET STATE ] [ RISK NOTES ]`.

See `ROADMAP.md` for the full logical specification.

## Pairing with Volumatic S/R Levels

`Volumatic_SR.pine` is BigBeluga's open-source v5 indicator (MPL-2.0). It is
intentionally kept as a **separate** indicator on the chart so each model
remains auditable in isolation. Recommended layering:

1. Add **AYA Line** — gives you the daily bias, anchor, invalidation, and TPs.
2. Add **Volumatic S/R Levels** on the same chart — overlays the volume-weighted
   horizontal levels.
3. Treat the *intersection* of an AYA pullback zone with a high-percentage
   Volumatic level as a confluence pickup. If the volume level is bull-color
   (`#00e677`) and inside the AYA discount zone, the long has additional
   structural sponsorship.

Volumatic S/R is informational only — invalidation logic still belongs to AYA
Line's 1H full-body close rule.
