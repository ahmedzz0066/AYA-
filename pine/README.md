# AXIOM · Pine Script v6 Indicator

`AXIOM.pine` — reference implementation of the [AXIOM specification](../docs/AXIOM-Institutional-Price-Action-Spec.md).
~1660 lines, Pine Script **v6**, overlay indicator.

## Install

1. TradingView → Pine Editor → **Open** → *New indicator*
2. Replace the contents with `AXIOM.pine`
3. **Save**, then **Add to chart**

## What you see on a clean chart

At default settings the chart carries **≤ 14 objects**. Most of the time it will show *nothing but
context* — that is the design, not a failure. Tier-1 zones are intended to appear roughly once per
150–400 bars per direction.

| Element | Meaning |
|---|---|
| Neutral box, 2px border, `A+ 84 ★` | Tier-1 intent node (all 10 gates passed); ★ = HTF-backed |
| Thin dotted box, no label | Tier-2 node — watchlist only, cannot trigger |
| Very faint box | Imbalance channel, rendered at 50% (CE) by default |
| Ultra-faint box + dotted line | State-shift zone (anchor → shift extreme) |
| Dotted horizontal + `⌫` | Swept liquidity (unswept levels stay invisible) |
| `⌃` / `⌄` | Confirmed ATR-filtered swing |
| ▲ / ▼ | Confirmed entry · ○ = A+ setup arming |
| Entry/SL/TP1/TP2 lines | Live trade, with `✓ done` on filled targets |
| Panel | Regime, structure, stage *n*/7, confluence score, **next step**, size, opposing verdict |

The **Next step** row is the one to read. It always states a single imperative action for the
current FSM stage.

## Engine → code map

| Section | Engine |
|---|---|
| 4 | Layer 0 · bar anatomy, VWID, percentile ranks, regime classifier |
| 5 | MTC · HTF pack via `request.security` |
| 6 | Shared helpers · dual gate, displacement, Cost-of-Reversal, origin cluster |
| 7–9 | IIDE · node factory, mitigation simulation, merging |
| 8 | MSE · ATR-filtered swings, displacement-gated breaks |
| 10 | AIE · imbalance detection, fill tracking, inversion filter |
| 11 | LCC · sweep-gated liquidity |
| 12–13 | MTC upgrades · tier re-evaluation (10 hard gates) |
| 14–15 | SSE + CDE · anchor, final edge, arbitrator, Sequence Lock FSM |
| 16–18 | Execution, trade lifecycle, cross-asset sizing |
| 19–28 | Rendering, panel, alerts |

## Alerts

Six conditions: long/short entry confirmed, long/short A+ arming, arbitrator switch, stand-down.
All fire on **bar close only**.

## Tuning order

Change one thing at a time, in this order:

1. **Too few signals?** Lower `Tier-1 score` (78 → 72) *before* touching any gate.
2. Still too few? Raise `Max signals / 100 bars`, then disable `Gate · imbalance confluence`.
3. **Too many?** Raise `Displacement floor (ATR)` first — it is the master sensitivity control.
4. **Zones look wrong on your instrument?** Adjust `Origin cluster max bars` and
   `Max zone width (ATR)`. Do not adjust percentile gates; they self-calibrate.
5. Leave `Rank window` at 200 unless you are on Daily+ (use 100) or crypto (300).

Every filter is independently toggleable, and **a disabled gate passes** — it never inverts.

## Non-repainting

Enforced in code, not by convention: all classification under `barstate.isconfirmed`; HTF via
`close[1]` + `barmerge.lookahead_off`; no `varip`; no lower-timeframe requests; monotone object
states with terminal death; display updates intrabar while logic does not. Exactly **two**
`request.*` calls total.

## Known limitations — read before trading it

- **Not backtest-validated.** This is a faithful implementation of the spec, not a proven edge.
  Run the §19 protocol (especially the gate ablation study) before risking money.
- **Indicator, not a strategy.** No `strategy.*` calls, so TradingView's Strategy Tester cannot
  score it. Port the FSM to a `strategy()` script to get equity metrics.
- **Volume-dependent.** On feeds with synthetic or zero volume the participation surrogate engages
  and the panel shows `SYNTH VOL`. Signal quality is materially lower there; prefer futures or
  crypto over spot FX if you want the volume terms to mean anything.
- **Bar-close resolution.** When SL and TP print on the same bar, SL is assumed to fill first. Real
  fills may differ; intrabar sequence is unknowable from OHLCV.
- **Sizing assumes the quote currency converts via `request.currency_rate`.** If that returns `na`
  the rate falls back to 1.0. Verify the lot size against your broker before your first trade.
- **`VWID` is a proxy, not tick delta.** It is derived from close position within range. It is
  labelled as a proxy everywhere in the code and should be understood as one.
