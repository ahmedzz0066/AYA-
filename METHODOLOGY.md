# KAIROMETRIC FIELD THEORY (KFT)
### An Original Smart-Money Methodology Built from First Principles

*"Price does not move because it wants to. It moves because stored institutional
energy discharges through the path of least mass."*

---

## 1. Core Philosophy & Novel Framework

### 1.1 The foundational insight

Every institutional order too large for the visible book must be **worked**: sliced,
delayed, and hidden inside ordinary flow. This working leaves three physical traces
that no amount of camouflage can remove, because they are *conservation-law*
consequences, not patterns:

1. **Energy storage.** Absorbing flow without moving price compresses the return
   stream into unusually *ordered* micro-sequences. Order is measurable as an
   entropy deficit — you cannot absorb size and leave the tape maximally random.
2. **Self-excitation.** Institutional execution algorithms respond to their own
   fills (participation-of-volume, implementation-shortfall schedules). Their
   footprint is therefore *self-exciting*: one abnormal bar raises the conditional
   intensity of the next. Retail flow is (approximately) memoryless; institutional
   flow is a Hawkes process.
3. **Mass deposition.** Wherever inventory actually changes hands, "mass"
   accumulates at that price. Future price behaves like a particle in the
   potential field of that mass: it is attracted to heavy regions (unfinished
   business) and traverses light regions (no one defends them) almost freely.

Classic retail methodologies annotate *shapes* on a chart. KFT instead measures the
**field state** of the market — its entropy, its excitation level, and its mass
distribution — and trades only the moments when all three align: a compressed
(low-entropy) tape, ignited (self-exciting) flow, and a low-mass corridor to travel
through. That triple conjunction is rare, mechanically caused, and — because it is
computed from information theory and point-process statistics rather than visual
patterns — essentially invisible to discretionary chart readers.

### 1.2 The six original constructs

All quantities use OHLCV bars. $O_t,H_t,L_t,C_t,V_t$ are the bar fields,
$\mathrm{TR}_t$ the true range, $A_t$ the Wilder ATR(14), $\varepsilon$ a small
constant.

---

**Construct 1 — Participation Pulse $\rho_t$** *(abnormal participation)*

$$\rho_t = \operatorname{clip}\!\left(\frac{x_t - \bar{x}_{t,120}}{\sigma_{x,t,120}},\,-3,\,+4\right),
\qquad
x_t = \begin{cases}\ln(1+V_t) & \text{volume markets}\\[2pt]
\mathrm{TR}_t / A_t & \text{dealer (FX) markets}\end{cases}$$

A rolling z-score of participation. $\rho_t > 0$ means someone larger than the
ambient crowd is active *right now*.

---

**Construct 2 — Flow Imprint Vector $\varphi_t$, Imprint Field $\Phi_t$, Asymmetry Quotient $\mathrm{AQ}_t$**

Directional efficiency $d_t$ is the fraction of the bar's range the aggressor
side *kept*:

$$d_t = \frac{C_t - O_t}{H_t - L_t + \varepsilon} \in [-1, 1]$$

$$\varphi_t = d_t \cdot \big(1 + \max(\rho_t, 0)\big)$$

$$\Phi_t = \sum_{k \ge 0} \left(\tfrac{\tau-1}{\tau+1}\right)^{k} \varphi_{t-k}
\quad\text{(EMA, span } \tau\text{)},\qquad
\mathrm{AQ}_t = \frac{E^+_t - E^-_t}{E^+_t + E^-_t + \varepsilon} \in [-1,1]$$

where $E^\pm_t$ are EMAs of the positive/negative parts of $\varphi$.
$\mathrm{AQ}$ measures *who has been winning the auction, weighted by size* —
a conviction-weighted order-flow asymmetry, not a price oscillator.

---

**Construct 3 — Entropic Compression Index $\mathrm{ECI}_t$** *(stored energy)*

Embed the log-return stream $r_t$ in patterns of order $m$: each window
$(r_{t-m+1},\dots,r_t)$ maps to its ordinal permutation $\pi$. Over the last $W$
windows, with empirical pattern frequencies $\hat{p}(\pi)$:

$$H_t = -\sum_{\pi \in S_m} \hat{p}(\pi)\ln \hat{p}(\pi),
\qquad
\boxed{\;\mathrm{ECI}_t = 1 - \frac{H_t}{\ln m!}\;}$$

$\mathrm{ECI}\to 0$: maximally random tape (nothing stored).
$\mathrm{ECI}$ high (relative to its own trailing distribution): the return
stream has become *ordered* — the statistical signature of large passive
absorption. Defaults: $m=4$, $W=64$. Because raw levels are biased by window
size, all gates use **rolling quantiles of ECI against itself** (self-adaptive).

---

**Construct 4 — Kinetic Ignition Function $M_t$** *(institutional momentum propagation)*

Institutional momentum obeys a driven decay ODE:

$$\frac{dM}{dt} = -\beta M + J(t)
\quad\xrightarrow{\text{discretize}}\quad
\boxed{\;M_t = e^{-\beta} M_{t-1} + J_t\;}$$

with signed **participation shocks** admitted only above a range threshold $q$:

$$J_t = d_t \cdot \max\!\left(\frac{\mathrm{TR}_t}{A_t} - q,\; 0\right)$$

This is the intensity kernel of a marked Hawkes process: each admitted shock
excites future intensity with exponential decay $\beta$ (half-life
$\ln 2/\beta$ bars). The tradable statistic is the rolling z-score
$z_{M,t}$ over 250 bars. $|z_M|$ spiking = flow has become self-exciting =
an execution schedule is running.

---

**Construct 5 — Gravity Node Lattice** *(the mass field)*

A decaying kernel-density field over log-price. With typical price
$\bar{p}_t = (H_t+L_t+C_t)/3$ and grid $\{g_j\}$:

$$m_j(t) = \rho_m \, m_j(t-1) + w_t \, \mathcal{K}\!\left(\frac{\ln \bar{p}_t - g_j}{h_t}\right),
\qquad w_t = 1 + \max(\rho_t, 0),\quad \rho_m = 0.994$$

$\mathcal{K}$ Gaussian, bandwidth $h_t \propto A_t / C_t$. Derived per bar:

- **Gravity Nodes**: local maxima of $m_j$ above the field mean — shelves where
  inventory actually transferred and remains defended.
- **Attraction** $\mathcal{A}_t = \mathrm{sign}(\text{mass centroid within } \pm 6A_t - \ln C_t)$:
  which side of price holds the dominant unresolved inventory.
- **Vacuum Corridor** $\mathcal{V}_t \in [0,1]$: one minus the ratio of interior
  mass (between price and the next node in the attract direction) to that
  node's flank mass. $\mathcal{V}$ high = thin corridor = fast traversal.

Interpretation (quantum-inspired, implemented classically): the normalized mass
field is a probability amplitude over resting-inventory locations; an ignition
event "collapses" it onto the corridor actually taken.

---

**Construct 6 — Coherence Phases** *(regime tensor)*

Kinetic Efficiency Ratio over window $w$:
$$\mathrm{KER}_t = \frac{|C_t - C_{t-w}|}{\sum_{i=1}^{w} |C_{t-i+1} - C_{t-i}| + \varepsilon}$$

Volatility ratio $\mathrm{VR}_t = A^{(14)}_t / A^{(100)}_t$. Then:

| Phase | Condition | Physics |
|---|---|---|
| **LAMINAR** | $\mathrm{KER} \ge 0.35$ | directional conduction — energy flows |
| **COMPRESSIVE** | $\mathrm{KER} < 0.35$, $\mathrm{ECI} \ge \operatorname{med}_{252}(\mathrm{ECI})$, $\mathrm{VR} \le 1.6$ | energy storage — coiling |
| **TURBULENT** | otherwise (esp. $\mathrm{VR} > 1.6$ with low KER) | dissipation — no edge, stand down |

---

## 2. Mathematical Model

### 2.1 Regime / bias

Bias is **not** taken from price structure. It is the sign coalition of the flow
state: $\mathrm{sign}(z_{M,t})$ (excitation direction), $\mathrm{sign}(\mathrm{AQ}_t)$
(auction winner), and $\mathcal{A}_t\mathcal{V}_t$ (where the vacuum leads).
A tradable bias exists only when the first two agree and the phase is not
TURBULENT.

### 2.2 Ignition Score (the smart-money signal)

$$\boxed{\;\Sigma_t = z_{M,t} + w_a \,\mathrm{AQ}_t + w_g\, \mathcal{A}_t \mathcal{V}_t + w_r\, R_t\, \mathrm{sign}(z_{M,t})\;}$$

with default weights $w_a=1.5$, $w_g=0.5$, $w_r=0.5$, and the **compression
release flag**

$$R_t = \mathbf{1}\!\left[\max_{k\le 5}\mathrm{ECI}_{t-k} \ge Q^{0.8}_{252}(\mathrm{ECI})\right]\cdot
\mathbf{1}\!\left[\frac{\mathrm{TR}_t}{A_t} > q\right]$$

— "the tape was coiled within the last five bars and a real shock just landed."

### 2.3 Probability of continuation

Map the score through a logistic link:

$$P(\text{continuation} \mid \Sigma_t) = \frac{1}{1 + e^{-\gamma(|\Sigma_t| - \theta)}},\qquad \gamma \approx 1.2$$

$\theta$ is the ignition threshold (walk-forward-selected, default $0.9$). The
backtest expectancy per unit of $\Sigma$ above $\theta$ is the empirical estimate
of $\gamma$; the position-management layer only needs the *ordering* this
probability induces, not its absolute calibration.

### 2.4 Dynamic stops and targets

Noise-adaptive initial stop (noisier tape ⇒ wider stop):

$$\delta_t = \kappa_0\,\big(2 - \operatorname{clip}(\mathrm{ECI}_t,0,1)\big)\, A_t,
\qquad \kappa_0 = 1.25
\;\Rightarrow\; \delta_t \in [1.25 A_t,\, 2.5 A_t]$$

$$\text{stop} = P_e - s\,\delta_t,\qquad
\text{target} = P_e + s\,R^\ast\,\delta_t \quad (R^\ast = 3,\; s = \pm 1)$$

After the trade reaches $+1R$ of favorable excursion, a kinetic trail engages:
$\text{stop} \leftarrow \max(\text{stop},\, C_t - 2A_t)$ for longs (mirrored for
shorts).

### 2.5 Position sizing

Fixed-fractional risk with a Kelly-consistency check: with win probability $p$
and payoff ratio $R^\ast$, full Kelly is $f^\ast = p - (1-p)/R^\ast$. The system
risks a constant $f = 0.75\%$ of equity per trade, which is $\ll f^\ast/4$ for
any parameter set that survives walk-forward selection — i.e., deep fractional
Kelly, where the growth penalty is small and the drawdown compression is large.
Size in units: $\text{size} = f\,E / \delta_t$, notional capped at $10\times$
equity.

---

## 3. Trading Rules (systematic, codable)

### 3.1 Timeframe hierarchy

The constructs are scale-free; the reference implementation is daily. For
intraday use, compute the phase tensor and Gravity Lattice on the higher frame
(e.g., H4), and $\Sigma_t$ on the execution frame (e.g., M15), requiring
higher-frame bias agreement. Top-down process:

1. **Field frame** (weekly/daily): Coherence Phase + Gravity Node map.
2. **Ignition frame** (daily/H4): $z_M$, AQ, ECI, $\Sigma$.
3. **Execution frame** (= ignition frame in the reference implementation):
   entries at next bar's open after a signal close.

### 3.2 Entry (long; shorts mirrored)

Enter long at the **next open** when ALL hold on the signal close:

1. Phase is LAMINAR, **or** yesterday was COMPRESSIVE and $R_t = 1$
   (compression→ignition transition);
2. $\Sigma_t \ge \theta$;
3. $\mathrm{AQ}_t > 0.05$ (auction agreement);
4. $z_{M,t} > 0$ (excitation direction agreement);
5. No open position in the instrument (one position per instrument).

### 3.3 Exits

| Exit | Rule |
|---|---|
| Initial stop | $\delta_t$ below entry; gaps fill at the open |
| Target | $+3R$; on ambiguous bars **stop is assumed first** |
| Kinetic trail | after $+1R$ MFE: trail $2A_t$ off the close |
| Time decay | 40 bars without reaching $+0.5R$ ⇒ exit next open |
| Turbulence | phase flips TURBULENT before $+1R$ ⇒ exit next open |
| Ignition flip | $s\cdot\Sigma_t \le -\theta/2$ ⇒ exit next open |

### 3.4 Filters

- **Volatility**: TURBULENT phase blocks entries (this *is* the vol filter — it
  triggers on $\mathrm{VR} > 1.6$ regimes such as macro shocks).
- **News**: for intraday use, suppress entries within ±30 min of tier-1
  releases; on the daily frame the turbulence gate covers event shocks.
- **Correlation**: across a portfolio, cap simultaneous positions whose
  90-day return correlation exceeds 0.65 to two, halving risk on the second.

### 3.5 Risk & portfolio rules

- 0.75% equity risk per trade; max 4 concurrent positions; max 2 in one
  correlation cluster; portfolio heat (sum of open risk) ≤ 2.5%.
- Hard monthly circuit breaker: stop trading for the month at −6% equity.
- Sizing uses current (compounded) equity — drawdowns automatically de-risk.

---

## 4. Implementation

Complete, runnable implementation in this repository:

```
kft/data.py       # Yahoo Finance chart-API loader (cookie+crumb) with CSV cache
kft/concepts.py   # the six constructs (Sections 1–2), fully vectorized/causal
kft/strategy.py   # Ignition Score + entry/exit signal assembly
kft/backtest.py   # conservative event-driven backtester + metrics + benchmarks
kft/validate.py   # full-sample, walk-forward, Monte Carlo, report generation
run.py            # python run.py  → regenerates RESULTS.md
```

`pip install -r requirements.txt && python run.py`

Design guarantees against lookahead: every construct at bar $t$ uses data up to
$t$ only; fills occur at the open of $t+1$; ambiguous stop/target bars resolve
to the stop; costs charged per side.

## 5. Proof in Real Market Conditions

Assets and periods (Yahoo Finance daily): BTC-USD (2014→), EURUSD=X, GBPUSD=X,
^GSPC, ^NDX (2010→) — 11–16 years each. Validation protocol:

1. **Full-sample backtest** with a-priori default parameters (no tuning).
2. **Walk-forward optimization**: only $(\theta, \beta, \tau)$ searched on a
   small 18-point grid; ~4y train / 1y test, rolled annually; stitched equity
   is 100% out-of-sample.
3. **Monte Carlo**: 2000 bootstraps of the realized R-multiple sequence under
   fixed-fractional sizing → tail drawdown and return distributions.
4. **Benchmarks**: buy-and-hold and a 50/200 MA cross, identical cost model.

**All realized numbers live in [`RESULTS.md`](RESULTS.md), generated by
`python run.py` in this repository — nothing in that file is hand-typed.**
Read them with the limitations of Section 6 in mind.

### 5.1 Headline findings (honest summary of the actual run)

- **BTC-USD (2014–2026, 195 trades):** expectancy **+0.39R**, profit factor
  **2.26**, win rate 50.8%, Sharpe **1.03**, max drawdown **−4.4%** at 0.75%
  risk. Buy-and-hold earned far more absolute return (it's BTC) but with an
  −83% drawdown; on return-per-unit-drawdown KFT is ~2× better, and the Monte
  Carlo puts P(DD ≥ 20%) at ~0%.
- **^NDX:** marginally positive (PF 1.08, +0.03R) — the participation signal
  is real but the short side fights a 16-year structural drift.
- **EURUSD, GBPUSD, ^GSPC:** *negative* expectancy (−0.05R to −0.11R). For FX
  this is exactly what Section 6 predicts: Yahoo FX bars carry no volume, so
  the Participation Pulse degrades to a range proxy and the flow constructs
  lose their information content. The framework's edge lives where true
  participation data exists.
- Walk-forward OOS tracks the full-sample sign everywhere (no
  optimistic in-sample-only mirage), and the annual parameter picks are
  stable per asset — evidence the grid is not being data-mined fold to fold.

The correct conclusion is not "trade everything"; it is: **deploy where the
participation signal is physically real (volume-bearing, volatile assets),
and treat volume-less daily FX as out of the instrument universe until tick
data replaces the proxy.**

## 6. Limitations, Curve-Fitting Risk & Forward Plan

- **Daily-bar proxies.** $d_t$ and $\rho_t$ proxy signed order flow; with real
  tick/L2 data the constructs strengthen (signed volume replaces $d_t\cdot w_t$
  directly). Yahoo FX bars are indicative quotes without volume — the
  range-based Participation Pulse fallback is weaker there, and FX results
  should be read accordingly.
- **Selection risk.** Even an 18-point grid re-selected annually can overfit a
  quiet decade; the honest number is the stitched OOS row, not the full-sample
  row. Defaults were fixed *before* seeing results and are reported unchanged.
- **Cost model.** Per-side bps approximate spread+slippage; thin books (BTC
  weekends, FX rollover) can be worse. Halve the position size assumption
  before believing any live projection.
- **Regime dependence.** The edge concentrates in compression→ignition
  transitions; a permanently turbulent market (2022-style chop everywhere)
  produces long flat periods. That is a feature (capital preservation), but it
  tests patience.
- **Forward plan.** (1) 3–6 months of paper execution with the exact code path,
  logging signal-time snapshots of all six constructs; (2) live at half risk
  (0.375%) until 30 trades match paper expectancy within confidence bounds;
  (3) full risk thereafter, with the monthly circuit breaker always armed.

## 7. Psychological & Practical Edge

The methodology's discipline value comes from three properties:

1. **Rarity is enforced by mathematics, not willpower.** The triple conjunction
   (compressed entropy + self-excitation + vacuum) simply does not occur most
   days. The system's default state is *flat*, which removes the overtrading
   failure mode structurally.
2. **Every trade has a falsifiable physical thesis.** "Stored energy is
   discharging toward the nearest heavy node through a thin corridor" is either
   confirmed within ~8 bars (average hold) or the kinetic trail / time decay
   takes you out. There is nothing to argue with.
3. **Risk is a constant, not a feeling.** 0.75% fixed-fractional with a monthly
   breaker means the worst month is a decision made *in advance*.

**Journaling template (one row per trade):**

| Field | Entry |
|---|---|
| Date / instrument / direction | |
| Phase at signal (L/C/T) + KER, VR | |
| $\Sigma$, $z_M$, AQ, ECI percentile, $\mathcal{V}$ | |
| Thesis (one sentence, physics language) | |
| $\delta$ (stop), target, size, % risk | |
| Exit reason (stop/target/trail/time/turbulence/flip) | |
| R realized / MFE / MAE | |
| Deviation from system? (Y = why) | |

**Edge-maintenance rules:** re-run the walk-forward annually, never mid-drawdown;
recalibrate cost assumptions quarterly from your own fills; if 30-trade rolling
expectancy drops below 0 R, cut risk to 0.375% until it recovers above +0.15 R;
review every "Deviation = Y" row weekly — the goal is zero.
