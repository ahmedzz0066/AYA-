# 99 — Hypothesis Graveyard

Ideas that were tested and failed, or were rejected before testing. **This file is the denominator
of the search.** Without it, the surviving hypotheses look far more impressive than they are, and
the Deflated Sharpe trial count is understated.

Append-only. Entries are never deleted. A killed idea may return only under the resurrection rule
(`docs/07-experiment-protocol.md` §C.4), at Level 0, with a fresh pre-registration.

## Entry format

```
### GY-nnn — <name>
Date killed:
Version killed under:
Statement:
Why it was plausible:
How it was tested (or why it was rejected pre-test):
What killed it (specific criterion from §C):
Would new evidence resurrect it? What evidence specifically?
```

---

## Pre-test rejections (recorded for trial-count honesty)

### GY-001 — Composite-operator attribution
**Date:** 2026-09-01 · **Version:** v0.1 · **Killed pre-test.**
**Statement:** Persistent one-sided pressure can be explained by a unified intelligent operator
accumulating or distributing.
**Why plausible:** it fits observed price paths and is intuitively satisfying.
**Why rejected without testing:** unfalsifiable. Any path can be retro-fitted with a story about
operator intent, and no observation can contradict it. Replaced by the explicit generator table
(G1–G6) with noise as the default (`docs/01-theory.md` §1.4).
**Resurrection:** would require a *direct observable* identifying a single coordinated actor —
e.g. verified participant-level data. Order-flow inference is not sufficient.

### GY-002 — Tick-counted displacement measures
**Date:** 2026-09-01 · **Version:** v0.1 · **Killed pre-test.**
**Statement:** Displacement, sweep depth, and stop distance measured in ticks.
**Why plausible:** ticks are the natural unit of the book and are simple to compute.
**Why rejected:** tick size is a regulatory parameter, not a market property. `CL-2026-01` halves it
for tick-constrained NMS stocks around Nov 2026, which would silently break every tick-counted
threshold and make pre- and post-boundary data non-comparable. Replaced by design rule R3:
all distances in $\sigma$ or spread units.
**Resurrection:** none foreseeable. This is a design rule, not an empirical question.

### GY-003 — Indicator-first setup construction
**Date:** 2026-09-01 · **Version:** v0.1 · **Killed pre-test.**
**Statement:** Use oscillator states (RSI, MACD, stochastics) as primary causal signals.
**Why plausible:** widely used; trivially computable; occasionally correlated with outcomes.
**Why rejected:** these are deterministic transforms of past prices. They cannot add information to
the price series — only discard some. They may compress price history *inside* a model; they may
never serve as a causal explanation for why price should move (`docs/01-theory.md`, prime directive).
**Resurrection:** none. If an oscillator adds incremental information over the raw price path in a
properly controlled test, the finding is about the price path, and should be stated that way.

---

*No post-test entries yet. No hypothesis has been tested.*
