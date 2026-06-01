# Order Flow Profile — Footprint • Delta • Heatmap

A first-principles recreation of *Volume HeatMap With Profile [ChartPrime]*, rebuilt to be as
close to **real order flow, footprint and delta** as TradingView/Pine v5 allows.

File: [`OrderFlow_Footprint_Delta.pine`](./OrderFlow_Footprint_Delta.pine)

---

## First principles: what order flow actually is

Order flow is built from individual **trades**, each tagged as buyer‑initiated (executed at the
**ask**) or seller‑initiated (executed at the **bid**). From that primitive everything else follows:

| Concept | Definition |
|---|---|
| **Footprint** | Per price level, *within a single bar*: volume bought (ask) vs sold (bid). |
| **Delta** | `buy volume − sell volume` (per level, per bar, or per session). |
| **Cumulative Delta (CVD)** | Running sum of bar deltas. |
| **POC** | Price level with the most traded volume. |
| **Value Area** | Smallest band around the POC holding ~70% of volume. |
| **Imbalance** | One side ≥ N× the other at a level → "stacked" pressure. |

## Why the original is *not* order flow

```
array.set(Volumes, x, array.get(Volumes,x) + volume[x])   // <- bug: volume[x], x is a LEVEL index
```

1. **Indexing bug** — it adds `volume[x]` where `x` is the *price‑level* index (0…levels), not the
   bar index `i`. The wrong bar's volume is credited to each level.
2. **Close‑only binning** — all of a bar's volume is dumped into the single level containing the
   *close*, ignoring where price actually traded across the bar's range.
3. **Whole‑bar polarity** — bull/bear is decided by `close > open` for the entire bar, so there is
   no real intra‑bar buy/sell split, i.e. no real delta.
4. **"Points" ≠ volume** — heat/percentages are driven by *counts of closes* per level rather than
   traded volume.

The result looks like a profile but is a close‑print histogram, not order flow.

## How this version rebuilds it from the data up

1. **Drill into every bar** with `request.security_lower_tf()` to recover intrabar OHLCV
   (e.g. 1‑second/1‑minute bars inside each chart bar).
2. **Estimate buy vs sell per intrabar** (delta proxy), two selectable estimators:
   - **Proportional** *(default, most accurate)* — split each intrabar's volume by where its close
     sits in its range: `buy = v·(c−l)/(h−l)`, `sell = v·(h−c)/(h−l)`. This accounts for wick
     rejection instead of a hard up/down flip.
   - **Polarity** — classic tick rule (`close > open` → buy, `<` → sell).
3. **Distribute volume across the range**, not just the close: each bar's estimated buy/sell volume
   is spread over every price level its high–low spans, weighted by overlap fraction.
4. **Aggregate per level** → `buy`, `sell`, `total`, `delta`, from which POC, value area,
   cumulative delta and the footprint cells are derived.

## What you get

- **Volume profile** with a **bid/ask split** (green buy segment + red sell segment per level) or a
  volume‑shaded mode.
- **Heatmap** gradient (linefills) by traded volume.
- **POC** box + price label, and **Value Area** band (configurable %).
- **Footprint table** for the last bar: `Sell │ Price │ Buy │ Δ` per level, with **stacked
  imbalances** highlighted (configurable ratio).
- **Stats table**: total volume, buy/sell %, delta, window CVD and its high/low excursion, POC.
- **Windowing**: rolling last‑N bars or an anchored "From Date" profile.

## Honest limitations

TradingView does **not** expose true bid/ask trade prints, so this is a high‑quality
*estimation*, not exchange‑accurate footprint data. Accuracy is driven by intrabar granularity:
the lower the intrabar timeframe relative to the chart, the closer to true delta. Use intrabar mode
on **1‑minute and higher** charts (sub‑minute intrabar data may be unavailable, in which case the
script falls back to chart‑bar classification). Intrabar history is also limited by TradingView, so
very old bars in a long anchored window fall back to chart‑bar estimation.

## Usage

Paste `OrderFlow_Footprint_Delta.pine` into the TradingView Pine Editor and *Add to chart*.
Key inputs: **Window mode** (Rolling/From Date), **Price levels**, **Delta estimator**
(Proportional/Polarity), **Intrabar timeframe** (blank = auto), and the visual toggles.
