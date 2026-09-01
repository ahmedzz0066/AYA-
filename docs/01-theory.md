# 01 — What Actually Moves Intraday Price in a 2026 Electronic Auction

> **Proof level: 1 (logically coherent).** This document contains no empirical results. It is a
> causal model constructed to be *falsifiable*, and its purpose is to generate testable claims —
> not to persuade.

---

## 1.1 Start with the mechanism, not the chart

In a continuous double auction with a central limit order book, "price" is not a quantity that
drifts. It is a **pointer into a discrete queue structure**. The best bid is the highest price at
which unexecuted buy interest currently rests; the best offer is the lowest price at which
unexecuted sell interest rests. The mid-price is an arithmetic convenience with no independent
existence.

It follows — as an *identity*, not a theory — that the price at the touch can change through
exactly three mechanisms:

1. **Execution.** Aggressive orders consume the resting queue at the best price until it is empty.
2. **Cancellation.** Liquidity providers withdraw the resting queue without any trade occurring.
3. **Improvement.** A new limit order is placed inside the prevailing spread.

There is no fourth mechanism. Every intraday price change that has ever occurred in an electronic
CLOB is some sequence of (1), (2), and (3).

This identity is the entire foundation of ALAT, and it has an immediate and unfashionable
consequence:

> **A price move is not evidence of buying or selling. It is evidence that liquidity at a price was
> removed and not replaced.**

Removal by execution and removal by cancellation look identical on a candlestick chart. They are
completely different economic events. Any methodology built only on OHLC bars is structurally
incapable of distinguishing them. That is the specific respect in which chart-based methodologies —
including Wyckoff's — are underdetermined: they observe the *result* of a process whose two most
important inputs are, at that resolution, unobservable.

---

## 1.2 The variable that matters is not flow — it is the response to flow

Consider the standard linear-impact form used throughout the microstructure literature:

$$\Delta m_{t} \;=\; \lambda_t \cdot \mathrm{OFI}_t \;+\; \varepsilon_t$$

where $\Delta m_t$ is the change in mid-price over an interval, $\mathrm{OFI}_t$ is net order-flow
imbalance (signed pressure at the touch, counting executions, cancellations, and improvements —
i.e. exactly mechanisms 1–3 above), and $\lambda_t$ is the local price-impact coefficient — Kyle's
lambda, allowed to vary in time.

Almost the entire retail and much of the professional intraday effort is aimed at forecasting
$\mathrm{OFI}$: predicting the next aggressive buyer. ALAT's central claim runs the other way.

> ### The Resilience Primacy Hypothesis (RPH)
>
> **At intraday horizons, $\mathrm{OFI}_t$ is close to unforecastable from public information,
> because it is competitively arbitraged on latency scales far below discretionary reach.
> $\lambda_t$ is not. $\lambda_t$ is a slowly-varying, persistent, partially observable state
> variable — and it is where forecastable structure lives.**

Why should $\lambda$ be persistent when flow is not? Because $\lambda$ is not a property of traders'
opinions. It is a property of the **liquidity supply function** — the conditional rate at which
providers replace consumed depth — and that function is governed by variables that move on
*minute-to-hour* timescales, not microsecond ones:

- market-maker **inventory** and its distance from risk limits,
- the provider's current estimate of **adverse selection** (how often getting filled is followed by
  a loss),
- **realized and implied volatility**, which sets quoting width,
- the presence of large **metaorders** consuming one side of the book persistently,
- **mandated hedging obligations** that force certain participants to trade in a known direction
  given price,
- the **participant mix** of the current session.

None of these can be changed in a microsecond. All of them have memory. This is the asymmetry that
makes a discretionary or minute-scale systematic method conceivable at all: you cannot beat a
co-located market maker to the next tick, but the *conditions under which that market maker will
step back* persist long enough to be estimated and acted upon.

**This reframes every classical concept.** "Effort versus result" is a folk description of
$\lambda$. "Absorption" is the claim that $\lambda$ is currently low despite high $|\mathrm{OFI}|$.
"A spring" is the claim that a displacement occurred into a region where $\lambda$ was
transiently high and liquidity supply then repaired at the old level. Wyckoff had the phenomenology
right and the mechanism unavailable. We now have the mechanism, and it is measurable.

**Falsifier for RPH:** if a rolling estimate $\hat\lambda_t$ shows autocorrelation no greater than
$\mathrm{OFI}_t$'s, and if conditioning forward returns on $\hat\lambda$ state adds no information
beyond conditioning on realized volatility, the Resilience Primacy Hypothesis is dead and ALAT with
it. **This is why H2 (`docs/05-hypotheses.md`) must be tested first.**

---

## 1.3 Six generators of intraday movement, ranked by persistence

Price moves for different reasons on different timescales, and the reasons have *different
half-lives*. Persistence — not size — determines tradability, because a move that has already
finished by the time you can act is not an opportunity.

| # | Generator | Mechanism | Typical persistence | Directional predictability | Observable in |
|---|---|---|---|---|---|
| G1 | **Inventory repricing** | A provider accumulates unwanted inventory and skews quotes to shed it | Seconds–minutes | Mean-reverting | Quote asymmetry, replenishment asymmetry |
| G2 | **Metaorder execution** | A parent order is worked over minutes–hours by a scheduling algorithm | Tens of minutes–hours | Persistent same-sign flow; concave price path; partial post-completion reversion | Signed-flow autocorrelation, sustained one-sided absorption |
| G3 | **Mandated hedging** | Options dealer gamma/vanna/charm hedging, ETF create/redeem arbitrage, leveraged-ETF end-of-day rebalance, index reconstitution | Contingent on price; sharply concentrated in time and at strikes | **Direction is a known function of price**, magnitude uncertain | Options OI, ETF basis, calendar, closing-auction imbalance |
| G4 | **Information shock** | A scheduled print or headline re-anchors the conditional value distribution | Instant re-price, then decaying volatility | Direction unpredictable; *volatility* highly predictable | Event calendar, quote withdrawal preceding the print |
| G5 | **Liquidity-structural cascade** | Stop activation, forced liquidation, latency-driven vacuum: a price move causes flow that causes more price move | Seconds–minutes, self-terminating | Continuation while the cascade runs; sharp reversion after | Depth collapse, spread widening, trade-intensity spike |
| G6 | **Cross-venue propagation** | ES leads SPY leads constituents; the "price" is a network, and displacement propagates through it | Milliseconds at the tick level; minutes at the *state* level | Tick-level lead-lag is a latency business, closed to us | Basis dislocations, correlated depth withdrawal |

**Two conclusions follow immediately and they constrain everything downstream:**

1. **G6 is not our business.** Tick-level lead-lag between ES and SPY is arbitraged at the speed of
   light between Aurora and Carteret. A discretionary or minute-scale trader competing there loses
   by construction. What *is* accessible is the propagation of **state** — when liquidity withdraws
   in the lead instrument, the follower's liquidity supply function degrades for a period long
   enough to matter.

2. **G3 is the defining feature of the modern intraday auction, and it has no Wyckoff analogue.**
   Wyckoff's market had no participant obligated to buy as price fell and sell as it rose (or the
   reverse) as a mechanical consequence of positions taken elsewhere. In 2026 a majority of SPX
   option volume expires the same day (`CL-2026-04`), which means a large, price-contingent,
   *non-discretionary* flow is continuously superimposed on the underlying. This is not a
   "composite operator." It is a feedback coefficient. It can be estimated — poorly — and it must
   never be asserted as known.

---

## 1.4 Killing the composite operator

Classical Wyckoff explains persistent one-sided pressure by positing a "composite operator" — a
unified intelligent actor accumulating or distributing. This is unfalsifiable: any price path can be
retro-fitted with a story about what the operator intended.

The honest 2026 replacement is an **explicit list of competing mechanisms** that produce the same
observable, with a rule that we may not select among them without discriminating evidence.

**Observation:** price holds a level while heavy aggressive selling continues.

**Candidate generators, all consistent with that observation:**

| Explanation | Discriminating observable |
|---|---|
| A metaorder is buying passively (G2) | Signed-flow autocorrelation stays positive; replenishment concentrated at one price; reversion *after* the level breaks or the flow stops |
| A market maker is accumulating inventory involuntarily and will need to shed it | Quote skew develops; the level fails shortly after with an outsized move as the maker reverses |
| Dealers are long gamma near a large strike and are mechanically buying dips (G3) | Effect strengthens near concentrated OI and weakens with distance from it (a *dose-response* test) |
| ETF arbitrage: the ETF is cheap to fair value, so authorized participants buy it (G3) | Basis to NAV/futures; effect disappears when basis is flat |
| A wholesaler is hedging retail flow already internalized elsewhere (`CL-2026-03`) | The lit trade is an echo: it lags the off-exchange print, and carries no forward information |
| Short covering | Borrow rates, prior-period short interest, prior downtrend |
| **Nothing. Ordinary noise in a thick book.** | The behavior is within the distribution of matched control periods |

**The last row is the default.** ALAT's rule: *the null hypothesis for any observed structure is
that it is a draw from the unconditional distribution.* We do not name an actor. We estimate a
state, and we require the state to have discriminating power against matched controls.

---

## 1.5 Why efficiency does not preclude an edge — and where the edge would have to live

If flow is unforecastable and $\lambda$ is contested by faster participants, why would anything
remain?

Three structural reasons, each of which generates a testable prediction:

1. **Risk-bearing, not prediction.** Liquidity provision earns a premium for absorbing inventory and
   adverse selection. Any strategy that supplies liquidity when it is scarce is compensated for a
   *real risk*, not for a forecast. Edges of this kind do not decay from being known — they decay
   only if capital floods in faster than the risk. **Prediction:** the profitable side of an
   ALAT setup should coincide with the side that is *bearing* inventory risk, and its return should
   be positively related to the risk borne (drawdown, MAE), not inversely.

2. **Constrained participants.** G3 flows are not opinions. A dealer hedging gamma, an authorized
   participant closing a basis, a leveraged ETF rebalancing into the close, an index fund tracking a
   reconstitution — these trade because they must, at times and prices largely determined in
   advance. They are price-insensitive by mandate. **Prediction:** their footprint should show
   dose-response with the mandate's intensity (strike concentration, basis width, rebalance
   notional) — not merely correlation with volatility.

3. **Capacity and horizon segmentation.** The fastest participants are capacity-limited: a strategy
   holding for minutes and risking meaningful size cannot be run by a firm whose edge is measured in
   microseconds and whose risk limits require flatness. Some structure survives *not because nobody
   sees it* but because seeing it is not enough to trade it at scale.

Conversely, three reasons an apparent edge will most often be an illusion, and these are the
priors:

- It is the bid-ask bounce in a costume (a "signal" that predicts mid-price reversion after a trade
  at the offer predicts nothing you can monetize).
- It is a **latency fantasy**: measurable at $t$, actionable only at $t$ minus your reaction time.
- It is volatility timing wearing a microstructure hat — and a simple realized-volatility control
  destroys it.

**Every ALAT hypothesis must therefore be tested against three specific nulls, not one:** matched
random entry, the volatility-conditioned baseline, and the naïve queue/order-book-imbalance
baseline. See `docs/07-experiment-protocol.md`.

---

## 1.6 The eight questions, answered by the theory

The prime directive requires that the methodology answer eight questions for any trade. Here is how
the theory answers each in principle; `docs/05-hypotheses.md` instantiates them concretely.

| Question | ALAT's answer form |
|---|---|
| **WHY should price move?** | Because the liquidity supply function on one side is degraded relative to the other, so equivalent flow produces unequal displacement. Not "because buyers are stronger." |
| **WHO is causing it?** | A named generator from G1–G6, with an explicit alternative-explanation table and an assigned probability — never a composite operator. |
| **WHERE is liquidity concentrated?** | Where replenishment has been *demonstrated* (repeated restoration after depletion), not where visible size sits (`A3`: displayed depth is a biased estimator). |
| **WHAT confirms it?** | A pre-specified, causally-computable change in the state variables — displacement per unit flow, replenishment failure, acceptance score. |
| **WHAT invalidates it?** | A pre-specified condition of equal precision, written before entry. If invalidation cannot be stated as a computable condition, the trade does not exist. |
| **WHEN must it occur?** | Within a horizon measured in *event time* (volume/trade counts), because the hypothesis concerns a liquidity state and liquidity states are consumed by activity, not by the clock. Expiry of that horizon is an exit, not a hope. |
| **HOW do costs affect it?** | The edge equation is evaluated *net*: spread crossing, fees, realistic slippage, market impact. At intraday horizons this term is the same order of magnitude as the gross edge — it is a first-order term, not a rounding error. |
| **HOW does regime change it?** | Every rule declares the regimes in which it is claimed to hold. A setup that must be traded in every regime is a setup that has not been tested in any. |

---

## 1.7 Chapter conclusions

1. Price change is queue depletion without replenishment. This is an identity and it is the only
   non-negotiable statement in this repository.
2. Executions and cancellations are economically different and chart-identical. Order-level data is
   therefore not a luxury; it is the minimum resolution at which ALAT's questions are even
   well-posed.
3. The forecastable object is the **price-impact coefficient / liquidity supply function**, not the
   flow. This is the Resilience Primacy Hypothesis, and it is the load-bearing claim: falsifying it
   falsifies the framework.
4. Six generators produce intraday movement. Their *persistence* determines tradability. G6 is
   closed to us; G3 is the structurally novel one and the most dangerous to model, because dealer
   positioning is estimated, never observed.
5. The composite operator is replaced by an explicit alternative-explanation table with noise as the
   default.
6. Any edge that survives must be explicable as compensation for risk, a constrained participant's
   footprint, or horizon segmentation. An edge with none of those three stories attached should be
   presumed to be a backtest artifact.

## Research questions arising

- **RQ-1.** Is $\hat\lambda_t$ measurably more persistent than $\mathrm{OFI}_t$, and is that
  persistence anything more than the persistence of realized volatility?
- **RQ-2.** What fraction of top-of-book depletion events are cancellation-driven versus
  execution-driven, and does that ratio carry forward information at all?
- **RQ-3.** Can dealer gamma *sign* be estimated with enough reliability to condition on, or does
  the sign-estimation error swamp the mechanism?
- **RQ-4.** Does the ES→SPY relationship transmit *state* (liquidity conditions) on horizons long
  enough to act on, as distinct from *price*, which does not?
