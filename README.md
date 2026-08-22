# AYA — al-Mīzān li-l-Dhahab

*The Balance for Gold* — an institutional, algorithmically rigorous method for identifying true
Supply and Demand levels when day trading **XAUUSD**, set down in the manner of al-Khwārizmī:
classify, restore, balance, then execute without ambiguity.

| File | What it is |
|---|---|
| [`docs/KITAB_AL_MIZAN_LI_AL_DHAHAB.md`](docs/KITAB_AL_MIZAN_LI_AL_DHAHAB.md) | The full treatise: the six forms of the zone, the twelve-step algorithm, the proof of superiority over classic S/R, pivots, unfiltered ICT and volume profile, and the XAUUSD-specific rules. |
| [`docs/OPERATOR_CARD.md`](docs/OPERATOR_CARD.md) | One page. The gates, the balance, the sessions, the risk law — for use at the screen. |
| [`algorithm/mizan.py`](algorithm/mizan.py) | Dependency-free reference implementation: zone detection, the 100-point balance, zone selection and a fully specified trade plan (entry, stop, targets, size). |

## The doctrine in one paragraph

True supply/demand is **institutional imbalance left behind by aggressive, one-sided order flow**.
It is proved — not assumed — by a tight base (1–5 candles) from which price departs with
displacement ≥ 2×ATR, carrying a conviction candle and leaving a **Fair Value Gap**, which is the
arithmetic certificate that no two-sided auction occurred. Such a zone is ranked by eight
near-independent measures (displacement, base quality, imbalance width, liquidity sweep,
higher-timeframe alignment, freshness, psychological magazine, session of birth) and traded only
in the tail of that conjunction. Everything else — touch counts, indicator confluence, lines
drawn where price merely stopped — is discarded by restoration and balancing.

## Usage

```bash
python3 algorithm/mizan.py --selftest
python3 algorithm/mizan.py --csv m15.csv --h4 h4.csv --d1 d1.csv --equity 10000 --risk 0.5 --all
```

CSV columns (header required): `time,open,high,low,close`. Naive timestamps are read as UTC.

## Caveat

The astrolabe does not command the stars; it only measures them. This is a decision procedure of
high rigour, not a promise of profit. Verify expectancy over at least 200 historical occurrences
on your own data, spread and execution before risking capital.
