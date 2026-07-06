# SMC Elite — Smart Money Concepts Suite (Pine Script v6)

A complete Smart Money Concepts toolkit for TradingView, built on a *quality-over-quantity*
filtering philosophy: instead of flooding the chart with every retrospective level, zones are
strictly validated against institutional order-flow logic before they are ever drawn.

**File:** [`SMC-Elite.pine`](SMC-Elite.pine)

## Installation

1. Open TradingView → **Pine Editor**.
2. Paste the full contents of `SMC-Elite.pine`.
3. Click **Add to chart**, then **Save**.

## Modules

| Module | What it does |
|---|---|
| Smart Structure | BOS / CHoCH mapping with an ATR volatility filter (swings must displace ≥ 0.3 × ATR) so retail micro-structure is ignored. Optional internal (dotted) structure layer. |
| Order Blocks | "Scorecard" validation: displacement body ratio ≥ 60%, relative-volume check, and a Trinity test (liquidity sweep + FVG displacement + structure break) that promotes a zone to **Tier 1 / A+**. First touch marks a zone mitigated and hides it instantly — no ghost zones. |
| Fair Value Gaps | Volatility-normalized: gap ≥ 0.4 × ATR and middle-candle body ≥ 72%. A close past the 50% level (CE) invalidates the gap. Optional 50%-Zone render mode halves the visual footprint. Overlapping OB + FVG areas are merged into a single confluence zone. |
| Inverted FVG (IFVG) | Broken gaps flip into inversion zones (support ↔ resistance), filtered by displacement and Premium/Discount location. Purple = bearish, orange = bullish. |
| CISD | Change In State of Delivery: tracks the impulsive series that raided liquidity and fires on a body close through the level. Two modes: **Origin Break** and **Raid Candle**. Optional trend filter and an ultra-light zone render. |
| Liquidity | EQH/EQL pools with a wick-to-body sweep filter; by default levels appear only *after* they are swept (`✕ BSL` / `✕ SSL`). PDH/PDL lines included. |
| Premium / Discount | Live dealing-range overlay with PREMIUM / EQ 50% / DISCOUNT labels. |
| HTF Zones | Two higher-timeframe layers (Auto or Manual) overlay HTF FVGs and OBs in an ultra-transparent style. When an HTF zone forms over an existing local zone, that zone is upgraded live: thicker border and a ★ tag (e.g. `FVG ★ [1H]`). |
| Trend Cloud | 3-layer EMA gradient ribbon (13/21/50) with ◉ twist points at structural reversals. |
| Risk Engine | Real-time lot-size calculation from account size, risk %, SL distance and asset-class contract specs (Forex 100k, XAU 100 oz, indices, crypto, stocks). Lot size is printed directly on Order Block labels. |
| Trade Guide Panel | State machine: *scanning → watching zone → touched (awaiting confirmation) → running*. Confirmation requires a valid retest plus a body close from the final zone edge — no early entries. Plots Entry / SL / TP1 / TP2 lines, an optional R:R box, and marks `TP1 ✔ done` / `TP2 ✔ done` / `SL ✕` on the chart. A Decision Assistant row warns when an opposite A+ setup forms while a trade is running. |

## How to use

1. **Read the bias** from the BOS/CHoCH structure lines and the Trend Cloud.
2. **Wait for Tier 1 zones** — solid/neon A+ Order Blocks or ◆/★ FVGs are the high-probability POIs.
3. **Prefer swept liquidity** — an `✕ SSL` / `✕ BSL` marker near your POI is added confluence.
4. **Let the panel confirm** — enter on the confirmation close, use the suggested SL line and the
   lot size from the Risk Engine, and target TP1/TP2 or opposing liquidity (PDH/PDL).

## Alerts

BOS, CHoCH, CISD trigger, liquidity sweep, IFVG formed, zone touched, trade confirmed,
take-profit hit, and stop-loss hit are all available via `alertcondition`.

## Notes

- Signal logic runs on confirmed bars (`barstate.isconfirmed`) and HTF data uses only closed
  higher-timeframe bars, so zones and signals do not repaint.
- This is an analysis tool, not a signal service. All trading involves risk.
