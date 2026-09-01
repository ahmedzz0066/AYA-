# 07 — Experiment Protocol, False-Positive Catalogue, and Kill Criteria

> This document is written **before** any data is examined, and it is binding. Its purpose is to
> remove the researcher's discretion at exactly the points where discretion produces false
> discoveries.

---

# Part A — Backtest Protocol

## A.1 Data partitioning

| Partition | Share | Use | Rule |
|---|---|---|---|
| **Exploratory** | Oldest ~40% | Feature engineering, distribution inspection, parameter surface mapping, orthogonalization coefficient fitting, HMM regime fitting | Look at this as much as you like |
| **Validation** | Next ~30% | Walk-forward evaluation of a *pre-registered* specification | Limited passes; each pass logged in the pre-registration record |
| **Locked holdout** | Most recent ~30% | Final evaluation | **Touched once, ever, per hypothesis.** A second touch converts it into validation data permanently and it must be relabelled as such in the results. |

Chronological, never random. Random splits across a time series leak the future into the past
through autocorrelation.

## A.2 Sampling: event bars

Primary: **dollar bars** (bars close after a fixed notional traded), sized so that the median bar
count per session is comparable across the sample period. Alternatives tested for robustness: volume
bars, tick bars, imbalance bars, and — as the honest control — **fixed 1-minute time bars**.

**If time bars perform equivalently, use time bars.** They are simpler and they do not carry the
leakage risk of A.3. Complexity must earn its place (R6).

## A.3 The bar-boundary leakage rule

A dollar bar's closing *time* is determined by volume that arrives after the bar opens. Naïvely
computing a feature "at bar close" and acting "at bar close" therefore uses knowledge of when future
volume arrived.

**Binding rule:** the decision point is a **message index**, not a bar boundary. Features are
computed from all messages up to message $n$; the order is submitted at $n$ with decision lag
$\delta$; the fill is simulated against messages at or after $n + \delta$. Bars are used for
*aggregation and labelling*, never to define the moment of action.

**Verification:** a shuffled-future unit test. Randomly permute all data after each decision point
and confirm that feature values are bit-identical. Any feature that changes has a look-ahead bug.
**Every feature must pass this test before any hypothesis is run.** This single test catches the
majority of leakage bugs and it is cheap.

## A.4 Labelling: triple barrier

Each decision point is labelled by which of three barriers is hit first:
- **Profit barrier:** $+\kappa_p \sigma_t$ (volatility-scaled, never a fixed tick count — `CL-2026-01`)
- **Loss barrier:** $-\kappa_l \sigma_t$
- **Time barrier:** $h$ event bars

The time barrier is a **real exit**, not an accounting convenience: it is the trade's answer to
"WHEN must the expected move occur?" (§1.6). If the hypothesized move has not occurred within the
horizon over which the liquidity state was hypothesized to persist, the hypothesis for that trade
was wrong, and holding on is hoping.

## A.5 Overlapping-label correction

Trades sampled densely have overlapping outcome windows, which grossly inflates effective sample
size and t-statistics. Apply:
- **Purging:** remove training observations whose label window overlaps the test window.
- **Embargo:** additionally drop a buffer of observations after each test window.
- **Sample-weighting by uniqueness:** weight each observation by the inverse of the number of
  concurrent labels touching the same period.

Without these, a t-statistic computed on overlapping intraday labels is not merely optimistic — it
is uninterpretable.

## A.6 Walk-forward design

Anchored expanding-window walk-forward on the validation partition. Each fold: fit only what the
pre-registration permits to be fitted (orthogonalization coefficients, HMM parameters, `AAS`
weights), then evaluate out-of-sample on the next fold. **Report every fold**, not the aggregate.
A strategy whose profit comes from two of twelve folds is a strategy with two observations.

## A.7 Fill and cost model — conservative by construction

### Aggressive (marketable) orders
- Fill at the **far touch as of $n+\delta$**, walking the book for size.
- Add **fees**: exchange + clearing + regulatory, from the *historical* schedule.
- Add **modelled slippage**: for size exceeding top-of-book depth, walk the reconstructed book.
- Add **impact**: a square-root participation model (`A4`), with the coefficient set from the
  literature's functional form and treated as an unknown scaled by a robustness multiplier — never
  fitted to make results look better.

### Passive (resting) orders — the assumption that quietly destroys most intraday backtests
The optimistic assumption ("my limit order filled because price touched my level") is wrong roughly
whenever it matters most, because at the moments your signal fires, the queue ahead of you is
exactly what did *not* get filled.

**Binding rule:** a passive order is assumed filled only if price trades **through** the level by at
least one tick, *or* if queue position can be explicitly tracked from MBO and the queue ahead of the
order is demonstrably exhausted. Where MBO is unavailable, the trade-through rule applies with no
exceptions.

**Additional requirement:** every result is reported at **three cost levels — 1.0×, 1.5×, and 2.0×
assumed costs.** A result that survives only at 1.0× is reported as failed. This is not conservatism
theatre; live costs are systematically worse than modelled costs, and the direction of that error is
known in advance.

## A.8 The edge equation

Every candidate trade family must satisfy, **net**:

$$\mathbb{E}[\text{PnL}] = P_{\text{win}} \bar{W} - P_{\text{loss}} \bar{L} - c_{\text{comm}} - c_{\text{spread}} - c_{\text{slip}} - c_{\text{impact}} \;>\; 0$$

with the cost terms computed per trade from the model above, not applied as an average haircut.

**Reported alongside, always:** profit factor; expectancy per trade in $R$ and in currency; Sharpe;
Sortino; max drawdown (depth and duration); MAE and MFE distributions; win/loss ratio; risk of ruin
at the intended sizing; tail loss (CVaR at 95% and 99%); return skew; time-in-trade distribution;
return per unit of exposure; and **turnover**, because turnover determines how quickly the cost model
error compounds.

**Win rate is not a headline metric and is never reported alone.**

## A.9 Mandatory baselines

The sophisticated method must demonstrate **incremental** information. Every hypothesis is compared
against all of:

| Baseline | Why it is included |
|---|---|
| **Matched random entry** | Same trade count, same holding-time distribution, same session distribution, same side distribution. *This is the correct null* — an unmatched random benchmark is a strawman. |
| **Static book imbalance** | The known short-horizon predictor. **H1's primary comparison.** |
| **Realized-volatility conditioning alone** | **H2's primary comparison.** |
| **Time-of-day dummies alone** | Tests whether "regime" is just a clock (`A6`). |
| Opening-range breakout | Standard intraday benchmark |
| VWAP reversion | Standard intraday benchmark |
| Simple momentum / simple mean reversion | The two populations H2 claims to separate |
| Buy-and-hold | Context only; not a fair comparison for an intraday method, and reported as such |

**Reporting rule:** the headline figure is the **incremental** result over the relevant primary
baseline, not the standalone result. A method that makes money but adds nothing over book imbalance
has discovered book imbalance.

## A.10 Statistical standards

| Requirement | Method |
|---|---|
| Multiple testing | White's Reality Check / Hansen's SPA across the **entire** declared parameter grid — not the reported subset |
| Overfitting probability | Probability of Backtest Overfitting (combinatorially symmetric CV) |
| Sharpe inflation | **Deflated Sharpe Ratio**, with the true number of trials as declared in the pre-registration |
| Path dependence | Block bootstrap (block length ≥ label horizon) and Monte Carlo trade-order shuffling |
| Parameter stability | Full parameter-surface heatmaps. **Require a plateau, not a peak.** |
| Entry perturbation | Randomly jitter entry timing by ±$k$ event bars; the effect must degrade gracefully, not collapse |
| Cost sensitivity | 1.0× / 1.5× / 2.0× |
| Latency sensitivity | $\delta \in \{0.1, 0.5, 1, 5\}$ seconds |
| Regime partition | Results reported separately by volatility regime, session, and year |

## A.11 Pre-registration

Before the validation partition is touched, a completed `preregistration/TEMPLATE.md` is **committed
to this repository**. The git commit hash and timestamp are the proof of precedence — this is why
the research log lives in version control rather than in a notebook.

The pre-registration states: the hypothesis, the exact feature definitions, the exact parameter grid
(and therefore the true trial count for the Deflated Sharpe calculation), the primary statistic, the
baselines, the kill criteria, and the predicted direction of effect. **Anything not in the
pre-registration is exploratory and must be reported as exploratory**, regardless of how good it
looks.

---

# Part B — How Each Experiment Could Produce a False Positive

Catalogued so that each has a specific, pre-declared control. This list is the most valuable part of
this document, because every item on it has produced a published false discovery somewhere.

### FP-1 — Bar-boundary leakage
Event-bar close times depend on future volume. **Control:** A.3 message-index decision rule +
shuffled-future unit test.

### FP-2 — Feature-window leakage
`RRI` needs a forward window to compute; using an incomplete window at $t$ leaks. **Control:** only
depletion events whose full $\tau$-window closed before $t$; unit-tested.

### FP-3 — Same-day open interest
OI is published post-session. **Control:** prior-session OI only, with the publication timestamp
verified against the vendor spec, not assumed.

### FP-4 — Overlapping labels inflating significance
Dense sampling with multi-bar horizons. **Control:** purge, embargo, uniqueness weighting (A.5).

### FP-5 — Bid-ask bounce masquerading as reversion
Mid-price returns at short horizons are mechanically negatively autocorrelated. **Control:** use
micro-price or trade-weighted returns; require the effect to persist at horizons where bounce is
immaterial; the matched-random-entry baseline absorbs this by construction.

### FP-6 — Volatility conditioning in disguise
`LAM`, `LSI`, and `RRI` all correlate with $\sigma$. **Control:** orthogonalization against
$\sigma$, $s$, and time-of-day, with coefficients fitted on the exploratory partition only, frozen
thereafter. **The orthogonalized result is the primary result.**

### FP-7 — Time-of-day seasonality
Both features and returns have strong deterministic intraday shape; their correlation can be
entirely spurious. **Control:** time-of-day in the orthogonalization plus within-session reporting.

### FP-8 — Multiple testing across the grid
Windows × horizons × thresholds × instruments = hundreds to thousands of trials. **Control:** full
grid declared in pre-registration; SPA/Reality Check; Deflated Sharpe using the true trial count.

### FP-9 — Regime coincidence
One volatile period dominates the sample. **Control:** per-year and per-regime breakdowns; block
bootstrap; results reported by fold.

### FP-10 — Latency optimism
Signal computable at $t$, actionable only at $t+\delta$; MBO reconstruction is not instantaneous.
**Control:** measure actual computation time, include it in $\delta$, report the $\delta$ grid.

### FP-11 — Passive-fill optimism
Assuming limit fills on touch. **Control:** trade-through rule (A.7). *This alone reverses the sign
of a great many published intraday results.*

### FP-12 — Cross-venue timestamp artifacts
Apparent ES→SPY lead-lag from feed latency, not economics. **Control:** deliberately degrade
timestamp precision; if the effect needs sub-millisecond alignment, it is not tradable.

### FP-13 — Sign-model artifact (H3)
$\widehat{G}$ embeds an unvalidated heuristic. **Control:** ≥2 alternative sign models; primary test
built on the observed $d^{\text{strike}}$ dose-response instead.

### FP-14 — Reverse causality
Feature responds to a move already underway. **Control:** condition on a quiet precursor window;
report quiet-precursor cases separately.

### FP-15 — Iceberg contamination
Hidden refills inflate `RRI`. **Control:** identify reserve refills where the feed permits; flag as
unresolved measurement bias on equities and discount conclusions accordingly.

### FP-16 — Instrument selection
ES/SPY chosen for liquidity and data availability. **Control:** state the selection openly; test on
instruments not used in development before any Level 5 claim.

### FP-17 — Researcher degrees of freedom
Every choice — $\phi$, $\tau$, bar size, quantile cutoffs, regression window — is a fork.
**Control:** pre-registration; parameter surfaces; plateau requirement; and the honest declaration
of trial count in the Deflated Sharpe calculation.

### FP-18 — Survivorship in the research process itself
The hypotheses that reach this document already survived informal filtering by plausibility.
**Control:** the graveyard (`docs/99-hypothesis-graveyard.md`) records rejected ideas so the
denominator of the search remains visible.

---

# Part C — Kill Criteria

**Killing a hypothesis is a success.** It costs one experiment and saves the capital that a false
positive would have destroyed. The graveyard is the most valuable file in this repository.

## C.1 Universal kill criteria (any hypothesis)

A hypothesis is **KILLED** if any of the following holds:

1. Net expectancy $\le 0$ at **1.5×** modelled costs.
2. No monotone dose-response where the theory predicts one.
3. Effect present in exploratory data, absent in the locked holdout.
4. No stable parameter plateau — performance collapses at neighbouring parameter values.
5. Effect vanishes at a decision lag of 1 second.
6. Incremental improvement over the relevant primary baseline is trivial (cross-validated
   $\Delta$AUC $\le 0.005$, or no significant improvement in a nested likelihood-ratio test).
7. Deflated Sharpe Ratio $\le 0$ given the declared trial count.
8. Sign instability across instruments or across years with no *pre-stated* structural explanation.
9. The effect is fully explained by any single control variable ($\sigma$, spread, time-of-day,
   book imbalance).
10. Fewer than ~100 independent (uniqueness-weighted) observations supporting the effect. **Any
    result resting on a handful of days is a story, not a finding.**

## C.2 Hypothesis-specific kills

| | Kill condition |
|---|---|
| **H1** | Does not beat static book imbalance incrementally, **regardless of standalone performance** |
| **H2** | Effect disappears after orthogonalizing $\lambda$ against realized volatility. *(Most likely outcome. Report as a kill, not as "λ is a useful volatility proxy.")* |
| **H3** | $\beta_3$ (the dose-response interaction) indistinguishable from zero, **or** results reverse under an alternative OI sign model |

## C.3 What is *not* grounds for modification

- A losing streak in forward testing shorter than the pre-declared evaluation window.
- A drawdown within the modelled distribution.
- A result that is positive but smaller than hoped.
- Intuition that "it should work better with one more filter." **Adding a filter after seeing
  results is fitting, and the resulting specification requires a fresh holdout.**

## C.4 Resurrection rule

A killed hypothesis may return **only** with genuinely new evidence: new data, a corrected
measurement bug, or a structural change recorded in the changelog that plausibly alters the
mechanism. It returns at **Level 0** and requires a fresh pre-registration and a fresh holdout.
"Retesting with different parameters" is not new evidence — it is the search continuing, and it must
be counted in the trial count.
