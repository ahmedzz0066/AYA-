# AYA · XAUUSD Liquidity Engine [SMC]

A non-repainting Smart Money Concepts liquidity engine for **XAUUSD on M1 and M5**, written in
**Pine Script v6**.

It is a ground-up rebuild of *Liquidity Trendline With Signals [StratifyTrade]*. The original idea
— project a channel off two pivots and trade the break — is kept and turned into one input among
many. Everything around it is new: a liquidity map, a grab/break classifier, a dual-resolution
structure engine, a weighted confluence score, a full risk model and a live performance tracker.

**Source:** [`pine/AYA_XAUUSD_Liquidity_Engine.pine`](pine/AYA_XAUUSD_Liquidity_Engine.pine)

---

## 1. Install

1. TradingView → **Pine Editor** → **Open → New blank indicator**.
2. Paste the entire contents of `pine/AYA_XAUUSD_Liquidity_Engine.pine`.
3. **Save**, then **Add to chart**.
4. Open an XAUUSD 1m or 5m chart. Leave the profile on **Auto** for the first session.

Object budget is capped in code (500 lines / 500 labels / 500 boxes) and every collection is
bounded, so the script will not die with "too many drawings" on a long history.

---

## 2. The non-repainting contract

This is the part most "liquidity" indicators quietly get wrong, so it is stated precisely.

Every piece of state that can produce a signal is mutated **only** inside `if barstate.isconfirmed`.

* On historical bars that flag is always `true`.
* On the live bar it is `true` only on the closing tick.

So the live code path executes exactly the same computation, on exactly the same inputs, as the
historical path. Concretely:

| Guarantee | How |
|---|---|
| Signals never move, vanish or appear late | Fired on bar close; `fireBuy/fireSell` reset to `false` every bar and are only set behind the confirm gate |
| Pivots never repaint | `ta.pivothigh/low(len, len)` is only *registered* once its confirmation window has closed |
| Structure breaks never re-fire | A level is **consumed** (set to `na`) the moment it is taken; only a fresh pivot can arm a new one |
| HTF bias never leaks the future | `request.security(..., expr[1], lookahead_on)` — the canonical confirmed-bar idiom |
| Drawings can't contaminate logic | The cosmetic layer is a separate pass; Pine rolls intrabar drawing state back on every tick |
| Alerts fire once, at close | `alert.freq_once_per_bar_close` |

**The honest cost.** A pivot of length *L* is only *known* *L* bars after it happened. That latency
is real. It is not hidden, not smoothed over, and not worked around with `lookahead` — because
every trick that removes it also removes the guarantee.

**What is *not* claimed.** The performance tracker is a *first-touch simulation*, not a backtest:
it has no spread, no commission, no slippage, and when the stop and TP1 both sit inside one bar it
books a **loss** because intrabar sequence is unknowable from bar data. Treat it as a diagnostic
for parameter tuning, nothing more.

---

## 3. How the engine works

```
                pivots ─┬─► LIQUIDITY MAP  (equal highs/lows, session & daily extremes)
                        └─► TRENDLINES     (validated, slope-clamped, projected)
                                  │
                                  ▼
                        ┌──────────────────┐
   every closed bar ───►│  SWEEP CLASSIFIER│  wick through + close back inside → GRAB
                        └──────────────────┘  close clean through              → BREAK
                                  │ GRAB
                                  ▼
                        ┌──────────────────┐
                        │  SETUP ARMED     │  direction = opposite of the grab
                        └──────────────────┘  expires after `confirmation window` bars
                                  │           dies if price closes beyond the grab extreme
                                  ▼
                        ┌──────────────────┐
                        │ INTERNAL CHoCH / │  structure must flip in the setup's direction
                        │ BOS + candle     │
                        └──────────────────┘
                                  │
                                  ▼
                        ┌──────────────────┐
                        │ CONFLUENCE SCORE │  ≥ threshold → SIGNAL
                        └──────────────────┘  entry · stop · TP1/2/3 · lot size · alert
```

### 3.1 Liquidity map

Swing pivots inside `equal-level tolerance` (an ATR fraction) are not two levels — they are **one
pool that got deeper**. `hits` is that depth and feeds the score directly. Session extremes
(Asia / London / NY) and PDH / PDL / PWH / PWL are injected as higher-grade pools, because those
are the levels gold actually hunts.

A pivot that price has *already closed through* during the bars it took to confirm is never born
live — it is stale geometry, not resting liquidity.

### 3.2 Grab vs. break

| | Wick clears the pool | Body closes through |
|---|---|---|
| **Meaning** | stops taken, price rejected | pool consumed, trend continues |
| **Engine** | `GRAB` → arms a **reversal** setup | `BREAK` → pool retired, no reversal setup |

Conflating these two is why naive tools buy every breakout of a high and get stopped on the
retrace. Penetration depth is bounded on both sides: too shallow and the level was merely tagged;
too deep and it is a news expansion, which is not a fade.

### 3.3 Liquidity trendlines — what changed from the original

| Original | This rebuild |
|---|---|
| `y2 += slope` once per bar inside a loop | exact projection `y = y1 + slope·(x − x1)` — no accumulated drift, no desynchronised band edges |
| any two consecutive pivots | min/max **pivot span** — kills 2-bar "trendlines" |
| any slope | **slope clamp** in ATR/bar — kills near-vertical junk built off spike pivots |
| one shared `broken` flag for both directions | independent state per side (in the original, a break on one side silently re-validated the other) |
| break = `low > line` (intrabar, repaints) | break = **close** beyond the band, evaluated on the confirmed bar |
| break only | **grab vs. break** — a wick through the band that closes back inside is a trendline liquidity grab and arms the *opposite* setup |
| lines live forever | age limit, live-line cap per side, retirement and disposal |

### 3.4 Confluence score

| Component | Weight |
|---|---|
| Sweep quality (depth · rejection wick · pool depth · pool grade · rel. volume) | 1.0 … 3.9 |
| Internal CHoCH / BOS | 1.5 / 0.8 |
| Displacement candle | 1.0 |
| Fresh FVG in direction | 0.8 |
| HTF bias aligned / opposed | +1.2 / **−1.5** |
| Discount for longs, premium for shorts (wrong side) | +0.8 / **−0.5** |
| Inside a killzone | 0.7 |
| Relative volume | 0.5 |
| Swing bias aligned | 0.5 |

Practical ceiling ≈ **10.8**. Default threshold **4.5** is balanced; **6.0** is sniper-only;
below **3.5** the chart floods.

### 3.5 Risk model

* **Stop** — beyond the grab extreme plus `max(ATR buffer, minimum $ distance)`. If the structural
  stop is wider than `max stop distance`, the setup is **rejected**, not resized: that is bad
  structure, not a sizing problem.
* **Targets** — R multiples, or *opposing liquidity* mode, which targets the nearest untouched pool
  on the other side (where the liquidity your exit needs actually sits).
* **Size** — `lots = (account × risk%) / (stop_distance × ounces_per_lot)`, standard 100 oz contract,
  printed on the signal label and in the dashboard.

---

## 4. Inputs

| Group | What matters most |
|---|---|
| **❶ Profile · Core** | `Auto` picks the M1 preset on 1–3m charts, M5 otherwise. `Manual` takes every length literally. ATR length is the volatility unit for the whole script. |
| **❷ Market structure** | Swing length sets bias; internal length is what actually triggers entries. Close-confirmed breaks = fewer, cleaner events. |
| **❸ Liquidity pools** | `Equal-level tolerance` is the single most important knob: 0.18×ATR on M1 gold ≈ 10–15 cents. |
| **❹ Liquidity trendlines** | Slope clamp and pivot span do the quality filtering. Padding is the band half-width in 0.1×ATR units. |
| **❺ Sweeps · displacement** | Penetration bounds, rejection wick ratio, displacement body size, relative-volume confluence. |
| **❻ Imbalance · order blocks** | The FVG minimum size filter is what makes FVGs usable on M1 gold, which prints dozens of 2-cent gaps an hour. |
| **❼ Sessions · killzones** | Entered in **UTC** by default. London 07:00–10:00 and NY 12:00–15:00 UTC cover the gold open-drive windows. |
| **❽ Signal engine** | Score threshold, confirmation window, cooldown, daily cap, direction filter, ATR regime gate. |
| **❾ Risk model** | Stop buffer, target mode, R multiples, time stop, account/risk% for live lot sizing. |
| **❿ Dashboard · style** | Position, size, colours, and the live performance tracker. |

### Suggested starting points

|  | M1 scalp | M5 intraday |
|---|---|---|
| Profile | `M1 Scalp` or `Auto` | `M5 Intraday` or `Auto` |
| Min score | 5.0 | 4.5 |
| Confirmation window | 10 | 12 |
| Cooldown | 10 | 6 |
| Stop buffer | 0.35 ×ATR | 0.30 ×ATR |
| Killzone filter | ON (London + NY) | OFF |
| Require HTF alignment | OFF | ON |

Raise `min score` before you loosen anything else. It is the cleanest single lever.

---

## 5. Reading the chart

| Mark | Meaning |
|---|---|
| Dotted horizontal lines | pivot-cluster liquidity pools (red above, blue below) |
| Solid amber lines | session / daily / weekly liquidity — the high-grade pools |
| `EQH×3` / `EQL×2` | pool depth: how many pivots are stacked there |
| `SWEPT` (purple) | that pool was grabbed |
| ✕ above / below a bar | liquidity grab on this bar |
| Blue / red channel bands | ascending support / descending resistance liquidity trendlines |
| Small triangles | liquidity-trendline break |
| Dashed line + `BOS` / `CHoCH` | swing structure event |
| Shaded boxes | FVG (light) and order blocks (darker) |
| Grey line | equilibrium — the 50% of the current dealing range |
| ▲ BUY / ▼ SELL label | the signal, with score, reasons, entry, stop, targets and lot size |

---

## 6. Alerts

Both mechanisms are provided:

* **`alert()`** — fires on bar close with a fully dynamic message:
  `BUY XAUUSD 5 | entry 2412.35 | SL 2410.90 | TP1 … TP2 … TP3 … | risk $1.45 (0.34 lots) | score 6.2 | EQL×3 → CHoCH · DISP · FVG · DISCOUNT · LONDON`
  Create it with *Add alert → Condition: this indicator → Any alert() function call*.
* **`alertcondition()`** — seven static conditions (buy, sell, any signal, buy-side grab,
  sell-side grab, trendline break up/down) for people who want separate alert rows.

---

## 7. Known limitations

* **Pivot latency is structural.** See §2. Anything that removes it repaints.
* The tracker follows **one trade at a time**. With *One trade at a time* off, an outstanding trade
  is booked at market when the next signal replaces it, so the record stays complete — but it is
  still a single-slot tracker, not a portfolio simulator.
* Session inputs are **wall-clock**, so DST shifts move London/NY relative to a UTC setting. Set the
  timezone input to `Europe/London` / `America/New_York` if you want the sessions to follow DST.
* Volume-based confluence degrades to neutral on feeds that report no volume for gold. That is
  handled (it scores 0), not broken.
* Designed and tuned for **XAUUSD M1/M5**. It will run on anything, but the defaults are gold's.

---

## 8. Licence

Attribution-NonCommercial-ShareAlike 4.0 International (**CC BY-NC-SA 4.0**).

Original concept: *Liquidity Trendline With Signals* © **StratifyTrade**, released under the same
licence. This is a derivative work and is released under the same terms.
<https://creativecommons.org/licenses/by-nc-sa/4.0/>

---

*Nothing here is financial advice. It is a signal engine, not a guarantee.*
