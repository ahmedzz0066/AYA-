# Smart SR Zones — audit and v2 rewrite

An engineering review of the TradingView indicator
[**Smart SR Zones [JOAT]**](https://www.tradingview.com/script/NXuV5E1i-Smart-SR-Zones-JOAT/)
(Pine v6, MPL-2.0, © officialjackofalltrades), and a rewrite that replaces its
rebuild-every-frame clustering with a persistent tracker, a calibrated
probability, and an on-chart reliability check.

## Contents

| Path | What |
|---|---|
| `docs/AUDIT.md` | What v1 gets right, and 7 critical + 8 significant defects with line references |
| `docs/ALGORITHM.md` | The v2 pipeline, the maths, parameter reference, tuning notes, known limits |
| `pine/smart_sr_zones_v2.pine` | The v2 indicator, ready to paste into the Pine editor |
| `reference/smart_sr_zones_v1_original.pine` | Verbatim v1 source, so every citation is checkable |

## The core finding

v1 is a *detector* with no *tracker*. Every confirmed pivot clears both zone
pools and re-derives them from scratch (`resZones.clear()`, L517). Nothing
persists, so there is no such thing as "this level, one bar later" — which is
what produces the zone flicker, the touch count that never counts a touch, the
single-close kill that permanently blacklists a good level, and a star rating
that is relative to whatever else happens to be on screen.

## What v2 changes

| | v1 | v2 |
|---|---|---|
| **Zone identity** | Cleared and rebuilt each pivot | Persistent tracks with ids, O(1) recursive update |
| **Clustering** | Greedy, seed-anchored, order-dependent | Gated nearest-neighbour + IoU non-max suppression |
| **Zone width** | Fixed ±0.25 ATR | `kσ` of the level's own member dispersion |
| **Scale** | Today's ATR applied to all history | Each detection carries the ATR of its own bar |
| **Touch count** | Pivots in the cluster | Pivots *and* resolved tests, shown separately |
| **Break** | One close past the edge, then blacklisted | ATR buffer + N confirming closes + volume, then **flips role** |
| **Score** | Weighted sum, stars relative to the best on screen | Feature prior + Laplace-smoothed outcome evidence → absolute `P(hold)` |
| **Context** | — | Volume profile node, higher-TF confluence, round numbers |
| **Repainting** | Undisclosed | Honest mode draws from the confirmation bar |
| **Validation** | None | On-chart reliability: predicted vs realised hold rate, with `n` |

## The reliability row

The dashboard's bottom row is the point of the whole exercise:

```
Reliability   68% vs 64%   n=143
```

Every resolved test is filed into the probability bucket that was live *before*
its outcome was known, and the panel reports how often those predictions
actually held. Green under a 7-point gap, amber under 15, red beyond. If they
diverge on your symbol, the model is miscalibrated there and the stars should
be discounted accordingly.

A strength score nobody checks is decoration. This is the check.

## Install

Paste `pine/smart_sr_zones_v2.pine` into the TradingView Pine editor and add it
to the chart. Defaults (`Auto` preset, honest mode on, closed bars only) are
the intended starting point; see the tuning notes in `docs/ALGORITHM.md` before
moving weights.

## Status

The v2 source has been statically reviewed but **not compiled** — I had no
TradingView editor in this environment. Expect to fix trivial syntax
complaints on first paste; the algorithm and structure are the deliverable.

## Licence

v1 is MPL-2.0 and the derived v2 is distributed under the same licence, with
the original attribution retained in the file header.
