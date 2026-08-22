# The Operator's Card — al-Mīzān li-l-Dhahab (XAUUSD)
*One page. Read it before the session; obey it during the session.*
All times **UTC**. `A` = ATR(14) on M15. `A_D1` = ATR(14) on D1.

## 06:00 — Preparation (no execution)
- [ ] Compute `A`, `A_D1`. If `A_D1` < 60% of its 20-day mean → gates +15%, size ÷2.
- [ ] Mark Asian range `AR_high` / `AR_low` (23:00–06:00). If range > $18, the day already trends.
- [ ] Mark `PDH`, `PDL`, `PDC`.
- [ ] Mark magazines within ±2×`A_D1`: ×100 (w3) > ×50 (w2) > ×25 / ×10 (w1).
- [ ] Mark news blocks (±15 min: CPI, NFP, FOMC, PCE, PPI, ISM). Inside a block the algorithm is **halted**.
- [ ] `BIAS` from D1 + H4 break of structure. Conflict → `BIAS = 0` → **Form III only, half size**.
- [ ] Mark nearest unmitigated H4 opposing zone above and below (the day's ceiling on ambition).

## The five gates (a zone that fails one is erased, not adjusted)
1. **Base** 1–5 candles, height ≤ 0.60`A`, mean body/range ≤ 0.50, 50% overlap.
2. **Displacement** ≥ 2.0`A` from `proximal_body`, within ≤ 3 candles.
3. **Conviction** one departure candle with body/range ≥ 0.60 and opposing wick ≤ 25%.
4. **Imbalance** an FVG ≥ 0.20`A` (never < $0.60) inside base ∪ departure. *Mandatory — it is the proof.*
5. **Freshness** 0 taps = A-grade, 1 tap = confirmation only, 2 taps = dead. M15 close beyond `distal` = destroyed.
   Plus: departure must **close** beyond the last swing in its direction (BOS).

## Geometry (say these aloud; confusing them is the commonest error)
- Demand: `distal` = lowest low of base · `proximal_body` = highest body of base (**entry**) · `proximal_wick` = highest high (**tap count**).
- Supply: mirrored.

## The Balance — 100 points, trade nothing under 65
departure 20 · base 15 · imbalance 15 · sweep 15 · HTF 15 (**−25 if opposed**) · freshness 10 · magazine 5 · session 5
→ **A ≥ 80** limit order permitted. **B 65–79** M1/M5 CHoCH only. **< 65 no trade.**

## Sessions
| Window | State | Action |
|---|---|---|
| 23:00–06:00 | Accumulation | Mark the range. **Never trade its interior.** |
| 06:00–07:00 | Pre-London | Prepare only. |
| 07:00–10:00 | **Judas** | Sweep of AR extreme → displacement back = zone of the day (**Form III**). |
| 10:00–12:30 | Lull | Manage only. No new construction. |
| 12:30–16:00 | **New York** | Continuation of London, or sweep of London's extreme → second Form III (13:30–15:00 is the heart). |
| after 17:00 | — | **No new entries.** |
| after 20:00 | — | **Flat.** |

## Execution
- Entry: `proximal_body` (Grade A, fresh, killzone) **or** M1/M5 CHoCH + micro-FVG retest (all other cases).
- Stop: `distal ∓ [max(0.15A, $1.20) + $0.30 spread]`. Never at the proximal. Never a fixed pip count.
- Reward gate: **≥ 3R** to the first logical target, or the trade does not exist.
- T1 1.5R (50%) → stop to breakeven+spread · T2 session liquidity (30%) · T3 unmitigated H4 zone (20%).
- Trail beneath each new M5 base that displaces ≥ 1.5`A`. Never by a fixed distance.

## Governance
0.5% risk (1.0% ceiling: Grade A + Form III + full alignment) · `lots = equity×risk% ÷ (stop$ × 100)` ·
**2 trades max/day** · stop after 2 consecutive losses · stop the week at −2% · one trade per zone.

## Refuse to trade when
Against `BIAS` · inside the Asian range · zone on its 3rd tap · arrival candle is itself a ≥2`A` displacement
(that is a breach, not a test) · inside a news block · after 17:00 · when the 3R gate fails.

> **Mark only what was proved, take only what is fresh, and let the balance — not the eye — decide.**
