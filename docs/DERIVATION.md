# Reconstructing a Volume Footprint from OHLCV — a first-principles derivation

## 0. The problem, stated honestly

A real footprint chart needs, for every price level `p` inside a bar, two numbers:

- `ask[p]` — volume executed against the offer (buy-initiated / aggressive buyers)
- `bid[p]` — volume executed against the bid (sell-initiated / aggressive sellers)

That is `2N` unknowns for a bar spanning `N` price levels. An OHLCV bar gives us
**five** numbers: `O, H, L, C, V`. The reconstruction is therefore *massively
underdetermined* — there is no formula that recovers the true footprint, and any
implementation that claims otherwise is selling you a prior dressed up as a
measurement.

So the honest framing is: **choose the least-committal model consistent with the
five facts we have, and state the assumptions out loud.** Everything below is
derived from three assumptions, and nothing else:

| # | Assumption | Justification |
|---|---|---|
| **A1** | Price is continuous: it visited every level between the extremes it touched. | True for any traded instrument at tick resolution. |
| **A2** | Volume accrues in proportion to distance travelled: `dV ∝ |dp|`. | Each tick of price movement requires the resting size at that level to be consumed. |
| **A3** | Upward travel is buy-initiated, downward travel is sell-initiated. | Price only rises when aggressors lift offers, only falls when aggressors hit bids. This is the definition of the bid/ask split. |

A1–A3 are the whole model. The bid/ask split, the per-level distribution, the
delta, and the point of control all fall out of them without further inputs.

## 1. The two path hypotheses

By A1, price started at `O`, ended at `C`, and touched both `H` and `L`. The
shortest such journeys visit each extreme exactly once, giving exactly two
candidate paths:

```
Path A (up first):    O → H → L → C
Path B (down first):  O → L → H → C
```

Write `R = H − L` (the range) and `Δ = C − O` (the body). Decompose each path
into monotone **legs**, each with a price span and a length:

| Path | Leg | Span | Length | Direction (A3) |
|---|---|---|---|---|
| A | 1 | `[O, H]` | `H − O` | up → **buy** |
| A | 2 | `[L, H]` | `R`     | down → **sell** |
| A | 3 | `[L, C]` | `C − L` | up → **buy** |
| B | 1 | `[L, O]` | `O − L` | down → **sell** |
| B | 2 | `[L, H]` | `R`     | up → **buy** |
| B | 3 | `[C, H]` | `H − C` | down → **sell** |

Total path lengths collapse to a pleasingly simple form:

```
len(A) = (H−O) + R + (C−L) = 2R + Δ
len(B) = (O−L) + R + (H−C) = 2R − Δ
```

An up bar (`Δ > 0`) makes the *up-first* path the **longer** one — which is the
correct intuition: to close up having also printed the low, price that rallied
first had to come all the way back down and go up again.

## 2. Weighting the hypotheses — least action

We cannot know which path occurred, so we mix them. By A2, path length is
proportional to volume required, and the bar only had `V` to spend. A path that
demands more volume for the same `V` is a less likely explanation, so we weight
each hypothesis by a negative power of its length:

```
w_A ∝ len(A)^(−α)        w_B ∝ len(B)^(−α)        w_A + w_B = 1
```

`α` is the **least-action exponent**, the model's only free structural knob:

- `α = 0` — the two paths are equally likely (maximum ignorance).
- `α = 1` — inverse-length weighting, the natural choice, and the default.
- `α → ∞` — commit entirely to the shorter path.

At `α = 1` the weights simplify beautifully:

```
w_A = len(B) / (len(A)+len(B)) = (2R − Δ) / 4R
w_B = len(A) / (len(A)+len(B)) = (2R + Δ) / 4R
```

Both are in `[¼, ¾]` whenever `|Δ| ≤ R`, which A1 guarantees. No clamping needed.

## 3. The bid/ask split falls out for free

Sum the leg lengths by direction, weighted by path probability:

```
M_buy  = w_A·(H−O) + w_A·(C−L) + w_B·R = w_A·(R+Δ) + w_B·R
M_sell = w_A·R + w_B·(O−L) + w_B·(H−C) = w_A·R + w_B·(R−Δ)
```

By A2, volume is proportional to those masses, so

```
buyShare = M_buy / (M_buy + M_sell)
```

At `α = 1`, substituting `x = Δ/R ∈ [−1, 1]` gives a closed form:

```
              4 + 2x − x²
buyShare  =  ─────────────
               8 − 2x²
```

Sanity checks:

| Bar | `x` | `buyShare` |
|---|---|---|
| Doji (`C = O`) | `0` | `0.500` |
| Up marubozu (`C−O = R`) | `+1` | `0.833` |
| Down marubozu | `−1` | `0.167` |

The bounds `[1/6, 5/6]` are a **feature, not a bug**. Even a bar that closes on
its high had sellers — someone was on the other side of every print. A model
that reports 100 % buying for a marubozu is describing price direction, not
order flow. Delta is then simply

```
delta = V·buyShare − V·(1−buyShare) = V·(2·buyShare − 1)
```

## 4. The per-level distribution — no Gaussian required

Here is where most implementations reach for a bell curve and a magic width
parameter. We do not have to. A2 already tells us the answer.

Consider one leg, a monotone traversal of the span `[a, b]`. By A2 the volume
laid down per unit of price is *constant* along that leg, so the leg's
contribution to the price-level density is **uniform on `[a, b]` with total mass
equal to its length**. No assumption is added; this is A2 restated.

The bar's buy density is therefore a **mixture of uniforms over the up-legs**,
and the sell density a mixture of uniforms over the down-legs:

```
f_buy (p) ∝ w_A·(H−O)·U[O,H](p) + w_A·(C−L)·U[L,C](p) + w_B·R·U[L,H](p)
f_sell(p) ∝ w_A·R·U[L,H](p) + w_B·(O−L)·U[L,O](p) + w_B·(H−C)·U[C,H](p)
```

This is the crux of the whole construction, and it is what makes the output a
*footprint* rather than a decorated volume bar:

> **`f_buy` and `f_sell` have different shapes and different centres of mass.**

Buying concentrates where price was rising, selling where it was falling. If you
instead distribute one shared profile and colour it by a bar-level ratio — which
is what a single shared Gaussian does — then every row has the identical buy/sell
proportion, every diagonal imbalance fires or none does, and the overlap
coefficient is pinned at `1.00`. The footprint would carry no information the
candle did not already have.

### Row masses, in closed form

Rows are tick-aligned: row `k` covers `[k·s, (k+1)·s)` for row size `s`. Because
rows are anchored to an absolute grid rather than to each bar's low, columns from
different bars line up — which is what makes horizontal (diagonal) comparisons
meaningful at all.

A uniform leg's mass in a row is just the overlap of two intervals:

```
mass(row, leg) = m · max(0, min(p₂,b) − max(p₁,a)) / (b − a)
```

Exact, analytic, no sampling.

### Optional smoothing — and what the width parameter actually means

The two-path model is a deliberate simplification: the real path has thousands of
legs, not three. That uncertainty can be expressed by convolving each uniform leg
with a Gaussian kernel of bandwidth `σ`. This stays fully analytic. With
`Φ` the standard normal CDF, `φ` its density, and

```
Ψ(z) = z·Φ(z) + φ(z)          (an antiderivative of Φ, since Ψ′(z) = Φ(z))
```

the smoothed mass of leg `[a,b]` in row `[p₁,p₂]` is

```
              m·σ
mass  =  ───────────── · [ Ψ(z₂ᵃ) − Ψ(z₁ᵃ) − Ψ(z₂ᵇ) + Ψ(z₁ᵇ) ],   z_iᶜ = (p_i − c)/σ
             (b − a)
```

Setting `σ = R / κ` recovers the familiar "volume concentration" knob `κ`, but
now it has a precise meaning: **`κ` is not the shape of the distribution, it is
our confidence in the three-leg path approximation.** Large `κ` ⇒ narrow kernel ⇒
trust the legs. `κ → ∞` ⇒ the exact piecewise-uniform profile of §4.

This is why the sane default here (`κ ≈ 6`) is tighter than in models where the
Gaussian *is* the assumed profile and must be wide (`κ ≈ 3`) to have any shape at
all. Over-smoothing washes out precisely the buy/sell asymmetry the model exists
to express, collapsing `OVL` towards `1.00`.

### Conservation

Smoothing leaks mass outside `[L, H]`, and rows are a finite grid, so the discrete
row masses are renormalised to sum exactly to `V·buyShare` and `V·(1−buyShare)`.
Conservation of volume is therefore exact by construction, and the **residual**
diagnostic `|Σrows − V| / V` measures only floating-point error — if it is ever
larger than a few parts per million, something is genuinely wrong.

## 5. Metrics read off the profile

With `b_k`, `s_k` the buy/sell volume of row `k` and `t_k = b_k + s_k`:

**Point of Control** — `POC = argmax_k t_k`. The modal price of the reconstructed
distribution.

**Value Area** — the smallest contiguous band around the POC holding `V%`
(default 70 %) of total volume. Grown greedily: repeatedly annex whichever
neighbour, above or below, carries more volume, until the target is met. 70 % is
conventional, not derived — it is roughly `±1σ` of a normal, which is where the
convention came from.

**Diagonal imbalance** — a footprint's signature test. Compare across the spread,
not within a level: buyers at level `k` traded against sellers at level `k−1`.

```
buy  imbalance at k  ⇔  b_k > θ · s_{k−1}
sell imbalance at k  ⇔  s_k > θ · b_{k+1}
```

with `θ` a dominance threshold (default 3.0, i.e. 300 %). Stacked consecutive
imbalances are the classic absorption/initiative signature.

**Overlap coefficient (OVL)** — how much the buy and sell profiles agree on
*where* they traded. With `b̂`, `ŝ` normalised to unit mass:

```
OVL = Σ_k min(b̂_k, ŝ_k)  ∈ [0, 1]
```

`1.00` means buyers and sellers were active at identical prices (balance,
two-sided rotation). Low OVL means the sides were segregated by price — an
initiative move where one side chased. This is the standard overlapping
coefficient of two distributions, and it is precisely the metric that a
shared-shape model cannot produce, since it would be identically `1`.

**Balance tilt** — `(B − S)/(B + S) · 100`, the bar's delta as a percentage.
Below a threshold (default 5 %) the bar is reported as balanced rather than
given a spurious direction.

## 6. Engines

The path model is the default, but it is still a model. Three engines ship, in
increasing order of fidelity:

1. **`path`** (default) — the derivation above. Needs only OHLCV; works on every
   symbol, timeframe and account tier.
2. **`close`** — the naive `buyShare = (C−L)/(H−L)`. Included because it is the
   classic textbook split, and because the contrast is instructive: it is the
   `R → |Δ|` limit of an unweighted path model, saturates at 0 and 1, and so
   systematically overstates delta on trend bars. The row *shapes* still come
   from §4; only the totals are rescaled.
3. **`ltf`** — aggregate genuine up/down volume from a lower timeframe. This is a
   measurement, not a model, and it dominates the other two whenever lower
   timeframe data is available. The reconstruction of §4 is then applied
   per-sub-bar and summed, so each sub-bar contributes its own measured split to
   its own price levels — which is how the model degrades gracefully into the
   truth as the sub-timeframe shrinks.

## 7. What this cannot do

- It cannot see absorption that left no price trace. A thousand contracts filled
  at one level with no movement is invisible to A2 — that is the model's blind
  spot, and it is exactly where real footprint data earns its cost.
- It cannot distinguish a single large aggressor from many small ones.
- Diagonal imbalances derived here reflect *modelled* path geometry, not observed
  order flow. They are a hypothesis generator, not a confirmation.

Used as a lens on bar geometry it is rigorous and self-consistent. Used as a
substitute for tick data it will mislead you. The `ltf` engine exists to narrow
that gap.
