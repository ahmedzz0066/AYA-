# Volumetric Supply & Demand Zones — Version 6

A logic-driven, math-first supply/demand engine for TradingView (Pine Script v6).
It replaces subjective "draw-a-box-on-a-swing" zone marking with an objective pipeline:
**base→impulse structure detection → volume profiling → composite strength scoring →
freshness/consumption decay → multi-timeframe confluence**.

The implementation lives in [`VolumetricSupplyDemandZones_v6.pine`](./VolumetricSupplyDemandZones_v6.pine).

---

## 1. First Principles

Everything below is derived from a single mechanic, not from chart aesthetics.

1. **Price is a continuous double auction.** Every print is a transaction where one
   party crossed the spread. Direction tells you who was more *urgent*; volume tells
   you how much *capital* was committed.
2. **A zone is a depth event, not a line.** When a large resting/refilled order pool
   absorbs the opposing flow and reverses price, it leaves a footprint: a tight
   *base* (acceptance / order accumulation) followed by a violent *impulse* (the
   imbalance discharging once the opposite book is exhausted).
   - **Demand zone** = base that resolved *upward* with a high-volume bullish impulse
     → residual unfilled **buy** interest.
   - **Supply zone** = base that resolved *downward* with a high-volume bearish impulse
     → residual unfilled **sell** interest.
3. **Volume is the only direct evidence of committed capital.** Swing highs/lows are
   *where* something happened; volume is *how much*. We therefore anchor zones to
   volume, not to raw price geometry.
4. **Auction value (Volume Profile).** Within any window the distribution of traded
   volume has a mode (**POC**, point of control = fair value) and a **Value Area**
   (default 70% of volume, bounded by **VAH/VAL**). High-Volume Nodes (HVN) =
   acceptance/equilibrium = *strong, sticky* prices. Low-Volume Nodes (LVN) =
   rejection/transit = price moves through fast. Strong zones cluster on HVNs; the
   *edges* of zones often sit on LVNs (the imbalance gap).
5. **Zones are consumable and perishable.** Each retest fills some of the residual
   order pool (consumption); time lets the resting orders get cancelled/filled
   elsewhere (freshness decay). A *fresh, untested* zone is strongest; a zone that has
   been tapped multiple times or traded through is spent (**mitigated**).

These five facts produce every rule in the indicator. No rule is added for visual
reasons alone.

---

## 2. Mathematical Foundations

Let `ATR` be the 14-period Average True Range and `V̄ = SMA(volume, 50)`.

### 2.1 Base → Impulse detection (objective, not eyeballed)

For the **last closed bar** (offset `1`, so the indicator never repaints):

```
range₁  = high₁ − low₁
body₁   = |close₁ − open₁|
direc   = body₁ / max(range₁, mintick)            # directional purity 0..1

isImpulse = range₁ > k_atr · ATR                  # imbalance: large range
          ∧ volume₁ > k_vol · V̄                  # capital: high relative volume
          ∧ direc  ≥ k_body                       # one-sided: real departure
```

The **base** is the `L` bars immediately preceding the impulse. It must be a genuine
consolidation (acceptance), enforced by:

```
baseHigh − baseLow  <  k_base · ATR
```

- Up-impulse + valid base ⇒ **Demand** zone, body = `[baseLow, baseHigh]`.
- Down-impulse + valid base ⇒ **Supply** zone, body = `[baseLow, baseHigh]`.

**Why these inequalities?** They are scale-free (everything is normalized by ATR or
by average volume), so the same thresholds transfer across instruments and
timeframes — a core anti-curve-fitting property. We are testing for the *physics* of
an imbalance (small base, big high-volume one-sided exit), not for a hard-coded
pattern.

### 2.2 Volume Profile (rolling)

Over a lookback `N`, partition `[lo, hi]` into `B` bins of width `Δ = (hi−lo)/B`.
Each bar `i` distributes its volume **uniformly across the bins its range spans**
(a standard, unbiased volume-at-price estimator):

```
for each bar i in lookback:
    loBin = clamp(⌊(lowᵢ − lo)/Δ⌋, 0, B−1)
    hiBin = clamp(⌊(highᵢ − lo)/Δ⌋, 0, B−1)
    each bin in [loBin..hiBin] += volumeᵢ / (hiBin − loBin + 1)
```

- **POC** = `lo + (argmaxᵦ binVol[b] + 0.5)·Δ`.
- **Value Area (VAH/VAL):** start at the POC bin; repeatedly annex whichever adjacent
  bin (above or below) holds more volume until cumulative volume ≥ `vaPct%` of total.
  This is the classic Market-Profile 70% VA construction (greedy expansion from the
  mode), which provably yields the smallest-width contiguous interval around the POC
  for a unimodal-ish distribution.

Inside each detected zone we use the **base VWAP** as a local POC proxy:

```
zonePOC = Σ(hlc3ᵢ · volumeᵢ) / Σ(volumeᵢ)   over the base bars
```

VWAP is the first moment of the price–volume distribution — the volume-weighted fair
value of the base — and is a robust, cheap estimator of the local control price.

### 2.3 Composite Strength Score (0–10)

Five **orthogonal**, individually-normalized factors are combined as a weighted mean
so the result is interpretable and bounded. Each factor ∈ [0, 1]:

| Factor | Symbol | Definition | Rationale |
|---|---|---|---|
| Volume percentile | `sᵥ` | `percentrank(volume, 100)` of the impulse bar / 100 | More committed capital ⇒ deeper book event |
| Impulse ratio | `sᵢ` | `min(1, (range₁/ATR) / (1.5·k_atr))` | Sharper departure ⇒ larger imbalance |
| Delta imbalance | `s_d` | Demand: `(close₁−low₁)/range₁`; Supply: `(high₁−close₁)/range₁` | Close-location proxy for net aggressive flow (no L2 needed) |
| Width efficiency | `s_w` | `max(0, 1 − (top−bot)/(k_w·ATR))` | Tight HVN zones are higher-conviction than diffuse ones |
| HTF confluence | `s_h` | `1` if HTF trend (EMA) agrees with the zone side, else `0` | Higher-TF order flow dominates lower-TF |

```
S = 10 · ( wᵥ·sᵥ + wᵢ·sᵢ + w_d·s_d + w_w·s_w + w_h·s_h )
        / ( wᵥ + wᵢ + w_d + w_w + w_h )
```

Because it is a *normalized weighted mean of bounded factors*, `S ∈ [0,10]` always, and
each weight has a transparent marginal effect — there is no opaque magic constant to
overfit. The **delta proxy** is the standard close-location value (CLV); with real
buy/sell volume it can be swapped for true delta (see §6).

### 2.4 Freshness & Consumption (mitigation) decay

Static strength `S` is fixed at creation. The **live** strength shown on the chart
decays continuously:

```
age      = bar_index − createdBar
fresh    = 0.5 ^ (age / H)          # exponential decay, half-life H bars
consumed = d ^ touches              # geometric absorption per retest, d∈(0,1]
S_live   = S · fresh · consumed
```

- **Exponential time decay** encodes the empirical fact that resting liquidity is
  cancelled/refilled and that older zones lose predictive value; the half-life `H` is
  the single, intuitive tuning knob.
- **Geometric touch decay** models order-pool absorption: each retest fills part of
  the residual liquidity, so the `k`-th touch leaves `dᵏ` of the original strength.

**Mitigation (zone death):** a demand zone is mitigated when price *closes below* its
bottom (or wicks through, configurable); supply mirrors this. Mitigated zones are
removed (or greyed). This is the binary limit of the absorption model: the pool is
fully consumed / invalidated.

### 2.5 Regime filter

`ADX(14)` separates trending from ranging conditions. Optionally only create zones when
`ADX ≥ threshold` (trending), because supply/demand reversals are most reliable when
they align with directional order flow; in chop, zones churn and mitigate quickly.

---

## 3. Logic Flow / Pseudocode

```
on every bar:
    compute ATR, V̄, volPercentile, ADX, HTF trend (lookahead OFF → no repaint)

    if bar is CONFIRMED:                      # historical bars are always confirmed
        detect impulse on offset 1
        if impulse ∧ base is tight ∧ regimeOK:
            top, bot = base high/low
            S = compositeStrength(...)
            if S ≥ minStrength:
                zonePOC = baseVWAP(base bars)
                draw box (opacity ∝ S), POC line, strength label
                push zone to per-side array; if over cap, drop oldest

        for each active zone (both sides):
            if price closed/wicked through  → mark mitigated, remove/grey
            else:
                if newly touching            → touches += 1
                                              if S_live ≥ thr ∧ rejection ∧ vol spike → ALERT
                recompute S_live, update box opacity, extend right, update label

    if last bar ∧ profile enabled:
        build rolling volume profile → draw POC/VAH/VAL + histogram
        update regime/diagnostics table
```

---

## 4. Inputs (grouped)

| Group | Key inputs | Purpose |
|---|---|---|
| Base → Impulse | base length, max base range ×ATR, impulse ×ATR, impulse ×vol, body ratio | Define the imbalance physics |
| Volume Profile | lookback, bins, Value-Area %, histogram | POC/VAH/VAL context |
| Strength | per-factor weights, width normalization, **min strength to display** | Scoring & filtering |
| Mitigation | freshness half-life, per-touch decay, trigger (close/wick), remove, max zones | Decay & lifecycle |
| MTF | enable, resolution, trend EMA length | Higher-TF confluence |
| Regime | trending-only toggle, ADX length & threshold | Market-state filter |
| Visuals | colors, POC line, label, extend, opacity range | Display |
| Alerts | retest+rejection toggle, volume-spike multiple | Notifications |

---

## 5. Usage, Entries, Exits & Risk

**Read the zones, don't chase them.**

- **Bias:** trade *with* HTF confluence (a demand zone scoring high *because* the HTF
  trend is up is a higher-probability long).
- **Entry (reaction trade):** wait for price to *retest* a fresh, high-`S_live` zone and
  print a **rejection candle on a volume spike** (the built-in alert). Enter on the
  close of the rejection bar or on a lower-TF confirmation.
- **Stop:** just beyond the *far* edge of the zone (below `bot` for demand, above `top`
  for supply). The zone width already adapts to volatility (ATR-normalized), so the
  stop is volatility-aware by construction. If the zone is mitigated, the thesis is
  void — exit.
- **Targets:** opposing zone, the rolling **POC**, or **VAH/VAL**. Scale out at the POC
  (fair value) and trail the remainder toward the opposing zone.
- **Position sizing:** size so that `risk = entry − stop` is a fixed fraction of equity
  (e.g. ≤1%). Optionally scale size by `S_live/10` so conviction maps to exposure.
- **Filters:** in `RANGING` regime (table shows it), prefer fading zone-to-zone; in
  `TRENDING`, prefer with-trend zone entries and ignore counter-trend zones.

---

## 6. Optional Order-Flow Upgrades

- **True delta:** if a buy/sell-volume feed is available, replace the CLV delta proxy
  `s_d` with `Σ(buyVol−sellVol)/Σvol` over the base+impulse for genuine cumulative
  delta bias.
- **Footprint POC:** replace base VWAP with the per-zone binned profile POC for an
  exact HVN anchor (the `f_profile` routine already does binning and can be scoped to
  the base region).
- **LVN edges:** snap zone boundaries to the nearest LVNs of the local profile to
  capture the true imbalance gap.

---

## 7. Validation / Backtesting Approach (proving edge, avoiding curve-fit)

The indicator is built for falsifiable testing:

1. **Forward, non-repainting logging.** Because zones form only on confirmed bars and
   HTF data uses `lookahead_off`, you can log `{createdBar, side, top, bot, S}` and the
   subsequent outcome without look-ahead bias.
2. **Event study / bounce-rate.** For every zone at first touch, measure the MFE/MAE
   over the next `n` bars. Bucket by strength decile. **Hypothesis:** mean reaction
   (e.g. MFE in the zone direction) increases monotonically with `S`. If higher-`S`
   buckets don't react better, the score has no edge.
3. **Expectancy.** Using the mechanical rule (enter on retest+rejection+spike, stop at
   far edge, target POC) compute expectancy `E = p_win·avg_win − p_loss·avg_loss` per
   strength bucket and per regime. Edge exists if `E > costs` out-of-sample.
4. **Walk-forward, not in-sample optimization.** Tune weights/thresholds on a training
   window, then evaluate on an untouched window. Because all thresholds are ATR/volume-
   normalized and the score is a transparent weighted mean, there are few free
   parameters — the main anti-overfitting safeguard.
5. **Robustness sweep.** Re-run across instruments (equities, FX, futures, crypto) and
   timeframes with the *same* settings. A genuine market-mechanic edge should survive;
   a curve-fit one will not.
6. **Null controls.** Compare zone-reaction stats against (a) random price levels and
   (b) shuffled-volume series. Real edge must beat both.

---

## 8. Anti-Repaint & Robustness Notes

- Zones are created only on `barstate.isconfirmed` and reference the **closed** impulse
  bar (offset 1) — a zone that appears never moves or disappears on history.
- HTF series use `request.security(..., lookahead = barmerge.lookahead_off)` and the
  `[1]` offset, the standard non-repainting MTF pattern.
- All thresholds are normalized (ATR, average volume, percentile), so behavior is
  consistent across symbols and resolutions; no symbol-specific constants.
- Drawing objects are capped (`max_*_count`, `maxZones` per side) so the script stays
  within TradingView limits on long histories.

---

## 9. Limitations

- Delta is a **proxy** (close-location) unless a real buy/sell feed is supplied.
- Volume quality varies by venue (FX/spot crypto volume is broker/exchange-specific);
  interpret the profile relative to the same feed, not across feeds.
- The indicator describes *where reactions are probable*, not certainties — always
  combine with risk management.
