# KÖNIG

### Kinetic Coherence — a first-principles replacement for Smart Money Concepts

> One number. Two rules. Three marks on the chart.

---

## a. Name

**KÖNIG** — after *König's decomposition theorem*, which states that the total kinetic
energy of a system of particles separates exactly into the kinetic energy of its centre of
mass plus the kinetic energy of the particles relative to that centre:

$$K_{\text{total}} \;=\; \underbrace{K_{\text{bulk}}}_{\text{coherent}} \;+\; \underbrace{K_{\text{internal}}}_{\text{thermal}}$$

That single identity is the entire system. The state variable is called **coherence**, written
$\mathcal{C}$.

---

## b. Philosophy

A market is a medium, and a price series is the record of momentum transferred through it.
Every transaction moves mass (volume) through a displacement (price change) in a unit of time
— nothing else is observable, and nothing else is needed. Over any window of bars, the energy
injected into the medium splits, by König's theorem, into exactly two parts: **bulk flow**, the
component in which all the mass moves the same way, and **thermal agitation**, the component in
which mass moves against itself and cancels. An efficient market is pure thermal noise: mass
churns, energy is injected, and net displacement stays at the diffusive scale $\sqrt{t}$. A
market with a real imbalance is one where the bulk term dominates — the medium is flowing, not
merely vibrating. So there is only one question worth asking of a chart: *what fraction of the
energy in this window is coherent?* The answer is a dimensionless number with a known
distribution under the random-walk null, which means it is a **measurement with a p-value**
rather than a pattern with a story. Momentum, once coherent, persists until dissipated
(Newton's first law); the trade is simply to ride a measured flow until it re-thermalises, with
risk sized to the noise the medium can produce by chance alone.

There are no zones, no levels, no narrative about who is trapped. There is a medium, and it is
either flowing or it is not.

---

## c. Governing equation

Let $\delta_i$ be the displacement of bar $i$ and $m_i$ its mass:

$$\delta_i = p_i - p_{i-1}, \qquad m_i = V_i$$

Over the trailing window of $n$ bars, with normalised masses $w_i = m_i / \sum m_j$:

| quantity | definition | meaning |
|---|---|---|
| $\bar v$ | $\sum_i w_i \delta_i$ | bulk (centre-of-mass) velocity |
| $u$ | $\sqrt{\sum_i w_i \delta_i^{\,2}}$ | total RMS speed — the thermal speed |
| $n_{\text{eff}}$ | $\left(\sum_i m_i\right)^2 / \sum_i m_i^2$ | effective sample size (Kish) |

**The coherence:**

$$\boxed{\;\;\mathcal{C} \;=\; \sqrt{n_{\text{eff}}}\;\frac{\bar v}{u} \;=\; \frac{\sum_i m_i \delta_i}{\sqrt{\dfrac{\left(\sum_i m_i^2\right)\left(\sum_i m_i \delta_i^{\,2}\right)}{\sum_i m_i}}}\;\;}$$

This one scalar admits three exact readings, which is why the system needs nothing else:

**1. Thermodynamic.** The bulk energy fraction, i.e. König's theorem as a ratio:

$$\Phi \;=\; \frac{K_{\text{bulk}}}{K_{\text{total}}} \;=\; \frac{\mathcal{C}^2}{n_{\text{eff}}} \;=\; \left(\frac{\bar v}{u}\right)^{\!2} \;\in\; [0,\,1]$$

bounded by Cauchy–Schwarz. $\Phi = 1$ is perfectly laminar flow (every bar identical);
$\Phi = 0$ is perfect cancellation. Note $\bar v / u$ is a **Mach number** — bulk speed over
the medium's own agitation speed. A coherent market is a supersonic one.

**2. Geometric.** Writing $D = n_{\text{eff}}\bar v$ for the coherent displacement and
$\ell = \sqrt{n_{\text{eff}}}\, u$ for the diffusive scale:

$$\mathcal{C} \;=\; \frac{D}{\ell} \qquad\Longleftrightarrow\qquad D = \mathcal{C}\,\ell$$

**Coherence is displacement measured in units of diffusion.** In the unit-mass limit this
collapses to a one-line closed form — net displacement over the $L^2$ norm of the steps:

$$\mathcal{C} \;=\; \frac{\sum_i \delta_i}{\sqrt{\sum_i \delta_i^{\,2}}} \;=\; \sqrt{n}\,\cos\theta$$

where $\theta$ is the angle in $\mathbb{R}^n$ between the step vector and the pure-drift
diagonal $(1,1,\dots,1)$. Coherence is literally the alignment of the price path with drift.

**3. Statistical.** Under the null hypothesis that price is a martingale with zero-mean
increments,

$$\mathbb{E}[\Phi] = \frac{1}{n_{\text{eff}}}, \qquad n_{\text{eff}}\Phi \sim \chi^2_1, \qquad \mathcal{C} \sim \mathcal{N}(0,1)$$

**The threshold is a p-value.** $\mathcal{C}$ is a *self-normalised sum* — the denominator is
built from the same sample as the numerator — so it needs no volatility estimate, no
standardisation period, and no assumption of finite variance. It is scale-free by construction:
multiply the instrument's price by 1000 and $\mathcal{C}$ is unchanged.

### Market state

The entire market condition is one number in one of three bands:

| $\lvert\mathcal{C}\rvert$ | state | physics | action |
|---|---|---|---|
| $< 1$ | **Thermal** | diffusive; energy cancels | none |
| $1 \to \kappa$ | **Drift** | bulk flow present, not significant | none |
| $\ge \kappa$ | **Coherent** | flow dominates agitation | trade |

Default $\kappa = 2.58$.

### Verified properties

Monte Carlo, 400 000 windows per case, $n = 20$ ([`verify/`](verify/)):

| null process | mean $\mathcal{C}$ | sd $\mathcal{C}$ | $P(\lvert\mathcal{C}\rvert > 2.58)$ |
|---|---|---|---|
| Gaussian random walk | −0.001 | 1.001 | 0.0063 |
| Student-$t(3)$ walk (infinite kurtosis) | −0.002 | 0.999 | 0.0039 |
| GARCH-type volatility clustering | 0.002 | 1.003 | 0.0065 |
| price rescaled ×1000 | −0.000 | 0.999 | 0.0061 |

The null survives fat tails and volatility clustering — the two properties that break almost
every normalised indicator — because self-normalisation cancels the scale of the increments
whatever it is. Finite-$n$ quantiles of $\lvert\mathcal{C}\rvert$ are slightly *tighter* than
asymptotic normal ($q_{99} = 2.45$ at $n{=}20$), so $\kappa = 2.58$ is mildly conservative:
about **0.6 % of random windows** are flagged, not 1 %.

Power at $n = 20$, $\kappa = 2.58$, for a true drift of $\mu$ per bar in units of $\sigma$:

| $\mu/\sigma$ | 0.0 | 0.2 | 0.3 | 0.5 | 0.75 | 1.0 |
|---|---|---|---|---|---|---|
| flagged | 0.003 | 0.026 | 0.063 | 0.238 | 0.612 | 0.900 |

It is a deliberately rare, high-specificity detector. Expect few signals.

---

## d. Detection algorithm

Causal and non-repainting by construction. Every quantity at bar $t$ is a function of closed
bars $\le t$ only; once bar $t$ closes, $\mathcal{C}_t$ is immutable forever.

**Per closed bar $t$:**

1. $\delta_t = \text{close}_t - \text{close}_{t-1}$; $\;m_t = \text{volume}_t$ (if volume is
   absent or synthetic, set $m_t = 1$ — the system degrades gracefully to the unit-mass closed
   form).
2. Update four rolling sums over the last $n$ bars, each $O(1)$:
   $$W=\textstyle\sum m,\quad W_2=\sum m^2,\quad S=\sum m\delta,\quad Q=\sum m\delta^2$$
3. $n_{\text{eff}} = W^2/W_2$, $\;\bar v = S/W$, $\;u = \sqrt{Q/W}$.
4. $\mathcal{C}_t = \sqrt{n_{\text{eff}}}\;\bar v / u$, and the risk unit
   $\ell_t = \sqrt{n_{\text{eff}}}\;u$.
5. **Ignition** if $\lvert\mathcal{C}_t\rvert \ge \kappa$ **and** $\lvert\mathcal{C}_{t-1}\rvert < \kappa$
   — the transition into coherence, not its persistence. A sustained flow therefore fires once,
   not on every bar. It *can* re-fire if $\mathcal{C}$ dips under $\kappa$ and re-crosses, which
   in practice clusters two or three ignitions inside one strong move; holding a single position
   at a time absorbs this, and it is a position-management choice rather than a rule of the
   system.
6. On ignition, freeze $\ell_t$ and $\mathcal{C}_t$. They do not update for the life of the trade.

Total state: four accumulators. Lookback: $n = 20$ bars (default). No smoothing, no nested
timeframes, no request for higher-timeframe data, hence no lookahead surface at all.

**Why it cannot repaint:** step 4 uses no future bars; step 5 compares two already-closed
values; step 6 freezes the geometry at signal time. Evaluate only on `barstate.isconfirmed` and
the live bar cannot flicker either.

---

## e. Rules

Let $\sigma = \operatorname{sign}(\mathcal{C})$ at ignition, and let $\ell$ be the frozen risk
unit.

**Entry — 2 rules.**
1. **Ignition:** $\lvert\mathcal{C}\rvert$ crosses $\kappa = 2.58$ from below on a closed bar.
   Direction is $\sigma$.
2. **Alignment:** the ignition bar itself flows with the bulk — $\operatorname{sign}(\delta_t) = \sigma$.

Fill at the next bar's open.

**Stop — 1 rule.** $\;$ Stop $= \text{entry} - \sigma\,\ell$.

*One diffusive standard deviation against the position.* $\ell$ is exactly the displacement a
random walk produces over this window by chance; if the flow cannot withstand a single move of
the size noise makes for free, it was never coherent. Nothing is chosen here — $\ell$ is
measured.

**Target — 1 rule.** $\;$ Target $= \text{entry} + \sigma\,\mathcal{C}\,\ell$.

*Inertial projection.* Since $D = \mathcal{C}\ell$, the target is one more window-displacement:
conservation of momentum over an equal interval. The flow travels as far again as it just
travelled.

### The closure

Risk is $\ell$ and reward is $\mathcal{C}\ell$, so

$$\text{R:R} \;=\; \mathcal{C}, \qquad \text{breakeven win rate} \;=\; \frac{1}{1+\mathcal{C}}$$

**The one number that authorises the trade also sets its payoff.** At the $\kappa = 2.58$
threshold the geometry is 2.58 : 1 and needs a 28 % hit rate to break even; a stronger flow
automatically buys a longer target off the same risk. Position sizing is the only discretion
left in the system, and it is not part of the system.

**Chart — 3 elements.** One arrow at the ignition bar; one stop ray; one target ray. Nothing
else — no zones, no boxes, no labels, no panel. (If you prefer to see the state, plotting
$\mathcal{C}$ with a line at $\pm\kappa$ *replaces* the arrow; still three.)

Reading a setup: *arrow up, two lines.* Under two seconds.

---

## f. Why this is better

**Against SMC, on scientific grounds.**

- **It has a null hypothesis.** Order blocks, fair-value gaps, BOS/CHoCH, sweeps, inducement,
  premium/discount — none of them define what a chart *without* the phenomenon looks like, so
  none of them can be wrong. $\mathcal{C}$ states exactly how often randomness produces what
  you are looking at: 0.6 % of windows. A claim that can fail is worth more than a vocabulary
  that cannot.
- **It is derived, not observed.** Every constant comes from an identity — the bound
  $\Phi \le 1$ from Cauchy–Schwarz, the null $\mathbb{E}[\Phi] = 1/n_{\text{eff}}$ from the
  martingale assumption, $n_{\text{eff}}$ from Kish, the split itself from König. The only free
  parameters are the window $n$ and the significance $\kappa$, and $\kappa$ is a p-value, not a
  setting to optimise.
- **It is dimensionless.** Same thresholds on 1-minute crypto and weekly equities, on a \$3
  stock and a \$70 000 index, with no normalisation, no ATR scaling, no per-market presets. A
  ratio of energies has no units to tune.
- **It is robust where indicators break.** Self-normalisation holds the null at
  $\mathcal{N}(0,1)$ under infinite-kurtosis increments and under volatility clustering
  (verified above). Anything that divides by a *separately estimated* volatility fails both.
- **Non-repainting is structural, not a setting.** There is no HTF call, no centred smoothing,
  no "confirmed break" that reinterprets old bars. SMC labelling is retrospective by nature: a
  swing becomes structure only after the move that validates it, which is why SMC backtests
  flatter and SMC live results disappoint.
- **Volume enters as mass, not as an opinion.** No "high volume node" heuristic — volume is the
  weight in a weighted mean, which is what mass is.

**Against SMC, on practical grounds.** SMC asks you to identify swing structure, mark blocks,
find imbalance, check the sweep, confirm displacement, check HTF bias, grade premium/discount,
then judge. Perhaps twenty discretionary decisions, each a place where two competent traders
disagree — which is why SMC does not replicate between people. KÖNIG asks: *is the arrow there?*
Four rules, zero discretion, one glyph and two rays, identical for every trader and every
market. It is fully specified in about twenty lines of code and can be verified by hand on a
calculator.

**What is honestly unproven.** The measurement is verified; the *edge* is a hypothesis. That
coherent flow persists rather than reverts — momentum continuation on the scale of one window —
is an empirical claim about markets that I have tested here only against synthetic nulls, not
against real price history. Backtest it per market before risking capital, and measure two
things: realised hit rate against the $1/(1+\mathcal{C})$ breakeven, and whether continuation or
reversion follows ignition on your instrument. If your market mean-reverts after coherence, the
same measurement inverts cleanly — trade $-\sigma$ — and the system does not otherwise change,
which is itself a point in its favour. Also note that fills at the next open in thin markets,
and the correlation between volume and $\lvert\delta\rvert$ in real data (absent in the
synthetic mass test above), will move the effective false-positive rate somewhat from 0.6 %.

---

## g. Pine Script skeleton

Core logic only — see [`konig.pine`](konig.pine).

```pinescript
//@version=6
indicator("KÖNIG — Kinetic Coherence", overlay = true)

n     = input.int(20,     "Window n",     minval = 5)
kappa = input.float(2.58, "Ignition κ",   minval = 1.0, step = 0.01)

// ---- observables: displacement and mass -----------------------------------
d = close - close[1]                       // δ
m = volume > 0 ? volume : 1.0              // mass; degrades to unit mass

// ---- four rolling accumulators, O(1) each ---------------------------------
W  = math.sum(m,       n)                  // Σ m
W2 = math.sum(m * m,   n)                  // Σ m²
S  = math.sum(m * d,   n)                  // Σ mδ    bulk momentum
Q  = math.sum(m*d*d,   n)                  // Σ mδ²   total kinetic energy

// ---- state ---------------------------------------------------------------
neff = W * W / W2                          // effective sample size (Kish)
vbar = S / W                               // bulk velocity
u    = math.sqrt(Q / W)                    // thermal speed
C    = u > 0 ? math.sqrt(neff) * vbar / u : 0.0   // coherence ~ N(0,1)
phi  = C * C / neff                        // bulk energy fraction ∈ [0,1]
ell  = math.sqrt(neff) * u                 // diffusive scale = risk unit

// ---- rules ---------------------------------------------------------------
ignite = math.abs(C) >= kappa and math.abs(C[1]) < kappa    // 1: ignition
align  = math.sign(d) == math.sign(C)                       // 2: alignment
long   = ignite and align and C > 0
short  = ignite and align and C < 0

// ---- geometry, frozen at ignition ----------------------------------------
var int   dir    = 0
var float entry  = na
var float stop   = na
var float target = na

if (long or short) and barstate.isconfirmed
    dir    := long ? 1 : -1
    entry  := close                        // live: fill at next open
    stop   := entry - dir * ell            // 1 diffusive σ
    target := entry + dir * C * ell        // inertial projection; R:R = |C|
```

---

## Reference card

$$\mathcal{C} = \sqrt{n_{\text{eff}}}\,\frac{\bar v}{u} = \frac{D}{\ell}, \qquad \Phi = \frac{\mathcal{C}^2}{n_{\text{eff}}}$$

| | |
|---|---|
| **Enter** | $\lvert\mathcal{C}\rvert$ crosses 2.58, bar closes with the flow |
| **Stop** | $1\,\ell$ against |
| **Target** | $\mathcal{C}\,\ell$ with |
| **R:R** | $\mathcal{C}$ |
| **Chart** | arrow, stop ray, target ray |
