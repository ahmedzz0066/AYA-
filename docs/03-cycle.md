# 03 — The Depletion–Repair Cycle (DRC)

> A proposed replacement for Accumulation → Markup → Distribution → Markdown.
> **Proof level: 0–1.** The state definitions are computable (Level 1); the transition structure is
> a hypothesis with no measured probabilities (Level 0). **All transition probabilities below are
> written as symbols, never as numbers, because no number has been measured.**

---

## 3.1 Why the classical cycle is the wrong shape

The Wyckoff cycle has three structural properties that do not survive contact with a 2026 intraday
auction:

1. **It is linear and closed.** Four phases in fixed order. Intraday markets skip states routinely —
   an equilibrium can be shattered by a macro print with no intervening "accumulation" whatsoever.
2. **Its states are defined by price shape.** But price shape is the *output* of the mechanism
   (§1.1), and the same shape is produced by different mechanisms with different forward
   distributions. Classifying on the output discards the discriminating information.
3. **Its timescale is a campaign.** It was designed for position-building over days to weeks by a
   large operator. Compressing it onto a 5-minute chart is an unjustified analogy, not a derivation.

The DRC is designed to fix all three: it is a **graph, not a ring**; its states are defined by
**liquidity conditions, not price shapes**; and it is indexed in **event time**, so it runs at
whatever speed the market is actually running.

---

## 3.2 The eight states

The cycle is named for what it actually describes: liquidity gets **depleted**, and then it gets
**repaired** — either at a new price (the market has moved) or at the old one (the move failed).
Everything else is detail.

Each state is defined by conditions on the seven state variables of `docs/04-state-variables.md`.
The thresholds are deliberately written as quantiles of the instrument's own recent distribution,
never as absolute numbers — absolute thresholds are the signature of overfitting and they break at
every structural change (`CL-2026-01`).

---

### D0 — Provisioned Equilibrium
**Condition:** $\hat\lambda$ at or below its rolling median; `RRI` high and symmetric; `LSI` low;
`|OFI|` unremarkable; spread at the modal value.
**Economics:** providers are quoting two-sided with inventory near their target. Flow is absorbed
without displacement. Adverse selection is perceived as low.
**Observable:** price oscillates within a band; depletion events at the touch are followed by prompt
restoration at the *same* price.
**Trading implication:** this is the state in which *taking* liquidity is most expensive relative to
the move you get. Most intraday losses are made here by traders who mistake noise for structure.

### D1 — Inventory Loading
**Condition:** persistent same-sign `OFI` **without** commensurate displacement; `RRI` still high on
the absorbing side; $\hat\lambda$ flat or falling.
**Economics:** either a metaorder is being filled passively (G2) or a provider is accumulating
inventory involuntarily (G1). **These have opposite forward implications and are not yet
distinguishable.** That ambiguity is the honest content of this state.
**Observable:** high volume, low range, one-sided aggression, repeated restoration at one price.
**Trading implication:** **no directional trade is justified in D1.** This state's value is that it
is a precondition — the resolution out of D1 is informative, D1 itself is not.

### D2 — Resilience Erosion  ← *the state classical charting cannot see*
**Condition:** `RRI` falling on one side; `CIR` rising (cancellations replacing trades as the
depletion channel); depth-weighted asymmetry growing; **price has not yet moved.**
**Economics:** providers are stepping back — reducing size, widening, or pulling entirely — because
their inventory, their adverse-selection estimate, or their volatility forecast has changed.
**Observable:** on a candlestick chart, *nothing*. This is the specific claim to ALAT's novelty and
the specific reason order-level data is required.
**Trading implication:** this is the highest-value state in the cycle **if it is real**. It is the
substance of hypothesis **H1**.

### D3 — Depletion Event
**Condition:** touch queue exhausted; price moves through one or more levels; $\hat\lambda$ spikes;
`LSI` spikes; trade intensity spikes.
**Economics:** flow arrives against a book that cannot absorb it. The trigger may be informational
(G4), structural (G5 — stops), or simply the first ordinary order to arrive after supply degraded.
**Observable:** the visible "breakout." By the time it is visible it is largely over.
**Trading implication:** chasing here is buying at the worst point of the impact curve. The
tradeable question is not D3 but what follows it.

### D4 — Repricing Search
**Condition:** elevated $\hat\lambda$; wide spread; low, unstable depth; `AAS` near zero (neither
acceptance nor rejection established); high revisit rate.
**Economics:** the market is searching for the price at which liquidity supply returns. Providers
quote defensively and re-price rapidly.
**Observable:** fast, erratic movement on thin volume; poor fills; large realized slippage.
**Trading implication:** **execution quality is at its worst here.** Many "great signals" in D4 are
unprofitable purely on slippage. The cost model, not the signal, decides.

### D5 — Repair
The cycle's fork. Two mutually exclusive outcomes:

- **D5a — Repair at the new level (Acceptance).** `RRI` recovers *at the new price*; `AAS` rises
  positive; $\hat\lambda$ normalizes; volume builds at the new level. The market has re-anchored.
  Forward behavior resembles a new D0/D1 at the new price.
- **D5b — Repair at the old level (Rejection / Failed Displacement).** Liquidity returns at the
  *pre-displacement* price; `AAS` at the new level stays negative; price retraces through the
  displacement. This is the mechanism underlying what Wyckoff called a spring or upthrust — with no
  operator required. It is simply: **supply was never actually gone, only temporarily withdrawn.**

**Trading implication:** the D5a/D5b fork is the single most consequential transition in the cycle,
and it is resolvable with causally-available data — you can observe *where* replenishment returns
without knowing where price goes next.

### D6 — Hedge Feedback
**Condition:** displacement has occurred, and mandated flows (G3) now respond to it.
**Economics:** dealers, APs, and rebalancing vehicles trade as a function of the *realized* move.
Long-dealer-gamma conditions damp continuation; short gamma amplifies it.
**Observable:** conditional on estimated positioning — and that estimate is unreliable (`A5`).
**Trading implication:** this state does not generate trades on its own. It **modulates** the
expected continuation of every other state. It is the substance of hypothesis **H3**, and it is the
most likely source of a spurious result in this entire framework.

### D7 — Re-provisioning
**Condition:** inventory unwound; `RRI` restored and symmetric; $\hat\lambda$ back to baseline;
`LSI` normalized.
**Economics:** providers have flattened, re-widened their comfort, and are quoting two-sided again.
**Observable:** volatility contracts, spread returns to modal, depth rebuilds.
**Outcome:** the market re-enters D0 — possibly at a new price, possibly at the old one.

---

## 3.3 The transition structure

The DRC is a graph with skips, not a ring. The transitions ALAT claims are *possible* — with
probabilities to be estimated, **never assumed**:

```
                 ┌──────────────────────────────── D7 ◄───────────────┐
                 ▼                                                    │
   ┌──►  D0 ──► D1 ──► D2 ──► D3 ──► D4 ──┬──► D5a ──► D6 ──► D7 ─────┘
   │      │             ▲       ▲         │
   │      │             │       │         └──► D5b ──► D6 ──► D7 ──► D0
   │      └─────────────┘       │
   │                            │
   └──────── D0 ────────────────┘   (G4 shock: D0 → D3 directly, no D1/D2)
```

**Transitions to estimate (as conditional probabilities in event time, with confidence intervals):**

| Quantity | Question it answers | Why it matters |
|---|---|---|
| $P(D3 \mid D2)$ | Does resilience erosion actually precede displacement? | **The core test of H1.** If erosion does not predict depletion, D2 is not a state, it is noise. |
| $P(D3 \mid D2^c)$ | Base rate of displacement without prior erosion | Without this, $P(D3\mid D2)$ is meaningless. **The base rate is the entire test.** |
| $P(D5a \mid D3, D4)$ | Does displacement stick? | Determines whether continuation trades have positive expectancy at all |
| $P(D5b \mid D3, D4)$ | Does displacement fail? | The failed-displacement family of setups |
| $P(D5a \mid D3, D4, \text{HFP} > 0)$ vs $P(D5a \mid D3, D4, \text{HFP} < 0)$ | Does hedging feedback modulate acceptance? | **The core test of H3**, as a *difference*, not a level |
| $P(D1 \to D3 \text{ in direction of the absorbing side})$ | Was D1 a metaorder or a trapped maker? | Resolves the D1 ambiguity — the answer determines whether D1 is ever tradable |

**Method for estimating these:** they must be estimated as *conditional frequencies with confidence
intervals on out-of-sample data*, not as parameters fitted to make a strategy profitable. A
transition probability that was tuned is not a probability.

**Discipline rule:** a state must be assigned using only information available at the moment of
assignment. It is trivially easy to label D5b after seeing the retrace — and completely worthless.
Every state label in this framework must be produced by a **causal classifier** that could have run
in real time, and the backtest must use the classifier's live output, not a post-hoc label.

---

## 3.4 Mapping classical concepts onto the DRC

Not to validate Wyckoff, but to show the classical vocabulary is a *lossy projection* of the
liquidity state onto price shape — and to make clear exactly what is lost.

| Classical term | DRC reading | What the classical term discards |
|---|---|---|
| Accumulation | D1 with unresolved ambiguity | Whether it is a metaorder (G2) or a trapped maker (G1) — which have opposite outcomes |
| Spring / shakeout | D3 → D4 → **D5b** | Whether supply actually left or was withdrawn and returned |
| Upthrust | Same, inverted | Same |
| Effort vs. result | The $\hat\lambda$ / `PRE` measurement | Any quantification; "effort" and "result" were never scaled |
| Sign of strength | D3 → **D5a** with fast `RRI` recovery at the new level | The distinction between acceptance and momentum-that-fails |
| Markup | Repeated D0→D3→D5a chains in one direction | Whether the driver is G2, G3, or G5 — which determines whether it continues |
| Distribution | D1 at the top of a range | Same ambiguity as accumulation |
| Composite operator | **Deleted.** Replaced by G1–G6 with an alternative-explanation table | An unfalsifiable narrative |

---

## 3.5 Session architecture — event-time, configurable, not constant

Time-of-day matters (`A6`), but the classical session map is **already obsolete** and about to
become more so (`CL-2026-02`). Session boundaries are therefore **configuration**, and any
session-conditional statistic must be re-estimated when the configuration changes.

For **ES**, a working partition (to be validated by clustering the state variables, not asserted):

| Session | ET | Distinguishing microstructure hypothesis |
|---|---|---|
| Asia | 18:00–02:00 | Thin book, wide effective spread, high `LSI` baseline |
| Europe | 02:00–07:00 | Depth rebuilds; European macro |
| Pre-US | 07:00–09:30 | Macro prints; positioning ahead of cash open |
| Cash open | 09:30–10:30 | Maximum activity; highest $\hat\lambda$ variance; ETF/futures arbitrage most active |
| Morning discovery | 10:30–12:00 | Trend resolution or reversion |
| Midday | 12:00–14:00 | Lowest volume; **hypothesis: highest `RRI`, lowest $\hat\lambda$** |
| Afternoon | 14:00–15:30 | Repricing; FOMC days diverge sharply |
| Close | 15:30–16:15 | Closing auction pressure, leveraged-ETF and index rebalancing (G3) |
| Post | 16:15–18:00 | Thin; earnings |

**Mandatory rule:** no setup may be reported as validated without a per-session expectancy
breakdown. A strategy whose entire edge lives in one session is not a strategy with a regime filter
— it is a strategy with one-ninth of the sample size, and its statistics must be computed on that
smaller sample.

**Standing warning (`CL-2026-02`):** if near-24-hour equity trading launches as scheduled in
December 2026, the equity session map above breaks, the opening auction's role changes, and *every
session-conditional statistic estimated on pre-2026 data must be re-estimated.* Do not pool across
that boundary.

---

## 3.6 Chapter conclusions

1. The DRC is a graph of **liquidity states**, not a ring of price shapes. Skips are normal.
2. **D2 (Resilience Erosion) is the framework's distinctive claim** — a pre-displacement state
   invisible to price-based analysis. If D2 has no predictive content, ALAT offers nothing that
   order-book-imbalance methods do not already offer.
3. **The D5a/D5b fork** (acceptance vs. rejection of the new price) is the highest-value transition,
   and it is resolvable with causally-available data.
4. Every transition probability in this document is currently a **symbol with no measured value**.
   `UNTESTED HYPOTHESIS — DATA REQUIRED.`
5. State labels must come from a causal classifier. Post-hoc labeling would make every result in
   this framework meaningless, and it is the easiest possible mistake to make.

## Research questions arising

- **RQ-5.** Do the eight states emerge from unsupervised clustering of the state variables, or are
  they an imposed narrative? *Test: cluster the state-variable vector and compare the empirical
  partition with the proposed one. If the data prefers three states, use three.*
- **RQ-6.** Is $P(D3 \mid D2)$ meaningfully greater than the base rate $P(D3)$, at a horizon long
  enough to act on and after controlling for realized volatility?
- **RQ-7.** Does the D1 ambiguity resolve? Is there any causally-available feature that separates
  "metaorder absorbing" from "market maker trapped"?
