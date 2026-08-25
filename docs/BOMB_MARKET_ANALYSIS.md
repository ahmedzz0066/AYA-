# "Bomb Market" — Reverse-Engineering Analysis

Analysis of 10 published trade screenshots (XAUUSD, EURUSD, GBPUSD, USDJPY,
GBPCHF; timeframes 1m → 1D) of the premium "Bomb Market" strategy, and the
rationale behind the Pine Script v6 implementation in
[`bomb_market.pine`](../bomb_market.pine).

## What the screenshots show

| Chart | TF | Zone location | Trade | Observed R/R |
|---|---|---|---|---|
| EURUSD | ~1m scalp | Thin band at swept swing **high** (1.11714–1.11716) | Short → 1.11613, stop 0.2 pips above | **50.5** |
| GBPUSD | 4H | Band at swept swing **low** (1.26568–1.26745) | Long → laddered structure targets to 1.31258 | very high |
| XAUUSD | 4H | Band at swept swing low (~2364–2371) | Long → 2477, stop 6.66 (0.28 %) below | **15.99** |
| USDJPY | 1D | Band 146.037–146.570 under a double-bottom sweep | Long → +430 pips | high |
| XAUUSD | 1H | Band 2334.73–2336.55 | Two stacked longs → 2358 | high |
| USDJPY | 1m | Band at swept high 156.200–156.219 | Short → 155.945 | high |
| EURUSD | 5m | Supply band at swept high 1.04811–1.04831 | Short, targets 1.04597 / 1.04522 / 1.04432 | high |
| EURUSD | 4H | Demand band 1.04759–1.04987 | Long → 1.07543 | high |
| GBPCHF | 2H | Demand band 1.11896–1.12025 | Long → 1.13028, stop 14.3 pips | **7.01** |
| XAUUSD | 4H (with EMA ribbon) | Two stacked "Bomb Market" supply bands in a downtrend | Shorts from each band | — |

## Decoded mechanics

Every screenshot is consistent with the same five-step template:

1. **Liquidity sweep.** Price wicks through an obvious prior swing extreme
   (equal lows, a double bottom, session low/high), harvesting resting stops.
2. **Displacement ("the bomb").** The market immediately leaves that extreme
   with an outsized impulsive move — the origin candle is the detonation
   point. This is what qualifies the level; a plain pivot without an
   explosive departure is never marked.
3. **The band.** A narrow box is drawn at the origin: **distal edge = the
   wick extreme**, **proximal edge = the candle body**. On every chart the
   band is far thinner than the impulse it spawned — it is a wick zone /
   extreme-refined order block, not a full supply-demand zone.
4. **Entry on the return.** Nothing is traded at zone creation. The trade
   triggers only when price retraces all the way back into the band —
   a limit fill at the proximal edge (screenshot 1's entry sits exactly on
   the band's edge).
5. **Stop & target.** Stop = a few ticks beyond the distal wick (0.2 pips on
   the 1m scalp, 0.13–0.28 % on 2H/4H). Target = opposing structure /
   liquidity, which lands at roughly 7R (2H), 16R (4H), 50R (tight scalps).
   The colossal R/R ratios are a mechanical consequence of the stop being
   measured from the proximal entry to the nearby wick tip.

Auxiliary observations: an EMA ribbon (~50/100/200) appears on one XAUUSD
chart and the bands there align with the prevailing downtrend — implemented
as the optional EMA trend filter. Zones are reused on multiple timeframes
unchanged; the method itself is timeframe-agnostic.

## Mapping to the implementation

| Concept | Pine implementation |
|---|---|
| Liquidity sweep | `ta.pivotlow/high(swingLen)` that exceeds the `liqLookback`-bar extreme preceding the pivot |
| Displacement | by pivot confirmation, price ≥ `dispMult × ATR` away from the swept extreme |
| Band | box from wick extreme (distal) to candle body (proximal); `zoneMode` widens it if desired, `maxZoneATR` caps it |
| Entry | one resting limit order at the proximal edge of the nearest valid zone |
| Stop | distal wick ± `slBufTicks` ticks |
| Target | `rrTarget` × risk (default 15R) |
| Invalidation | zone dies if price closes/wicks through the distal edge before a retest, or after `zoneLife` bars |
| Sizing | `riskPct` % of equity divided by stop distance |

## Quant reality check (read before trading this)

- **The advertised R/R is a geometry trick, not edge.** A 50R target with a
  0.2-pip stop needs a ~2 % win rate to break even *in a frictionless
  world*. Whether the zone has edge is an empirical question — backtest it.
- **Spread kills the flagship trades.** EURUSD's typical 0.1–0.3 pip spread
  is *larger than the stop* in screenshot 1. On real fills that trade is
  stopped by the spread alone. Set realistic `commission_value` and
  slippage in the strategy properties before believing any backtest.
- **Survivorship bias.** Story-format screenshots show winners only. Expect
  long strings of 1R losses between rare multi-R winners; the equity curve
  is lumpy and psychologically brutal.
- **Fill assumptions.** TradingView's broker emulator fills the limit at the
  proximal edge; live, the retest often comes with momentum and partial
  fills/slippage at exactly the worst moments.
- Use the strategy as a **research harness**: sweep `dispMult`, `rrTarget`,
  and `zoneMode` per instrument/timeframe, and demand out-of-sample and
  forward results before risking capital.

*This code is for research/education. Nothing here is financial advice.*
