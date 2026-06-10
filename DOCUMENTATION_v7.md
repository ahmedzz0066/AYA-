# VolSD Quantum v7 — Volumetric Supply & Demand, Elite Edition

> Next-generation, non-repainting Supply/Demand engine that fuses **Auction Market
> Theory** (Volume Profile, POC/Value Area, HVN/LVN) with **Smart Money Concepts**
> (market structure BOS/CHoCH, Order Blocks, Fair Value Gaps, liquidity sweeps,
> premium/discount + OTE) into a single, math-normalized **confluence score**.

Implementation: [`VolSD_Quantum_v7.pine`](./VolSD_Quantum_v7.pine).
v6 (and its docs) remain in the repo for comparison.

---

## 0. Why v7 is a different class of tool than v6

v6 was already objective, but it anchored zones to a generic **base→impulse**
heuristic. That answers *"where did price move fast?"* — not *"why did institutions
move it?"*. v7 re-architects the engine around the **cause** of institutional moves
and then demands that *multiple independent forms of evidence agree* before a zone is
shown.

| Dimension | v6 | **v7 (Quantum)** |
|---|---|---|
| Zone origin | Base→impulse heuristic | **Order Block at the origin of a structural break (BOS/CHoCH)** |
| Market structure | none | **Full swing engine: BOS / CHoCH / dealing range / bias** |
| Imbalance proof | impulse range + volume | **Displacement + Fair Value Gap (3-bar imbalance)** |
| Liquidity logic | none | **Stop-hunt / liquidity-sweep detection** |
| Location logic | none | **Premium/Discount + OTE (dealing range)** |
| Volume context | profile + base VWAP | profile + **HVN-overlap confluence** |
| Volume threshold | fixed ×average | **adaptive volume z-score** (regime-robust) |
| Score channels | 5 | **10 orthogonal channels** |
| Targets / R:R | none | **projected target to opposing liquidity + R:R label** |

The thesis: **conviction = quantity of independent, orthogonal evidence that agrees.**
A zone that is *simultaneously* an Order Block + structural break + displacement + FVG
+ liquidity sweep + in discount + on an HVN + with HTF bias is, by construction, the
rare A+ setup. The score makes that explicit and rankable.

---

## 1. First Principles (unchanged foundation, extended)

1. **Price is a continuous double auction.** Direction = urgency; **volume = capital
   committed**. (Auction Market Theory.)
2. **Institutions cannot fill size at one price.** They accumulate inside a tight
   **Order Block**, then **displace** price (a violent, one-sided, high-volume move)
   once the opposing book is exhausted. The displacement tears a **Fair Value Gap** —
   a price range crossed so fast it was *not* auctioned two-sidedly (an inefficiency
   the market tends to revisit).
3. **Markets seek liquidity.** Stops rest beyond swing highs/lows (equal highs/lows).
   Smart money often **sweeps** that liquidity (a stop-hunt) to fill its own orders,
   *then* reverses. A zone created right after a sweep is fuel-loaded.
4. **Structure encodes intent.** A **BOS** (break of structure) confirms trend
   continuation; a **CHoCH** (change of character) is the first evidence of reversal.
   The Order Block that *caused* the break is the highest-quality zone.
5. **Location matters (premium/discount).** Within the current **dealing range**
   (last swing low → swing high), buy in **discount** (lower half) and sell in
   **premium** (upper half); the **OTE** band (0.62–0.79 retracement) is the
   institutional sweet spot.
6. **Volume profile = the auction's memory.** **HVNs** are accepted/fair prices
   (sticky, strong); **LVNs** are rejected/transit prices. Strong zones sit on HVNs;
   FVGs live in LVNs.
7. **Zones are perishable and consumable.** Freshness decays exponentially with time;
   each retest absorbs residual liquidity (geometric decay); a close through =
   mitigation (dead).

Every rule below is a direct mechanical consequence of 1–7. Nothing is added for looks.

---

## 2. The Engines

### 2.1 Market-structure engine (non-repainting)
- Swings via `ta.pivothigh(pivLen, pivLen)` / `ta.pivotlow(...)`. A pivot is only
  confirmed `pivLen` bars *after* it forms — this lag is exactly what makes the engine
  non-repainting (a confirmed swing never changes).
- Persistent levels: `lastSwH/lastSwL` (and `prevSwH/prevSwL`) define the **dealing
  range** and the **liquidity pools**.
- **Break logic** on a confirmed close:
  - `close > swH` ⇒ **BOS up** if bias was already bullish, else **CHoCH up**; set
    bias = bullish; consume `swH`.
  - Mirror for `close < swL`. Consuming the level prevents re-triggering and tolerates
    late pivot confirmation (a break still registers if price was already through it).

### 2.2 Order Block extraction
When a break fires, scan back up to `obScan` bars for the **last opposite-color
candle** — the institutional footprint before displacement:
- Demand: last **bearish** candle before the up-break → zone = its range (or body).
- Supply: last **bullish** candle before the down-break.

### 2.3 Displacement gate (adaptive)
The breakout candle must prove an imbalance, using **scale-free** tests so the same
settings transfer across symbols/timeframes:
```
range  > dispATR · ATR                  # large, volatility-relative move
volZ   = (volume − mean)/stdev ≥ volZmin   # ADAPTIVE volume (z-score, not fixed ×)
body/range ≥ bodyRatio                  # one-sided / directional
direction agrees with the break
(optional) a Fair Value Gap exists
```
Using a **volume z-score** instead of a fixed multiple is a key v7 upgrade: it
self-calibrates to each instrument's volume regime, reducing false zones on
low-liquidity symbols and missed zones on high-liquidity ones.

### 2.4 Fair Value Gap (imbalance)
3-bar gap: bullish FVG ⇔ `low > high[2]` (current low above the high two bars back);
bearish FVG ⇔ `high < low[2]`. Gap size (in ATR) feeds the score continuously.

### 2.5 Liquidity sweep (stop-hunt)
Demand sweep ⇔ price took out the **prior** swing low and reclaimed it:
`lowest(low, sweepLook) < prevSwL ∧ close > prevSwL`. Mirror for supply. This is the
"spring/upthrust" signature of accumulation/distribution.

### 2.6 Premium / Discount + OTE
Dealing range `[rngBot, rngTop]`, midpoint `rngMid`. A demand OB scores the location
channel when it sits **below** mid (discount); supply when **above** mid (premium).
The **OTE band** (`oteLo–oteHi`, default 0.62–0.79) marks the optimal-entry sweet spot
for discretionary refinement.

### 2.7 Volume Profile (state-free)
Rolling profile over `vpLookback` into `vpBins`; each bar spreads its volume across the
bins it spans. **POC** = modal bin; **Value Area** (default 70%) by greedy expansion
from the POC. The profile is computed **without `ta.*`** (manual min/max), so it can be
evaluated on demand for HVN-overlap checks without repaint/state hazards.

---

## 3. Composite Strength (0–10): 10 orthogonal channels

Each channel is normalized to [0,1]; strength is their **weighted mean × 10** (bounded,
interpretable, hard to overfit):

| # | Channel | Normalized definition | Mechanic |
|---|---|---|---|
| 1 | Structure | CHoCH = 1.0, BOS = 0.75 | reversal context > continuation |
| 2 | Volume percentile | `percentrank(vol,100)/100` | committed capital |
| 3 | Displacement | `min(1, (range/ATR)/(1.6·dispATR))` | imbalance magnitude |
| 4 | Delta imbalance | close-location value (CLV) | net aggressor proxy |
| 5 | Fair Value Gap | `min(1, gap/(0.5·ATR))` | inefficiency to be revisited |
| 6 | Liquidity sweep | 1 if stop-hunt + reclaim | engineered liquidity |
| 7 | Premium/Discount | 1 if correct half of range | buy low / sell high |
| 8 | HVN alignment | 1 if OB overlaps Value Area | acceptance / sticky price |
| 9 | HTF bias | 1 if HTF EMA agrees | higher-TF order flow |
| 10 | Width efficiency | `max(0, 1 − width/(maxW·ATR))` | tight = high conviction |

```
S = 10 · Σ(wᵢ · channelᵢ) / Σ wᵢ           (default min display = 6.0/10)
```

**Live strength** (shown, decaying):
```
S_live = S · 0.5^(age/H) · touchDecay^touches
```
plus binary **mitigation** (close/wick through the far edge ⇒ zone removed/greyed).

---

## 4. Logic Flow / Pseudocode

```
every bar (all ta.* hoisted):
    ATR, avgVol, volSD, volZ, volPercentile, ADX, HTF bias, sweep extremes
    update swing pivots → lastSw/prevSw, dealing range, bias
    detect BOS / CHoCH on confirmed close

    if confirmed and regimeOK:
        for each fired break (up→demand, down→supply):
            ob = last opposite candle within obScan      # Order Block
            compute: CLV, FVG(+gap), sweep, premium/discount, HVN-overlap
            gate = displacement ∧ volZ ∧ directional ∧ body ∧ (FVG if required)
            if gate:
                S = weightedMean(10 channels) · 10
                if S ≥ minStrength:
                    target = opposing range extreme;  R:R = reward/risk
                    draw OB box (opacity∝S), POC line, target line, label
                    push zone; cap per side

        for each active zone:
            close/wick through far edge → mitigate (remove/grey)
            else: count retests (decay), recompute S_live, update visuals
                  retest + rejection + volume spike on strong zone → ALERT

    on last bar (if enabled): draw POC/VAH/VAL + histogram; update dashboard
```

---

## 5. Usage, Entries, Exits, Risk

**Trade the A+ confluence, skip the rest.** The dashboard shows structural **bias** and
whether price is in **discount/premium** and **trending/ranging**.

- **Bias filter:** prefer **demand in discount within a bullish structure** (and the
  mirror for shorts). The HTF channel already rewards this.
- **Entry (reaction):** wait for price to **retest** a fresh, high-`S_live` zone and
  print a **rejection candle on a volume spike** (built-in alert). Refine entry inside
  the **OTE** band for the best R:R. Confirm on a lower TF if discretionary.
- **Stop:** beyond the **far edge** of the OB (below `bot` for demand / above `top` for
  supply). Width is ATR-adaptive, so the stop is volatility-aware. Mitigation = thesis
  void → exit.
- **Targets:** the projected **target line** (opposing range liquidity); scale at the
  **POC** (fair value) and at **VAH/VAL**. The label prints the **R:R** at creation.
- **Sizing:** risk a fixed fraction (≤1%) of equity per trade; optionally scale size by
  `S_live/10` so conviction maps to exposure.
- **Regime:** in **RANGING**, fade zone-to-zone; in **TRENDING**, take with-trend zones
  and ignore counter-trend ones (or enable the regime filter to suppress them).

---

## 6. Non-Repaint & Robustness

- Zones form **only on `barstate.isconfirmed`**, from Order Blocks that reference
  **already-closed** candles; pivots confirm with `pivLen` lag → confirmed structure
  never changes.
- HTF series use `request.security(..., lookahead = barmerge.lookahead_off)` with `[1]`.
- `f_profile` is **state-free** (manual min/max), and every `ta.*` (ATR, stdev,
  percentrank, ADX, lowest/highest) is **hoisted to global scope** so it evaluates every
  bar — eliminating the classic "stateful function called conditionally" repaint/bug.
- All thresholds are **ATR- or z-score-normalized** ⇒ instrument/timeframe agnostic.
- Drawing objects are capped (`max_*_count`, `maxZones` per side).

---

## 7. Validation / Edge-Proving (avoid curve-fit)

1. **Non-repainting forward log:** record `{bar, side, top, bot, S, channels...}` and
   the subsequent MFE/MAE over `n` bars (no look-ahead by construction).
2. **Monotonicity test:** bucket zones by strength decile; mean reaction should rise
   monotonically with `S`. If it doesn't, the score has no edge.
3. **Ablation study:** drop one channel at a time and re-measure expectancy. A channel
   that doesn't move expectancy is noise — remove it (parsimony beats curve-fit).
4. **Expectancy by regime:** `E = p_win·avg_win − p_loss·avg_loss` for the mechanical
   rule, split by trending/ranging and discount/premium. Edge ⇔ `E > costs` OOS.
5. **Walk-forward:** tune weights on a train window, evaluate untouched. Few free
   parameters (transparent weighted mean) is the main anti-overfitting safeguard.
6. **Cross-market / cross-TF robustness sweep** with identical settings; a true
   mechanic survives, a fit does not.
7. **Null controls:** compare against random levels and shuffled-volume series; real
   edge must beat both.

---

## 8. Optional Order-Flow Upgrades
- **True delta** (if buy/sell volume available): replace CLV in channel 4 with
  `Σ(buyVol−sellVol)/Σvol` over the OB + displacement.
- **LVN-snapped edges:** snap OB boundaries to the nearest profile LVNs (true imbalance
  gap) using the binning already in `f_profile`.
- **Footprint POC** per zone instead of OB midpoint.

---

## 9. Limitations
- Delta is a **proxy** unless a real buy/sell feed is supplied.
- Volume quality is venue-specific (FX/spot crypto) — interpret relative to one feed.
- The tool ranks *probability*, not certainty. Risk management is non-negotiable.
- Very large `vpLookback × vpBins` increases compute; defaults are tuned for balance.
