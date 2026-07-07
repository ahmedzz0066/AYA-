# AYA — Kairometric Field Theory (KFT)

An original smart-money trading methodology built from first principles:
information theory (permutation entropy), self-exciting point processes
(Hawkes-style ignition), and a decaying mass field over price (Gravity Node
Lattice). No recycled retail-SMC vocabulary — every construct is defined
mathematically in [METHODOLOGY.md](METHODOLOGY.md).

## Quick start

```bash
pip install -r requirements.txt
python run.py          # downloads real daily data, runs the full validation,
                       # regenerates RESULTS.md
```

## Repository layout

| Path | Contents |
|---|---|
| `METHODOLOGY.md` | Full specification: philosophy, math, trading rules, risk framework, psychology |
| `RESULTS.md` | Machine-generated validation report (real data, real numbers) |
| `kft/data.py` | Yahoo Finance daily loader (cookie+crumb, CSV cache) |
| `kft/concepts.py` | The six core constructs |
| `kft/strategy.py` | Ignition Score + signal assembly |
| `kft/backtest.py` | Conservative event-driven backtester, metrics, benchmarks |
| `kft/validate.py` | Full-sample + walk-forward + Monte Carlo suite |

## Honesty statement

Every number in `RESULTS.md` was produced by running `run.py` against real
market data with a conservative execution model (next-open fills, stop-first
on ambiguous bars, per-side costs). Results include the losing markets, not
just the winners — read Section 5.1 and 6 of the methodology before drawing
conclusions. Nothing here is investment advice.
