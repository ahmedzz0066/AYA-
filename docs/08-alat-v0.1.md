# 08 — ALAT v0.1

**Version:** ALAT v0.1
**Date:** 2026-09-01
**Session:** RS-001
**Confidence level: LEVEL 1 — Logically coherent.**
**No empirical support of any kind. No data has been examined. Not tradable.**

---

## On the name

The working name **Adaptive Liquidity Auction Theory** is retained for v0.1, with one refinement:
the framework's central claim now has its own name, because it — not the framework — is what is
actually being tested.

> **The Resilience Primacy Hypothesis (RPH):** at intraday horizons, forecastable structure resides
> in the *price-impact coefficient* (the liquidity supply function), not in *order flow*.

If RPH survives testing, a more precise name for the framework would be justified — something
naming resilience rather than "adaptive," which currently promises more than the framework delivers.
Renaming before there is evidence would be marketing. **Deferred to v0.2, contingent on H2.**

---

## What ALAT v0.1 consists of

### Core theory
1. Price change is queue depletion without replenishment. An identity, auditable against MBO data.
2. Executions and cancellations are economically distinct and chart-identical — so order-level data
   is the minimum resolution at which the framework's questions are well-posed.
3. **RPH**: the forecastable object is $\lambda$, not flow.
4. Six generators (G1–G6), ranked by persistence. G6 is closed to non-latency participants; G3
   (mandated hedging flow) is the structurally novel one and the most treacherous to model.
5. The composite operator is deleted and replaced by an explicit alternative-explanation table with
   **noise as the default hypothesis**.

### The Depletion–Repair Cycle (DRC)
Eight liquidity states — D0 Provisioned Equilibrium, D1 Inventory Loading, D2 Resilience Erosion,
D3 Depletion Event, D4 Repricing Search, D5a/D5b Repair (acceptance / rejection), D6 Hedge Feedback,
D7 Re-provisioning — arranged as a **graph with skips**, indexed in event time, with all transition
probabilities currently **unmeasured symbols**.

### Seven state variables
`OFI`, `LAM` ($\hat\lambda$, `PRE`, $\Lambda^{\text{asym}}$), `RRI`, `CIR`, `AAS`, `LSI`, `HFP`
— plus a *derived* regime classifier, fitted rather than asserted.

### Three hypotheses
H1 (asymmetric resilience erosion), H2 (impact-regime conditioning), H3 (hedging feedback
dose-response). All at Level 0–1.

### Protocol
Pre-registration; chronological partitioning with a once-touched holdout; message-index decision
points; triple-barrier labels; purge/embargo/uniqueness weighting; conservative fill model with the
trade-through rule; three cost levels; mandatory baselines with **incremental** reporting; Deflated
Sharpe and SPA over the declared trial count; 18 catalogued false-positive mechanisms with controls;
explicit kill criteria.

---

## What ALAT v0.1 explicitly does NOT contain

**And will not until data has been examined:**

- **No setups.** The prompt's architecture calls for 5–10 setup families with entries, stops, and
  targets. Writing them now would be writing fiction: a setup is a *claim about a conditional
  distribution*, and no conditional distribution has been estimated. Setups are deferred to the
  first version that reaches Level 2. What exists instead is `docs/03-cycle.md` §3.3 — the specific
  transitions that, if they prove real, *become* setups.
- **No transition probabilities.** Symbols only.
- **No performance figures of any kind.**
- **No claim that any of this is profitable.**

This absence is the most important content of v0.1.

---

## Rules that ARE in force from v0.1

These are methodological, not predictive, so they can be adopted before any data exists.

### The Confidence Engine — required output before any theoretical trade

No trade may be considered without every field completed **from information available at that
moment**:

```
Timestamp / message index:
Instrument:
DRC state (from causal classifier):
Regime (derived VR):
Directional hypothesis:
Generator claimed (G1–G6):
Alternative explanations considered + why rejected:
Expected move (in σ):
Invalidation condition (computable, stated before entry):
Time stop (in event bars):
Liquidity condition (LSI percentile):
Volatility condition:
Expected execution quality (modelled slippage):
Estimated probability:
Estimated R multiple:
Primary evidence:
Contradictory evidence:
```

**Trade Quality Score (0–100)** — the multiplicative structure is deliberate:

$$\mathrm{TQS} = 100 \times \underbrace{\hat p_{\text{edge}}}_{\text{prob.}} \times \underbrace{\frac{R_{\text{expected}}}{R_{\text{max}}}}_{\text{payoff}} \times \underbrace{(1 - \mathrm{LSI}_{\text{pct}})}_{\text{executability}} \times \underbrace{\mathbb{1}[\text{regime permitted}]}_{\text{regime gate}}$$

**Because it is multiplicative, a poor execution environment zeroes the score no matter how strong
the signal.** High confidence alone never justifies a trade — probability × payoff × execution
quality does. `UNTESTED — the calibration of $\hat p_{\text{edge}}$ requires Level 3+ data;
until then TQS is a discipline device, not a probability.`

### Risk Engine

| Rule | v0.1 setting | Status |
|---|---|---|
| Risk per trade | Fixed fraction, volatility-normalized so that 1R is a constant fraction of equity in $\sigma$ terms | Standard practice, not an ALAT finding |
| Daily max loss | Pre-declared; hitting it ends the session, no exceptions | Behavioural control |
| Consecutive-loss response | **Reduce** size on a pre-declared schedule | Never the reverse |
| Martingale | **Prohibited.** Never increase size because previous trades lost. | Absolute |
| Correlated exposure | ES/SPY/NQ treated as one position for risk purposes | Obvious but routinely violated |
| Event risk | Flat or reduced into scheduled prints unless the hypothesis *is* the event | |
| Liquidity risk | Position size capped as a fraction of measured executable depth, not displayed depth (`A3`) | |
| Gap risk | Sized against overnight gap distribution — **and note `CL-2026-02`: the gap is becoming a thin session rather than a jump, which changes this calculation** | |

**Three modes, with objective transitions:**

| Mode | Entry condition | Behaviour |
|---|---|---|
| **NORMAL** | `LSI` below upper quantile; drawdown within modelled range; slippage tracking within tolerance | Full size |
| **REDUCED** | Any one of: drawdown beyond a pre-declared fraction of modelled max; realized slippage exceeding modelled by a declared multiple; `LSI` elevated; consecutive-loss trigger | Fractional size, highest-TQS setups only |
| **NO-TRADE** | Any kill switch below | Flat |

### Kill Switches — automatic, not discretionary

Trading suspends immediately when:
1. Realized slippage materially and persistently exceeds the modelled distribution.
2. The spread regime shifts outside its tested range (**explicitly including the Nov 2026 tick
   change, `CL-2026-01`**).
3. `LSI` exceeds its extreme quantile.
4. Data feed integrity fails: gaps, sequence errors, stale book, or a failed reconstruction audit.
5. Measured latency exceeds the tested $\delta$ range.
6. Drawdown exceeds the pre-declared limit.
7. Statistical deterioration: the monitoring statistic breaches its pre-declared threshold.
8. A **MARKET STRUCTURE CHANGELOG** entry invalidates a structural precondition of the active rule.

**Switch 8 is the one that matters and the one that will be rationalized away.** A rule reverts to
Level 0 when its preconditions change. It is not grandfathered because it worked last month.

### Journal specification — every trade, no exceptions

`timestamp | message_index | instrument | setup_id | DRC_state | regime | entry | stop | target |
exit | size | spread_at_entry | modelled_slippage | realized_slippage | commission | MAE | MFE |
result_R | expected_R | TQS | OFI | LAM | RRI | CIR | AAS | LSI | HFP±CI | entry_reason |
exit_reason | rule_adherence (bool) | data_reference`

Conditional analysis every 20–50 observations: expectancy by state, by regime, by session, by TQS
decile, by liquidity condition. **Rules are not modified on the basis of a few losses.** The purpose
of the journal is to accumulate the conditional distributions that the framework currently lacks.

---

## VERSION BLOCK — ALAT v0.1

**NEW DISCOVERY (conceptual, not empirical):**
The reframing of intraday forecasting from *flow prediction* to *liquidity-supply-regime estimation*
— the Resilience Primacy Hypothesis. Its corollary is that classical "effort versus result" is an
unquantified statement about $\lambda$, and that the same price pattern should carry opposite
expectancy in different $\lambda$ regimes.

**EVIDENCE:** None empirical. Support is mechanical (the queue-depletion identity, `A1`) and
literature-derived (impact models, order-flow imbalance, volatility and liquidity clustering,
square-root impact). **Literature citations are pointers to verify, not evidence in themselves.**

**COUNTER-EVIDENCE:** The most likely outcome of H2 is that $\hat\lambda$ is a realized-volatility
proxy carrying no incremental information — in which case RPH is false. This is stated up front so
that it cannot later be reframed as a partial success. Additionally, `CL-2026-03` means the entire
apparatus may be inapplicable to fragmented equity markets, where the visible book is a biased
minority of activity.

**RULES ADDED:** All of §"Rules that ARE in force" above; the seven state-variable definitions; the
DRC state definitions; the protocol in `docs/07-experiment-protocol.md`; the design rules R1–R6.

**RULES MODIFIED:** None (initial version).

**RULES REMOVED:** The composite operator, as an explanatory device, is removed from the permitted
vocabulary of this framework.

**UNRESOLVED QUESTIONS:** RQ-1 through RQ-10 across `docs/01`, `docs/03`, `docs/04`.

**REQUIRED DATA:** Tier 1 (CME MDP 3.0 MBP-10 for ES, ≥3 years spanning multiple volatility
regimes) is sufficient to run the decisive first experiment. See `docs/06-data-requirements.md`.

**NEXT EXPERIMENT:** H2 — the $\lambda$-regime test, orthogonalized against realized volatility.

**CONFIDENCE LEVEL: 1.** Logically coherent, empirically untouched.

---

## The question this session ends on

The framework now has three testable hypotheses, and they are not equal candidates. **H2 should be
falsified first**, for four reasons:

1. **It is load-bearing.** H2 *is* the Resilience Primacy Hypothesis in testable form. If
   $\lambda^{\perp}$ carries no information, ALAT has no theoretical claim and H1/H3 are — at best —
   unexplained regularities in need of a different theory.
2. **It is the cheapest.** Tier 1 data only: no MBO, no OPRA, no cross-venue timestamp alignment.
   Roughly an order of magnitude less expensive than testing H1 first.
3. **A negative result is decisive.** Most experiments fail ambiguously. H2's primary failure mode —
   "the effect is absorbed by realized volatility" — is a clean, unarguable kill.
4. **The result gates the entire budget.** `docs/06` sequences data acquisition behind H2's outcome.
   Testing H1 first would require buying MBO data to answer a question that H2 may render moot.

The counterargument deserves stating: H1 is the more *distinctive* claim — resilience erosion
invisible to price-based analysis is the idea that would make this framework original, whereas H2
generalizes an existing literature. If the goal were novelty, H1 comes first. **If the goal is to
find out whether the foundation holds before building on it, H2 comes first.** This repository's
stated objective is the latter.

> ### Which hypothesis should we attempt to falsify first?
>
> My recommendation is **H2**. Do you want to proceed with H2, override in favour of H1's greater
> novelty, or challenge the framing before any experiment is run?
