"""Kairometric Field Theory — core concept computations.

Six original constructs, computed strictly causally (bar t uses data up to and
including bar t; execution happens at the open of t+1):

  1. Participation Pulse  (rho_t)   — abnormal-participation weight
  2. Flow Imprint Vector  (phi_t)   — signed conviction of each bar; its
     exponential aggregate is the Imprint Field (Phi_t) and the normalized
     directional asymmetry is the Asymmetry Quotient (AQ_t)
  3. Entropic Compression Index (ECI_t) — 1 - normalized permutation entropy
     of the return stream: how much "order" (stored energy) the tape holds
  4. Kinetic Ignition Function (M_t) — a self-exciting (Hawkes-style) state
     variable integrating signed participation shocks:
         M_t = e^{-beta} M_{t-1} + J_t
  5. Gravity Node Lattice — an exponentially-decaying mass field over
     log-price; local maxima are Gravity Nodes (institutional inventory
     shelves), low-mass gaps between them are Vacuum Corridors
  6. Coherence Phases — LAMINAR / COMPRESSIVE / TURBULENT regime tensor from
     (kinetic efficiency, ECI, volatility ratio)
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

EPS = 1e-12


# ----------------------------------------------------------------------
# Building blocks
# ----------------------------------------------------------------------
def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["Close"].shift(1)
    return pd.concat(
        [df["High"] - df["Low"], (df["High"] - pc).abs(), (df["Low"] - pc).abs()],
        axis=1,
    ).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1.0 / n, adjust=False).mean()


def rolling_z(x: pd.Series, win: int) -> pd.Series:
    mu = x.rolling(win, min_periods=win // 2).mean()
    sd = x.rolling(win, min_periods=win // 2).std()
    return (x - mu) / (sd + EPS)


# ----------------------------------------------------------------------
# 1. Participation Pulse
# ----------------------------------------------------------------------
def participation_pulse(df: pd.DataFrame, win: int = 120) -> pd.Series:
    """z-score of abnormal participation.

    Uses log-volume when a real volume stream exists; otherwise (spot FX)
    falls back to the true-range/ATR activity proxy, which is monotone in
    tick participation for continuous dealer markets.
    """
    v = df["Volume"].astype(float).fillna(0.0)
    if (v > 0).mean() > 0.5:
        x = np.log1p(v)
    else:
        x = true_range(df) / (atr(df) + EPS)
    return rolling_z(x, win).clip(-3.0, 4.0)


# ----------------------------------------------------------------------
# 2. Flow Imprint Vector, Imprint Field, Asymmetry Quotient
# ----------------------------------------------------------------------
def flow_imprint(df: pd.DataFrame, pulse: pd.Series, tau: int = 20):
    """phi_t = d_t * (1 + max(rho_t, 0)) where d_t is directional efficiency.

    d_t = (C-O)/(H-L) in [-1, 1]: the fraction of the bar's range the
    aggressor side actually kept. Weighting by abnormal participation makes
    phi a proxy for *institutional* conviction rather than noise.
    """
    d = (df["Close"] - df["Open"]) / (df["High"] - df["Low"] + EPS)
    w = 1.0 + pulse.clip(lower=0.0)
    phi = (d * w).rename("phi")
    Phi = phi.ewm(span=tau, adjust=False).mean().rename("Phi")
    pos = phi.clip(lower=0.0).ewm(span=tau, adjust=False).mean()
    neg = (-phi).clip(lower=0.0).ewm(span=tau, adjust=False).mean()
    aq = ((pos - neg) / (pos + neg + EPS)).rename("AQ")
    return phi, Phi, aq


# ----------------------------------------------------------------------
# 3. Entropic Compression Index (rolling permutation entropy)
# ----------------------------------------------------------------------
def entropic_compression(close: pd.Series, m: int = 4, win: int = 64) -> pd.Series:
    """ECI_t = 1 - H_perm / ln(m!)  over the last `win` embedded patterns.

    High ECI = ordered, repetitive micro-structure = coiled tape.
    Vectorized: each length-m window of returns maps to a Lehmer code; the
    rolling pattern histogram comes from a cumulative one-hot sum.
    """
    r = np.diff(np.log(close.to_numpy(dtype=float)))
    n = len(r)
    n_pat = math.factorial(m)
    out = np.full(len(close), np.nan)
    if n < m + win:
        return pd.Series(out, index=close.index, name="ECI")

    emb = np.lib.stride_tricks.sliding_window_view(r, m)          # (n-m+1, m)
    ranks = emb.argsort(axis=1, kind="stable").argsort(axis=1)
    weights = np.array([math.factorial(m - 1 - j) for j in range(m)])
    codes = ranks @ weights                                        # Lehmer codes

    onehot = np.zeros((len(codes) + 1, n_pat))
    onehot[np.arange(1, len(codes) + 1), codes] = 1.0
    cum = onehot.cumsum(axis=0)
    counts = cum[win:] - cum[:-win]                                # rolling hist
    p = counts / win
    with np.errstate(divide="ignore", invalid="ignore"):
        h = -np.nansum(np.where(p > 0, p * np.log(p), 0.0), axis=1)
    eci = 1.0 - h / math.log(n_pat)

    # codes[i] describes returns r[i..i+m-1] -> close index i+m; the window
    # ending at pattern k lands on close index k+m+win-1... align causally:
    start = m + win - 1  # close index of the first fully-formed window
    out[start : start + len(eci)] = eci
    return pd.Series(out, index=close.index, name="ECI")


# ----------------------------------------------------------------------
# 4. Kinetic Ignition Function (self-exciting shock integrator)
# ----------------------------------------------------------------------
def kinetic_ignition(
    df: pd.DataFrame,
    atr_: pd.Series,
    beta: float = 0.08,
    q: float = 1.25,
    z_win: int = 250,
):
    """M_t = e^{-beta} M_{t-1} + J_t,   J_t = d_t * max(TR_t/ATR_t - q, 0).

    J_t is a signed participation shock: only bars whose range exceeds q
    ATRs inject energy, signed by who won the bar. beta is the institutional
    memory decay (half-life ln2/beta bars). Returned as a rolling z-score.
    """
    d = (df["Close"] - df["Open"]) / (df["High"] - df["Low"] + EPS)
    shock = (true_range(df) / (atr_ + EPS) - q).clip(lower=0.0)
    J = (d * shock).to_numpy(dtype=float)
    decay = math.exp(-beta)
    M = np.zeros_like(J)
    acc = 0.0
    for i, j in enumerate(np.nan_to_num(J)):
        acc = decay * acc + j
        M[i] = acc
    M = pd.Series(M, index=df.index, name="M")
    zM = rolling_z(M, z_win).rename("zM")
    return M, zM


# ----------------------------------------------------------------------
# 5. Gravity Node Lattice
# ----------------------------------------------------------------------
def gravity_lattice(
    df: pd.DataFrame,
    pulse: pd.Series,
    atr_: pd.Series,
    n_bins: int = 240,
    rho: float = 0.994,
    kernel_atr: float = 0.75,
    horizon_atr: float = 6.0,
):
    """Exponentially-decaying participation-mass field over log-price.

    Each bar deposits mass w_t = 1 + max(rho_t, 0) as a Gaussian kernel
    centred on the typical price with bandwidth kernel_atr * ATR. The field
    decays by rho per bar (half-life ~115 bars), so stale inventory fades.

    Per bar (causal) outputs:
      attract  : sign of (mass-centroid within +/- horizon_atr*ATR - price)
                 -> which side holds the dominant unresolved inventory
      node_up  : price of nearest above-market Gravity Node (local mass max)
      node_dn  : price of nearest below-market Gravity Node
      vacuum   : 1 - (interior mass / flank mass) in the attract direction;
                 high vacuum = thin corridor, price traverses it fast
    """
    lp = np.log(((df["High"] + df["Low"] + df["Close"]) / 3.0).to_numpy(float))
    close = np.log(df["Close"].to_numpy(float))
    atr_pct = (atr_ / df["Close"]).to_numpy(float)
    w = (1.0 + pulse.clip(lower=0.0)).fillna(1.0).to_numpy(float)

    lo, hi = np.nanmin(lp), np.nanmax(lp)
    pad = 0.05 * (hi - lo) + 1e-4
    grid = np.linspace(lo - pad, hi + pad, n_bins)
    step = grid[1] - grid[0]

    mass = np.zeros(n_bins)
    n = len(df)
    attract = np.zeros(n)
    node_up = np.full(n, np.nan)
    node_dn = np.full(n, np.nan)
    vacuum = np.zeros(n)

    for t in range(n):
        mass *= rho
        h = max(kernel_atr * (atr_pct[t] if np.isfinite(atr_pct[t]) else 0.01), step)
        k = np.exp(-0.5 * ((grid - lp[t]) / h) ** 2)
        mass += w[t] * k / (k.sum() + EPS)

        if t < 30:
            continue
        c = close[t]
        horiz = horizon_atr * (atr_pct[t] if np.isfinite(atr_pct[t]) else 0.01)
        near = np.abs(grid - c) <= horiz
        if mass[near].sum() > EPS:
            centroid = (grid[near] * mass[near]).sum() / mass[near].sum()
            attract[t] = np.sign(centroid - c)

        # Gravity Nodes: local maxima above the field's mean level.
        m = mass
        peaks = np.where(
            (m[1:-1] > m[:-2]) & (m[1:-1] >= m[2:]) & (m[1:-1] > m.mean())
        )[0] + 1
        if len(peaks):
            gp = grid[peaks]
            above = gp[gp > c + 0.25 * horiz / horizon_atr]
            below = gp[gp < c - 0.25 * horiz / horizon_atr]
            if len(above):
                node_up[t] = math.exp(above.min())
            if len(below):
                node_dn[t] = math.exp(below.max())

        # Vacuum toward the attracting side: interior mass vs. node mass.
        target = node_up[t] if attract[t] > 0 else node_dn[t]
        if np.isfinite(target) and target > 0:
            tl = math.log(target)
            a, b = (c, tl) if tl > c else (tl, c)
            interior = mass[(grid > a) & (grid < b)]
            flank = mass[np.abs(grid - tl) <= 2 * step].mean() + EPS
            if len(interior):
                vacuum[t] = float(np.clip(1.0 - interior.mean() / flank, 0.0, 1.0))

    idx = df.index
    return pd.DataFrame(
        {
            "attract": attract,
            "node_up": node_up,
            "node_dn": node_dn,
            "vacuum": vacuum,
        },
        index=idx,
    )


# ----------------------------------------------------------------------
# 6. Coherence Phases (regime tensor)
# ----------------------------------------------------------------------
LAMINAR, COMPRESSIVE, TURBULENT = 1, 0, -1


def coherence_phase(
    df: pd.DataFrame,
    eci: pd.Series,
    ker_win: int = 20,
    ker_thresh: float = 0.35,
    vol_fast: int = 14,
    vol_slow: int = 100,
    turb_ratio: float = 1.6,
) -> pd.DataFrame:
    """Phase from Kinetic Efficiency Ratio, ECI and the volatility ratio.

    KER_t = |C_t - C_{t-w}| / sum |dC|  (fraction of path converted to travel)
    LAMINAR      : KER >= ker_thresh              (directional conduction)
    TURBULENT    : vol ratio > turb_ratio & low KER (dissipative chaos)
    COMPRESSIVE  : otherwise, with ECI above its rolling median (coiling)
    Residual low-KER, low-ECI bars are treated as TURBULENT (no edge).
    """
    dc = df["Close"].diff()
    ker = (df["Close"].diff(ker_win).abs() / (dc.abs().rolling(ker_win).sum() + EPS)).rename("KER")
    vr = (atr(df, vol_fast) / (atr(df, vol_slow) + EPS)).rename("volratio")
    eci_med = eci.rolling(252, min_periods=100).median()

    phase = pd.Series(TURBULENT, index=df.index, name="phase")
    compressive = (ker < ker_thresh) & (eci >= eci_med) & (vr <= turb_ratio)
    phase[compressive] = COMPRESSIVE
    phase[ker >= ker_thresh] = LAMINAR
    phase[(vr > turb_ratio) & (ker < ker_thresh)] = TURBULENT
    return pd.concat([phase, ker, vr], axis=1)
