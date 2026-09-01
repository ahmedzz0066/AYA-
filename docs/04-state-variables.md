# 04 — Seven Measurable State Variables

> **Proof level: 1.** Every variable below is fully specified — computable from a named data feed
> with no free interpretation and no look-ahead. None has been computed on real data.
> `UNTESTED HYPOTHESIS — DATA REQUIRED` applies to every claim of usefulness.

## Design rules (binding on all seven)

| # | Rule | Reason |
|---|---|---|
| R1 | **Causality.** Every variable at index $t$ uses only messages timestamped $\le t$. | Look-ahead is the dominant cause of false positives. |
| R2 | **Event-time indexing.** $t$ indexes event bars (volume/dollar/imbalance), not clock seconds. | `A7`. Clock sampling mixes regimes. |
| R3 | **Scale-free normalization.** Never absolute ticks, dollars, or contracts. Always quantiles of the instrument's own trailing distribution, or units of $\sigma$ or spread. | Survives `CL-2026-01`, contract changes, and cross-instrument transfer. |
| R4 | **Declared decision lag.** Each variable declares the minimum realistic latency $\delta$ between the last message used and the earliest actionable moment. | An unactionable signal is not a signal. |
| R5 | **Uncertainty carried.** Estimated variables (notably `HFP`) carry an explicit confidence band and are never reported as known. | `A5`. |
| R6 | **Earn your place.** A variable is retained only if it adds measurable incremental information over the simpler variables already in the set. | Complexity must be paid for. |

**Notation.** $b_t, a_t$ = best bid/ask price; $q^b_t, q^a_t$ = displayed size at the touch;
$m_t = (b_t+a_t)/2$; $s_t = a_t - b_t$; $\sigma_t$ = trailing realized volatility on the same event
grid; $V_t$ = traded volume in bar $t$. All windows $W$ are stated in **event-bar counts**.

---

## SV1 — `OFI` : Order Flow Imbalance

**What it measures.** Net directional pressure at the touch, counting *all three* price-change
channels (§1.1) — not just trades.

**Definition** (Cont–Kukanov–Stoikov form, per book update $n$):

$$
e_n =
\underbrace{\mathbb{1}[b_n \ge b_{n-1}] \, q^b_n - \mathbb{1}[b_n \le b_{n-1}] \, q^b_{n-1}}_{\text{bid-side contribution}}
\;-\;
\underbrace{\big(\mathbb{1}[a_n \le a_{n-1}] \, q^a_n - \mathbb{1}[a_n \ge a_{n-1}] \, q^a_{n-1}\big)}_{\text{ask-side contribution}}
$$

$$\mathrm{OFI}_t = \sum_{n \in \text{bar } t} e_n \qquad\text{and}\qquad \widetilde{\mathrm{OFI}}_t = \frac{\mathrm{OFI}_t}{\mathrm{MAD}_W(\mathrm{OFI})}$$

using median absolute deviation over a trailing window $W$ for normalization (robust to the fat
tails that will otherwise dominate any standard-deviation scaling).

**Why this and not signed volume.** Signed volume counts only executions. OFI counts cancellations
and in-spread improvements as well — the other two channels by which price actually changes. On
equities, where aggressor side must be *inferred* (`CL-2026-03`), OFI computed from quote updates is
also less contaminated than trade-classification-based measures.

**Data required.** MBP-10 minimum; MBO preferred. Nanosecond timestamps.
**Decision lag $\delta$.** One book-update round trip plus reaction time. For a non-colocated
participant, assume $\delta \ge$ 100 ms and test sensitivity to $\delta \in \{0.1, 0.5, 1, 5\}$ s.
**Known failure mode.** Quote flickering inflates OFI without any economic pressure. Control: a
minimum-resting-time filter, tested as a robustness parameter rather than tuned.

---

## SV2 — `LAM` : Realized Impact Coefficient $\hat\lambda$  ← *the central variable*

**What it measures.** How much price moves per unit of net pressure — the empirical slope of the
liquidity supply function. Low $\hat\lambda$ = resilient market. High $\hat\lambda$ = fragile.

**Definition.** Rolling constrained regression over the trailing $W$ event bars:

$$\Delta m_{\tau} = \lambda \cdot \widetilde{\mathrm{OFI}}_{\tau} + \varepsilon_\tau, \quad \tau \in (t-W, t]$$

$$\hat\lambda_t = \frac{\sum_\tau \widetilde{\mathrm{OFI}}_\tau \, \Delta m_\tau}{\sum_\tau \widetilde{\mathrm{OFI}}_\tau^2}
\qquad
z^\lambda_t = \frac{\hat\lambda_t - \mathrm{median}_{W'}(\hat\lambda)}{\mathrm{MAD}_{W'}(\hat\lambda)}
\qquad
\dot\lambda_t = z^\lambda_t - z^\lambda_{t-k}$$

**Derived: Price Response Efficiency.** The instantaneous deviation from the prevailing regime:

$$\mathrm{PRE}_t = \frac{\Delta m_t}{\hat\lambda_{t-1}\,\widetilde{\mathrm{OFI}}_t}$$

$\mathrm{PRE} \gg 1$: price moved far more than the current regime implies (liquidity vacuum).
$\mathrm{PRE} \ll 1$: flow was absorbed with unusually little displacement.
**Note the lag:** $\hat\lambda_{t-1}$, never $\hat\lambda_t$ — using the contemporaneous estimate
would embed the very move being evaluated. This is a real and easy leak.

**Directional decomposition** (required, because supply is not symmetric — this asymmetry is the
whole point):

$$\hat\lambda^{+}_t \text{ from bars with } \widetilde{\mathrm{OFI}} > 0, \qquad
\hat\lambda^{-}_t \text{ from bars with } \widetilde{\mathrm{OFI}} < 0, \qquad
\Lambda^{\text{asym}}_t = \frac{\hat\lambda^{+}_t - \hat\lambda^{-}_t}{\hat\lambda^{+}_t + \hat\lambda^{-}_t}$$

**This is the quantitative replacement for "effort versus result."** Effort $=|\widetilde{\mathrm{OFI}}|$.
Result $=|\Delta m|$. Efficiency $=\mathrm{PRE}$. Regime $= z^\lambda$.

**The confound that will kill naïve use of this variable:** $\hat\lambda$ is mechanically correlated
with realized volatility — thin books are volatile books. Any claim that $\hat\lambda$ carries
information **must** be made on the residual after projecting out $\sigma_t$, $s_t$, and time-of-day.
This is not optional and it is the single most likely way H2 produces a false positive.

**Data required.** Same as SV1. **Decision lag.** As SV1, plus $W$ bars of warm-up.

---

## SV3 — `RRI` : Replenishment Resilience Index

**What it measures.** After liquidity at the touch is consumed, does it come back — how much, how
fast, and **at what price**? This is the direct observable of the liquidity supply function and the
variable that has no chart-based analogue.

**Definition.** For each depletion event $j$ (the touch queue on one side falling below a fraction
$\phi$ of its pre-event size, $\phi$ tested over a range, not tuned), measure over the following
$\tau$ event-units two separate components:

$$
R^{\text{qty}}_j = \frac{\text{depth restored within } \tau}{\text{depth consumed}}
\qquad
R^{\text{px}}_j = \mathbb{1}\!\left[\text{restoration occurred at the same price level}\right]
$$

$$\mathrm{RRI}^{\text{side}}_t = \text{EWMA}\big(R^{\text{qty}}_j \cdot (\,\alpha + (1-\alpha) R^{\text{px}}_j\,)\big), \quad
\Delta\mathrm{RRI}_t = \mathrm{RRI}^{\text{ask}}_t - \mathrm{RRI}^{\text{bid}}_t$$

**The two components must be kept separate as well as combined.** Restoring the same size one tick
worse is a *different* event from restoring it at the same price — the first is a market pulling
back, the second is a market holding. Collapsing them into one number destroys the distinction that
motivates the variable.

**Why this matters more than depth.** Static depth answers "what is showing now?" `RRI` answers
"what came back after it was hit?" — which is the only depth that was ever real (`A3`).

**Data required.** **MBO (L3) strongly preferred.** With MBP-10 you can approximate quantity
recovery but cannot distinguish a *new* order from a *modified* one, nor observe queue position.
Degradation from MBO to MBP-10 must itself be measured, as an information-value test.
**Known failure mode.** Iceberg refills look like replenishment but are the same order. On CME,
iceberg/reserve behavior is partly identifiable from MBO; on equities it is not. Flag as a
measurement bias for equities, do not pretend it is solved.

---

## SV4 — `CIR` : Cancellation Intensity Ratio

**What it measures.** *Which channel* is depleting the book — trades or cancels. Execution-driven
depletion means someone paid to remove liquidity. Cancellation-driven depletion means providers
left for free. These are different events with plausibly different consequences, and they are
**identical on a chart**.

**Definition.** Over the top $N$ levels within the trailing window:

$$\mathrm{CIR}_t = \frac{\text{cancelled volume}}{\text{cancelled volume} + \text{executed volume}}, \qquad
\mathrm{CIR}^{\text{asym}}_t = \mathrm{CIR}^{\text{bid}}_t - \mathrm{CIR}^{\text{ask}}_t$$

**Interpretation hypothesis (untested).** Rising $\mathrm{CIR}$ with rising $\hat\lambda$ and flat
`OFI` is the signature of **D2 (Resilience Erosion)**: supply leaving without being paid to leave.
This combination is the most specific candidate marker of the DRC's distinctive state.

**Data required.** **MBO is mandatory.** MBP feeds report net depth change and cannot separate the
channels at all. This is the single most expensive data requirement in the framework, and it should
be justified by an explicit information-value test: *does adding `CIR` improve out-of-sample
prediction over `RRI` + `OFI` + `LAM` alone?* If not, `CIR` is dropped and the data budget is saved.

---

## SV5 — `AAS` : Auction Acceptance Score

**What it measures.** Whether the market has *accepted* a price region — replacing "support and
resistance" with something computable.

**Definition.** For a price region $\mathcal{P}$ (bucketed at a volatility-scaled width, not a tick
count) over a trailing horizon, combine four causally-available components, each converted to a
trailing-window quantile in $[0,1]$:

| Component | Symbol | Meaning |
|---|---|---|
| Time at price | $T_\mathcal{P}$ | fraction of event-time spent in the region |
| Volume at price | $V_\mathcal{P}$ | fraction of volume transacted in the region |
| Revisit count | $N_\mathcal{P}$ | distinct entries into the region after leaving it |
| Departure decay | $\Xi_\mathcal{P}$ | mean $|$displacement$|$ following departures, sign-adjusted for return |

$$\mathrm{AAS}(\mathcal{P}, t) = w_1 T_\mathcal{P} + w_2 V_\mathcal{P} + w_3 N_\mathcal{P} - w_4 \Xi_\mathcal{P} \;\in [-1, 1]$$

**Weight discipline.** Start with $w_i = 1/4$ (equal weighting). Weights may be fitted **only** on
the exploratory partition and must then be frozen. A fitted-weight version that does not beat the
equal-weight version out-of-sample is discarded in favor of equal weights — **the simpler object
wins ties**.

**Definitions this makes precise:**
- *Accepted:* $\mathrm{AAS} > $ upper quantile — high time and volume, low subsequent displacement.
- *Rejected:* $\mathrm{AAS} < $ lower quantile — low time, low volume, large displacement away.
- *Discovering:* `AAS` near zero with rising $\hat\lambda$ — state D4.
- *Returning to equilibrium:* `AAS` rising toward a previously-accepted region.

**Data required.** Trades + top of book. This is the **cheapest** of the seven variables — a point
in its favor under R6, and a reason to test it early.

---

## SV6 — `LSI` : Liquidity Stress Index

**What it measures.** A single scalar for "how broken is the book right now" — the gate on whether
*any* setup is executable.

**Definition.** Robust z-scores against the trailing distribution **for the same session** (`A6` —
otherwise a normal overnight book scores as a daytime crisis, `CL-2026-02`):

$$
\mathrm{LSI}_t = \mathrm{median}\Big(
z(s_t),\;
-z(q^b_t + q^a_t),\;
z(|\Delta \text{depth}|_t),\;
z(\text{quote update rate}_t),\;
-z(\text{mean trade size}_t),\;
z(\hat\lambda_t)
\Big)
$$

**Median, not mean**, so that a single misbehaving component cannot dominate — this is a robustness
choice, not a performance choice, and it is made before any fitting.

**Use.** `LSI` is primarily a **veto**, not a signal. Above its upper quantile: execution assumptions
are invalid, slippage models are unreliable, and no setup is permitted regardless of how attractive
it appears. This is the variable that connects to the kill switches in the risk architecture.

**Data required.** MBP-10 + trades. **Decision lag.** Immediate but noisy; smooth over a small
number of event bars and test sensitivity to the smoothing length.

---

## SV7 — `HFP` : Hedging Feedback Pressure  ⚠️ *estimated, never observed*

**What it measures.** The magnitude and sign of price-contingent mandated flow (G3) — dealer gamma
being the dominant component for index products.

**Definition.** A vector, not a scalar, because the components have different reliabilities:

$$\mathrm{HFP}_t = \big(\; \widehat{G}_t \pm \mathrm{CI},\;\; d^{\text{strike}}_t,\;\; \Theta_t,\;\; B_t \;\big)$$

| Component | Definition | Reliability |
|---|---|---|
| $\widehat{G}_t$ | Estimated net dealer gamma at spot, from OPRA open interest × a **declared sign model** | **Low.** The sign model is a heuristic assumption, not data. |
| $d^{\text{strike}}_t$ | Volatility-scaled distance from spot to the nearest large-OI strike | High — OI is observed |
| $\Theta_t$ | Time-to-expiry weighting (charm/gamma concentration into the close) | High — deterministic |
| $B_t$ | ETF/futures basis relative to its trailing distribution | High — observed |

**Mandatory epistemic discipline.** $\widehat{G}_t$ is the output of an assumption about *who owns
which side of the open interest*. It is not a measurement. Every result conditioned on
$\widehat{G}_t$ must be re-run under **at least two alternative sign models**, and any result that
does not survive the swap is reported as a property of the sign model, not of the market.

**The one component that is genuinely testable without the sign model** is $d^{\text{strike}}_t$:
if gamma hedging is real, its effect must show **dose-response with distance from concentrated
strikes**. That dose-response is falsifiable without ever knowing the dealer's sign, which is why
H3 is built on it rather than on $\widehat{G}$ alone.

**Data required.** OPRA trades and quotes, OCC open interest (T+1), a dividend/rate curve for
Greeks, index/ETF/futures prices for basis. **Note the timing:** OI is published after the fact.
Using same-day OI is look-ahead. **Use prior-session OI only.**

---

## Derived: the regime classifier $VR(t)$

Volatility regime is **not** an eighth peer variable — it is a *function* of the seven, and it
should be derived rather than asserted, because hand-labeled regimes are a well-known way to smuggle
hindsight into a model.

**Method.** Fit a small-state hidden Markov model or a constrained clustering on the vector
$(\sigma_t,\ z^\lambda_t,\ \mathrm{LSI}_t,\ \mathrm{CIR}_t,\ \text{trade intensity}_t)$, **fitted
only on the exploratory partition and then frozen.** Label the resulting states *after* fitting by
inspecting their properties. Do not pre-name states and then look for them.

Anticipated (not assumed) states: compression, normal auction, expansion, trend acceleration, event
shock, post-event digestion, vacuum, mean-reverting chop. **If the data supports three states, use
three.** The number of states is chosen by out-of-sample likelihood, not by how well it matches the
narrative in this document.

---

## Deliberately rejected candidate variables

Recorded so that the reasoning is not repeated later:

| Rejected | Why |
|---|---|
| Raw static book imbalance $(q^b-q^a)/(q^b+q^a)$ | Not rejected as *false* — it is a well-known short-horizon predictor. It is excluded from the ALAT variable set because it is the **baseline H1 must beat**, and including it in the model would obscure that test. |
| Cumulative delta | An unnormalized running sum with an arbitrary origin. `OFI` is the same idea done correctly, and it counts all three price-change channels. |
| Any oscillator (RSI/MACD/stochastics) | A deterministic transform of past prices. It cannot add information beyond the price series; it can only lose some. Permitted only as a *compression* of price history inside a model — never as a causal explanation. |
| Volume profile / "point of control" | Subsumed by `AAS`, which measures the same intuition causally and outputs a signed score rather than a picture. |
| VWAP as a signal | Retained only as an **execution benchmark** and as a cost-model input, not as a directional feature, until it demonstrates incremental information over `AAS`. |

---

## Chapter conclusions

1. Seven primitives — `OFI`, `LAM`, `RRI`, `CIR`, `AAS`, `LSI`, `HFP` — plus a *derived* regime
   classifier.
2. `LAM` is the central variable and it carries the framework's central confound: it correlates
   mechanically with realized volatility, so all of its claims must be made on the orthogonalized
   residual.
3. `RRI` and `CIR` are what genuinely require order-level data. If their information-value tests
   fail, ALAT's expensive data requirement is unjustified and the framework should collapse toward
   the cheaper variables. **That outcome must be reported, not buried.**
4. `HFP` is estimated. Its sign component is a modeling assumption wearing a number's clothing, and
   it is fenced off accordingly.
5. `AAS` and `LSI` are cheap and should be tested first for that reason alone.

## Research questions arising

- **RQ-8.** Does `CIR` add measurable information over `RRI`+`OFI`+`LAM`? (If not, MBO data is not
  required and the research program becomes dramatically cheaper.)
- **RQ-9.** How much does each variable degrade from MBO → MBP-10 → trades-only? This determines the
  minimum viable data budget.
- **RQ-10.** Is $z^\lambda$ anything other than a slow realized-volatility estimator in disguise?
