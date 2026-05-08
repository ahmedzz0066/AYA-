# AYA Line

Institutional-style intraday decision-support model.

> "Less is better. Precision over frequency. Protect capital first."

## Files

| File             | Purpose                                                           |
|------------------|-------------------------------------------------------------------|
| `ROADMAP.md`     | Full trading-model roadmap, logic, and build order                |
| `AYA_Line.pine`  | Pine Script v6 indicator implementing every component             |

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
