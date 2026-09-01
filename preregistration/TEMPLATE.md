# Pre-Registration — <hypothesis id> — <date>

**Commit this file BEFORE touching the validation or holdout partition.**
The git commit hash and timestamp are the proof of precedence. A specification that was not
committed in advance is exploratory by definition, and must be reported as exploratory no matter how
good the result looks.

---

## 1. Hypothesis
**ID:**
**Statement (one sentence, directional):**
**Causal mechanism (which generator G1–G6, and why):**
**Theory reference:**

## 2. Prediction — stated before any test-partition data is examined
**Primary predicted relationship (with sign):**
**Required dose-response / monotonicity:**
**Predicted effect size (or "no prior"):**
**What result would surprise me:**

## 3. Data
**Instrument(s):**
**Feed and tier:**
**Date range — exploratory / validation / holdout:**
**Known data quality issues:**

## 4. Features — exact definitions
| Feature | Formula reference | Window | Normalization | Decision lag δ |
|---|---|---|---|---|

**Shuffled-future leakage unit test passed:** ☐ yes (commit hash: ______)

## 5. Parameter grid — declare the FULL grid
| Parameter | Values to be tried |
|---|---|

**Total trial count $N$ = ______**
*(This number goes directly into the Deflated Sharpe calculation. Understating it invalidates the
result. Include every value you will actually try, including ones you expect to discard.)*

## 6. Primary statistic
**The single number that decides the outcome:**
**Baseline it is measured incrementally against:**
**Secondary statistics (reported, not decisive):**

## 7. Baselines
☐ Matched random entry ☐ Static book imbalance ☐ Realized-vol conditioning
☐ Time-of-day only ☐ ORB ☐ VWAP reversion ☐ Simple momentum / mean reversion

## 8. Cost model
**Fees:** **Spread assumption:** **Slippage model:**
**Impact model:** **Passive fill rule:** ☐ trade-through ☐ MBO queue tracking
**Reported at:** ☐ 1.0× ☐ 1.5× ☐ 2.0×

## 9. Kill criteria — specific and numeric
1.
2.
3.
**Universal criteria from `docs/07-experiment-protocol.md` §C.1 also apply:** ☐ acknowledged

## 10. Analyses NOT permitted without a new pre-registration
- Adding a filter after seeing results
- Changing the horizon after seeing results
- Changing the primary statistic
- Reporting a subgroup that was not pre-specified

## 11. Sign-off
**Researcher:** **Date:** **Commit hash of this file:**
**Holdout partition untouched as of this commit:** ☐ confirmed
