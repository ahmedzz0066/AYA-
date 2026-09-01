# 05 — Three Original Candidate Hypotheses

> **Proof level: 0–1 for all three.** Each is stated formally, with the prediction fixed *before*
> any data is examined, an adversarial review, and explicit kill criteria.
> **No performance claim is made for any of them. None has been tested.**

Each hypothesis derives from the theory rather than from a chart pattern, and each attacks a
different link in the causal chain:

| | Attacks | Data cost | If it fails |
|---|---|---|---|
| **H1 — Asymmetric Resilience Erosion** | Does the invisible pre-displacement state D2 exist? | High (MBO) | D2 is not a state; ALAT reduces to book-imbalance methods |
| **H2 — Impact-Regime Conditioning** | Is $\lambda$ a real regime variable, or just volatility? | Low (MBP-10) | **The Resilience Primacy Hypothesis dies. ALAT dies with it.** |
| **H3 — Hedging Feedback Dose-Response** | Does mandated flow modulate continuation? | Medium (+ options) | G3 is not exploitable; H1/H2 unaffected |

---

# H1 — Asymmetric Resilience Erosion Precedes Directional Displacement

### Causal claim

Displacement occurs when the liquidity supply function degrades on one side (§1.2). Degradation is
observable *before* displacement, as a fall in the rate and quality of replenishment on that side —
**even when aggressive flow is balanced**. The direction of the eventual move is toward the weaker
side, because that is the side where the same flow will produce more displacement.

The explicit conditioning on balanced flow is what makes this a *supply* claim rather than a
restatement of "imbalance predicts direction."

### Formal statement

Let $\Delta\mathrm{RRI}_t = \mathrm{RRI}^{\text{ask}}_t - \mathrm{RRI}^{\text{bid}}_t$ (SV3) and
$\mathrm{CIR}^{\text{asym}}_t$ (SV4). Define the composite erosion asymmetry, standardized on the
trailing window:

$$E_t = \tfrac{1}{2}\left( z\big(-\Delta\mathrm{RRI}_t\big) + z\big(\mathrm{CIR}^{\text{asym}}_t\big) \right)$$

$E_t > 0$: the **bid** side is eroding (replenishing worse, cancelling more) ⇒ predicted
displacement **down**.

**Prediction (fixed before testing):** conditional on balanced contemporaneous flow,

$$\mathbb{E}\big[\,r_{t \to t+h} \;\big|\; |\widetilde{\mathrm{OFI}}_t| < Q_{0.25},\; E_t > Q_{0.85}\,\big] \;<\; 0$$

with the symmetric statement for $E_t < Q_{0.15}$, and — critically — **monotonicity across
quintiles of $E_t$**. A monotone dose-response is required; a result appearing only in the extreme
bucket is treated as noise.

$h$ is measured in **event bars**, tested over a grid $h \in \{5, 10, 20, 50, 100\}$ with the grid
declared in advance and the multiple-testing correction applied across it.

### Falsification conditions — H1 is killed if any of these hold

1. No monotone relationship between $E_t$ quintile and $\mathbb{E}[r_{t\to t+h}]$ out-of-sample.
2. The effect does not survive orthogonalization against **static book imbalance**, $\sigma_t$,
   $s_t$, and time-of-day. *This is the hard one: `RRI` is correlated with depth, and depth
   imbalance already predicts short-horizon direction. H1's entire claim is incremental.*
3. Cross-validated $\Delta$AUC over the book-imbalance baseline $\le 0.005$.
4. The effect disappears with a decision lag of 1 second.
5. Net expectancy after modelled costs $\le 0$ at 1.5× assumed costs.
6. Sign flips across instruments (ES / SPY / BTC perp) or across years without a structural
   explanation stated *in advance*.

### THE DESTROYER — adversarial review

| Attack | Assessment |
|---|---|
| **"This is book imbalance with extra steps."** | The most serious objection. `RRI` is partly a function of depth, and depth imbalance is a known predictor. **Mitigation: the baseline is mandatory, and H1's result is reported only as incremental $\Delta$AUC and incremental net expectancy over it. If the increment is trivial, H1 fails regardless of standalone performance.** |
| **Look-ahead in `RRI`.** | `RRI` needs $\tau$ event-units *after* a depletion event to be computed. If a signal at $t$ uses a depletion event whose $\tau$-window extends past $t$, that is direct leakage. **Mitigation: `RRI` at $t$ uses only events whose full $\tau$-window closed before $t$. This must be asserted in code and unit-tested with a shuffled-future control.** |
| **Reverse causality.** | Replenishment falls *because* price has already started moving, in which case the "prediction" is a lagged echo of a move already underway. **Mitigation: condition on no significant displacement in the immediately preceding window; report the effect separately for quiet-precursor cases only.** |
| **Latency impossibility.** | Requires book reconstruction from MBO within the decision window. **Mitigation: measure computation time; include it in $\delta$; report results across the $\delta$ grid.** |
| **Iceberg contamination.** | Iceberg refills inflate apparent replenishment; venues differ. Biases `RRI` in an unknown direction. **Mitigation: identify reserve refills where the feed permits; on equities, flag as an unresolved measurement bias and weight results accordingly.** |
| **Selection bias in "depletion events."** | The definition of a depletion event ($\phi$ threshold) is a researcher choice. **Mitigation: report the full $\phi$ surface, not the best $\phi$. Require a stable plateau.** |
| **Execution impossibility.** | The signal fires precisely when one side's liquidity is thinning — i.e. when it is hardest to get filled on that side. **This is not a bias, it is a real economic cost, and it may consume the entire edge. It must be in the fill model, not a footnote.** |

### Verdict
**Survives adversarial review as a hypothesis worth testing**, conditional on the incremental test
against book imbalance being treated as the primary result rather than a robustness check.

---

# H2 — The Impact Coefficient Governs Continuation vs. Reversion  ★ *test this first*

### Causal claim

Whether a short-horizon move continues or reverts is not a property of the move. It is a property of
the **liquidity supply regime in which the move occurred**.

- $\hat\lambda$ **rising** ⇒ supply is thinning ⇒ each unit of flow displaces more ⇒ moves extend
  ⇒ **continuation regime**.
- $\hat\lambda$ **falling while flow is high** ⇒ supply is deepening against pressure — genuine
  absorption ⇒ **reversion regime**.

This is the quantitative content of "effort versus result," and it makes a strong, unusual, and very
falsifiable prediction: **the same price pattern has opposite expectancy in the two regimes.** Any
strategy that ignores $\lambda$ state is averaging two opposite-signed populations together — which
would explain the well-known tendency for simple momentum and simple mean-reversion rules to each
work "sometimes."

### Formal statement

Let $z^\lambda_t$ and $\dot\lambda_t$ be as defined in SV2, and let $\rho_t = \mathrm{sign}(r_{t-k \to t})$
be the sign of the recent move. Define the **continuation payoff**:

$$C_{t,h} = \rho_t \cdot r_{t \to t+h}$$

**Prediction (fixed before testing):**

$$\mathbb{E}\big[C_{t,h} \mid \dot\lambda_t > 0\big] \;>\; \mathbb{E}\big[C_{t,h} \mid \dot\lambda_t < 0,\; |\widetilde{\mathrm{OFI}}| > Q_{0.75}\big]$$

and, critically, **the difference must survive orthogonalization of $z^\lambda$ against realized
volatility:**

$$\lambda^{\perp}_t = z^\lambda_t - \big(\hat\beta_0 + \hat\beta_1 z(\sigma_t) + \hat\beta_2 z(s_t) + \hat\beta_3 \text{ToD}_t\big)$$

with $\hat\beta$ estimated **on the exploratory partition only** and then frozen. The primary
reported statistic is the effect of $\lambda^{\perp}$, not of $z^\lambda$.

### Why this is the first test

1. **It is the load-bearing claim.** If $\lambda$ carries no information beyond volatility, the
   Resilience Primacy Hypothesis (§1.2) is false and *the entire framework is unmotivated.* H1 and
   H3 become uninteresting whether or not they work.
2. **It is the cheapest.** MBP-10 + trades. No MBO, no options data, no cross-market alignment.
3. **It has the widest reach.** It re-frames every existing momentum/reversion rule rather than
   proposing a new one, so a positive result is immediately testable against decades of published
   baselines.
4. **A negative result is decisive and cheap** — which is exactly the property a first experiment
   should have.

### Falsification conditions — H2 is killed if any of these hold

1. $\lambda^{\perp}$ shows no relationship to $C_{t,h}$ out-of-sample.
2. The entire effect is captured by $\sigma_t$ alone (i.e. the raw $z^\lambda$ result vanishes after
   orthogonalization). **This is the single most likely outcome and it must be reported as a kill,
   not spun as "λ is a volatility proxy that still works."**
3. Effect present in-sample, absent in the locked holdout.
4. Sign is not stable across at least two of three instruments.
5. Net expectancy $\le 0$ at 1.5× assumed costs.
6. Effect requires $W$ (the regression window) within a narrow band — no stable plateau across
   $W \in \{20,50,100,200,500\}$ event bars.

### THE DESTROYER — adversarial review

| Attack | Assessment |
|---|---|
| **"$\lambda$ is just volatility."** | **The central risk.** $\hat\lambda$ and $\sigma$ are mechanically linked. Volatility-conditional momentum/reversion is already documented in the literature, so a raw-$z^\lambda$ result would be a rediscovery, not a discovery. **Mitigation: the orthogonalized $\lambda^{\perp}$ is the only primary statistic. The raw result is reported but explicitly labelled non-novel.** |
| **Regression-slope instability.** | $\hat\lambda$ from a rolling OLS on fat-tailed, heteroskedastic data is noisy, and a single outlier bar dominates the slope. **Mitigation: robust regression (Theil–Sen or Huber) as a pre-declared alternative; report both; a result that exists only under OLS is an outlier artifact.** |
| **Denominator instability.** | `PRE` divides by $\widetilde{\mathrm{OFI}}$, which crosses zero, producing explosive values. **Mitigation: `PRE` is used only in bars where $|\widetilde{\mathrm{OFI}}|$ exceeds a floor; the floor is a declared robustness parameter with a reported surface.** |
| **Bid-ask bounce.** | $C_{t,h}$ over short $h$ on mid-prices is contaminated by microstructure noise, which is mechanically negatively autocorrelated and can manufacture a "reversion" result from nothing. **Mitigation: use trade-weighted or micro-price returns; report results across $h$; require the effect at $h$ large enough that bounce is immaterial.** |
| **Look-ahead via $\hat\lambda_t$.** | Using the contemporaneous $\hat\lambda_t$ to evaluate bar $t$ embeds the current move in its own predictor. **Mitigation: strictly $\hat\lambda_{t-1}$; verified by a shuffled-future unit test.** |
| **Multiple testing.** | Grid over $W$, $k$, $h$, quantile cutoffs. Easily hundreds of combinations. **Mitigation: full grid declared in the pre-registration; Hansen SPA / White's Reality Check applied across the whole grid; Deflated Sharpe reported.** |
| **Time-of-day confound.** | $\hat\lambda$ has a strong deterministic intraday shape, and so does return autocorrelation. Both could be driven by the clock alone. **Mitigation: time-of-day is in the orthogonalization; additionally report within-session-bucket results.** |

### Verdict
**The strongest of the three, because a negative result is as informative as a positive one and both
are cheap to obtain.** This is the correct first experiment.

---

# H3 — Hedging Feedback Modulates Displacement Persistence, With Dose-Response in Strike Distance

### Causal claim

A material share of intraday flow is mandated and price-contingent (`A5`, `CL-2026-04`). Dealers
hedging short gamma must trade *with* the move; hedging long gamma they trade *against* it.
Therefore the probability that a displacement is accepted (D5a) rather than rejected (D5b) should
depend on the local hedging configuration.

**The distinctive and hard-to-fake prediction is not the level effect — it is the dose-response:**
the modulation should be **strongest near large-open-interest strikes and decay monotonically with
volatility-scaled distance from them**, and should **strengthen into expiry** as gamma concentrates.

A day-level classification ("today is a long-gamma day") can be produced by chance or by a
volatility proxy. **A monotone decay in strike distance cannot.** That is why H3 is built on
$d^{\text{strike}}$ rather than on $\widehat{G}$.

### Formal statement

For each displacement event $j$ (defined causally from SV2: $\mathrm{PRE}_j > Q_{0.9}$ with
$|\Delta m_j| > \kappa\sigma$), let $Y_j = \mathbb{1}[\text{acceptance (D5a) within } \tau]$, where
acceptance is determined by `RRI` recovery at the new level and `AAS` turning positive — **and is
labelled by a causal classifier, not by looking at the subsequent price path.**

$$\mathrm{logit}\, P(Y_j = 1) = \beta_0 + \beta_1 \widehat{G}_j + \beta_2 d^{\text{strike}}_j + \beta_3 \big(\widehat{G}_j \times d^{\text{strike}}_j\big) + \beta_4 \Theta_j + \gamma' X_j$$

with controls $X_j$ containing $\sigma$, `LSI`, session dummies, and event-size.

**Prediction (fixed before testing):** $\beta_3 \ne 0$ with the sign implying that the $\widehat{G}$
effect **attenuates as distance from the concentrated strike grows**; and $\beta_1$ has the sign
implying long dealer gamma reduces acceptance probability (displacement damped).

### Falsification conditions — H3 is killed if any of these hold

1. $\beta_3$ not distinguishable from zero — **no dose-response, no mechanism.** This is the primary
   test and it is not negotiable.
2. Results reverse under an alternative OI sign model (SV7). Then the finding is about the sign
   model, not the market.
3. $\sigma$ and `LSI` controls absorb the effect entirely.
4. The effect exists only on monthly/quarterly OPEX dates — a handful of observations per year,
   which is a sample-size illusion, not a finding.
5. No effect in a non-options-overlaid control instrument where the mechanism should be absent.
6. Net expectancy $\le 0$ at 1.5× costs.

### THE DESTROYER — adversarial review

| Attack | Assessment |
|---|---|
| **"Dealer positioning is unknowable."** | **Correct, and it is the deepest problem with H3.** OI does not disclose who is long. Every GEX figure in public circulation embeds an unvalidated sign heuristic. **Mitigation: build H3's primary test on $d^{\text{strike}}$ and $\Theta$, both directly observed; treat $\widehat{G}$ as a secondary, uncertainty-banded variable; require survival under multiple sign models.** |
| **Reverse causality.** | Large OI accumulates at strikes the market was already likely to gravitate toward (round numbers, prior settlements, high-attention levels). Pinning may cause OI rather than OI causing pinning. **Mitigation: control for round-number proximity and for prior-day levels explicitly; test whether OI concentration at *non*-round strikes produces the same effect. If only round strikes show it, the mechanism is attention, not gamma.** |
| **Look-ahead via open interest.** | OI is published after the session. Same-day OI is unambiguous leakage. **Mitigation: prior-session OI only, with the publication timestamp verified, not assumed.** |
| **Event-date clustering.** | OPEX and macro dates dominate the tails, so a handful of days can drive everything. **Mitigation: report with and without event dates; require the effect to survive their exclusion.** |
| **Circularity in the acceptance label.** | If acceptance is labelled using future price, the regression predicts the future with the future. **Mitigation: acceptance is defined by the causal `RRI`/`AAS` classifier evaluated over a fixed forward window that is disjoint from the prediction window, and the classifier is validated separately.** |
| **Multiple testing across the strike grid.** | Many strikes, many distances, many expiries. **Mitigation: dose-response is fitted as a single continuous interaction term, not as a search over strike buckets. That is precisely why the hypothesis is framed as a coefficient rather than a screen.** |
| **Execution.** | Setups derived from H3 fire near strikes with concentrated OI — often exactly where liquidity behaves unusually. **Mitigation: cost model must use realized spreads conditional on strike proximity, not average spreads.** |

### Verdict
**Weakest of the three on data quality, strongest on economic distinctiveness.** The mechanism is
the most genuinely novel feature of the 2026 market and has no Wyckoff analogue. But it depends on
an unobservable, and it should be tested **third** — after H2 establishes whether the framework's
foundation holds at all, and after H1 establishes whether liquidity-supply variables carry
information.

---

## Cross-hypothesis discipline

- The three hypotheses share state variables. **A shared bug is a shared false positive.** Every
  variable gets a unit test with a shuffled-future control before any hypothesis is run.
- If H2 fails, **H1 and H3 are not "still worth trying."** They are reframed: without RPH, ALAT has
  no theoretical claim and any surviving effect is an unexplained empirical regularity that must be
  justified independently. Say so plainly if it happens.
- **No hypothesis may be modified after seeing test-set results.** Modification is permitted only
  after exploratory-partition results, and the modified version is a *new* hypothesis requiring a
  fresh pre-registration and a fresh holdout.
