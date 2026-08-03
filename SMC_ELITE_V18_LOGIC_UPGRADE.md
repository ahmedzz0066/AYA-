# SMC Elite — v18 "Elite Logic Engine 2.0" Upgrade Specification

Scope: logic quality, filtering accuracy, confirmation reliability, false-signal reduction.
Architecture, themes, visual style, and the modular closed-source structure are preserved.
No full Pine Script source in this document — logic descriptions, critical-filter pseudo-code, and changelog only.

Global conventions used in all pseudo-code below:

- All triggers evaluate on **confirmed bars only** (`barstate.isconfirmed`) — zero repaint on historical bars.
- All HTF requests use `lookahead_off` and act only on **closed HTF bars**.
- `ATR` = `ta.atr(14)` unless stated. `range = high - low`, `body = abs(close - open)`.
- Every new filter is an input toggle in the reorganized settings groups
  (General / Structure / OB / FVG / Liquidity / Confirmation / HTF / Risk).

---

## 1. Order Blocks — Scorecard 2.0

### 1.1 Volume & Momentum Validation (strengthened)

Three changes to candidate qualification:

1. **Adaptive body-to-range floor.** The fixed 60% requirement becomes regime-adaptive:
   base floor raised to **65%**, and in high-volatility regimes (ATR above its own
   70th percentile over 200 bars) it tightens to **70%**, because wide-range bars in
   volatile conditions must show proportionally more displacement to imply institutional intent.
2. **Relative Volume Ranking.** Instead of comparing volume to a single moving average,
   the candidate bar's volume is **percentile-ranked against the last 50 bars**.
   Candidate OBs require ≥ **70th percentile**; Tier-1 promotion requires ≥ **85th percentile**.
   Percentile ranking is robust to volume-regime shifts that break `volume > sma(volume)` checks.
3. **Stricter wick rejection.** The wick *opposing* the OB direction must be ≤ **25% of range**
   (was implicit/loose), and **total wick** ≤ 35% of range. A bar that swept liquidity with a
   long *aligned* wick is still allowed (the sweep wick points away from the zone body).

```
// --- OB Candidate Filter v2 (per confirmed bar) ---
volRank      = percentrank(volume, 50)                  // 0..100
atrRegimeHi  = percentrank(ATR, 200) > 70
bodyFloor    = atrRegimeHi ? 0.70 : 0.65

opposingWick = isBullOB ? (high - max(open, close))     // upper wick for bullish OB
                        : (min(open, close) - low)      // lower wick for bearish OB
totalWick    = range - body

validOB =
      body / range        >= bodyFloor
  and volRank             >= 70
  and opposingWick/range  <= 0.25
  and totalWick / range   <= 0.35
  and range               >= 0.5 * ATR                  // reject compression noise
```

### 1.2 "Freshness" / Smart Mitigation 2.0 (faster zone death, no ghost zones)

The v17 simulation checked whether Candle 1 touched the zone. v18 generalizes this into a
**per-bar zone lifecycle pass** that runs before any drawing:

- **Immediate-test kill (widened):** if any of the first **3** bars after formation touches the
  zone's proximal edge without first leaving an "activation buffer" of **0.75 × ATR** away from
  the zone, the zone is killed instantly (never rendered). A zone must *prove distance* before
  it earns a retest.
- **Wick-touch mitigation for stale zones:** zones older than 100 bars mitigate on **wick touch**;
  younger zones mitigate on the configured rule (default: body close past the 50% level of the zone).
- **Hard expiry:** any zone not tested within **250 bars** is archived (state kept in arrays,
  drawing removed). Nothing lingers visually — ghost zones are structurally impossible because
  the lifecycle pass deletes the drawing object in the same bar the state flips.

```
// --- Zone lifecycle (runs each confirmed bar, before rendering) ---
for zone in activeZones:
    if not zone.activated:
        if barsSince(zone.birth) <= 3 and touches(price, zone.proximalEdge):
            kill(zone)                        // immediate-test kill: never earned distance
        else if distanceFrom(zone) >= 0.75 * ATR:
            zone.activated := true            // proved displacement; retest now meaningful
    else:
        mitRule = age(zone) > 100 ? WICK_TOUCH : BODY_PAST_50PCT
        if mitigated(zone, mitRule):  kill(zone)
        if age(zone) > 250:           archive(zone)
```

### 1.3 Tier-1 (A+) Promotion — hard Trinity + weighted score

All three Trinity conditions are now **mandatory gates** (previously any strong pair could
promote), each additionally contributing a weight to a confluence score, and **HTF alignment
can be made a fourth mandatory gate** via toggle:

```
// --- Tier-1 promotion (evaluated once, on the bar the OB is confirmed) ---
sweep   = low[1] < lowestSwingLow(lookback)              // (mirror for bearish)
displ   = fvgExistsWithin(2)                             // FVG within next 2 candles
bos     = bosWithin(N_bars)
htfOK   = htfPoiOverlap(zone) or not requireHtfForAPlus  // input toggle, default ON

score   = (sweep ? 30 : 0) + (displ ? 30 : 0) + (bos ? 25 : 0)
        + (volRank >= 85 ? 15 : 0)

isTier1 = sweep and displ and bos and htfOK and score >= 85
```

Effect: Tier-1 zones become rarer and materially stronger; everything else stays Tier-2
(transparent styling), preserving the quality-over-quantity philosophy.

---

## 2. Fair Value Gaps & Inverted FVGs

### 2.1 FVG detection (tightened)

- ATR gap filter raised: **0.4 → 0.5 × ATR(14)**.
- Displacement-candle body ratio raised: **72% → 75%**.
- New: the displacement candle's volume must rank ≥ **60th percentile** (same ranking engine as OB).

### 2.2 Invalidation (50% fill rule, hardened)

- A **body close** beyond the gap's Consequent Encroachment (CE = 50%) invalidates the gap on
  that confirmed bar. Wick penetration past CE only *weakens* (score −20), it does not invalidate.
- Fill percentage is tracked per confirmed bar; partially filled gaps shrink their drawn box to
  the unfilled remainder so the chart always shows only live edge.
- **50% Zone Mode is now the default**: only the premium half (entry → CE) renders.

```
// --- FVG invalidation pass ---
for gap in activeFVGs:
    fillPct = penetrationInto(gap, close)         // body-based
    if fillPct >= 0.50 and barstate.isconfirmed:
        invalidate(gap)                           // candidate for IFVG flip (2.3)
    else:
        gap.score -= (wickPast(gap.CE) ? 20 : 0)
        shrinkBoxToUnfilled(gap)
```

### 2.3 IFVG detection (stricter, self-pruning)

An invalidated FVG only flips to an Inversion zone if **all** of:

1. **Displacement on the break candle:** body ≥ 65% of range AND the break move ≥ 0.5 × ATR.
2. **Location filter:** bearish IFVG must sit in the **premium** half of the dealing range,
   bullish IFVG in the **discount** half.
3. **Sweep confluence:** a liquidity sweep occurred within the last 10 bars in the direction
   of the original gap (the trapped side).

Weak IFVGs are **auto-disabled**: any IFVG scoring < 60 on the composite (displacement 40 /
location 30 / sweep 30) is never drawn. IFVGs remain OFF by default and project exactly 5 bars.

---

## 3. Structure (BOS / CHoCH) — Macro-only mapping

- ATR volatility filter for swing validity raised: **0.3 → 0.4 × ATR**, and made adaptive:
  in low-volatility regimes (ATR below its 30th percentile) the threshold *relaxes* to 0.3
  so structure doesn't go silent in quiet markets; in high-volatility regimes it tightens to 0.5.
- **Swing survival requirement (new):** a fractal swing only becomes structural if it remains
  unviolated for **3 confirmed bars** after formation. This suppresses the micro-structure
  whipsaws that trap retail entries.
- **Synchronization guarantee:** structure is computed in a single state machine early in the
  per-bar pass; the OB, FVG, CISD, and Liquidity engines all read that same bar-indexed state.
  No engine recomputes swings independently, so BOS/CHoCH labels, OB tiers, and CISD triggers
  can never disagree about the current structure.

```
// --- Swing validation v2 ---
volPct   = percentrank(ATR, 200)
minMove  = volPct > 70 ? 0.5*ATR : volPct < 30 ? 0.3*ATR : 0.4*ATR

swingValid(s) =
      awayMove(s) >= minMove          // price displaced away by threshold
  and survivedBars(s) >= 3            // not violated for 3 confirmed bars
```

---

## 4. CISD — Precision Origin Break + HTF Gate

### 4.1 Origin Break Mode (precision upgrade)

The origin is now defined as the **open of the first candle of the contiguous same-direction
sequence that performed the liquidity raid** (not merely the raid candle itself). The trigger
requires a **body close** beyond that origin level on a confirmed bar, plus a minimum
displacement on the trigger candle:

```
// --- CISD Origin Break v2 ---
raidBar   = candleThatSweptLiquidity()
originBar = walkBackWhile(sameDirection, from = raidBar)   // first candle of impulse leg
originLvl = open[originBar]

cisdFire =
      barstate.isconfirmed
  and bodyCloseBeyond(originLvl)                 // close, not wick
  and body / range >= 0.55                       // trigger candle displacement floor
  and htfBiasAligned()                           // 4.2 — mandatory when Trend Filter ON
```

### 4.2 Trend Filter (HTF-gated, non-repainting)

HTF bias is derived from the higher-timeframe structure state using `lookahead_off` on
**closed HTF bars only**. When the Trend Filter is enabled (default ON), CISD signals that
oppose HTF bias are fully suppressed — not grayed, suppressed.

### 4.3 A++ trigger chain

The highest-confidence entry chain is now explicitly scored: price taps a **Tier-1 OB** →
CISD fires per 4.1 → a **Diamond FVG** forms within 2 bars of the CISD trigger. When all
three link, the setup is stamped **A++** and the Trade Guide Panel promotes it to the top
recommendation. CISD zones stay ultra-light (96% bg / 75% border) by default.

False-early-trigger reduction: CISD candidates that fire within 2 bars of the raid without
an intervening pullback of ≥ 0.25 × ATR are rejected (stop-run often not yet complete).

---

## 5. Confirmation & Entry Engine 2.0

### 5.1 Retest-only confirmation (final-edge rule)

Confirmation is a strict state machine. Newly forming FVG candles can never confirm;
only a **return to the zone's proximal ("final") edge after price has left the zone** counts.

```
// --- Confirmation state machine (per zone) ---
states: ACTIVE -> LEFT -> TOUCHED -> CONFIRMED -> (ENTRY_DIRECT | ENTRY_PENDING)

ACTIVE:    zone formed; price still inside/adjacent      -> no confirmation possible here
LEFT:      price displaced >= 0.75*ATR away from edge
TOUCHED:   price returns within 0.1*ATR of proximal edge (wick or body)
CONFIRMED: on a confirmed bar, a rejection candle at the edge:
              closes back in trade direction
              body >= 50% of its range
              close beyond the touch bar's midpoint
ENTRY:     if close within entryBand (edge ± 0.35*ATR): ENTRY_DIRECT at market
           else: ENTRY_PENDING limit at proximal edge, expires in K bars
```

### 5.2 Decision Assistant 2.0 (opposing setups)

Both live setups are scored on a 0–100 composite; the panel recommends
**HOLD / WATCH / SWITCH** with hysteresis so it can't flip-flop:

```
setupScore = tierPts        // Tier-1: 30, Tier-2: 15
           + htfAlignPts    // aligned: 20
           + freshnessPts   // untested zone: 15, once-tested: 7
           + rrPts          // RR>=3: 15, RR>=2: 10, RR>=1.5: 5
           + sweepPts       // clean sweep behind zone: 10
           + confirmPts     // CONFIRMED state: 10

recommend:
    SWITCH  iff newSetup.state == CONFIRMED
            and newScore >= currentScore + 15      // hysteresis — objectively stronger only
    WATCH   iff newScore > currentScore            // stronger on paper, not confirmed
    HOLD    otherwise
```

TP1/TP2 keep their on-chart "done" stamps; the R/R box remains optional.

---

## 6. HTF Multi-Timeframe & A+ Confluence

- **Real-time dynamic upgrade (non-repainting):** on every *closed* HTF bar, active LTF zones
  are scanned for overlap. If ≥ **60%** of the LTF zone's range sits inside a fresh HTF POI,
  the LTF zone is upgraded in place — thicker border + `★ [TF]` label — on the next confirmed
  LTF bar. Because only closed HTF bars are read, historical upgrades never move.
- **Confluence-only rendering:** at most the **3 nearest HTF zones per side** are drawn;
  all others exist only as state for the upgrade/confluence scan. HTF layers 1+2 and
  Auto/Manual selection are unchanged.
- HTF alignment feeds three consumers from one shared computation: OB Tier-1 gate (§1.3),
  CISD Trend Filter (§4.2), and Decision Assistant scoring (§5.2).

---

## 7. Liquidity, Zone Merging & Clutter Control

- **Post-sweep-only liquidity (default):** a level renders only after a sweep event
  (wick beyond level + close back inside on a confirmed bar). Pre-sweep levels are hidden
  unless the "Show unswept liquidity" toggle is enabled.
- **OB+FVG merge:** when an FVG overlaps an OB by ≥ **50% of the smaller zone's range**,
  they merge into a single confluence zone carrying the **sum-capped score** of both and the
  combined label (`OB+FVG`). One box, one label, higher score — no stacked rectangles.
- **Zone Display Limit (single setting):** one input `maxVisibleZones` (default 6). Every
  confirmed bar, all active zones are sorted by absolute distance from current price; only the
  nearest N render. Non-rendered zones keep full state in arrays, so they reappear when price
  approaches — display limiting never destroys logic state.

```
// --- Display pass (last step each confirmed bar) ---
sortBy(activeZones, z -> abs(price - z.proximalEdge))
for i, zone in activeZones:
    zone.visible := i < maxVisibleZones
    syncDrawing(zone)          // create/delete box+label to match .visible exactly
```

---

## 8. Risk & Money Management Engine (robustness pass)

- Contract specification resolution is table-driven per asset class, keyed off
  `syminfo.type` / `syminfo.currency` / tick metadata: Forex (standard/mini/micro lot,
  pip value with quote-currency conversion), Metals (XAU/XAG contract sizes),
  Indices/CFDs (point value from `syminfo.pointvalue`).
- Lot size = `riskCurrency / (slDistance × valuePerPoint)`, rounded **down** to the broker
  lot step, clamped to [minLot, maxLot]. Rounding down guarantees realized risk ≤ configured risk.
- Live updates unchanged: recomputed every tick from current Entry↔SL distance; the label on
  the zone always shows the executable size, never a stale one.

---

## 9. Non-Repaint & Performance Guarantees

- **Non-repaint:** every state transition (zone birth/death, tier promotion, CISD fire,
  confirmation, HTF upgrade) is gated on `barstate.isconfirmed`; all `request.security`
  calls use `lookahead_off` and consume only closed HTF bars. Realtime-bar previews are
  visual-only and finalize identically at bar close.
- **Performance:** single shared structure state machine (§3) removes duplicated swing scans;
  all zone collections are fixed-cap arrays with delete-on-invalidate; the display-limit pass
  bounds total drawing objects to `maxVisibleZones + HTF caps` regardless of history length;
  remaining legacy/dead branches from pre-v15 modes removed.
- **Settings:** all new filters exposed as toggles/inputs, grouped:
  General · Structure · Order Blocks · FVG/IFVG · Liquidity · Confirmation · HTF · Risk.

---

## 10. Changelog — v18 Logic Changes (concise)

**Order Blocks**
- Body-to-range floor 60% → 65% (70% in high-vol regime, adaptive).
- Volume validation switched to 50-bar percentile rank (≥70 candidate, ≥85 Tier-1).
- Opposing-wick cap 25%, total-wick cap 35% of range.
- Mitigation: immediate-test kill window widened to 3 bars with 0.75×ATR activation buffer;
  wick-touch mitigation for zones >100 bars old; hard archive at 250 bars. Ghost zones eliminated.
- Tier-1: Sweep + Displacement-FVG + BOS all mandatory, score ≥ 85; optional mandatory
  HTF-alignment gate (default ON).

**FVG / IFVG**
- Gap filter 0.4 → 0.5×ATR; body ratio 72% → 75%; +60th-percentile volume requirement.
- Invalidation = body close past CE only; wick past CE penalizes score; boxes shrink to unfilled remainder.
- 50% Zone Mode now default.
- IFVG requires displacement + Premium/Discount location + 10-bar sweep confluence;
  IFVGs scoring <60 auto-disabled (never drawn).

**Structure**
- Swing filter 0.3 → 0.4×ATR, adaptive 0.3–0.5 by volatility percentile.
- New 3-bar swing-survival requirement kills micro-structure traps.
- Single structure state machine shared by all engines (guaranteed sync).

**CISD**
- Origin redefined as first candle of the raid impulse leg; body-close break + 55% trigger-candle
  displacement required.
- HTF Trend Filter now fully suppresses counter-bias CISD (default ON).
- Explicit A++ chain: Tier-1 OB tap → CISD → Diamond FVG within 2 bars.
- Anti-early rule: reject CISD within 2 bars of raid without a 0.25×ATR pullback.
- Ultra-light CISD styling remains default.

**Confirmation & Entry**
- Strict state machine; confirmation only on retest of the final (proximal) zone edge after
  a 0.75×ATR departure — new FVG candles can never confirm.
- Direct vs pending entry decided by 0.35×ATR entry band; pending orders expire.
- Decision Assistant: 6-component 0–100 score; SWITCH only when new setup is CONFIRMED and
  ≥15 points stronger (hysteresis); otherwise WATCH/HOLD.

**HTF**
- LTF zones dynamically upgraded (★, thick border) when ≥60% overlapped by a later HTF POI,
  using closed HTF bars only — non-repainting.
- Max 3 rendered HTF zones per side; unlimited as invisible confluence state.

**Liquidity & Clutter**
- Liquidity renders post-sweep only (toggle to show unswept).
- OB+FVG overlap ≥50% merges into one confluence zone with combined score.
- Single `maxVisibleZones` input; nearest-to-price prioritization; hidden zones retain state.

**Risk Engine**
- Table-driven contract specs (Forex/Metals/Indices) with quote-currency conversion;
  lot rounding down to broker step, min/max clamps.

**Platform**
- Zero repainting on historical bars for all new logic (confirmed-bar gating, lookahead_off).
- Dead code removed; fixed-cap arrays + bounded drawing objects; settings regrouped into
  General / Structure / OB / FVG / Liquidity / Confirmation / HTF / Risk.
