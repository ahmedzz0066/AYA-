# AYA-1: An FSD-Grade Intraday Trading System

**Design document v1.0 — 2026-07-15**
**Status:** Design / pre-implementation
**Target instruments:** MES/MNQ (micro E-mini S&P/Nasdaq futures) primary; SPY/QQQ equities secondary; EURUSD/XAUUSD deferred to v3 (see roadmap)
**Horizon:** Intraday only. Flat by 15:55 ET, hard. No overnight risk, ever.

---

## 0. Framing, Honesty, and Assumptions (read first)

This document applies autonomous-driving engineering discipline to intraday trading. The analogy is
useful because both domains share the same failure geometry: a noisy, partially observable,
non-stationary, **adversarial** environment where the cost of a rare failure dwarfs the benefit of
many small successes. But the analogy breaks in one critical place, and the whole design honors it:

> **In driving, the environment does not adapt to defeat you. In markets, it does.**
> Roads don't learn your policy and front-run it. Other market participants do. Therefore every
> edge decays, every backtest is optimistic, and the *continuous learning loop is not a
> nice-to-have — it is the product.*

### Hard assumptions (flagged, per instructions)

| # | Assumption | Why it matters | Mitigation if false |
|---|-----------|----------------|---------------------|
| A1 | TradingView is **monitoring + alerting only**, not the execution or inference engine. Pine Script cannot run neural nets, has no L2 data, and webhook alerts have 1–5 s latency and no delivery guarantee. | Determines the whole architecture. | None needed — this is a fact, not a bet. Execution runs in our own Python service. |
| A2 | We target **1–15 minute holding periods**, not sub-second HFT. | Retail/prosumer infra (≈50–300 ms round trip) cannot win latency games. Our edge must be *predictive*, not *fast*. | If fills degrade, widen horizon further, never shorten it. |
| A3 | Realistic per-trade friction on MES: ~$1.24 commission/side + 1 tick ($1.25) average slippage per side ⇒ ≈ **$5.00 round trip per contract** ≈ 0.4 index points. Backtests use **2×** this. | Most "profitable" intraday backtests die here. | If live friction exceeds 2× model, halt and re-measure. |
| A4 | Net out-of-sample edge, if it exists at all, will be **small**: think 0.05–0.15 R expectancy per trade, Sharpe 1.0–2.0 annualized *after* friction. Anyone promising Sharpe > 3 intraday at retail latency is curve-fitting. | Sets realistic success criteria (§6). | If validation shows Sharpe < 0.8 OOS, the system does not deploy. Full stop. |
| A5 | Historical L2/order-flow data is purchasable (Databento, Polygon, dxFeed) and live feeds cost $100–500/mo. | Sensor suite depends on it. | v1 can run on L1 + volume-derived proxies (see §2). |
| A6 | Capital base for sizing math: $100k notional account, micro contracts. Scale linearly only after §6 gates pass. | All risk numbers below reference this. | Recompute limits for actual capital. |
| A7 | **Nothing here is a guarantee of profit.** This is an engineering process for *finding and safely exploiting* an edge, with gates that prevent deployment if no edge is found. The most likely outcome of v1 validation is "no deployable edge yet" — and the system is designed to tell us that truthfully rather than flatter us. | Intellectual honesty is the first safety system. | — |

---

## 1. System Overview — Architecture

Same five-stage decomposition as an AV stack, plus the offline loop that actually creates the value:

```
                        ┌──────────────────────────────────────────────────────────┐
                        │                     OFFLINE / FLEET LOOP                 │
                        │  Data lake ─ Label factory ─ Training ─ Backtest/Sim ─   │
                        │  Walk-forward eval ─ Model registry ─ Shadow deploy      │
                        └───────────────▲──────────────────────────┬───────────────┘
                                        │ trade logs, features,    │ signed model
                                        │ regime tags, slippage    │ artifacts
                                        │                          ▼
 ┌───────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
 │ SENSORS   │──▶│ PERCEPTION   │──▶│ PREDICTION   │──▶│ PLANNING     │──▶│ EXECUTION    │
 │ (feeds)   │   │ (state est.) │   │ (models)     │   │ (policy+risk)│   │ (order mgmt) │
 └───────────┘   └──────────────┘   └──────────────┘   └──────┬───────┘   └──────┬───────┘
   L1/L2 mkt data   bar builder       direction p(up)     entry/exit/size    broker API
   trades tape      feature vector    vol forecast        stops/targets      order types
   news/macro cal   regime classifier meta-labeler        risk vetoes        fill tracking
   cross-asset      data QA/health    (ensemble)          kill switches      slippage log
                                                                 │
                        ┌────────────────────────────────────────▼───────────────┐
                        │                    MONITORING / MRM                    │
                        │  Watchdogs ─ P&L & drawdown guards ─ feature drift ─   │
                        │  TradingView dashboards & alert webhooks ─ human HMI ─ │
                        │  "Minimal Risk Maneuver" = FLATTEN AND HALT            │
                        └─────────────────────────────────────────────────────────┘
```

**Module responsibilities (one line each):**

- **Sensors** — redundant market data ingestion; like camera+radar, we never trust one feed.
- **Perception** — turn raw ticks into a clean, versioned state vector: bars, features, regime, data-health flags.
- **Prediction** — learned models estimate short-horizon return distribution + probability the *setup* works (meta-labeling).
- **Planning** — deterministic, auditable policy layer: converts predictions into orders *subject to risk vetoes*. **ML proposes, rules dispose.**
- **Execution** — order management with idempotency, OCO brackets, fill/slippage telemetry.
- **Monitoring / MRM** — watchdogs at every layer; the trading equivalent of "pull over and stop" is **flatten all positions and disable entries**. It must be reachable from every state, in one action, with no model in the loop.

**Key architectural decision (mirrors FSD's planner):** we do **not** let a neural net emit orders
end-to-end in v1. The net outputs calibrated probabilities and distributions; a small, fully
interpretable planner turns them into orders. Reasons: (a) auditability — you can't debug a blown
account with a saliency map; (b) safety invariants (max loss, position caps) must be *provably*
enforced outside the learned component, exactly like an AV's collision-check layer sits outside the
policy net. End-to-end RL is a v4 experiment behind shadow-mode gates (§8).

**Where TradingView fits (per A1):**
- Charting/HMI for the human supervisor: our engine pushes its state (regime, signal, position, stops) to a TradingView chart via a webhook-driven Pine indicator or simply mirrors on a self-hosted dashboard.
- **Independent cross-check alerts:** simple Pine scripts (e.g., "price crossed VWAP ± 2σ", "session loss guard") fire webhooks to our engine as a *redundant sensor* — a cheap "ultrasonic" that can veto or wake the operator if the primary stack disagrees with reality.
- Optionally, v0 signal prototyping in Pine before porting to Python.

---

## 2. Data Pipeline & Features (Sensor Fusion)

### 2.1 Inputs (the sensor suite)

| Sensor | Content | Cadence | AV analogy | v1? |
|---|---|---|---|---|
| Primary market data (Databento/dxFeed/Rithmic) | trades + L1 quotes, MES/MNQ/ES/NQ | tick | main camera | ✅ |
| L2 / MBP-10 depth | top-10 book levels | tick | radar | v2 |
| Secondary feed (broker feed, e.g., IBKR/Tradovate) | L1 snapshot | 250 ms | redundant camera | ✅ |
| Cross-asset context | ES vs NQ spread, VIX, DXY, 2s10s, TICK, ADD, sector ETFs | 1 s–1 min | map / traffic flow | ✅ |
| Economic calendar (pre-known) | FOMC, CPI, NFP, earnings times | daily file | construction-zone map | ✅ |
| News/sentiment (headline embargo detector) | low-latency headline flags, not NLP alpha | event | emergency-vehicle siren | v2 |
| TradingView webhook cross-checks | independent simple-rule alerts | seconds | ultrasonic | ✅ |

**Redundancy rule:** two independent L1 sources; if they disagree (last price divergence > 2 ticks
for > 3 s, or one goes stale > 2 s during RTH), perception raises `SENSOR_DEGRADED` → planner
blocks new entries (existing brackets remain live at the exchange, so we stay protected).

### 2.2 Preprocessing (perception front-end)

1. **Time discipline:** all timestamps exchange-time, monotonic checks, feed latency measured continuously (it's a first-class health metric).
2. **Bar building:** primary clock is **volume bars** (e.g., 2,500 contracts/bar for MES-equivalent flow) not time bars — information arrives per unit of *activity*, not per minute; this normalizes the "frame rate" across quiet lunch and frantic open, the same reason AV perception normalizes exposure. Time bars (1m/5m) kept for human display and TradingView mirroring.
3. **Outlier handling:** median-of-feeds price; reject prints > 10σ of 1-s returns unless confirmed by both feeds (bad-tick = lens flare).
4. **Feature store:** every feature computed live is computed by the *same code* in research (single library, point-in-time correct, versioned). Train/serve skew is the trading equivalent of sim-to-real gap — we kill it at the source.

### 2.3 Engineered features (~60 total; interpretable "classical CV" channel)

Grouped, all z-scored against rolling regime-conditional distributions:

- **Price/trend:** multi-horizon log returns (5/15/30/60 bars), distance from VWAP in σ-units, distance from session open/high/low, EMA(9/21/55) slopes and spreads, opening-range position.
- **Volatility:** realized vol (Yang–Zhang, multiple windows), ATR percentile vs 20-day, vol-of-vol, intraday vol curve residual (is *this* 11:00 quieter than a normal 11:00?), VIX level + 1-day change.
- **Volume/flow (L1-derived proxies for v1):** relative volume vs time-of-day curve, signed tick volume (uptick − downtick), trade-size distribution shift, VWAP-anchored cumulative delta, large-print detector.
- **Order book (v2, with L2):** top-5 imbalance, depth-weighted mid, book slope, quote churn/spoof-iness score, liquidity-at-touch percentile.
- **Cross-asset:** NQ−ES relative strength, TICK/ADD internals, DXY & rates 15-min momentum, sector dispersion.
- **Context/clock:** minutes since open (sin/cos), day-of-week, minutes to next scheduled event (capped), overnight gap size, prior-day range position.

### 2.4 Learned features

A small **causal temporal-convolution encoder** (TCN) over the last 128 volume bars of raw
(OHLCV + signed volume + spread) → 32-dim embedding. This is the "learned backbone" channel that
picks up microstructure patterns hand-crafted features miss. It is trained jointly with the heads
(§3) but its output is logged per decision so drift is monitorable.

### 2.5 Regime classifier (the "scene understanding" module)

Separate, deliberately simple model (gradient-boosted trees or 5-state Gaussian HMM on
{trend strength, RV percentile, volume anomaly, event proximity}) emitting one of:

`TREND_UP · TREND_DOWN · RANGE · HIGH_VOL_EVENT · ILLIQUID/HALTED`

Regime gates *everything* downstream: which sub-models vote, thresholds, sizing multipliers, and
whether trading is allowed at all. `HIGH_VOL_EVENT` and `ILLIQUID` are no-trade states, exactly like
weather-based ODD (operational design domain) exits in an AV. **The system must know when it is
outside its ODD, and the default outside the ODD is: do nothing.**

---

## 3. Core Model / Logic

### 3.1 Two-stage prediction: direction model + meta-labeler

Stage 1 — **Direction/return model** (the "trajectory predictor"):

- Input: 60 engineered features + 32-dim TCN embedding + regime one-hot.
- Backbone: TCN encoder → 2-layer MLP heads. (~200k params total — deliberately small; intraday datasets are ~10⁵–10⁶ effective samples and big transformers just memorize. Sub-ms CPU inference, satisfying the real-time budget trivially.)
- Heads:
  - `p_up`: P(next-horizon return > +θ before < −θ) — triple-barrier style label (profit barrier, loss barrier, time barrier ≈ 15 volume-bars).
  - `q_ret`: quantile regression (τ = 0.1/0.5/0.9) of horizon return → gives an uncertainty interval, our "perception confidence".
  - `p_vol`: short-horizon realized-vol forecast → feeds sizing and barrier widths.
- **Calibration is mandatory:** isotonic/temperature calibration on validation folds; a model that says 0.62 must win ~62%. Uncalibrated probability is uncalibrated perception — worthless for planning.

Stage 2 — **Meta-labeler** (the "should I act on this detection?" gate — López de Prado's trick, and the single highest-value ML pattern in this domain):

- Gradient-boosted classifier (LightGBM) answering: *given the primary model has signaled, what's the probability this trade nets > 0 after friction?*
- Trained on the primary model's own historical signals with realized outcomes; features include the signal's context (regime, spread, time-of-day, feature-drift score, recent model hit-rate).
- This is also our chief **explainability** device: SHAP values on the meta-labeler give a human-readable "why we took / skipped this trade" for every decision, logged alongside the trade.

### 3.2 Ensemble & disagreement

Three primary models trained on shifted walk-forward windows + one "slow" model trained on 3× the
history. Combined by regime-conditional weighted average. **Ensemble disagreement (std of `p_up`) is
itself a feature and a veto:** high disagreement = low visibility = don't drive fast in fog.

### 3.3 Entry / exit policy (the deterministic planner)

```
ENTER LONG iff ALL of:
  p_up_ensemble        ≥ 0.58            (calibrated; regime-adjusted, e.g. 0.62 in RANGE)
  meta_label_p         ≥ 0.55
  ensemble_std         ≤ 0.08
  q_ret_median         ≥ 2.0 × expected_friction
  regime               ∈ {TREND_UP, RANGE}   (RANGE only for mean-reversion template)
  risk_layer.approve() == True           (§4 — can veto for ANY reason, never overridden)
(mirror for shorts)

EXIT on FIRST of:
  bracket stop (at exchange)             = entry ∓ 1.3 × forecast_σ_horizon
  bracket target (at exchange)           = entry ± 1.8 × forecast_σ_horizon   (asymmetric, R:R ≈ 1.4)
  signal decay: p_up_ensemble < 0.50     → exit at market ("the reason we entered is gone")
  time stop: 3 × label horizon elapsed   → exit ("thesis expired")
  session close 15:55 ET                 → mandatory flatten
  ANY safety trigger (§7)                → flatten
```

Two policy templates share this skeleton with different thresholds/barriers: **trend-continuation**
(active in TREND regimes) and **VWAP mean-reversion** (active in RANGE). The regime classifier picks
the template; the models score within it.

**Confidence → action mapping is monotone and coarse** (skip / half-size / full-size at
p ≥ 0.58 / 0.63). Coarse buckets resist overfitting to the third decimal of a probability.

---

## 4. Risk & Capital Management (the "do no harm" layer)

Non-negotiable design rule, identical to AV safety architecture: **the risk layer is code-separate
from the ML stack, simpler than everything it guards, and its vetoes cannot be overridden by any
model output.** It would still function if the models returned garbage.

### 4.1 Position sizing

Volatility-targeted with a fractional-Kelly ceiling:

```
risk_per_trade      = 0.35% of equity                      (≤ quarter-Kelly for our edge estimates)
stop_distance       = 1.3 × forecast_σ_horizon (in points)
contracts           = floor( (equity × 0.0035) / (stop_distance × point_value) )
contracts           = min(contracts, hard_cap)             (hard_cap = 5 micros at $100k, period)
size_multiplier     = 1.0 normal · 0.5 low-confidence bucket or elevated-vol regime
                      · 0.0 whenever ODD is violated
```

Full Kelly is never used: Kelly assumes you *know* your edge; we only estimate it, with error bars,
in a non-stationary world. Quarter-Kelly keeps estimation error from becoming ruin.

### 4.2 Loss limits — layered like AV braking (comfort → emergency)

| Layer | Trigger | Action | Reset |
|---|---|---|---|
| L1 per-trade | bracket stop | position closed | immediate |
| L2 consecutive | 3 losses in a row | halve size, raise entry thresholds +0.03 | 2 wins or next session |
| L3 daily soft | −1.0% equity day | no new entries, manage open exits | next session |
| L4 daily hard | −1.5% equity day | **flatten + disable**; human must re-arm | human review |
| L5 weekly | −3% week | disabled until weekly review | human review |
| L6 drawdown | −6% from HWM | system offline; full re-validation (§6) required before re-arm | full gate re-run |

Sizes also scale down inside a drawdown: `equity_for_sizing = min(equity, HWM × (1 − 0.5 × dd))` —
the system drives slower after a near-miss.

### 4.3 Portfolio heat & correlation controls

- Max concurrent positions: 2 (v1: usually 1). Combined open risk ("heat") ≤ 0.6% equity.
- MES and MNQ count as **one** correlated exposure (ρ > 0.9); never long one and size-stacked in the other. Cross-asset module computes rolling correlations; any pair with |ρ| > 0.7 shares a single heat budget.
- No entries within 10 min before / 5 min after scheduled Tier-1 events (FOMC, CPI, NFP); no entries first 3 min after open; no new entries after 15:30 ET.

### 4.4 Structural safeguards

- Stops/targets live **at the exchange** as OCO brackets, not in our process — if our box dies, protection survives (the "mechanical brake" independent of the compute stack).
- Watchdog heartbeat: if the engine misses 3 heartbeats, an independent tiny process (separate host/VPS) issues flatten-all via broker API and pushes phone + TradingView alerts.
- Broker-side max position and daily-loss limits configured as a final backstop (defense in depth: our bug ≠ account death).

---

## 5. Execution & Infrastructure

### 5.1 Order logic

- **Entries:** marketable limit (cross the spread but capped at +1 tick beyond touch). Unfilled in 2 s → cancel, re-evaluate; never chase more than 2 ticks from signal price. Chasing converts a good signal into a bad price — the model's edge is measured *from signal price*.
- **Exits:** OCO bracket placed atomically with entry fill. Signal-decay/time exits go as marketable limits with a 1-s market-order fallback. 15:55 flatten is always market.
- **Idempotency & state:** every order has a client-side UUID; the OMS reconciles its intended state vs broker-reported state every 1 s; any mismatch → `EXECUTION_DEGRADED` → no new entries, alert human. (Duplicate orders from retries are the trading version of a stuck actuator — reconciliation is what catches it.)
- **Slippage telemetry:** every fill logs signal-time price vs fill price; live distribution is compared weekly to the backtest friction model (A3). Live slippage > 2× modeled → auto-halt for review. *This closes the sim-to-real loop for execution.*

### 5.2 Stack & latency budget

| Component | Choice (v1) | Budget |
|---|---|---|
| Feed handler → feature update | Rust or Cython hot path, ring buffers | < 5 ms |
| Model inference | PyTorch → ONNX Runtime, CPU | < 2 ms |
| Planner + risk checks | pure Python, no allocation in hot path | < 1 ms |
| Order to broker (Tradovate/Rithmic/IBKR API) | REST/WebSocket | 30–150 ms network |
| **Total decision-to-wire** | | **< 200 ms** — fine for minutes-horizon (A2) |

Colocated VPS near the broker's gateway (e.g., Chicago for CME) is a cheap 30–80 ms improvement
for v2; v1 explicitly does not depend on it.

- Deployment: Docker; engine + watchdog on separate hosts; append-only event log (every tick decision optional, every feature-vector-at-signal mandatory) → this *is* the training data flywheel.
- HMI: Grafana or self-hosted dashboard + TradingView chart mirror + phone push for all state transitions (armed/halted/flattened).

---

## 6. Validation & Performance Metrics (the release gate)

An FSD build doesn't ship because it "drove well on Tuesday." Same standard here — a strict
promotion ladder, each gate mandatory:

### 6.1 Backtest protocol

1. **Data hygiene:** point-in-time everything; purged & embargoed splits (embargo ≥ label horizon) so labels never leak across boundaries; costs = 2× measured friction (A3); fills modeled conservatively (limit fills require price to *trade through* the limit, not touch it).
2. **Walk-forward:** train 12 months → validate 1 month → test 1 month, roll monthly across ≥ 6 years (must include 2020 COVID crash, 2022 bear grind, 2024 vol events — every "weather condition" in the dataset). **No global hyperparameter search on the full set** — hyperparams chosen once on the earliest 2 years, frozen.
3. **Regime-sliced scorecards:** metrics reported *per regime*, not just aggregate. A system that makes everything in trends and dies in ranges is only deployable with a regime gate that provably keeps it out of ranges.
4. **Monte Carlo:** (a) trade-order bootstrap → drawdown distribution (need P95 max-DD ≤ 1.5× historical max-DD); (b) friction perturbation ±50%; (c) entry timing jitter ±1 bar — edge must survive all three. Edge that dies under 1 bar of jitter is a data artifact, not an edge.
5. **Stress replays:** full tick replays of 2010 flash crash (proxy), Aug 2015 open, Feb 2018 Volmageddon, Mar 2020, plus synthetic: feed freeze mid-position, 10-tick gap through stop, exchange halt. **Pass criterion is graceful degradation, not profit** — the system must flatten/halt correctly.
6. **Deflated Sharpe / multiple-testing control:** every configuration ever evaluated is counted; report the deflated Sharpe. This is our defense against ourselves — the researcher is the biggest overfitting risk in the building.

### 6.2 Success criteria (deploy/no-deploy — conservative per A4)

| Metric (OOS walk-forward, after 2× friction) | Gate |
|---|---|
| Sharpe (annualized, daily P&L) | ≥ 1.0 |
| Sortino | ≥ 1.4 |
| Calmar | ≥ 1.5 |
| Max drawdown | ≤ 8% (target ≤ 6%) |
| Profit factor | ≥ 1.25 |
| Win rate | 45–60% (outside band ⇒ investigate label/friction bug) |
| Expectancy | ≥ +0.05 R per trade |
| Trades/day | 2–8 (enough sample, low enough friction) |
| % profitable walk-forward windows | ≥ 60%, no window < −3% |
| Deflated Sharpe p-value | < 0.05 |

### 6.3 Promotion ladder (each stage 100% green before next)

```
Backtest gates → 8+ weeks SHADOW MODE (live data, real-time inference, logged
phantom orders with modeled fills; must reproduce backtest expectancy within CI,
slippage model verified against live spread/quote data) → 4+ weeks PAPER via broker
sim → LIVE at 25% size for 4 weeks → LIVE full size. Any gate failure → back one
stage minimum. L6 drawdown at any live stage → back to shadow + full re-validation.
```

Shadow mode never stops, even in full production: the *next* model candidate always runs shadow
alongside the champion (champion/challenger), exactly like FSD shadow-mode mining disagreements
between deployed and candidate policies. Disagreement events become priority training data.

---

## 7. Edge Cases & Failure Modes

Detection + response for every known hazard. Default response to anything unrecognized:
**flatten + halt** (the minimal-risk maneuver). Unknown-unknowns get the safe default, not a guess.

| # | Hazard | Detection | Response |
|---|---|---|---|
| 1 | Scheduled macro event (FOMC/CPI/NFP) | calendar sensor | no-entry window −10/+5 min; if holding into window boundary: exit early. Regime forced `HIGH_VOL_EVENT`. |
| 2 | Unscheduled news shock | 1-s RV > 8σ of regime norm, or headline flag | cancel working orders; tighten stop to breakeven+ if profitable, else exit; entries disabled 15 min. |
| 3 | Flash crash / air pocket | 5-s return > k·σ with book evaporation | **flatten at market immediately**, halt for session, page human. We do not "buy the dip" on structural breaks. |
| 4 | Gap through stop | fill price ≪ stop price | accept (bracket at exchange limits damage); if realized loss > 2× intended, count as L4-equivalent → halt day. |
| 5 | Low liquidity (lunch, holidays, Globex-thin) | volume-bar arrival rate < 30% of ToD norm; spread > 2 ticks | `ILLIQUID` regime → no entries; existing positions managed to exit. |
| 6 | Short squeeze / one-way tape | signed volume + trend features off historical support | disagreement veto typically fires (models outside training support); explicit extrapolation detector (feature vector Mahalanobis distance > threshold) blocks entries. |
| 7 | Exchange halt / circuit breaker | feed status msgs; no prints > N s with market open | freeze OMS state, cancel nothing during halt (can't), plan exit for reopen with wide-slippage assumption; alert human. |
| 8 | Data feed failure / divergence | cross-feed monitor (§2.1) | `SENSOR_DEGRADED`: no entries; exchange-side brackets already protect open position; if both feeds dark > 30 s with a position: watchdog flattens via broker API. |
| 9 | Broker API failure | order acks missing, reconciliation mismatch | `EXECUTION_DEGRADED`: stop entries; retry with backoff; independent watchdog channel for flatten; phone alert. |
| 10 | Model regression post-deploy | rolling 30-trade hit rate < 5th pct of backtest distribution; calibration error drift; feature drift (PSI) alarms | auto-revert to previous model from registry (blue-green), or halt if none healthy. |
| 11 | Ourselves (overrides, "just this once") | — | config changes require 2-step confirm + are logged; **no manual entries through the engine**; manual flatten is always one button, manual *entry* doesn't exist. Human can always make the system safer, never riskier, in-session. |
| 12 | Regime never seen before (new microstructure, tick-size change, contract roll) | extrapolation detector + calendar (roll dates hard-coded) | roll days: reduced size, remapped continuous contract verified; extrapolation: no-trade. |

---

## 8. Iteration Roadmap (release trains, FSD-style)

Each version ships only through the §6.3 ladder. Data flywheel is the constant: every live/shadow
decision logged with full feature state = next version's training set, with **hard-example mining**
(losing trades, vetoed trades, disagreement events) over-weighted, exactly like mining
interventions and disengagements.

- **v0 (weeks 0–6) — "Data & sim rig before the car":** data pipeline, feature store, backtester with friction model, TradingView HMI skeleton. Baseline *rules-only* strategies (VWAP reversion, opening-range trend) to validate the rig end-to-end and set the bar the ML must beat. If plumbing can't make simple rules break even before costs, fix plumbing.
- **v1 (weeks 6–16) — "Highway autopilot":** MES only, L1 features, TCN + meta-labeler ensemble, both policy templates, full risk stack, shadow → paper → 25% live. Success = surviving the ladder, not P&L records.
- **v2 (weeks 16–28) — "City streets":** add L2/order-flow sensors (book imbalance, depth features), MNQ as second (correlated-capped) instrument, colocated VPS, learned execution micro-tactics (limit-vs-market bandit trained on our own fill logs).
- **v3 (weeks 28–40) — "New ODDs":** SPY/QQQ equities session, EURUSD/XAUUSD **only after** their friction/microstructure models are separately validated (different tick economics; FX has no consolidated tape — weaker sensors, so gates are stricter). Cross-instrument shared encoder, per-instrument heads.
- **v4 (40+) — "Research fleet":** offline RL / decision-transformer policy trained on the logged decision dataset, run in shadow against the champion for months before any capital; news-NLP sensor; regime-conditional ensembles at scale. Note SPY options (0DTE) remain out of scope until here — nonlinear greeks + spread friction is a different vehicle class, not a new road.
- **Cadence forever:** weekly metric review vs backtest bands; monthly scheduled retrain on rolling window (champion/challenger, auto-promote only if challenger beats champion OOS *and* in 4+ weeks shadow); quarterly full re-validation; automated retrain triggers on drift alarms (§7#10).

---

## 9. Pseudocode / Implementation Sketch

Python-first; the full runnable skeleton lives in [`src/aya_trader/`](../src/aya_trader/) —
see `engine.py` in this repo for the working outline. Condensed version:

```python
# ---- deps: pandas, numpy, torch, lightgbm, onnxruntime, databento, ccxt/broker-sdk,
# ----       vectorbt or backtrader (research), fastapi (webhooks/HMI), grafana/tv (display)

class Perception:
    def on_tick(self, tick) -> StateVector | None:
        self.health.check(tick)                      # latency, staleness, cross-feed divergence
        bar = self.volume_bars.update(tick)          # volume-clock bars
        if bar is None: return None                  # no new bar => no new decision
        f_eng   = self.features.compute(bar)         # ~60 engineered, z-scored, PIT-correct
        f_emb   = self.encoder(self.window)          # TCN embedding (ONNX, <2ms)
        regime  = self.regime_clf.predict(f_eng)
        drift   = self.drift_monitor.score(f_eng)    # Mahalanobis / PSI
        return StateVector(bar, f_eng, f_emb, regime, drift, self.health.status)

class Prediction:
    def infer(self, s: StateVector) -> Signal:
        outs   = [m(s.features) for m in self.ensemble]          # p_up, q_ret, p_vol
        p_up   = regime_weighted_mean(outs, s.regime)
        dis    = float(np.std([o.p_up for o in outs]))
        meta_p = self.meta_labeler.predict(meta_features(s, p_up, dis, self.recent_stats))
        shap   = self.meta_labeler.explain_last()                # logged, human-auditable
        return Signal(p_up, quantiles(outs), vol(outs), dis, meta_p, shap)

class RiskLayer:                                    # ZERO ML in this class. Ever.
    def approve(self, intent, state, account) -> Verdict:
        checks = [
            self.within_odd(state),                 # regime tradable, not event window,
            state.health.ok, state.drift.ok,        #   sensors green, in-distribution
            account.daily_pnl > -self.L3_soft,
            account.heat + intent.risk <= self.max_heat,
            self.correlation_budget_ok(intent),
            self.consecutive_loss_ok(),
            now() < self.last_entry_time,           # 15:30 cutoff
        ]
        return Verdict(all(checks), failed=[c for c in checks if not c])   # reasons logged

class Planner:
    def decide(self, s: StateVector, sig: Signal, acct) -> Order | None:
        tpl = self.template_for(s.regime)           # trend / meanrev / None
        if tpl is None or not tpl.entry_ok(sig):    # thresholds of §3.3
            return None
        stop   = 1.3 * sig.vol_forecast
        target = 1.8 * sig.vol_forecast
        qty    = size(acct, stop, sig.confidence_bucket)      # §4.1
        intent = Order.bracket(tpl.side(sig), qty, stop, target, ttl_bars=3*HORIZON)
        v = self.risk.approve(intent, s, acct)
        self.log.decision(s, sig, intent, v)        # EVERY decision logged w/ full state
        return intent if v.ok else None

class Execution:
    def submit(self, order):
        order.uuid = uuid4()
        self.broker.place_marketable_limit(order, max_chase_ticks=2, entry_ttl_s=2)
        # OCO bracket attached atomically at exchange on fill
    def reconcile(self):                            # every 1s
        if self.broker.state() != self.intended_state():
            self.mode = EXECUTION_DEGRADED; alert()

class Monitor:                                      # separate process/host
    def loop(self):
        if heartbeat_missed(3):        self.broker.flatten_all(); page_human()
        if daily_loss() > L4_HARD:     flatten_disable();          page_human()
        if slippage_ratio() > 2.0:     halt_entries();             page_human()
        self.push_tradingview_state(); self.push_grafana()

# ---- main loop (live & shadow share this code path; shadow just swaps Execution
# ---- for PhantomExecution that models fills — one codebase, no sim/real skew)
while session.open():
    tick = feed.next()
    s = perception.on_tick(tick)
    if s is None: continue
    planner.manage_open(s, prediction.infer(s))      # decay/time/flatten exits
    if (o := planner.decide(s, prediction.infer(s), account)):
        execution.submit(o)
```

Research side (`research/`): `vectorbt` for fast sweeps, event-driven replayer (same Perception/
Planner classes) for final validation, `mlflow` model registry, purged walk-forward splitter,
Monte Carlo harness. **The event-driven replayer and the live engine are the same code** — the
single most important line in this section.

---

## Closing note (the safety-culture paragraph)

The deliverable of v1 is not profit. It is a **truth-telling machine**: an apparatus that can
determine, with controlled false-discovery risk, whether we have an edge — and that is physically
incapable of destroying the account while we find out. Profit is what you're allowed to attempt
*after* that machine says yes. Every shortcut around the gates is the trading equivalent of
shipping an FSD build because it looked good on the demo route. We don't do that.
