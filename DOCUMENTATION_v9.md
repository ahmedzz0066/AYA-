# VolSD v9 — "Apex"

> v8 reviewed from first principles, flaws found, flaws fixed. Every v9 change below
> exists because v8 had a specific, articulable defect — not because more features
> are better.

Implementation: [`VolSD_v9_Apex.pine`](./VolSD_v9_Apex.pine).

---

## 1. The v8 review that produced v9

| # | v8 defect | Why it matters | v9 fix |
|---|---|---|---|
| 1 | **Selection-bias feedback loop.** Only zones with `P ≥ minProb` were created, so only those ever trained the model. | The model can never discover its false negatives — if the prior wrongly rejects a factor combination, no data ever arrives to correct it. This is the single worst flaw in v8. | **Shadow learning.** Every candidate zone is tracked internally (invisible, no drawings); all of them resolve and train the model. `minProb` filters *display only*. |
| 2 | **Binary labels.** Bounce = 1, break = 0. | A zone that ran 90% of target before breaking carries real information; treating it as a pure failure discards magnitude. | **Soft labels via MFE.** Each tested zone tracks its Maximum Favorable Excursion. Full target → `y = 1`. Broken after a partial run → `y = 0.5 · clamp(MFE/target)`, i.e. partial credit capped at 0.5 (a break is still mostly a failure). |
| 3 | **One model for two markets.** Trending and ranging regimes were blended into a single weight vector. | Delta and HTF agreement predict differently in trend vs range; averaging them mutes both. | **Dual experts.** Two independent weight vectors (RANGE / TREND) gated by ADX at zone creation; each zone trains the expert that was active when it formed. The dashboard shows the currently active expert's weights. |
| 4 | **n=1 learning.** Each resolved zone produced one SGD step and was discarded. | Slow convergence, high variance early on. | **Experience replay + L2.** A 128-slot circular buffer of past `(x, y, expert)` examples; each resolution triggers 1 fresh step + `k` replay steps with **deterministic** indexing (no `math.random` — reloads reproduce exactly). L2 weight decay prevents runaway weights. |
| 5 | **Probability without economics.** P(bounce) alone doesn't say whether a trade is worth taking. | A 70% zone with terrible geometry loses money; a 55% zone with 4R geometry prints. | **EV in R-multiples on every label:** `EV = (P·target − (1−P)·risk)/risk` with `risk = zone height + 0.1·ATR` and `target = reactMult·ATR` — the *same* target the model is trained on, so P and EV are consistent. Entry signals additionally require `EV ≥ minEV`. |
| 6 | **Zone quality ≠ entry quality.** v8 alerted on any rejection candle + volume spike. | The approach into the zone carries independent information the zone score can't. | **Graded entries (≥3 of 4):** exhaustion into the zone (true range below its 5-bar mean), rejection wick ≥50% of the candle, rejection close, volume spike. Passing entries print an ENTRY marker + alert; failing retests stay silent. |
| 7 | **Duplicate stacked zones.** Overlapping same-side zones were double-drawn and double-counted. | Redundant part. Best part is no part. | **Overlap dedup:** a candidate overlapping an active same-side zone ≥50% is skipped. |
| 8 | **No actionable threshold.** v8 showed calibration buckets but left the cutoff to eyeballing. | The data already contains the answer. | **Auto-threshold:** the dashboard derives the break-even probability from realized average zone geometry (`p_BE = 1/(1+RR)`) and reports the lowest calibration bucket that clears it with margin and `n ≥ 10`: e.g. `trade P ≥ 60% (BE 41%)`. |

Deleted relative to v8 (deliberately): the separate regime *creation filter* — the dual-expert
gate supersedes it (regime now routes learning instead of censoring data).

---

## 2. The learning system, precisely

**Features** (unchanged, normalized to [0,1]): volume percentile, impulse ratio,
true LTF delta (CLV fallback), width efficiency, HTF agreement, HVN/Value-Area
overlap, session-relative volume.

**Prediction** at zone creation, frozen forever (non-repainting):
```
e      = trending ? TREND : RANGE                # expert gate (ADX)
P      = σ(b_e + w_e · x)
```

**Labeling** (walk-forward only, tested zones only):
```
tested & MFE ≥ reactMult·ATR₀        → y = 1              (resolved: HELD)
tested & broken with partial MFE     → y = 0.5·min(1, MFE/target)
never tested                         → no label
```

**Update** per resolution:
```
one fresh SGD step on expert e:   w_e ← clamp(w_e + η(y−p)x − λw_e)
k replay steps over the buffer:   deterministic indices (seed = resolution count)
calibration bookkeeping:          quintile buckets of predicted p accumulate (n, Σy)
```

**Displayed per zone:** `DEMAND P:72% | hist 68% (n=23) | EV +0.8R | 2T`
— model prediction, realized rate of similar predictions, trade economics, touches.

---

## 3. How to use it

1. **Warm-up:** let the dashboard's `n` reach a few dozen. Shadow learning makes this
   faster than v8 (every candidate teaches, not just the pretty ones).
2. **Obey the auto-threshold row.** When it says `trade P ≥ 60% (BE 41%)`, that is the
   empirically justified cutoff for this symbol/TF — not a guess.
3. **Take only ENTRY-marked retests.** They already encode: high P, positive EV, and a
   graded approach (≥3 of 4 quality criteria). Stop beyond the zone's far edge;
   first target = `reactMult × ATR` (the exact event the probability refers to);
   runner to the opposing zone / profile POC.
4. **Risk:** ≤1% per trade; optionally size ∝ EV.
5. **Research mode:** the weight rows tell you what the current regime rewards on this
   market. Two regimes, two answers — that's the point.

## 4. Non-repaint & reproducibility

All v8 guarantees hold (confirmed bars, frozen per-zone P, `lookahead_off`, hoisted
`ta.*`, walk-forward-only learning). New in v9: replay uses deterministic indexing, so
a reload reproduces the identical learned state — no randomness anywhere.

## 5. Limitations

- Learned state still re-derives from history each reload (Pine has no persistence) —
  deterministic, so nothing is lost, but weights are per-chart-session.
- Soft-label cap of 0.5 for broken zones is a design choice (a break is mostly a
  failure); it is one input away from being tunable if evidence disagrees.
- Dual experts halve per-expert sample rates; on very short histories prefer one
  regime's signals only after its own `n` is meaningful.
- `P(bounce | tested)` remains conditional; untested zones carry a model prior.
