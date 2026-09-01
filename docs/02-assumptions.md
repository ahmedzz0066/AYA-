# 02 — Ten Assumptions, Their Support, and Their Falsifiers

Each assumption below is load-bearing: if it fails, specific parts of ALAT fail with it. Each entry
records what would count as support, what would count as refutation, and **what breaks** if it is
false.

**On citations:** where the literature is invoked, it is invoked *qualitatively* and by name. No
numerical result from any paper is reproduced here, because I cannot verify the numbers from memory
and inventing them would violate the repository's first rule. Every citation below is a **pointer
for the researcher to verify**, not evidence in itself.

---

## A1 — Price change is queue depletion without replenishment

**Statement.** Any change in the best bid or offer occurs through execution, cancellation, or
in-spread improvement. There is no other channel.

**Support.** This is a mechanical consequence of the matching-engine rules of every major CLOB
(CME Globex, Nasdaq, Cboe, NYSE Pillar, major crypto venues). It is verifiable directly by
reconstructing a book from an order-level feed and confirming that reconstructed and published
top-of-book agree message-for-message. **This is not a belief; it is an audit.**

**Falsifier.** A book reconstruction from MBO data that fails to reproduce published BBO. In
practice this indicates hidden/iceberg liquidity, self-match prevention, or implied orders — all of
which are *real* and would qualify the assumption rather than destroy it.

**Known qualifications, all material:** iceberg and reserve orders (visible size understates true
size); implied orders across futures spreads; self-match prevention cancels; on NMS stocks,
midpoint/hidden liquidity at ATSs (`CL-2026-03`) means the identity holds *per venue* but not for a
consolidated "price."

**If false:** nothing in ALAT stands. Everything is built here.

---

## A2 — Short-horizon aggressive flow is close to unforecastable; its price impact is not

**Statement.** $\mathrm{OFI}_{t+1}$ cannot be forecast from public information with enough edge to
overcome costs at discretionary latency. $\lambda_t$ can be estimated and is persistent.

**Support.** Competitive arbitrage of a directly-observable public signal by co-located
participants; the general finding in the microstructure literature (Cont–Kukanov–Stoikov and the
order-flow-imbalance line of work) that *contemporaneous* OFI explains price change well while
*predictive* power decays extremely fast. Separately, the well-documented clustering of volatility
and liquidity (Engle's ARCH line; intraday periodicity work by Andersen–Bollerslev) supports the
persistence of the *coefficient*.

**Falsifier.** Demonstrating out-of-sample forecastability of next-interval OFI net of costs at
realistic latency. That would be a better discovery than ALAT and should be pursued instead.
Conversely, RPH fails if $\hat\lambda$ turns out to be no more autocorrelated than OFI once both are
measured on the same event-time grid.

**If false:** the Resilience Primacy Hypothesis collapses and the framework has no reason to exist.
**This is the single most important assumption to test, and H2 tests it.**

---

## A3 — Displayed depth is a biased estimator of executable liquidity

**Statement.** The visible book systematically misstates true liquidity, in both directions, and the
bias is state-dependent.

**Support.** Cancel-to-trade ratios in modern electronic markets are large — the overwhelming
majority of submitted orders never execute. Iceberg orders hide size; quote-flickering displays size
that evaporates on approach; and in NMS stocks the majority of volume executes away from the lit
book entirely (`CL-2026-03`). Also: the same displayed size means different things at different
queue positions, and queue position is not observable from MBP feeds.

**Falsifier.** Show that displayed depth at time $t$ is an unbiased predictor of the volume actually
executable at that price over the following interval. Direct test: for each depletion event, compare
displayed size before the sweep with realized fill quantity at that level.

**If false (i.e. if displayed depth *is* reliable):** ALAT is unnecessarily complicated. Static
book-imbalance methods would suffice and the whole replenishment apparatus (`RRI`, `CIR`) adds
nothing. **This must be tested, not assumed** — the naïve book-imbalance baseline in
`docs/07-experiment-protocol.md` is precisely the test.

---

## A4 — Metaorders exist and produce persistent signed flow with concave impact

**Statement.** Institutional parent orders are worked over extended periods, producing
autocorrelated same-sign flow, a concave (approximately square-root-in-participation) price path
during execution, and partial reversion afterward.

**Support.** The square-root impact law is one of the more replicated findings in empirical
microstructure (Bouchaud and collaborators; the Almgren–Chriss optimal-execution framework assumes
and the propagator-model literature measures it). The mechanism is not mysterious: execution
algorithms deliberately slice orders to reduce impact, which mechanically creates autocorrelated
flow.

**Falsifier.** Signed trade flow exhibiting no long-memory autocorrelation on the instrument being
studied; or measured impact that is linear rather than concave in participation rate.

**Danger.** *Detecting* a metaorder in real time is a much stronger claim than *believing they
exist*. A4 supports the existence of the generator, not our ability to identify it. ALAT must not
smuggle detection in as though it were implied.

**If false:** G2 disappears as a generator, and any setup premised on "someone is working an order"
must be re-derived from G1 or G3.

---

## A5 — A material share of intraday flow is mandated and price-contingent

**Statement.** Options dealer hedging, ETF create/redeem arbitrage, leveraged-ETF rebalancing, index
reconstitution, and margin liquidation produce flows whose *direction given price* is determined in
advance rather than chosen.

**Support.** The mechanics are deterministic given a position: a delta-hedger short gamma must buy
as price rises. The scale precondition is documented in `CL-2026-04` — 0DTE options are a majority
of SPX volume, and Cboe's own research addresses their market impact. Leveraged-ETF rebalancing has
a known, publicly computable mechanical form. Index reconstitution dates and closing-auction
imbalances are published.

**Falsifier.** No dose-response: if the behavior attributed to gamma hedging shows no relationship
to strike concentration or to distance from strikes, the mechanism is not what is producing it. If a
plain realized-volatility control fully explains the effect, the same conclusion follows.

**Critical caveat, stated once and applied everywhere:** **dealer positioning is never observed.**
Open interest does not disclose which side of it is dealer-held. Every GEX-style estimate embeds a
sign model — usually a heuristic about which strikes retail buys and which institutions sell. ALAT
may condition on such an estimate only with an explicit uncertainty band and a test of whether the
*sign model* rather than the *mechanism* is generating the result.

**If false:** H3 dies. The rest of ALAT survives.

---

## A6 — Liquidity regimes are persistent

**Statement.** Spread, depth, impact coefficient, and trade intensity cluster in time; the current
value is informative about the near-future value.

**Support.** Volatility clustering is among the most robust facts in empirical finance, and
liquidity co-moves with volatility (Hasbrouck–Seppi on common factors in liquidity;
Chordia–Roll–Subrahmanyam on commonality). Intraday periodicity in volume, spread and volatility
is likewise long-documented.

**Falsifier.** Rolling estimates of these quantities showing no autocorrelation beyond a
deterministic time-of-day pattern. **This distinction matters enormously:** if all apparent
persistence is time-of-day seasonality, then "regime detection" is just a clock, and every regime
rule must be replaced by a time-of-day dummy — which is far more honest and far less impressive.

**If false, or if it reduces to seasonality:** the regime module reduces to a session table, and
every claimed regime-conditional edge must be re-tested against a time-of-day-only control.

---

## A7 — Information and liquidity arrive in event time, not clock time

**Statement.** The natural clock of the auction is activity — trades, volume, imbalance — not
seconds. Fixed-interval sampling mixes high- and low-information periods and distorts the
distribution of returns.

**Support.** The subordinated-process literature (Clark; Ané–Geman) shows returns sampled in
transaction/volume time are closer to normal and more statistically tractable. Event-based bar
construction (tick, volume, dollar, imbalance bars, as popularized by López de Prado) is the applied
form.

**Falsifier.** Volume- or dollar-bar returns showing no improvement in normality, no reduction in
serial correlation, and no improvement in signal stability relative to time bars on the same data.
This is directly measurable and cheap.

**Trap.** Bar construction is a classic leakage vector: a bar boundary defined by a volume threshold
means **the bar's own closing time depends on future volume.** Every feature must be computed from
information available strictly before the decision point, never "as of bar close" when bar close was
determined by data after the decision. See `docs/07-experiment-protocol.md` §FP-1.

**If false:** we sample in clock time, everything else is unchanged, and the framework is simpler.

---

## A8 — Cross-asset relationships transmit *state* on tradable horizons, even though *price* is arbitraged instantly

**Statement.** ES→SPY→constituents price lead-lag operates on latency scales closed to us, but
liquidity *conditions* (spread widening, depth withdrawal, elevated impact) propagate and persist
long enough to be informative.

**Support.** Price discovery concentration in index futures is a long-standing empirical result
(Hasbrouck's information-share work). Commonality in liquidity across assets is separately
documented. The conjunction — that the *conditions* propagate more slowly than the *prices* — is
plausible but is **ALAT's own conjecture and is untested.**

**Falsifier.** Liquidity-state variables in the lead instrument showing no incremental predictive
power for the follower's liquidity state beyond the follower's own history.

**Trap.** Cross-venue timestamp alignment. Apparent lead-lag is very often a feed-latency artifact.
Any cross-market result must be re-tested with deliberately degraded timestamp precision; if the
effect requires sub-millisecond alignment to appear, it is not tradable and quite possibly not real.

**If false:** the cross-market module is dropped. ALAT becomes single-instrument, which is a
cleaner research program anyway.

---

## A9 — Transaction costs are a first-order term

**Statement.** At intraday horizons, expected gross edge per trade is of the same order of magnitude
as spread + fees + slippage + impact. Costs cannot be treated as a haircut applied at the end.

**Support.** Arithmetic. On ES, one tick is $12.50 per contract; crossing the spread costs a tick
plus fees. A strategy targeting a few ticks gross gives up a large fraction of that to entry and
exit. On tick-constrained equities the same logic applies with the spread pinned at the minimum
increment — and `CL-2026-01` will change that arithmetic discontinuously.

**Falsifier.** None needed; this is arithmetic, not a hypothesis. What *is* testable is whether a
given cost model is accurate — which requires live execution data (Level 7).

**Consequence for method.** Cost assumptions are declared *before* results are computed, and every
result is reported at three cost levels: assumed, 1.5×, and 2×. **A result that survives only at the
assumed cost level is reported as failed.**

---

## A10 — Edges are perishable, and decay is measurable

**Statement.** Any exploitable regularity attracts capital and decays. The rate of decay is itself
an observable.

**Support.** The published-anomaly decay literature in cross-sectional equities (McLean–Pontiff)
establishes the phenomenon in a domain where it can be measured cleanly. In microstructure the
mechanism is faster and more direct: a profitable liquidity-taking pattern raises the adverse
selection cost of the counterparties who are being taken, and they re-price.

**Falsifier.** A microstructure edge showing stable magnitude over many years and across
participation levels. (Note: *risk-premium* edges — being paid to bear inventory risk — need not
decay the same way. Distinguishing "decayed" from "risk got smaller" is genuinely hard and is an
open problem for this program.)

**Consequence for method.** Every accepted rule carries a **monitoring statistic** and a
pre-declared deterioration threshold. Walk-forward testing is not a validation ritual — it is the
only design that can detect decay at all.

---

## Summary: dependency map

| If this fails… | …these die |
|---|---|
| A1 | Everything |
| A2 | RPH, H1, H2, H3 — the entire framework |
| A3 | `RRI`, `CIR`, H1 (naïve book imbalance would suffice) |
| A4 | G2-based setups; absorption-as-metaorder readings |
| A5 | H3 only |
| A6 | Regime module → reduces to a time-of-day table |
| A7 | Event-time sampling → revert to clock bars; framework otherwise intact |
| A8 | Cross-market module only |
| A9 | Not falsifiable — it is arithmetic |
| A10 | Would be good news; changes monitoring, not method |

**Read the map before celebrating any result.** Two assumptions (A1, A2) carry the whole structure,
and only one of them (A2) is genuinely uncertain.
