# ALAT — Adaptive Liquidity Auction Theory

A first-principles research program attempting to determine whether a **durable, executable,
statistically defensible intraday edge** exists in modern electronic markets — and if so, to
describe it in falsifiable terms.

This repository is a **research log**, not a trading system and not a course. Nothing here has
been backtested. Nothing here should be traded.

## Current status

| | |
|---|---|
| Version | **ALAT v0.1** |
| Highest proof level reached | **LEVEL 1 — Logically coherent** |
| Empirical support | **None. No data has been touched.** |
| Live capital justified | **No** |

## Proof standard

Every claim in this repository carries an explicit level. A claim may only be described at the
highest level it has *actually* reached.

| Level | Meaning |
|---|---|
| 0 | Hypothesis — stated, not yet checked for internal coherence |
| 1 | Logically coherent — mechanism is plausible, math is well-defined, causally consistent |
| 2 | Supported by exploratory data |
| 3 | Supported out-of-sample |
| 4 | Supported by walk-forward testing |
| 5 | Survived multiple regimes and instruments |
| 6 | Forward-tested prospectively |
| 7 | Live evidence after costs |

Logical coherence is **not** evidence of profitable expectancy. Levels 0–1 are cheap; everything
expensive lives at 2+.

Where data is required and absent, the text says so in the form:
`UNTESTED HYPOTHESIS — DATA REQUIRED.`

## Contents

| File | Purpose |
|---|---|
| [`docs/00-session-context.md`](docs/00-session-context.md) | Live market context + **MARKET STRUCTURE CHANGELOG** |
| [`docs/01-theory.md`](docs/01-theory.md) | What actually moves intraday price in a 2026 electronic auction |
| [`docs/02-assumptions.md`](docs/02-assumptions.md) | Ten load-bearing assumptions, their support, and their falsifiers |
| [`docs/03-cycle.md`](docs/03-cycle.md) | The Depletion–Repair Cycle — proposed replacement for Wyckoff phases |
| [`docs/04-state-variables.md`](docs/04-state-variables.md) | Seven measurable state variables + derived regime classifier |
| [`docs/05-hypotheses.md`](docs/05-hypotheses.md) | Three original candidate hypotheses with formal definitions |
| [`docs/06-data-requirements.md`](docs/06-data-requirements.md) | Exact data needed to test them |
| [`docs/07-experiment-protocol.md`](docs/07-experiment-protocol.md) | Backtest protocol, false-positive catalogue, kill criteria |
| [`docs/08-alat-v0.1.md`](docs/08-alat-v0.1.md) | The v0.1 version block and the open question |
| [`docs/99-hypothesis-graveyard.md`](docs/99-hypothesis-graveyard.md) | Ideas that died, and why |
| [`preregistration/TEMPLATE.md`](preregistration/TEMPLATE.md) | Pre-registration form — commit **before** touching test data |

## Rules of this repository

1. **No fabricated data.** No invented backtests, no invented order-flow examples, no
   illustrative-but-fake statistics. If a number is not from a cited source or a real computation,
   it does not appear.
2. **Version history is append-only.** Past version documents are never edited to look smarter.
   Corrections are made forward, in a new version, with the reason recorded.
3. **Every rule must survive The Destroyer** (the adversarial-review section in each hypothesis)
   before it enters the methodology.
4. **A rule that only works at one exact parameter value is presumed overfit.**
5. **Costs are part of the hypothesis, not an afterthought.**
