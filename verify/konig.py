"""KÖNIG — reference implementation of the coherence state.

Streaming, causal, non-repainting: feed bars in order, read the state after each.
Mirrors konig.pine exactly.

    C    = sqrt(neff) * vbar / u        coherence, ~N(0,1) under a martingale null
    phi  = C**2 / neff                  bulk energy fraction (Koenig), in [0, 1]
    ell  = sqrt(neff) * u               diffusive scale, the risk unit
    D    = C * ell                      coherent displacement
"""

from collections import deque
from dataclasses import dataclass
from math import copysign, sqrt


@dataclass(frozen=True)
class State:
    C: float        # coherence
    phi: float      # bulk energy fraction
    ell: float      # diffusive scale (risk unit)
    neff: float     # effective sample size
    ready: bool     # window full

    @property
    def band(self) -> str:
        a = abs(self.C)
        return "thermal" if a < 1.0 else ("drift" if a < 2.58 else "coherent")


@dataclass(frozen=True)
class Signal:
    direction: int  # +1 long, -1 short
    entry: float
    stop: float
    target: float

    @property
    def rr(self) -> float:
        return abs(self.target - self.entry) / abs(self.entry - self.stop)


class Konig:
    def __init__(self, n: int = 20, kappa: float = 2.58):
        if n < 5:
            raise ValueError("n must be >= 5")
        self.n, self.kappa = n, kappa
        self._d: deque[float] = deque(maxlen=n)
        self._m: deque[float] = deque(maxlen=n)
        self._prev_close: float | None = None
        self._prev_absC = 0.0

    def state(self) -> State:
        if len(self._d) < self.n:
            return State(0.0, 0.0, 0.0, 0.0, False)
        W = sum(self._m)
        W2 = sum(x * x for x in self._m)
        S = sum(m * d for m, d in zip(self._m, self._d))
        Q = sum(m * d * d for m, d in zip(self._m, self._d))
        if W <= 0 or W2 <= 0 or Q <= 0:
            return State(0.0, 0.0, 0.0, 0.0, False)
        neff = W * W / W2
        u = sqrt(Q / W)
        C = sqrt(neff) * (S / W) / u
        return State(C, C * C / neff, sqrt(neff) * u, neff, True)

    def update(self, close: float, volume: float = 1.0) -> tuple[State, Signal | None]:
        """Consume one *closed* bar. Returns (state, signal-or-None)."""
        if self._prev_close is None:
            self._prev_close = close
            return self.state(), None
        d = close - self._prev_close
        self._prev_close = close
        self._d.append(d)
        self._m.append(volume if volume > 0 else 1.0)

        st = self.state()
        sig = None
        if st.ready:
            ignite = abs(st.C) >= self.kappa and self._prev_absC < self.kappa   # rule 1
            align = d != 0.0 and copysign(1, d) == copysign(1, st.C)            # rule 2
            if ignite and align:
                direction = 1 if st.C > 0 else -1
                sig = Signal(
                    direction=direction,
                    entry=close,                                   # live: next bar's open
                    stop=close - direction * st.ell,               # 1 diffusive sigma
                    target=close + direction * abs(st.C) * st.ell,  # inertial projection
                )
            self._prev_absC = abs(st.C)
        return st, sig


if __name__ == "__main__":
    import random

    random.seed(3)
    k = Konig(n=20)
    px, fired = 100.0, 0
    for i in range(3000):
        px += random.gauss(0.0, 1.0) + (0.9 if 1000 <= i < 1060 else 0.0)  # injected drift
        st, sig = k.update(px, volume=random.lognormvariate(0, 0.5))
        if sig:
            fired += 1
            print(
                f"bar {i:4d}  {'LONG ' if sig.direction > 0 else 'SHORT'}"
                f"  C={st.C:+6.2f}  phi={st.phi:.3f}  band={st.band}"
                f"  entry={sig.entry:8.2f}  stop={sig.stop:8.2f}"
                f"  target={sig.target:8.2f}  R:R={sig.rr:.2f}"
            )
    print(f"\n{fired} ignitions in 3000 bars")
