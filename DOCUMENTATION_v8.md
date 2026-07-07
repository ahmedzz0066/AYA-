# VolSD v8 — Self-Learning Edition

> The v6 base→impulse engine upgraded from an indicator that **asserts** ("this zone
> is 7/10") into a system that **learns and proves** ("this zone is P:72%, and zones
> like it historically bounced 68% of the time, n=23").

Implementation: [`VolSD_v8_SelfLearning.pine`](./VolSD_v8_SelfLearning.pine).

---

## 1. What is fundamentally new

### 1.1 Online-learning weights (logistic regression, SGD)

v6/v7 scored zones with a *fixed* weighted mean — the weights were educated guesses.
v8 replaces the static score with a **probability model that trains itself on the
chart it is running on**:

- At creation, every zone stores a normalized **feature vector** `x ∈ [0,1]⁷`:

  | # | Feature | Definition |
  |---|---|---|
  | 0 | `vol`  | volume percentile of the impulse bar |
  | 1 | `imp`  | impulse range / ATR (normalized) |
  | 2 | `dlt`  | **true intrabar delta** (LTF), fallback CLV |
  | 3 | `wid`  | width efficiency (tight = 1) |
  | 4 | `htf`  | HTF trend agreement (0/1, 0.5 if disabled) |
  | 5 | `hvn`  | zone overlaps profile Value Area (0/1) |
  | 6 | `rvol` | session-relative volume (time-of-day adjusted) |

- Predicted probability: `P(bounce) = σ(b + w·x)` with `σ` the logistic function.
- **Label:** a zone that was *tested* (touched) and then moved `reactMult × ATR₀`
  away from its proximal edge resolves as a **bounce (y=1)**; a zone that is broken
  (mitigated) after being tested resolves as a **break (y=0)**. Untested zones never
  produce labels — we model `P(bounce | tested)`, which is the only question a trader
  actually asks.
- **Update (one SGD step per resolved zone):**

  ```
  p  = σ(b + w·x)
  w ← clamp(w + η·(y − p)·x)        # η = learning rate input
  b ← clamp(b + η·(y − p))
  ```

**Why this is non-repainting:** the model trains *only on already-resolved past
zones*, and each zone's displayed `P` is computed with the weights known **at its
creation** and never recomputed. History is a strict walk-forward: what you see on
bar N used only information available at bar N.

**Cold start:** weights initialize to a uniform prior (`w=1, b=−2.5`), which behaves
like the v6 static score until enough zones resolve. The dashboard shows `n` resolved
so you always know how warmed-up the model is.

**Honest caveats (by design, stated, not hidden):**
- Learning state lives in runtime arrays → it **re-learns from bar 0 on every script
  reload** (Pine has no persistence). That is equivalent to re-running the same
  walk-forward — results are reproducible, not lost.
- Only zones above the display threshold `minProb` are created and therefore trained
  on. Set `minProb = 0` if you want the model to learn from *all* candidate zones
  (recommended while evaluating; raise it for trading).

### 1.2 Empirical probability memory (evidence, not opinion)

Every resolution is also tallied into **predicted-probability quintile buckets**
(0–20%, …, 80–100%). Each zone's label shows:

```
DEMAND P:72% | hist 68% (n=23)
```

- `P:72%` — the model's prediction for *this* zone.
- `hist 68% (n=23)` — the realized bounce rate of past zones whose prediction fell in
  the same bucket, with the sample size.

This doubles as a **live calibration check**: if `P:72%` zones historically bounce
~70%, the model is calibrated; if they bounce 50%, you can see the overconfidence
directly on the chart and distrust it — no backtest required.

### 1.3 Absorption-aware touch decay

v6 multiplied strength by a fixed factor per touch — blind to *what happened* during
the touch. v8 grades each retest:

| Touch profile | Interpretation | Multiplier |
|---|---|---|
| Shallow penetration (<50% of zone) + rejection close + volume z ≥ 1 | **DEFENDED** — sellers/buyers absorbed the attack | ×1.0 (no decay) |
| Rejection close, but deeper / low volume | partial defense | ×√decay |
| Neutral touch | consumption | ×decay |
| Deep penetration (≥ `penDeep` of zone height) | heavy consumption | ×decay² |

The 7-touch supply on your gold chart is the motivating example: fixed decay declared
it dead; the absorption model would instead tell you *whether it was defended each
time* — which is the actual tradable information.

### 1.4 Data-quality upgrades

- **True delta** via `request.security_lower_tf()`: signed intrabar volume from a
  lower timeframe (default 1m), `Δ = Σ sign(close−open)·vol / Σ vol ∈ [−1,1]`. Falls
  back automatically to the close-location proxy when the chart TF is too low or the
  option is off. The dashboard shows which source is active.
- **Session-relative volume:** volume is compared to a running mean **for the same
  hour of day** (24-slot table), so an Asia-session "spike" and a NY-open spike are
  judged against their own baselines. Non-intraday charts fall back to SMA-relative.
- **Volatility shock filter:** when the true-range z-score exceeds `shockZ` (default
  4σ — news candles), zone creation is suspended for `shockBars` bars. News candles
  create structurally fake zones; refusing to learn from them protects the model.
- **Adaptive volume gate:** the impulse volume test is a **z-score** (≥ 0.8σ by
  default), not a fixed multiple — self-calibrating across instruments.

---

## 2. Zone lifecycle (state machine)

```
CREATED (confirmed bar, base→impulse, P ≥ minProb, no shock, regime OK)
   │ stores feature vector x, P = σ(b + w·x) with current weights (frozen)
   ▼
ACTIVE ──touch──► graded (defended / consumed) → decayMult updated
   │                    │
   │                    └─ high-P + rejection candle + volume spike → ALERT
   │
   ├─ tested & moves reactMult×ATR₀ away  → RESOLVED-HELD  → learn(y=1), stays on chart
   ├─ closes/wicks through far edge        → MITIGATED      → learn(y=0 if tested), removed/greyed
   └─ evicted by per-side cap (oldest)     → discarded, unlabeled
```

Visuals: opacity ∝ `P · 0.5^(age/halfLife) · decayMult` (live conviction), POC line
(base VWAP), probability label, rolling profile POC/VAH/VAL + histogram, and a model
dashboard (regime, delta source, n resolved, overall bounce rate, current weights).

---

## 3. How to use it

1. **Let it warm up.** Load a symbol/TF with plenty of history; check the dashboard —
   `n` should reach a few dozen before you weight the probabilities heavily. Until
   then treat `P` like the old static score.
2. **Trade the calibrated tail.** Only take retests where `P ≥ ~65%` *and* the `hist`
   figure with decent `n` agrees. The built-in alert fires exactly there (retest +
   rejection candle + volume spike on a high-P zone).
3. **Read the weights.** The dashboard's weight row tells you what *this market*
   rewards (e.g. `dlt 1.6, htf 1.3, rvol 0.4` → delta and HTF agreement matter here;
   session volume doesn't). That is research output, not just decoration.
4. **Entries/stops/targets/risk:** unchanged from v6 doctrine — enter on the
   rejection close at the retest, stop beyond the far edge, targets = opposing
   zone / POC / VAH-VAL, risk ≤ 1% per trade, optionally size ∝ P.
5. **Evaluation mode:** set `minProb = 0` so the model trains on every candidate
   zone, run it over history, and read the bucket calibration off the labels — a
   built-in walk-forward study with zero exported data.

---

## 4. Validation

The bucket memory *is* the primary validation instrument: monotonically increasing
`hist` across probability buckets = the model ranks zones correctly; `hist ≈ P` =
calibrated. Beyond that, the v6/v7 protocol still applies (ablation per feature,
cross-market sweeps with identical settings, null controls vs. random levels).

## 5. Limitations

- No cross-session persistence of learned weights (Pine constraint) — re-learns
  deterministically from history on each load.
- One global model per chart; different regimes within one symbol share weights
  (the regime filter mitigates this).
- `P(bounce | tested)` is conditional — an untested zone's `P` is a prior, not a
  measured frequency, until zones like it resolve.
- LTF delta is subject to TradingView intrabar limits on very long histories; the
  script degrades gracefully to CLV.
