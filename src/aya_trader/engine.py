"""AYA-1 intraday trading engine — implementation skeleton.

Design reference: docs/TRADING_SYSTEM_DESIGN.md

This is a *skeleton*: module boundaries, dataclasses, and the safety-critical
control flow are real; model internals, broker adapters, and feed handlers are
stubs marked with `NotImplementedError` or TODO. The live engine and the
research replayer are intended to share these exact classes (no sim/real skew).

Dependencies (research + live):
    pandas numpy torch lightgbm onnxruntime databento fastapi vectorbt mlflow
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Sequence

import numpy as np

log = logging.getLogger("aya")

# --------------------------------------------------------------------------
# Shared types
# --------------------------------------------------------------------------


class Regime(Enum):
    TREND_UP = auto()
    TREND_DOWN = auto()
    RANGE = auto()
    HIGH_VOL_EVENT = auto()  # no-trade ODD exit
    ILLIQUID = auto()        # no-trade ODD exit


class HealthStatus(Enum):
    OK = auto()
    SENSOR_DEGRADED = auto()     # feeds diverge/stale -> no new entries
    EXECUTION_DEGRADED = auto()  # broker state mismatch -> no new entries
    HALTED = auto()              # kill switch engaged -> flatten + disable


class Side(Enum):
    LONG = 1
    SHORT = -1


@dataclass(frozen=True)
class Bar:
    ts_exchange_ns: int
    open: float
    high: float
    low: float
    close: float
    volume: int
    signed_volume: int
    mean_spread_ticks: float


@dataclass(frozen=True)
class StateVector:
    bar: Bar
    features: np.ndarray          # ~60 engineered features, z-scored, PIT-correct
    embedding: np.ndarray         # 32-dim TCN embedding
    regime: Regime
    drift_score: float            # Mahalanobis distance vs training distribution
    health: HealthStatus


@dataclass(frozen=True)
class Signal:
    p_up: float                   # calibrated P(profit barrier hit before loss barrier)
    q_ret: tuple[float, float, float]   # 10/50/90 quantile of horizon return (points)
    vol_forecast: float           # forecast sigma over label horizon (points)
    ensemble_std: float           # disagreement -> "fog" veto
    meta_p: float                 # P(trade nets > 0 after friction | signal fired)
    explanation: dict             # SHAP top-k from meta-labeler, logged per decision


@dataclass
class OrderIntent:
    side: Side
    qty: int
    stop_points: float
    target_points: float
    ttl_bars: int
    signal_price: float
    uuid: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def risk_dollars_per_contract(self) -> float:
        return self.stop_points * CONFIG["point_value"]


@dataclass
class Verdict:
    ok: bool
    failed_checks: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Configuration (all risk numbers from design doc §4; A6: $100k reference)
# --------------------------------------------------------------------------

CONFIG = {
    "instrument": "MES",
    "point_value": 5.0,               # MES: $5 / index point
    "tick_size": 0.25,
    "friction_rt_dollars": 5.0,       # A3: measured round-trip; backtests use 2x
    # sizing (§4.1)
    "risk_per_trade_frac": 0.0035,
    "hard_contract_cap": 5,
    "max_heat_frac": 0.006,
    # thresholds (§3.3) — regime-adjusted at runtime
    "p_up_min": {"TREND": 0.58, "RANGE": 0.62},
    "p_up_full_size": 0.63,
    "meta_p_min": 0.55,
    "ensemble_std_max": 0.08,
    "edge_vs_friction_min": 2.0,
    "stop_sigma_mult": 1.3,
    "target_sigma_mult": 1.8,
    "label_horizon_bars": 15,
    # loss ladder (§4.2)
    "daily_soft_frac": 0.010,
    "daily_hard_frac": 0.015,
    "weekly_halt_frac": 0.030,
    "dd_offline_frac": 0.06,
    "consecutive_losses_degrade": 3,
    # session clock (ET)
    "no_entry_after": "15:30",
    "flatten_at": "15:55",
    "no_entry_first_minutes": 3,
    "event_blackout_before_min": 10,
    "event_blackout_after_min": 5,
    # execution (§5.1)
    "max_chase_ticks": 2,
    "entry_ttl_s": 2.0,
    "slippage_halt_ratio": 2.0,
    # perception health (§2.1)
    "feed_stale_s": 2.0,
    "feed_divergence_ticks": 2,
    "drift_block_threshold": 4.0,     # Mahalanobis units; extrapolation => no-trade
}


# --------------------------------------------------------------------------
# PERCEPTION — sensors -> clean state vector
# --------------------------------------------------------------------------


class FeedHealth:
    """Cross-checks two independent L1 feeds; measures latency & staleness."""

    def __init__(self):
        self.status = HealthStatus.OK

    def check(self, tick) -> None:
        # TODO: staleness (> feed_stale_s), cross-feed price divergence
        # (> feed_divergence_ticks for >3s), monotonic exchange timestamps,
        # latency percentiles as first-class metrics.
        pass


class VolumeBarBuilder:
    """Volume-clock bars: constant activity per bar, not constant time."""

    def __init__(self, contracts_per_bar: int = 2500):
        self.threshold = contracts_per_bar
        self._acc: list = []

    def update(self, tick) -> Optional[Bar]:
        self._acc.append(tick)
        if sum(t.size for t in self._acc) < self.threshold:
            return None
        bar = self._to_bar(self._acc)
        self._acc = []
        return bar

    def _to_bar(self, ticks) -> Bar:
        raise NotImplementedError("aggregate ticks -> Bar (incl. signed volume)")


class FeatureComputer:
    """Single source of truth for features — imported by BOTH research and live.

    Point-in-time correct; z-scored against rolling regime-conditional
    distributions. Feature groups per design doc §2.3.
    """

    VERSION = "feat-v1.0"

    def compute(self, bar: Bar) -> np.ndarray:
        raise NotImplementedError


class DriftMonitor:
    """Extrapolation detector: Mahalanobis distance of the live feature vector
    against the training distribution + PSI per feature (alarm feed)."""

    def score(self, features: np.ndarray) -> float:
        raise NotImplementedError


class Perception:
    def __init__(self, encoder, regime_clf):
        self.health = FeedHealth()
        self.volume_bars = VolumeBarBuilder()
        self.features = FeatureComputer()
        self.encoder = encoder          # ONNX TCN, <2ms CPU
        self.regime_clf = regime_clf    # GBT/HMM, deliberately simple
        self.drift = DriftMonitor()
        self._window: list[Bar] = []    # last 128 bars for the encoder

    def on_tick(self, tick) -> Optional[StateVector]:
        self.health.check(tick)
        bar = self.volume_bars.update(tick)
        if bar is None:
            return None                 # no new bar => no new decision
        self._window = (self._window + [bar])[-128:]
        f_eng = self.features.compute(bar)
        f_emb = self.encoder.embed(self._window)
        regime = self.regime_clf.predict(f_eng)
        return StateVector(bar, f_eng, f_emb, regime,
                           self.drift.score(f_eng), self.health.status)


# --------------------------------------------------------------------------
# PREDICTION — ensemble direction model + meta-labeler
# --------------------------------------------------------------------------


class Prediction:
    def __init__(self, ensemble: Sequence, meta_labeler, calibrators: Sequence):
        self.ensemble = ensemble          # 3 walk-forward-shifted TCN+MLP + 1 slow
        self.meta = meta_labeler          # LightGBM on the primary's own signals
        self.calibrators = calibrators    # isotonic, fit on validation folds

    def infer(self, s: StateVector) -> Signal:
        outs = [cal(m(s.features, s.embedding, s.regime))
                for m, cal in zip(self.ensemble, self.calibrators)]
        p_up = self._regime_weighted_mean([o["p_up"] for o in outs], s.regime)
        std = float(np.std([o["p_up"] for o in outs]))
        q = self._pool_quantiles([o["q_ret"] for o in outs])
        vol = float(np.mean([o["p_vol"] for o in outs]))
        meta_x = self._meta_features(s, p_up, std)
        meta_p = float(self.meta.predict_proba(meta_x))
        expl = self.meta.shap_top_k(meta_x, k=5)   # human-auditable "why"
        return Signal(p_up, q, vol, std, meta_p, expl)

    def _regime_weighted_mean(self, ps, regime) -> float:
        raise NotImplementedError

    def _pool_quantiles(self, qs) -> tuple[float, float, float]:
        raise NotImplementedError

    def _meta_features(self, s, p_up, std) -> np.ndarray:
        raise NotImplementedError


# --------------------------------------------------------------------------
# RISK LAYER — zero ML, simpler than everything it guards, veto is final
# --------------------------------------------------------------------------


class RiskLayer:
    """Every check returns (name, passed). ANY failure vetoes. No model output
    can override a veto; the failed-check list is logged with every decision."""

    def __init__(self, account, session, calendar):
        self.acct, self.session, self.calendar = account, session, calendar

    def approve(self, intent: OrderIntent, s: StateVector) -> Verdict:
        c = CONFIG
        checks = {
            "regime_tradable": s.regime not in (Regime.HIGH_VOL_EVENT, Regime.ILLIQUID),
            "sensors_ok": s.health is HealthStatus.OK,
            "in_distribution": s.drift_score < c["drift_block_threshold"],
            "not_event_window": not self.calendar.in_blackout(
                c["event_blackout_before_min"], c["event_blackout_after_min"]),
            "session_window": self.session.entries_allowed(),
            "daily_soft_ok": self.acct.daily_pnl_frac() > -c["daily_soft_frac"],
            "weekly_ok": self.acct.weekly_pnl_frac() > -c["weekly_halt_frac"],
            "dd_ok": self.acct.drawdown_frac() < c["dd_offline_frac"],
            "heat_ok": (self.acct.open_heat_frac()
                        + intent.qty * intent.risk_dollars_per_contract / self.acct.equity()
                        <= c["max_heat_frac"]),
            "correlation_budget_ok": self.acct.correlated_exposure_ok(intent),
            "consecutive_losses_ok": self.acct.consecutive_losses()
                                     < c["consecutive_losses_degrade"] or intent.qty <= 1,
        }
        failed = [name for name, ok in checks.items() if not ok]
        return Verdict(ok=not failed, failed_checks=failed)


def position_size(equity: float, stop_points: float, confidence_bucket: float,
                  in_drawdown_frac: float) -> int:
    """Vol-targeted size with quarter-Kelly ceiling semantics (§4.1)."""
    sizing_equity = equity * min(1.0, 1.0 - 0.5 * in_drawdown_frac)
    risk_dollars = sizing_equity * CONFIG["risk_per_trade_frac"]
    per_contract = stop_points * CONFIG["point_value"]
    n = int(risk_dollars // max(per_contract, 1e-9))
    n = int(n * confidence_bucket)                    # 0.0 / 0.5 / 1.0 — coarse on purpose
    return max(0, min(n, CONFIG["hard_contract_cap"]))


# --------------------------------------------------------------------------
# PLANNER — deterministic, auditable policy. ML proposes, rules dispose.
# --------------------------------------------------------------------------


class Planner:
    def __init__(self, risk: RiskLayer, decision_log, account):
        self.risk, self.log, self.acct = risk, decision_log, account

    def decide(self, s: StateVector, sig: Signal) -> Optional[OrderIntent]:
        template = self._template_for(s.regime)       # trend / meanrev / None
        if template is None:
            return None
        side = template.side(sig)
        if side is None or not self._entry_ok(s, sig, template):
            self.log.decision(s, sig, intent=None, verdict=None, reason="threshold")
            return None
        stop = CONFIG["stop_sigma_mult"] * sig.vol_forecast
        target = CONFIG["target_sigma_mult"] * sig.vol_forecast
        bucket = 1.0 if max(sig.p_up, 1 - sig.p_up) >= CONFIG["p_up_full_size"] else 0.5
        qty = position_size(self.acct.equity(), stop, bucket, self.acct.drawdown_frac())
        if qty == 0:
            return None
        intent = OrderIntent(side, qty, stop, target,
                             ttl_bars=3 * CONFIG["label_horizon_bars"],
                             signal_price=s.bar.close)
        verdict = self.risk.approve(intent, s)
        self.log.decision(s, sig, intent, verdict)    # EVERY decision, full state
        return intent if verdict.ok else None

    def _entry_ok(self, s: StateVector, sig: Signal, template) -> bool:
        c = CONFIG
        p_dir = max(sig.p_up, 1 - sig.p_up)
        friction_pts = 2 * c["friction_rt_dollars"] / c["point_value"]  # 2x measured (A3)
        return (p_dir >= template.p_up_min
                and sig.meta_p >= c["meta_p_min"]
                and sig.ensemble_std <= c["ensemble_std_max"]
                and abs(sig.q_ret[1]) >= c["edge_vs_friction_min"] * friction_pts)

    def manage_open(self, s: StateVector, sig: Signal) -> None:
        """Exchange brackets handle stop/target; here we handle the soft exits:
        signal decay (p flips through 0.50), time stop, session flatten."""
        raise NotImplementedError

    def _template_for(self, regime: Regime):
        raise NotImplementedError   # TREND_* -> trend-continuation; RANGE -> VWAP meanrev


# --------------------------------------------------------------------------
# EXECUTION — idempotent OMS; brackets live AT THE EXCHANGE
# --------------------------------------------------------------------------


class Execution:
    def __init__(self, broker, slippage_log):
        self.broker, self.slippage_log = broker, slippage_log
        self.mode = HealthStatus.OK

    def submit(self, intent: OrderIntent) -> None:
        # Marketable limit capped at touch + max_chase_ticks; cancel after ttl.
        # OCO stop/target bracket attached atomically at the exchange on fill.
        self.broker.place_bracket(intent,
                                  max_chase_ticks=CONFIG["max_chase_ticks"],
                                  entry_ttl_s=CONFIG["entry_ttl_s"])

    def on_fill(self, fill, intent: OrderIntent) -> None:
        slip_ticks = abs(fill.price - intent.signal_price) / CONFIG["tick_size"]
        self.slippage_log.record(intent, fill, slip_ticks)   # closes sim-to-real loop

    def reconcile(self) -> None:
        """Every 1s: intended state vs broker-reported state. Mismatch =>
        EXECUTION_DEGRADED (no new entries) + human alert. Catches duplicate
        orders, lost acks, zombie positions — the 'stuck actuator' class."""
        if not self.broker.state_matches(self._intended_state()):
            self.mode = HealthStatus.EXECUTION_DEGRADED
            log.critical("OMS reconciliation mismatch — entries disabled")

    def flatten_all(self) -> None:
        self.broker.cancel_all_and_flatten()   # market orders; must never raise

    def _intended_state(self):
        raise NotImplementedError


class PhantomExecution(Execution):
    """Shadow mode: identical interface, fills modeled from live quotes
    (limit fills require trade-through, not touch). Same code path as live —
    the whole point is zero sim/real skew."""

    def submit(self, intent: OrderIntent) -> None:
        raise NotImplementedError

    def flatten_all(self) -> None:
        pass


# --------------------------------------------------------------------------
# MONITOR — separate process/host; the minimal-risk-maneuver owner
# --------------------------------------------------------------------------


class Monitor:
    """Runs OUTSIDE the engine process. If the engine dies, this still fires.
    Broker-side max-position/daily-loss limits back THIS up (defense in depth)."""

    def __init__(self, broker, account, alerts, engine_heartbeat):
        self.broker, self.acct, self.alerts = broker, account, alerts
        self.heartbeat = engine_heartbeat

    def loop_once(self) -> None:
        c = CONFIG
        if self.heartbeat.missed() >= 3:
            self.broker.cancel_all_and_flatten()
            self.alerts.page("engine heartbeat lost — flattened")
        if self.acct.daily_pnl_frac() <= -c["daily_hard_frac"]:
            self.broker.cancel_all_and_flatten()
            self.alerts.page("L4 daily hard stop — flattened, human re-arm required")
        if self.acct.live_slippage_ratio() > c["slippage_halt_ratio"]:
            self.alerts.page("live slippage >2x model — entries halted for review")
        self.alerts.push_state_to_tradingview()   # HMI mirror (webhook -> Pine overlay)
        self.alerts.push_state_to_grafana()


# --------------------------------------------------------------------------
# MAIN LOOP — live and shadow share this exact path
# --------------------------------------------------------------------------


def run_session(feed, perception: Perception, prediction: Prediction,
                planner: Planner, execution: Execution, session) -> None:
    while session.is_open():
        tick = feed.next(timeout_s=1.0)
        if tick is None:
            continue
        state = perception.on_tick(tick)
        if state is None:
            continue                      # decisions only on new volume bars
        signal = prediction.infer(state)
        planner.manage_open(state, signal)             # decay/time/flatten exits
        if session.must_flatten():                     # 15:55 ET, unconditional
            execution.flatten_all()
            break
        intent = planner.decide(state, signal)
        if intent is not None:
            execution.submit(intent)
        execution.reconcile()


if __name__ == "__main__":
    raise SystemExit(
        "Skeleton only — wire feeds/broker/models per docs/TRADING_SYSTEM_DESIGN.md. "
        "Promotion ladder (§6.3): backtest gates -> shadow -> paper -> 25% live -> live."
    )
