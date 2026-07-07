# KFT Validation Report

All numbers below were produced by `python run.py` in this repository
against real Yahoo Finance daily data (see `data/` cache). Costs are
charged per side on notional; stops fill before targets on ambiguous
bars; all fills occur at the *next* bar's open.

## BTC-USD  (2014-09-17 → 2026-07-07, 4312 bars)

| Variant | Net Profit | CAGR | Sharpe | Sortino | MaxDD | Trades | Win% | PF | Expectancy |
|---|---|---|---|---|---|---|---|---|---|
| KFT (default params, full sample) | 70.3% | 3.16% | 1.03 | 1.15 | -4.4% | 195 | 50.8% | 2.26 | +0.394R |
| KFT (walk-forward OOS stitched) | 36.2% | 2.41% | 0.79 | 0.90 | -5.5% | 195 | 50.8% | 2.26 | +0.394R |
| Buy & Hold | 13669.1% | 33.35% | 0.80 | 1.06 | -83.4% | 1 | nan% | nan | +nanR |
| MA 50/200 cross (long only) | 13683.9% | 33.36% | 0.87 | 0.88 | -69.3% | 10 | 60.0% | 3.01 | +nanR |

Walk-forward parameter picks (per test year): 2017-06-20→θ=0.6,β=0.05,τ=20, 2018-02-27→θ=0.6,β=0.08,τ=20, 2018-11-06→θ=0.6,β=0.08,τ=20, 2019-07-16→θ=0.6,β=0.05,τ=20, 2020-03-24→θ=0.6,β=0.05,τ=20, 2020-12-01→θ=0.6,β=0.08,τ=20, 2021-08-10→θ=0.6,β=0.08,τ=20, 2022-04-19→θ=0.6,β=0.08,τ=20, 2022-12-27→θ=0.6,β=0.08,τ=20, 2023-09-05→θ=0.6,β=0.08,τ=20, 2024-05-14→θ=0.9,β=0.08,τ=20, 2025-01-21→θ=1.2,β=0.05,τ=20, 2025-09-30→θ=0.6,β=0.05,τ=10

Monte Carlo (2000 bootstraps of the R-sequence @0.75% risk): median return 76.1%, 5th-pct return 41.7%, worst-tail (5th-pct) drawdown -6.6%, P(DD ≥ 20%) = 0.0%

## EURUSD=X  (2010-01-01 → 2026-07-07, 4297 bars)

| Variant | Net Profit | CAGR | Sharpe | Sortino | MaxDD | Trades | Win% | PF | Expectancy |
|---|---|---|---|---|---|---|---|---|---|
| KFT (default params, full sample) | -10.3% | -0.64% | -0.36 | -0.27 | -12.1% | 124 | 41.9% | 0.67 | -0.108R |
| KFT (walk-forward OOS stitched) | -10.4% | -0.84% | -0.50 | -0.35 | -11.2% | 124 | 41.9% | 0.67 | -0.108R |
| Buy & Hold | -20.6% | -1.34% | -0.12 | -0.17 | -35.4% | 1 | nan% | nan | +nanR |
| MA 50/200 cross (long only) | -11.1% | -0.69% | -0.11 | -0.10 | -20.5% | 13 | 30.8% | 0.57 | +nanR |

Walk-forward parameter picks (per test year): 2013-11-14→θ=0.6,β=0.12,τ=10, 2014-11-03→θ=0.6,β=0.12,τ=10, 2015-10-21→θ=0.9,β=0.12,τ=10, 2016-10-09→θ=0.6,β=0.12,τ=10, 2017-09-27→θ=0.6,β=0.12,τ=10, 2018-09-17→θ=0.6,β=0.12,τ=10, 2019-09-05→θ=0.6,β=0.12,τ=10, 2020-08-24→θ=0.9,β=0.08,τ=10, 2021-08-11→θ=0.9,β=0.08,τ=10, 2022-07-31→θ=0.9,β=0.08,τ=10, 2023-07-18→θ=0.9,β=0.08,τ=10, 2024-07-04→θ=0.9,β=0.08,τ=10, 2025-06-26→θ=0.9,β=0.08,τ=10

Monte Carlo (2000 bootstraps of the R-sequence @0.75% risk): median return -9.9%, 5th-pct return -18.5%, worst-tail (5th-pct) drawdown -19.6%, P(DD ≥ 20%) = 4.4%

## GBPUSD=X  (2010-01-01 → 2026-07-07, 4295 bars)

| Variant | Net Profit | CAGR | Sharpe | Sortino | MaxDD | Trades | Win% | PF | Expectancy |
|---|---|---|---|---|---|---|---|---|---|
| KFT (default params, full sample) | -10.9% | -0.67% | -0.40 | -0.29 | -14.2% | 123 | 44.7% | 0.68 | -0.109R |
| KFT (walk-forward OOS stitched) | -6.5% | -0.52% | -0.30 | -0.23 | -7.9% | 123 | 44.7% | 0.68 | -0.109R |
| Buy & Hold | -17.1% | -1.09% | -0.08 | -0.11 | -37.5% | 1 | nan% | nan | +nanR |
| MA 50/200 cross (long only) | -19.4% | -1.26% | -0.21 | -0.21 | -26.9% | 13 | 23.1% | 0.30 | +nanR |

Walk-forward parameter picks (per test year): 2013-11-14→θ=0.6,β=0.12,τ=10, 2014-11-04→θ=0.6,β=0.12,τ=10, 2015-10-22→θ=0.6,β=0.12,τ=10, 2016-10-11→θ=0.6,β=0.12,τ=10, 2017-10-01→θ=0.6,β=0.12,τ=20, 2018-09-19→θ=0.6,β=0.12,τ=20, 2019-09-09→θ=0.6,β=0.12,τ=20, 2020-08-26→θ=0.6,β=0.12,τ=20, 2021-08-15→θ=0.6,β=0.12,τ=20, 2022-08-02→θ=0.6,β=0.12,τ=20, 2023-07-20→θ=0.6,β=0.12,τ=20, 2024-07-08→θ=0.6,β=0.12,τ=20, 2025-06-30→θ=0.6,β=0.12,τ=20

Monte Carlo (2000 bootstraps of the R-sequence @0.75% risk): median return -10.0%, 5th-pct return -19.2%, worst-tail (5th-pct) drawdown -20.2%, P(DD ≥ 20%) = 5.5%

## ^GSPC  (2010-01-04 → 2026-07-06, 4150 bars)

| Variant | Net Profit | CAGR | Sharpe | Sortino | MaxDD | Trades | Win% | PF | Expectancy |
|---|---|---|---|---|---|---|---|---|---|
| KFT (default params, full sample) | -8.1% | -0.51% | -0.22 | -0.18 | -11.6% | 158 | 40.5% | 0.80 | -0.055R |
| KFT (walk-forward OOS stitched) | -3.9% | -0.31% | -0.13 | -0.11 | -7.1% | 158 | 40.5% | 0.80 | -0.055R |
| Buy & Hold | 565.1% | 12.19% | 0.75 | 0.93 | -33.9% | 1 | nan% | nan | +nanR |
| MA 50/200 cross (long only) | 245.0% | 7.81% | 0.61 | 0.64 | -33.9% | 7 | 71.4% | 9.27 | +nanR |

Walk-forward parameter picks (per test year): 2014-01-03→θ=1.2,β=0.12,τ=20, 2015-01-05→θ=1.2,β=0.05,τ=20, 2016-01-05→θ=1.2,β=0.05,τ=20, 2017-01-04→θ=1.2,β=0.05,τ=20, 2018-01-04→θ=1.2,β=0.05,τ=10, 2019-01-07→θ=1.2,β=0.05,τ=10, 2020-01-07→θ=1.2,β=0.12,τ=20, 2021-01-06→θ=1.2,β=0.05,τ=10, 2022-01-05→θ=1.2,β=0.05,τ=10, 2023-01-06→θ=1.2,β=0.05,τ=10, 2024-01-09→θ=1.2,β=0.05,τ=10, 2025-01-10→θ=1.2,β=0.05,τ=10, 2026-01-13→θ=0.6,β=0.05,τ=20

Monte Carlo (2000 bootstraps of the R-sequence @0.75% risk): median return -7.0%, 5th-pct return -17.6%, worst-tail (5th-pct) drawdown -19.1%, P(DD ≥ 20%) = 3.6%

## ^NDX  (2010-01-04 → 2026-07-06, 4150 bars)

| Variant | Net Profit | CAGR | Sharpe | Sortino | MaxDD | Trades | Win% | PF | Expectancy |
|---|---|---|---|---|---|---|---|---|---|
| KFT (default params, full sample) | 2.4% | 0.15% | 0.08 | 0.06 | -8.6% | 154 | 44.2% | 1.08 | +0.034R |
| KFT (walk-forward OOS stitched) | 4.4% | 0.34% | 0.17 | 0.13 | -7.7% | 154 | 44.2% | 1.08 | +0.034R |
| Buy & Hold | 1473.6% | 18.22% | 0.91 | 1.17 | -35.6% | 1 | nan% | nan | +nanR |
| MA 50/200 cross (long only) | 874.9% | 14.83% | 0.87 | 0.98 | -28.0% | 9 | 88.9% | 26.06 | +nanR |

Walk-forward parameter picks (per test year): 2014-01-03→θ=1.2,β=0.08,τ=20, 2015-01-05→θ=1.2,β=0.08,τ=20, 2016-01-05→θ=1.2,β=0.08,τ=20, 2017-01-04→θ=1.2,β=0.08,τ=20, 2018-01-04→θ=1.2,β=0.08,τ=20, 2019-01-07→θ=1.2,β=0.08,τ=20, 2020-01-07→θ=1.2,β=0.08,τ=20, 2021-01-06→θ=1.2,β=0.08,τ=20, 2022-01-05→θ=1.2,β=0.08,τ=20, 2023-01-06→θ=1.2,β=0.08,τ=20, 2024-01-09→θ=1.2,β=0.08,τ=20, 2025-01-10→θ=1.2,β=0.08,τ=20, 2026-01-13→θ=1.2,β=0.08,τ=20

Monte Carlo (2000 bootstraps of the R-sequence @0.75% risk): median return 3.5%, 5th-pct return -9.4%, worst-tail (5th-pct) drawdown -13.7%, P(DD ≥ 20%) = 0.3%

## Notes

- `KFT (walk-forward OOS stitched)` re-selects θ, β, τ annually on the
  preceding ~4 years only; the equity shown is out-of-sample.
- Trade-level columns (Trades/Win%/PF/Expectancy) for the OOS row reuse
  the full-sample trade list; the OOS equity/Sharpe/DD columns are the
  honest out-of-sample figures.
