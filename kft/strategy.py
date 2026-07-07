"""Signal engine: composes the six KFT constructs into an Ignition Score and
long/short triggers. Everything is computed on bar-t information only; the
backtester executes at the open of t+1.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from . import concepts as C


@dataclass
class KFTParams:
    tau: int = 20            # Imprint Field memory (bars)
    beta: float = 0.08       # Kinetic decay (half-life ~ 8.7 bars)
    jump_q: float = 1.25     # shock admission threshold (TR/ATR)
    eci_m: int = 4           # permutation embedding order
    eci_win: int = 64        # entropy window
    theta: float = 0.90      # Ignition Score trigger
    aq_gate: float = 0.05    # minimum Asymmetry Quotient agreement
    w_aq: float = 1.5        # score weight: asymmetry
    w_grav: float = 0.5      # score weight: gravity attraction
    w_release: float = 0.5   # score weight: compression release bonus
    stop_atr: float = 1.25   # base stop multiple (scaled by entropy)
    r_target: float = 3.0    # profit objective in R
    trail_atr: float = 2.0   # trailing distance after +1R
    time_stop: int = 40      # max bars if trade never reaches +0.5R
    risk: float = 0.0075     # fraction of equity risked per trade


def build_features(df: pd.DataFrame, p: KFTParams) -> pd.DataFrame:
    atr14 = C.atr(df, 14)
    pulse = C.participation_pulse(df)
    phi, Phi, aq = C.flow_imprint(df, pulse, tau=p.tau)
    eci = C.entropic_compression(df["Close"], m=p.eci_m, win=p.eci_win)
    M, zM = C.kinetic_ignition(df, atr14, beta=p.beta, q=p.jump_q)
    lattice = C.gravity_lattice(df, pulse, atr14)
    phases = C.coherence_phase(df, eci)

    f = pd.concat(
        [
            df,
            atr14.rename("atr"),
            pulse.rename("pulse"),
            phi,
            Phi,
            aq,
            eci,
            M,
            zM,
            lattice,
            phases,
        ],
        axis=1,
    )

    # Compression-release: the tape was coiled (high ECI) within the last 5
    # bars and today injected a real shock -> stored energy is discharging.
    eci_q80 = f["ECI"].rolling(252, min_periods=100).quantile(0.80)
    was_coiled = (f["ECI"] >= eci_q80).rolling(5).max().fillna(0).astype(bool)
    shock_now = (C.true_range(df) / (f["atr"] + 1e-12)) > p.jump_q
    f["release"] = (was_coiled & shock_now).astype(float)

    # Ignition Score (signed).
    f["score"] = (
        f["zM"]
        + p.w_aq * f["AQ"]
        + p.w_grav * f["attract"] * f["vacuum"]
        + p.w_release * f["release"] * np.sign(f["zM"]).fillna(0.0)
    )

    phase_ok = f["phase"] != C.TURBULENT
    ignition = (f["phase"] == C.LAMINAR) | (
        (f["phase"].shift(1) == C.COMPRESSIVE) & (f["release"] > 0)
    )
    f["long_sig"] = (
        phase_ok
        & ignition
        & (f["score"] >= p.theta)
        & (f["AQ"] > p.aq_gate)
        & (f["zM"] > 0)
    )
    f["short_sig"] = (
        phase_ok
        & ignition
        & (f["score"] <= -p.theta)
        & (f["AQ"] < -p.aq_gate)
        & (f["zM"] < 0)
    )
    # Entropy-adaptive stop distance: noisier tape (low ECI) -> wider stop.
    f["stop_mult"] = p.stop_atr * (2.0 - f["ECI"].clip(0.0, 1.0))
    return f
