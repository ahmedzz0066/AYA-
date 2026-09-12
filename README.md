# XAUUSD M5 — 3:1 Limit-Order Strategy

A complete, testable trading system for gold on the 5-minute chart. Fixed 3:1
reward-to-risk, limit-order entries only, zero third-party dependencies.

Three implementations of one idea:

| Where | File | Purpose |
|---|---|---|
| Research | `xauusd/` | Bar-by-bar backtester, walk-forward, metrics |
| Live | `mt5/XAUUSD_M5_3R.mq5` | MetaTrader 5 expert advisor |
| Eyeballs | `pine/xauusd_m5_3r.pine` | TradingView, to *look* at the setups |

---

## Start with the physics

At 3:1 you do not need to be right. You need to be right **27.5% of the time.**

```
p·(RR − c) = (1 − p)·(1 + c)        break-even condition
p          = (1 + c) / (1 + RR)

RR = 3, costs c = 0.10R  ->  p = 1.10 / 4.00 = 27.5%
RR = 3, costs c = 0      ->  p = 25.0%
```

Everything in this repo exists to clear that one number. Nothing else is a
feature. The moment a filter, an indicator, or a "confluence" stops helping
clear 27.5%, delete it.

The corollary people miss: **a 3:1 system loses more often than it wins, by
design.** Seven losses in a row is a routine Tuesday, not a broken strategy.
If you cannot sit through that, trade 1:1 and stop reading — that is not an
insult, it is a specification.

| Win rate @ 3:1 | Expectancy per trade |
|---|---|
| 25% | 0.00 R |
| 30% | +0.20 R |
| 33% | +0.32 R |
| 40% | +0.60 R |

40% at 3:1 is a world-class discretionary trader. Do not build a plan around it.

---

## The strategy, precisely

**One question drives every rule: can price travel 3R before it travels 1R?**
Only three things make that true on gold's 5-minute chart.

### 1. Volatility — is 3R even reachable?
`ATR(14)` must sit inside the **30th–97th percentile** of its own trailing 480
bars (~2 trading days).

Below the 30th: the tape is dead, 3R is a fantasy, and you are paying spread
to watch paint dry. Above the 97th: you got filled on the last liquidity
before a news spike reverses. R is sized *from ATR*, so the target breathes
with the market instead of being a fixed pip count someone invented in 2009.

### 2. Direction — is there a reason to travel?
- H1 bias: last **closed** H1 close beyond its EMA(21), with the EMA sloping the same way.
- M5 alignment: EMA(21) vs EMA(50).
- **Displacement:** the M5 bar must *close* beyond the extreme of the previous
  20 bars. No displacement, no trade. A 3R run needs an impulse that already
  proved it exists.

### 3. Entry location — this is where 3R is won or lost
**We never chase.** Chasing the breakout puts your stop at the leg origin,
miles away, and turns 3R into an impossible 90-dollar move on gold.

So a **limit order** rests in the retracement:

```
leg      = |breakout close − leg origin|      (origin = 21-bar extreme)
limit    = close − 0.382 × leg                (pulled to EMA(21) if deeper)
stop     = leg origin ∓ 0.30 × ATR            (beyond the stop hunt)
R        = |limit − stop|                     must be 0.5–2.5 × ATR
target   = limit ± 3R
```

Same move. Tighter stop. 3R becomes reachable. That is the entire trick, and
it is the reason the brief said *limit order* — a market entry on this setup is
a different strategy wearing the same name.

### Order lifecycle
- Unfilled limit dies after **12 bars (1 hour)**. Dead money is worse than a
  loss: it also blocks the next setup. Cycle time is a risk parameter.
- Cancelled early if a close re-enters the leg origin — the structure that
  justified the trade is gone.
- Cancelled at session end. Never carried into thin liquidity.

### Sessions (UTC)
`07:00–11:00` London and `12:30–16:30` NY overlap. Flat by `20:00`. No new risk
after Friday 16:00.

Gold trends when London and New York are both awake. Asia chops, and chop eats
3:1 setups for breakfast — you pay full spread to get stopped by noise that
never had 3R of travel in it.

### Exits
**3R or the stop. That is the whole exit logic.**

No trailing, no partials, no break-even shuffle, no averaging down, no grid,
no martingale. You asked for 3:1 and this delivers exactly 3:1 — moving the
stop to break-even is available (`--be-at-r`) and **off by default**, because
it converts losses into scratches *and* winners into scratches, and on a 3:1
system the second effect is the bigger one. Measure it before you enable it.

### Risk
0.5% of equity per trade, sized from the stop distance. Max 4 trades/day, one
position at a time, stand down for the day after −2R. Lots always round
**down** — if the smallest tradable lot would exceed the budget, the trade is
skipped rather than silently over-risked. That is how accounts survive long
enough for a 27.5% threshold to matter.

---

## The backtester refuses to flatter you

Most 5-minute gold backtests are fiction. Here is what this one does instead.

**Bid/ask modelled explicitly.** Bars are mid prices. A buy limit fills only
when `low + spread/2 ≤ limit` — the *ask* has to reach your order. A long stop
triggers on the *bid*, so it trips **earlier** than the mid chart suggests. A
long target needs the mid to exceed it by half a spread. This is how MT5
actually behaves; the spread is paid inside the trigger conditions, not bolted
on afterwards as a fudge factor.

**Every ambiguity resolves against us.**
- Bar touches both stop and target → **loss booked.** Always.
- Bar fills the limit *and* hits the stop → **filled, then stopped.**
- Stops slip (0.10 default) and gap through at the gap price. Targets never slip.

**Defaults are unkind:** 0.30 USD/oz spread, $7/lot round-turn commission,
0.10 slippage on stops.

**Decisions at bar close, orders live from the next bar.** The H1 mapping
resolves to the last *closed* H1 bar — the single line where most backtests
secretly cheat. It lives alone in `data.htf_index()` and is unit-tested.

**A test that tries to catch me lying:**
`test_shifting_the_data_does_not_change_history` re-runs the backtest with the
future deleted and asserts the past came out identical. If any lookahead exists
anywhere in the pipeline, that test fails.

---

## Quickstart

```bash
git clone <this repo> && cd AYA-

# 1. prove the machinery works (36 tests, ~2s)
python3 -m unittest discover -s tests -v

# 2. see the engine run end to end on synthetic bars
python3 -m xauusd.cli backtest --synthetic 40000

# 3. the real work, once you have real data:
python3 -m xauusd.cli backtest    --csv data/XAUUSD_M5.csv --trades-csv blotter.csv
python3 -m xauusd.cli walkforward --csv data/XAUUSD_M5.csv
python3 -m xauusd.cli costcurve   --csv data/XAUUSD_M5.csv
python3 -m xauusd.cli signals     --csv data/XAUUSD_M5.csv --last 20
```

No pip install. No requirements.txt. Python 3.10+ and nothing else — the best
part is no part, and a dependency you don't have can't break in two years.

### Getting real data

MT5: `View → Symbols → XAUUSD → Bars → M5 → Export`. Or any broker's M5 CSV.
`load_csv` handles headered, headerless, MT5 two-column date/time, `;`/tab
delimiters, and epoch timestamps.

**Set your timezone.** Session filters assume UTC. A GMT+2 broker needs
`--tz-shift -2`. Get this wrong and you are trading Tokyo while believing you
are trading London, which will quietly invert your results.

Aim for **3+ years** of M5 (~220k bars). Two months is not a sample, it is a
mood.

---

## What this repo has NOT established

I have run this on **synthetic random-walk data only** — the container has no
market data in it. That run proved the plumbing works. It proved nothing about
whether the strategy makes money, and I am not going to imply otherwise.

Notably, the synthetic walk-forward returned **+0.046 R/trade — essentially
zero.** That is the correct answer. Data with no edge in it *should* produce
nothing. A backtester that finds alpha in noise is a random number generator
with a nice font.

### Validation protocol — run this before risking a cent

1. **Walk-forward, not backtest.** `walkforward` trains on ~2.5 months, trades
   the next ~3 weeks blind, rolls forward. Look only at the stitched
   out-of-sample curve. Everything else is a story you told yourself.
2. **Demand ≥200 out-of-sample trades.** Under 100 the CLI tells you it is an
   anecdote, because it is.
3. **Check the edge margin.** The report prints `win rate − break-even win
   rate` directly. Under +3 points, you have noise, not an edge.
4. **Run `costcurve`.** If the edge dies between 0.30 and 0.60 spread, it was
   never an edge — it was a rebate on someone else's bad fill. Gold's spread
   *triples* around NFP and FOMC.
5. **Check parameter stability.** `walkforward` prints how often each value got
   picked. A parameter that changes every fold is noise wearing a name tag —
   pin it or delete it.
6. **Then demo for a month.** Compare live fill rate against backtest fill rate
   (the report prints it). Limit orders are where theory and reality diverge:
   in backtest your order fills whenever price touches it, in reality you are
   at the back of the queue.
7. **Then trade 0.1% risk.** Then 0.25%. Then, maybe, 0.5%.

If it fails at any step, the answer is not more parameters. It is a different
entry model.

---

## Known failure modes

I would rather write these down than discover them at 0.5% a pop.

- **News.** FOMC, NFP, CPI. Gold moves $30 in seconds, spreads go to $2+, stops
  slip past any model. The ATR cap helps; it does not save you. Add an economic
  calendar block — see the ideas below.
- **Fill rate ~20%.** Limit entries skip every move that never pulls back, and
  those include the biggest ones. This is a real cost, paid for a tighter stop.
  It is also the single highest-leverage thing left to optimise.
- **Order-queue reality.** A backtest fill on a touch is optimistic at the tick
  level. Demo will tell you the truth.
- **Comment-based state in the EA.** The invalidation level rides in the order
  comment so nothing is lost on restart. If your broker rewrites comments, the
  early-cancel degrades to expiry-only. Check it on demo.
- **Broker timezone drift.** DST shifts server time twice a year. Re-check
  `InpServerGmtOffset` in March and October.
- **The MQL5 EA has not been compiled.** No MetaEditor in this container. It is
  written against the MQL5 API and statically checked, but compile it, then run
  the Strategy Tester on the same period as the Python backtest and **make the
  trade lists match** before it touches a live account. If they disagree, one of
  the two is lying, and you need to know which.

---

## Ideas worth more than tuning these parameters

Parameter tuning is the lowest-value work available. In rough order of expected
payoff:

1. **Attack the 80% no-fill rate.** Two-tier limits: half the risk at 0.382,
   half at 0.618. Same stop, blended entry, better fill rate. If the second
   tier fills, R shrinks and the *same* move pays 4R+. This is the most
   promising unexplored axis in the repo.
2. **Replace the fixed 0.382 with a conditional-distribution estimate.** For
   each setup, measure how deep similar historical pullbacks retraced before
   continuing, then place the limit at the depth that maximises
   `P(fill) × P(3R | filled)`. Stop guessing at Fibonacci numbers a
   13th-century accountant wrote down.
3. **Let RR float with realised volatility.** 3:1 is *your constraint*, and the
   market does not care about it. Instruments have a natural ratio; measure
   `E[MFE/MAE]` per regime and check whether gold's M5 is really 3.0 or nearer
   2.4. If it is 2.4, a 3:1 target is a tax you are paying on principle.
4. **Feed the backtester M1 bars** to resolve stop-vs-target order exactly
   instead of assuming the worst. The assumption is a floor on reality — useful,
   but the true number is knowable.
5. **Economic calendar as a hard gate.** Cancel all pending orders 15 minutes
   either side of tier-1 releases. Cheapest large risk reduction available.
6. **Regime classifier instead of a volatility band.** The ATR percentile is a
   crude proxy for "is gold trending". A 3-state classifier (trend / chop /
   shock) trained to predict *forward MFE/MAE* would gate trades on the thing
   that actually determines whether 3R is reachable.
7. **Stop trading one instrument.** This engine is symbol-agnostic. Run it
   across gold, silver, and the majors: 5 uncorrelated 0.2R edges beat one 0.5R
   edge, and they beat it with a third of the drawdown. Diversification is the
   only free lunch in finance and it is still sitting there, uneaten.

---

## Repo layout

```
xauusd/
  data.py         bar loading, resampling, no-lookahead H1 mapping, synthetic bars
  indicators.py   EMA, Wilder ATR, rolling extremes, incremental rolling percentile
  strategy.py     the setup logic and every parameter, in one dataclass
  broker.py       bid/ask fills, stop/target triggers, slippage, position sizing
  backtest.py     bar-by-bar engine, order lifecycle, daily risk governor
  metrics.py      R-multiples, edge margin, drawdown, MAE/MFE, monthly breakdown
  walkforward.py  rolling out-of-sample validation + parameter stability
  cli.py          backtest | walkforward | signals | costcurve | makedata
tests/            36 tests, the important ones hunt for lookahead and free money
mt5/              MetaTrader 5 expert advisor
pine/             TradingView script
```

---

## Not financial advice

This is engineering, not a promise. Leveraged gold can take more than you put
in. The system is unvalidated on real data until *you* validate it, and if the
validation says no, the correct response is to believe it.

Run the protocol. Let the data have the final word. Then go make something.
