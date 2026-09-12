# Data

Real M5 data does not live in git — it is large and broker-specific. Put your
CSV here (e.g. `XAUUSD_M5.csv`) and point the CLI at it.

## Getting it

**MetaTrader 5:** `View → Symbols → XAUUSD → Bars → M5 → Export`. Scroll the
chart back first (Home key) or MT5 exports only what it has cached.

**Any other source** works if it has time, open, high, low, close. `load_csv`
handles headered and headerless files, `,` `;` and tab delimiters, MT5's
two-column date/time layout, and epoch timestamps.

## Two things that will silently ruin your results

1. **Timezone.** Session filters are UTC. A GMT+2 broker needs
   `--tz-shift -2`. Get it wrong and you are trading Tokyo while convinced you
   are trading London.
2. **Sample size.** Aim for 3+ years (~220k M5 bars). Two months of gold is
   one regime, and one regime is not a sample.

## Generating synthetic bars

```bash
python3 -m xauusd.cli makedata --bars 60000 --out data/SYNTHETIC_M5.csv
```

Synthetic bars test the machinery. They contain no real market structure, so
performance measured on them is meaningless by construction. Never make a
decision on them.
