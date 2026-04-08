# HELIX v6 — Complete User Manual
## Hydraulic Energy Liquidity Intelligence eXtraction

---

## Table of Contents
1. [What is HELIX?](#1-what-is-helix)
2. [The Theory — Why This Works](#2-the-theory--why-this-works)
3. [Mathematical Foundations](#3-mathematical-foundations)
4. [The Five Pillars](#4-the-five-pillars)
5. [Reading the Chart](#5-reading-the-chart)
6. [The Dashboard Explained](#6-the-dashboard-explained)
7. [Settings Reference](#7-settings-reference)
8. [Entry Checklist](#8-entry-checklist)
9. [Trade Examples](#9-trade-examples)
10. [Critique of the Original Indicator](#10-critique-of-the-original-indicator)
11. [Why HELIX Beats Traditional Volume Indicators](#11-why-helix-beats-traditional-volume-indicators)
12. [FAQ](#12-faq)

---

## 1. What is HELIX?

**HELIX** is an original market-dynamics framework built on **fluid dynamics physics**, **smart money concepts**, and **Bayesian probability**.

The word HELIX is both an acronym and a metaphor:
- **H**ydraulic **E**nergy **L**iquidity **I**ntelligence e**X**traction
- A helix (spiral) represents the dual-strand relationship between **price** and **volume** — inseparable, always intertwined, encoding information at every turn.

> Core premise: Markets are not random. They are hydraulic systems where **pressure builds** (potential energy) and then **releases** (kinetic energy) in predictable, engineered sequences orchestrated by institutional participants.

HELIX identifies the exact moment when:
1. Institutional pressure has accumulated to maximum (compression)
2. Retail stop-losses have been engineered and taken (liquidity sweep)
3. Volume intent confirms the smart-money direction (absorption / exhaustion)
4. Probability exceeds a statistical threshold (≥ 65% by default)

Only then — when all four independent conditions align — does HELIX print a signal.

**Signal frequency is intentionally low. Quality is the only priority.**

---

## 2. The Theory — Why This Works

### 2.1 Markets as Hydraulic Systems

In fluid dynamics, pressure in a closed system obeys:

```
P = ρ · g · h
```

| Physics Term | Market Analog |
|---|---|
| Density (ρ) | Volume concentration (z-score) |
| Gravity (g) | Market gravity = mean-reversion force |
| Height (h) | Price compression (tight range = high head) |
| Pressure (P) | Hydraulic Pressure Score |

When a fluid is compressed into a narrow chamber under high density, it **must** expand. The same is true of price: tight consolidation under high volume = imminent expansion. HELIX quantifies exactly how "loaded the spring is."

### 2.2 The Liquidity Engineering Cycle

Institutional participants do not randomly buy and sell. They operate in a **three-phase cycle**:

```
Phase 1: INDUCEMENT
  └─ Create obvious levels (equal highs/lows) to attract retail stop orders

Phase 2: SWEEP (Manipulation)
  └─ Spike through those levels, trigger the stops, acquire their positions

Phase 3: EXPANSION (Distribution / Accumulation)
  └─ Move price in true direction with the liquidity just collected
```

HELIX detects Phase 2→3 transition: the sweep of a swing level followed immediately by compression and confirmed volume intent.

### 2.3 Energy Conservation

```
E_total = PE (Potential Energy) + KE (Kinetic Energy) ≈ constant
```

When PE is high (compression) and KE is low (stagnant price), the system is like a compressed spring. The energy ratio (PE / E_total > 0.60) is HELIX's confirmation that energy has been stored and is ready to release.

When KE spikes (price moves rapidly with volume), the energy has converted — this is the expansion phase. HELIX shows this as green/red expansion bars.

### 2.4 The Reynolds Number — Avoiding Chaos

Reynolds Number in fluid dynamics separates **laminar flow** (smooth, predictable) from **turbulent flow** (chaotic, unpredictable):

```
Re = (velocity × density) / viscosity
```

In markets:
- **Low Re (Laminar)** = trending, predictable market → trade it
- **High Re (Turbulent)** = choppy, news-driven, random → avoid it

HELIX applies a turbulence penalty to all probability calculations and **blocks signals entirely** when the market is turbulent. This alone eliminates a large percentage of false signals.

---

## 3. Mathematical Foundations

### 3.1 Hydraulic Pressure Score

```
VolDensity = (Volume - VolMean) / VolStdDev          [z-score]
Compression = -(PriceRange - RangeMean) / RangeStdDev  [inverted range z-score]
HydraulicP = VolDensity × (1 + max(Compression, 0))
SmoothedP  = EMA(HydraulicP, 5)
```

> Interpretation: SmoothedP > +1.5 → significant pressure building. A sustained reading above +2.0 is rare and indicates a high-probability expansion is imminent.

### 3.2 Kinetic / Potential Energy

```
PriceVelocity = |Close - Close[1]| / ATR             [normalised speed]
NormVolume    = Volume / VolumeSMA                   [relative volume]

KE = 0.5 × NormVolume × PriceVelocity²              [½mv² analog]
PE = NormVolume × max(Compression,0) × (Range/ATR)  [mgh analog]

EnergyRatio = PE / (PE + KE)
```

| EnergyRatio | Meaning |
|---|---|
| > 0.60 | PE dominant → **COMPRESSION** (spring loaded) |
| 0.40–0.60 | Balanced → transitional |
| < 0.40 | KE dominant → **EXPANSION** (spring released) |

### 3.3 Delta Z-Score (Buying vs Selling Pressure)

```
BuyPct  = (Close - Low) / (High - Low)
BuyVol  = Volume × BuyPct
SellVol = Volume × (1 - BuyPct)
NetDelta = BuyVol - SellVol

DeltaZ = (NetDelta - DeltaMean) / DeltaStdDev
```

> This is a proxy for the order book delta. DeltaZ > +1.5 = strong buying footprint. DeltaZ < -1.5 = strong selling footprint.

### 3.4 Composite Probability (Geometric Mean)

```
P_total = (P_energy × P_volume × P_structure × P_delta)^(1/4) × Re_penalty
Signal_Prob = 0.30 + P_total × 0.65   [mapped to realistic range 30%–95%]
```

**Why geometric mean?**
Arithmetic mean hides a weak component. Geometric mean forces ALL four legs to be strong. A single probability of 0.20 in any leg will drag the composite below the 0.65 threshold even if the other three are perfect. This is by design — it enforces multi-factor confluence.

| Component | Condition | Score |
|---|---|---|
| P_energy | EnergyRatio → compressed | 0.0–1.0 |
| P_volume | Absorption | 0.82 |
| P_volume | Exhaustion | 0.78 |
| P_volume | Aggression | 0.62 |
| P_volume | None | 0.30 |
| P_structure | Sweep present | 0.88 |
| P_structure | No sweep | 0.38 |
| P_delta | \|DeltaZ\| > 1.5 | 0.78 |
| P_delta | Weak | 0.40 |
| Re_penalty | Turbulent | ×0.72 |
| Re_penalty | Normal | ×1.00 |

---

## 4. The Five Pillars

### Pillar 1 — Hydraulic Pressure Engine
Detects when volume density is high AND price range is compressed. This is the "spring loading" phase. Without elevated hydraulic pressure, no signal fires.

### Pillar 2 — Energy State Model
Classifies every bar as Compression, Expansion, or Neutral based on the PE/KE ratio. Bars are coloured accordingly. Only compression-state bars can produce signals.

### Pillar 3 — Volume Intelligence Layer
Goes beyond raw volume magnitude. Separates three institutional signatures:

| Signature | What It Means |
|---|---|
| **Absorption** | Market maker taking the other side of retail without moving price. Wide spread imminent. |
| **Aggression** | Directional institutional push. Momentum confirmation. |
| **Exhaustion** | Climax volume — institutions distributing into retail FOMO or accumulating into retail panic. Reversal signal. |

### Pillar 4 — Liquidity Engineering Model
Identifies swing pivot clusters (engineered stop-loss pools) and detects when price sweeps through them and reverses. This is the trigger that converts accumulated energy into a directional trade.

### Pillar 5 — Probabilistic Gate + Execution Engine
All four components feed a Bayesian composite probability. Only when probability ≥ threshold AND risk:reward ≥ minimum does the system produce an entry signal with precise entry, stop-loss, and take-profit levels.

---

## 5. Reading the Chart

### Bar Colours (Energy State)

| Colour | State | Action |
|---|---|---|
| **Bright Green** | Bullish Expansion | Expansion in progress — do not chase; wait for next compression |
| **Bright Red** | Bearish Expansion | Same as above |
| **Amber/Orange** | Compression | Energy is building — watch for sweep signal |
| **Dark Grey** | Neutral/Dead zone | No edge — stand aside |

### Background Colours

| Background | Meaning |
|---|---|
| **Faint Green** | Bullish expansion zone |
| **Faint Red** | Bearish expansion zone |
| **Faint Amber** | Compression/accumulation zone |

### Markers

| Marker | Meaning |
|---|---|
| **✕ (red, above bar)** | Liquidity sweep of a swing HIGH — bearish trap sprung |
| **✕ (green, below bar)** | Liquidity sweep of a swing LOW — bullish trap sprung |
| **● (amber dot)** | Absorption candle — market maker present |
| **◆ (purple diamond)** | Exhaustion candle — climax volume, possible reversal |
| **▲ HELIX (green)** | Long entry signal — full confluence achieved |
| **▼ HELIX (red)** | Short entry signal — full confluence achieved |

### Entry Labels

When a signal fires, three labels appear:
- **TP label** (green) — Take Profit target at minimum specified RR, with probability shown
- **SL label** (red) — Stop Loss level
- **Dashed line** — Entry price reference extending right

---

## 6. The Dashboard Explained

The dashboard (top-right corner) updates on every bar.

| Row | What It Shows | How to Use |
|---|---|---|
| **Market State** | COMPRESSION / EXPANSION ▲▼ / NEUTRAL | Only trade COMPRESSION transitioning to EXPANSION |
| **Hydraulic P** | Smoothed pressure score | Above +1.0 = pressure building; above +2.0 = critical |
| **Energy Ratio** | % of total energy that is PE | Above 60% = loaded, ready to fire |
| **KE z-score** | How far kinetic energy is above its mean | Above threshold = expansion confirmed |
| **Delta z** | Buying vs selling pressure, standardised | Positive = buyers dominate; negative = sellers |
| **Reynolds #** | Market flow regime | LAMINAR = trade; TURBULENT = stand aside |
| **Vol Intent** | Classified volume behaviour | ABSORBING or EXHAUST = best signals |
| **Liq Sweep** | Whether a sweep just occurred | HIGH SWEPT or LOW SWEPT = trap sprung |
| **Probability** | Composite Bayesian score | Green = above threshold; red = below |
| **Signal** | Current signal state | ▲ LONG / ▼ SHORT / NO SIGNAL |

---

## 7. Settings Reference

### Hydraulic Pressure Engine
| Setting | Default | Description |
|---|---|---|
| Pressure Window | 20 | Lookback for all z-score calculations. Shorter = more reactive; longer = more stable. |
| Energy Release Threshold σ | 1.5 | How many standard deviations above mean KE must spike to confirm expansion. Raise to 2.0+ for very selective signals only. |

### Volume Intelligence
| Setting | Default | Description |
|---|---|---|
| Volume Base Period | 14 | Period for volume mean calculation. Should match your typical analysis window. |
| Absorption Volume Mult | 1.2 | Volume must be 1.2× mean to qualify as absorption. Lower = more signals, lower quality. |
| Exhaustion Volume Mult | 2.0 | Volume must be 2× mean to qualify as exhaustion climax. Keep above 1.8. |

### Liquidity Engineering
| Setting | Default | Description |
|---|---|---|
| Swing Pivot Length | 10 | Bars on each side of a pivot. Smaller = more pivots detected. Larger = only major swing points. |
| Sweep Tolerance % | 0.10 | How far past the swing level price must pierce (as % of ATR). Prevents false sweeps on micro-wicks. |

### Probabilistic Gate
| Setting | Default | Description |
|---|---|---|
| Minimum Probability | 0.65 | Composite score required. Raise to 0.75+ for fewer, higher-quality signals. Never go below 0.60. |
| Minimum Risk:Reward | 5.0 | Minimum RR for targets. Default 1:5 ensures asymmetric payoff. Lower only if your win rate is very high. |

### Execution Engine
| Setting | Default | Description |
|---|---|---|
| ATR Length | 14 | ATR period for stop-loss and target calculations. |
| Stop-Loss ATR Multiplier | 1.5 | Stop placed this many ATRs beyond the swept extreme. Increase on volatile instruments. |

### Display
All display toggles are self-explanatory. Turn off unused elements to reduce chart noise. It is recommended to keep:
- Bar colouring: ON
- Liquidity sweeps: ON
- Entry signals: ON
- Dashboard: ON

---

## 8. Entry Checklist

Before taking any HELIX signal, verify all five boxes mentally:

```
☐ 1. Market State = COMPRESSION (amber bars / background)
☐ 2. Liquidity Sweep marker present on this or previous 1-2 bars
☐ 3. Volume Intent = ABSORBING or *EXHAUST (not just NEUTRAL)
☐ 4. Delta z pointing in signal direction (positive for long, negative for short)
☐ 5. Reynolds # = LAMINAR or MIXED (not TURBULENT)
```

If all five are satisfied AND the dashboard shows green probability AND the ▲/▼ shape is present → **enter at the close of the signal bar**.

### Position Sizing
Use a fixed-risk approach:
```
RiskPerTrade  = AccountSize × RiskPercent  (e.g. 1%)
PositionSize  = RiskPerTrade / (Entry - StopLoss)
```
With default 1:5 RR, five losing trades require only one winner to break even. This math is your edge over time.

---

## 9. Trade Examples

### Example A — Bullish HELIX (Long Setup)

**Sequence of events on chart:**
1. Price has been in amber (compression) bars for 6–8 candles — potential energy accumulating
2. A wick briefly breaks below a recent swing low → green ✕ appears (swept low)
3. Candle closes back above the swing low — the trap has closed on short sellers
4. Absorption dot (●) appears — market maker taking the short side of panicked longs exiting
5. Dashboard: Hydraulic P > +1.0, Energy Ratio > 60%, Delta z > 0, Reynolds = LAMINAR
6. ▲ HELIX appears with TP label above and SL label below

**Action:** Enter long at close of signal bar. Stop at SL label. Target at TP label.

### Example B — Bearish HELIX (Short Setup)

**Sequence of events:**
1. Price rallies into amber (compression) zone near a prior swing high
2. Wick spikes above swing high → red ✕ appears (swept high)
3. Candle closes back below the swing high — buyers are trapped
4. Exhaustion diamond (◆) appears — climax buying volume absorbed by smart sellers
5. Dashboard: Hydraulic P elevated, Energy Ratio > 60%, Delta z < 0, Vol Intent = BULL EXHAUST
6. ▼ HELIX appears

**Action:** Enter short at close of signal bar. Stop at SL label. Target at TP label.

---

## 10. Critique of the Original Indicator

The original *Volume Bars and Lines* indicator (`@version=4`) was a creative volume-colouring tool with several structural limitations:

| Issue | Details |
|---|---|
| **No directional volume** | All 10 colour tiers were based purely on volume magnitude. No distinction between buying and selling pressure. High volume on a bearish candle looked identical to high volume on a bullish one. |
| **Broken `go()` function** | The `symb` parameter was accepted but never used — the function always returned values for `syminfo.ticker` regardless of what was passed. A silent logic bug. |
| **`max_lines_count = 10`** | Hard-coded to 10 lines total. Any chart with more than 10 significant pivots would silently drop the oldest lines, creating misleading historical references. |
| **No ATR normalisation** | Volume thresholds (Magnitude/Multiplier) were absolute numbers. A setting calibrated for BTC/USD would produce completely wrong colours on EURUSD or SPX. Every instrument required manual recalibration. |
| **Label + line overlap** | Both a line and a label were drawn at every pivot. On busy charts this created severe visual clutter with overlapping text. |
| **Heikin Ashi wicks misrepresent reality** | Painting Heikin Ashi candles over real price creates smooth visual output but hides the true high/low of each bar, making the wick data unreliable for stop placement. |
| **No edge or signal logic** | The indicator displayed volume intensity beautifully but provided no actionable entry, stop, or probability framework. Interpretation was entirely left to the user. |
| **Lagging pivot detection** | The symmetric pivot detection (`paintLines` function) requires `length` bars on both sides, meaning all levels were printed `length` bars *after* the event. On the default of 4, every level appeared 4 bars late. |
| **Static colour mapping** | The 10-colour spectrum (c0–c9) was fixed. There was no adaptation to changing market volatility or regime changes. |

HELIX resolves all of these issues through z-score normalisation (works on any instrument), directional delta separation, dynamic state detection, and a complete execution framework.

---

## 11. Why HELIX Beats Traditional Volume Indicators

| Indicator | What It Misses | HELIX Solution |
|---|---|---|
| VWAP | Direction of volume, not just price anchor | Delta z-score separates intent |
| OBV | Cumulative — gets polluted over time; no regime filter | Rolling z-scores auto-normalise |
| Volume Profile | Static levels, no energy state, no sweep detection | Hydraulic pressure + sweep triggers |
| Money Flow Index | Oscillator form causes false divergences; no structure | Composite probability, not oscillator |
| Raw Volume Bars | Magnitude only, no context, no signal | Full 5-pillar confluence required |

---

## 12. FAQ

**Q: Why are signals so rare?**
A: By design. HELIX requires four independent conditions to align simultaneously. In a typical session you may see 0–2 signals. Each one has a defined edge. More signals = lower quality. Accept the low frequency as a feature, not a bug.

**Q: What timeframes work best?**
A: HELIX is timeframe-agnostic by design (all calculations use z-scores). Best results on 1H, 4H, and Daily for swing trading. 15M and 5M work for intraday sessions with higher pivot length (reduce to 5–7).

**Q: Can I use it on crypto?**
A: Yes. Crypto's high volatility and 24/7 volume make it ideal. Keep Exhaustion Volume Mult at 2.0+ since volume spikes are more common.

**Q: Why use geometric mean for probability?**
A: Arithmetic mean allows a strong component to mask a weak one. Geometric mean demands every pillar to be independently valid. It is a more conservative and statistically honest aggregation.

**Q: What does "Turbulent" mean on the dashboard?**
A: The Reynolds Number is above 2× its mean — the market is exhibiting chaotic, non-directional behaviour (news events, low-liquidity sessions, erratic order flow). All signals are blocked. Wait for LAMINAR or MIXED.

**Q: How is the stop-loss placed?**
A: At the extreme of the sweep candle (low for longs, high for shorts) minus/plus an ATR buffer. This places the stop *beyond* the liquidity trap. If price returns there after the signal, the thesis is invalidated.

**Q: What if price hits TP before my entry order fills?**
A: Do not chase. HELIX signals are point-in-time. If the bar closes and price has already moved significantly, skip that signal. The next one will come.

---

*HELIX v6 — AYA Research*
*"The market is a hydraulic system. Pressure always finds its outlet."*
