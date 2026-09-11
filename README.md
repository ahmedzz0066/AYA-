# Volume Footprint — reconstructed from first principles

A volume footprint built from OHLCV alone, derived rather than copied. Ships as a
**TradingView Pine v6 indicator** and a **dependency-free Python reference
implementation** with a test suite that checks the derivation, not just the code.

Inspired by [Volume Footprint: Measuring by Math & Geometry][tv]. The source of
that script is not publicly retrievable, so nothing here is a transcription — the
model was re-derived from its stated premise (reconstruct order flow from bar
geometry) and the two differ in substance; see [What is different](#what-is-different-and-why).

[tv]: https://www.tradingview.com/script/Tm1cGCPD-Volume-Footprint-Measuring-by-Math-Geometry/

## The problem

A footprint needs bid and ask volume at every price level inside a bar — `2N`
unknowns. An OHLCV bar gives five numbers. **The reconstruction is
underdetermined**, and any implementation that hides that fact is selling a prior
dressed up as a measurement.

So this one states its assumptions out loud, and derives everything else:

| | Assumption | Why it holds |
|---|---|---|
| **A1** | Price is continuous — it visited every level between the extremes it touched. | True at tick resolution for any traded instrument. |
| **A2** | Volume accrues in proportion to distance travelled, `dV ∝ \|dp\|`. | Each tick of movement consumes the resting size at that level. |
| **A3** | Upward travel is buy-initiated, downward travel is sell-initiated. | Price rises only when aggressors lift offers. This *is* the bid/ask split. |

## What follows from them

**Two path hypotheses.** By A1 price started at `O`, ended at `C`, and touched
both extremes. The shortest such journeys are `O→H→L→C` and `O→L→H→C`, with
lengths `2R + Δ` and `2R − Δ` (`R` the range, `Δ` the body). They are weighted by
`length^−α` — a path demanding more volume for the same `V` is a worse
explanation of the bar. `α = 1` is the default.

**The bid/ask split, for free.** Summing leg lengths by direction gives, at
`α = 1`, a closed form in `x = Δ/R`:

```
buyShare = (4 + 2x − x²) / (8 − 2x²)        bounded to [1/6, 5/6]
```

The bounds are the point. Even a bar closing on its high had someone on the other
side of every print; a model reporting 100 % buying is describing price
direction, not order flow.

**The per-level distribution, with no bell curve.** A2 says volume per unit price
is constant along a monotone leg — so a leg *is* a uniform density. The buy
profile is the mixture of uniforms over up-legs, the sell profile over down-legs.
They therefore have **different shapes and different centres of mass**, which is
the whole reason the output is a footprint rather than a coloured volume bar.
Smoothing is an optional Gaussian *kernel* on top, and stays closed-form via
`Ψ(z) = z·Φ(z) + φ(z)`, an antiderivative of the normal CDF.

Full algebra, including why the overlap coefficient is identically `1.00` under a
shared-shape model: **[docs/DERIVATION.md](docs/DERIVATION.md)**.

## Output

```
              bar 1          bar 2          bar 3
------------------------------------------------------
  100.80                                  60 x 66
  100.70                                 105 x 135
  100.60                                 114 x 197   │
  100.50                                  94 x 234  ↑│
  100.40                                  77 x 248  ↑│
  100.30                                  75 x 249   │
  100.20   108 x 108                      91 x 240   │
  100.10   206 x 212   │  176 x 329   │  125 x 218   ◄
  100.00   205 x 244   ◄  204 x 435  ↑◄  150 x 187   │
   99.90   211 x 238   │   99 x 102      134 x 141
   99.80   197 x 199   │                  79 x 79
   99.70    83 x 83
------------------------------------------------------
   delta       +73           +387           +890
     vol      2.1k           1.3k           3.1k
    tilt      +3.5%         +28.8%         +28.7%
     OVL      0.97           0.91           0.82
```

`sell x buy` per level, `◄` point of control, `│` value area, `↑↓` diagonal
imbalance. Falling `OVL` across the three bars shows buyers and sellers
separating by price — the signature of an initiative move, and a reading a
shared-shape model cannot produce.

## Quickstart

**TradingView** — paste [`pine/volume_footprint.pine`](pine/volume_footprint.pine)
into the Pine Editor and add to chart. No external dependencies; works on any
plan, since the default engine needs only OHLCV.

**Python** — no third-party packages required.

```bash
cd python
python3 demo.py --bars 5 --row-size 0.1 --concentration 8
python3 demo.py --engine close          # contrast with the naive split
python3 -m unittest discover -s tests -v
```

```python
from vfootprint import Bar, FootprintConfig, build_profile

cfg  = FootprintConfig(row_size=0.25, concentration=6.0)
prof = build_profile(Bar(o=100.0, h=102.3, l=99.1, c=101.7, v=5000), cfg)

prof.delta, prof.tilt_pct, prof.ovl      # -> 1428.9, 28.6, 0.86
prof.poc.price_low                       # -> 100.0, the modal price level
prof.stacked_imbalances(min_run=3)       # runs of same-side diagonal imbalances
prof.residual_ppm                        # -> 0.0, conservation check
```

## Engines

| Engine | Needs | Split |
|---|---|---|
| **`path`** (default) | OHLCV only | The derived least-action model above. |
| **`close`** | OHLCV only | The textbook `(C−L)/(H−L)`. Included for contrast: it saturates at 0 and 1, so it systematically overstates delta on trend bars. |
| **`ltf`** | Lower-timeframe data | A *measurement*, not a model. Each sub-bar contributes its own split to its own price levels, so the reconstruction degrades into the truth as the sub-timeframe shrinks. |

Row shapes always come from the leg mixture; an engine only sets the totals.

## Settings

| Setting | Default | What it does |
|---|---|---|
| Split engine | `path` | See above. |
| Least-action exponent `α` | `1.0` | Path weighting. `0` = both paths equally likely; large = commit to the shorter one. |
| Ticks per row | `4` | Row height. Rows are anchored to an **absolute** price grid, not to each bar's low — without that, columns don't line up and diagonal comparisons are meaningless. |
| Window bars | `5` | Columns drawn. |
| Volume concentration `κ` | `6.0` | Kernel bandwidth `σ = R/κ`. Not the distribution's shape — the legs supply that — but how much we distrust the three-leg approximation. |
| Max rows per bar | `40` | Safety cap; the row size widens rather than exceeding TradingView's 500-drawing budget. |
| Value area % | `70` | Convention from market profile, not derived. |
| Imbalance ratio | `3.0` | Diagonal dominance: `buy[k] > θ · sell[k−1]`. |
| Stacked run | `3` | Consecutive imbalances before an alert fires. A single one is noise. |
| Balance tilt % | `5.0` | Below this the bar reads "balanced" rather than being given a spurious direction. |
| Residual tolerance | `1 ppm` | Volume conservation is exact by construction, so this only catches float error. |

## What is different, and why

Beyond being an independent derivation, three substantive choices differ from the
description of the original:

- **The split is derived, not asserted.** `(C−L)/(H−L)` is a plausible-looking
  ratio with no mechanism behind it. Weighting explicit price paths by least
  action produces a split with a stated model, and the `[1/6, 5/6]` bounds fall
  out rather than being clamped in. The naive formula is still available as the
  `close` engine so the two can be compared directly.
- **Buy and sell get different shapes.** Distributing one shared Gaussian and
  colouring it by a bar-level ratio gives every row the same buy/sell proportion
  — so every diagonal imbalance fires or none does, and `OVL` is pinned at
  `1.00`. Deriving each side from its own legs is what makes those metrics mean
  anything.
- **The Gaussian is a kernel, not the model.** The profile's shape comes from the
  leg geometry; smoothing only expresses uncertainty about the path. That is why
  the sane default here (`κ ≈ 6`) is tighter than for a model where the bell
  curve must be wide enough to *be* the distribution.

## What this cannot do

- **It cannot see absorption that left no price trace.** A thousand contracts
  filled at one level with no movement is invisible to A2. That is the model's
  blind spot, and exactly where real exchange footprint data earns its cost.
- It cannot distinguish one large aggressor from many small ones.
- Its diagonal imbalances reflect *modelled* geometry, not observed order flow —
  a hypothesis generator, not a confirmation.

Used as a lens on bar geometry it is rigorous and self-consistent. Used as a
substitute for tick data it will mislead you. The `ltf` engine exists to narrow
that gap.

## Layout

```
docs/DERIVATION.md              the algebra, start to finish
pine/volume_footprint.pine      TradingView Pine v6 indicator
python/vfootprint/core.py       the model: legs, split, rows, metrics
python/vfootprint/render.py     terminal footprint / profile / dashboard
python/demo.py                  runnable synthetic example
python/tests/test_core.py       property tests of the derivation
python/tests/test_pine_parity.py    Pine and Python kept in step
```

The parity suite re-implements the Pine's hand-rolled `erf` (Pine has no `math.erf`)
and checks the full pipeline agrees with the reference to within `1e-6` of bar
volume, then reads the leg table and input defaults straight out of the `.pine`
source so the two ports cannot silently drift.

## Licence

MPL-2.0, matching TradingView's house licence for open-source scripts.
