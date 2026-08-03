# KÖNIG

**Kinetic Coherence** — an algorithmic trading system derived from König's decomposition
theorem, built to replace Smart Money Concepts with a single measured quantity.

Over any window, the energy in a price series splits exactly into coherent bulk flow and
incoherent thermal agitation. The bulk fraction is the only thing worth measuring:

$$\mathcal{C} \;=\; \sqrt{n_{\text{eff}}}\,\frac{\bar v}{u} \;=\; \frac{D}{\ell}, \qquad \Phi = \frac{\mathcal{C}^2}{n_{\text{eff}}} \in [0,1]$$

$\mathcal{C}$ is dimensionless, self-normalising, and distributed $\mathcal{N}(0,1)$ under a
random-walk null — so its threshold is a p-value, not a setting. It is displacement measured in
units of diffusion.

| | |
|---|---|
| **Enter** | $\lvert\mathcal{C}\rvert$ crosses 2.58, and the bar closes with the flow |
| **Stop** | one diffusive $\sigma$ ($\ell$) against |
| **Target** | $\mathcal{C}\,\ell$ with — inertial projection |
| **R:R** | $\mathcal{C}$, automatically |
| **Chart** | an arrow, a stop ray, a target ray |

Four rules, zero discretion, four accumulators of state, 20 bars of lookback. Causal and
non-repainting by construction. No zones, no levels, no higher-timeframe overlays.

## Contents

- **[KONIG.md](KONIG.md)** — full derivation: philosophy, governing equation, detection
  algorithm, rules, and why it beats SMC on scientific and practical grounds.
- **[konig.pine](konig.pine)** — Pine v6, core logic.
- **[verify/konig.py](verify/konig.py)** — streaming reference implementation.
- **[verify/null_distribution.py](verify/null_distribution.py)** — Monte Carlo of the null.
- **[verify/power_and_geometry.py](verify/power_and_geometry.py)** — thresholds, power, geometry.

```
pip install numpy
python3 verify/null_distribution.py
python3 verify/power_and_geometry.py
python3 verify/konig.py
```

## Status

The *measurement* is verified: the null holds at $\mathcal{N}(0,1)$ under Gaussian, Student-$t(3)$
and volatility-clustered processes and is invariant to price scale. The *edge* — that coherent
flow continues rather than reverts — is an empirical hypothesis tested here only against
synthetic nulls, not against real price history. Backtest per market before risking capital.
