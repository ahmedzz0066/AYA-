"""Tests for the parts that can silently invent money.

Priorities, in order:
  1. No lookahead.
  2. No optimistic fills.
  3. No risk larger than the risk budget.
Everything else is a nice-to-have.
"""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from xauusd import backtest, indicators
from xauusd.broker import (
    Costs,
    Order,
    Side,
    Trade,
    breakeven_win_rate,
    limit_fills,
    size_lots,
    stop_fill_price,
    stop_hit,
    target_hit,
)
from xauusd.data import Bar, dedupe, htf_index, load_csv, resample, synthetic, write_csv
from xauusd.metrics import compute
from xauusd.strategy import StrategyConfig, build_context, signal_at

UTC = timezone.utc


def bar(ts_min: int, o: float, h: float, l: float, c: float) -> Bar:
    return Bar(datetime(2024, 1, 8, 8, 0, tzinfo=UTC) + timedelta(minutes=ts_min), o, h, l, c, 100)


class TestIndicators(unittest.TestCase):
    def test_ema_seeded_with_sma(self):
        vals = [1.0, 2.0, 3.0, 4.0, 5.0]
        out = indicators.ema(vals, 3)
        self.assertIsNone(out[1])
        self.assertAlmostEqual(out[2], 2.0)          # SMA seed
        self.assertAlmostEqual(out[3], 4 * 0.5 + 2.0 * 0.5)
        self.assertAlmostEqual(out[4], 5 * 0.5 + 3.0 * 0.5)

    def test_atr_wilder(self):
        bars = [bar(i * 5, 10 + i, 11 + i, 9 + i, 10 + i) for i in range(20)]
        out = indicators.atr(bars, 14)
        self.assertIsNone(out[13])
        self.assertIsNotNone(out[14])
        self.assertGreater(out[14], 0)

    def test_rolling_max_excludes_current_bar(self):
        vals = [1.0, 5.0, 2.0, 3.0]
        out = indicators.rolling_max(vals, 2, shift=1)
        self.assertIsNone(out[1])
        self.assertEqual(out[2], 5.0)   # max of bars 0..1, not including bar 2
        self.assertEqual(out[3], 5.0)   # max of bars 1..2

    def test_percentile_matches_naive(self):
        import random

        random.seed(3)
        vals = [None] * 12 + [random.gauss(1, 0.4) for _ in range(700)]
        for period in (40, 120):
            for pct in (0.0, 0.3, 0.97, 1.0):
                fast = indicators.rolling_percentile(vals, period, pct)
                for i in range(len(vals)):
                    start = i - period + 1
                    if start < 0:
                        self.assertIsNone(fast[i])
                        continue
                    window = sorted(v for v in vals[start : i + 1] if v is not None)
                    if len(window) < max(10, period // 2):
                        self.assertIsNone(fast[i])
                        continue
                    pos = pct * (len(window) - 1)
                    lo = int(pos)
                    hi = min(lo + 1, len(window) - 1)
                    want = window[lo] + (window[hi] - window[lo]) * (pos - lo)
                    self.assertAlmostEqual(fast[i], want, places=12)

    def test_swing_flag_written_at_confirmation(self):
        lows = [10, 9, 8, 9, 10, 11]
        bars = [bar(i * 5, l, l + 1, l, l) for i, l in enumerate(lows)]
        flags = indicators.swing_low(bars, left=2, right=2)
        # pivot is index 2; a live system only knows it at index 4
        self.assertFalse(flags[2])
        self.assertTrue(flags[4])


class TestData(unittest.TestCase):
    def test_resample_ohlc(self):
        bars = [bar(i * 5, 100 + i, 110 + i, 90 + i, 105 + i) for i in range(12)]
        h1 = resample(bars, 60)
        self.assertEqual(len(h1), 1)
        self.assertEqual(h1[0].open, bars[0].open)
        self.assertEqual(h1[0].close, bars[-1].close)
        self.assertEqual(h1[0].high, max(b.high for b in bars))
        self.assertEqual(h1[0].low, min(b.low for b in bars))

    def test_htf_index_never_sees_the_future(self):
        bars = [bar(i * 5, 100, 101, 99, 100) for i in range(36)]  # 3 hours
        idx = htf_index(bars, 60)
        htf = resample(bars, 60)
        for i, b in enumerate(bars):
            j = idx[i]
            if j < 0:
                continue
            htf_close_time = htf[j].ts + timedelta(minutes=60)
            # the referenced H1 bar must have CLOSED at or before this bar opens
            self.assertLessEqual(htf_close_time, b.ts, f"lookahead at bar {i}")

    def test_dedupe_keeps_last(self):
        b1 = bar(0, 1, 2, 0.5, 1.5)
        b2 = Bar(b1.ts, 9, 9, 9, 9)
        self.assertEqual(dedupe([b1, b2])[0].close, 9)

    def test_csv_roundtrip(self):
        import tempfile

        bars = synthetic(300)
        with tempfile.TemporaryDirectory() as d:
            path = str(Path(d) / "x.csv")
            write_csv(bars, path)
            back = load_csv(path)
        self.assertEqual(len(bars), len(back))
        self.assertEqual(bars[0].ts, back[0].ts)
        self.assertAlmostEqual(bars[-1].close, back[-1].close)


class TestExecution(unittest.TestCase):
    costs = Costs(spread=0.30, commission_per_lot=7.0, stop_slippage=0.10)

    def _order(self, side=Side.LONG, entry=2000.0, sl=1998.0, tp=2006.0) -> Order:
        return Order(side, entry, sl, tp, 0.1, 0, 12, sl, "t", abs(entry - sl))

    def test_buy_limit_needs_the_ask_to_reach_it(self):
        o = self._order()
        # mid low exactly at the limit: the ASK is still 0.15 above it -> no fill
        self.assertFalse(limit_fills(o, bar(0, 2001, 2001, 2000.0, 2001), self.costs))
        # mid low 0.15 below the limit: ask touches exactly -> fill
        self.assertTrue(limit_fills(o, bar(0, 2001, 2001, 1999.85, 2001), self.costs))

    def test_sell_limit_needs_the_bid_to_reach_it(self):
        o = self._order(Side.SHORT, 2000.0, 2002.0, 1994.0)
        self.assertFalse(limit_fills(o, bar(0, 1999, 2000.0, 1999, 1999), self.costs))
        self.assertTrue(limit_fills(o, bar(0, 1999, 2000.15, 1999, 1999), self.costs))

    def test_long_stop_triggers_on_the_bid(self):
        # bid = mid - 0.15, so a mid low of 1998.15 already trips a 1998 stop
        self.assertTrue(stop_hit(Side.LONG, 1998.0, bar(0, 2000, 2000, 1998.15, 1999), self.costs))
        self.assertFalse(stop_hit(Side.LONG, 1998.0, bar(0, 2000, 2000, 1998.16, 1999), self.costs))

    def test_long_target_needs_extra_for_the_spread(self):
        self.assertFalse(target_hit(Side.LONG, 2006.0, bar(0, 2000, 2006.0, 2000, 2005), self.costs))
        self.assertTrue(target_hit(Side.LONG, 2006.0, bar(0, 2000, 2006.15, 2000, 2005), self.costs))

    def test_stop_slips_and_gaps_are_worse(self):
        normal = stop_fill_price(Side.LONG, 1998.0, bar(0, 2000, 2000, 1997.0, 1998), self.costs)
        self.assertAlmostEqual(normal, 1997.90)
        gapped = stop_fill_price(Side.LONG, 1998.0, bar(0, 1990, 1991, 1989, 1990), self.costs)
        self.assertLess(gapped, 1990.0)  # filled at the gap, not at the stop

    def test_sizing_rounds_down_and_refuses_over_risk(self):
        c = self.costs
        self.assertAlmostEqual(size_lots(10_000, 0.005, 2.5, c), 0.20)
        self.assertAlmostEqual(size_lots(10_000, 0.005, 3.3, c), 0.15)  # 0.1515 -> 0.15
        self.assertEqual(size_lots(100, 0.005, 5.0, c), 0.0)            # cannot risk <= budget
        self.assertEqual(size_lots(10_000, 0.005, 0.0, c), 0.0)

    def test_breakeven_win_rate_formula(self):
        self.assertAlmostEqual(breakeven_win_rate(3.0, 0.0), 0.25)
        self.assertAlmostEqual(breakeven_win_rate(3.0, 0.10), 0.275)
        self.assertAlmostEqual(breakeven_win_rate(1.0, 0.0), 0.50)

    def test_same_bar_stop_and_target_books_the_loss(self):
        cfg = StrategyConfig()
        bars = [bar(i * 5, 2000, 2000.5, 1999.5, 2000) for i in range(3)]
        ctx = build_context(bars, cfg)
        ctx.minute_of_day = [8 * 60] * len(bars)
        tr = Trade(Side.LONG, 0.1, bars[0].ts, 0, 2000.0, 1998.0, 2006.0, 2.0)
        violent = bar(5, 2000, 2007.0, 1997.0, 2000)  # touches both levels
        closed = backtest._manage(tr, violent, 1, self.costs, cfg, ctx)
        self.assertTrue(closed)
        self.assertEqual(tr.exit_reason, "stop")
        self.assertLess(tr.pnl, 0)


class TestOrderLifecycle(unittest.TestCase):
    cfg = StrategyConfig()

    def _ctx(self, n=40):
        bars = [bar(i * 5, 2000, 2001, 1999, 2000) for i in range(n)]
        ctx = build_context(bars, self.cfg)
        return bars, ctx

    def test_order_expires(self):
        bars, ctx = self._ctx()
        o = Order(Side.LONG, 1999.0, 1997.0, 2005.0, 0.1, 1, 12, 1998.0, "t", 2.0)
        counters = {"expired": 0, "invalidated": 0}
        self.assertFalse(backtest._order_dead(o, bars[12], 12, self.cfg, ctx, counters))
        self.assertTrue(backtest._order_dead(o, bars[13], 13, self.cfg, ctx, counters))
        self.assertEqual(counters["expired"], 1)

    def test_order_cancelled_when_structure_breaks(self):
        bars, ctx = self._ctx()
        # previous close (bar 4) sits below the invalidation level -> cancel
        o = Order(Side.LONG, 1999.0, 1997.0, 2005.0, 0.1, 1, 12, 2001.0, "t", 2.0)
        counters = {"expired": 0, "invalidated": 0}
        self.assertTrue(backtest._order_dead(o, bars[5], 5, self.cfg, ctx, counters))
        self.assertEqual(counters["invalidated"], 1)

    def test_order_cancelled_outside_session(self):
        bars, ctx = self._ctx()
        ctx.in_session = [False] * len(bars)
        o = Order(Side.LONG, 1999.0, 1997.0, 2005.0, 0.1, 1, 999, 1990.0, "t", 2.0)
        counters = {"expired": 0, "invalidated": 0}
        self.assertTrue(backtest._order_dead(o, bars[3], 3, self.cfg, ctx, counters))


class TestInvariants(unittest.TestCase):
    """Run the real engine over synthetic data and assert things that must hold
    no matter what the market did."""

    @classmethod
    def setUpClass(cls):
        cls.bars = synthetic(40_000, seed=11)
        cls.cfg = StrategyConfig()
        cls.costs = Costs()
        cls.res = backtest.run(cls.bars, cls.cfg, cls.costs, 10_000.0)

    def test_produced_trades(self):
        self.assertGreater(len(self.res.trades), 20, "no trades: filters are too tight to test")

    def test_no_trade_wins_more_than_rr(self):
        for t in self.res.trades:
            self.assertLessEqual(t.r_multiple, self.cfg.rr + 1e-6, f"impossible win: {t}")

    def test_losses_never_much_worse_than_1r(self):
        for t in self.res.trades:
            if t.exit_reason in ("stop", "be-stop"):
                self.assertGreater(t.r_multiple, -1.6, f"stop leaked risk: {t}")

    def test_target_exits_pay_about_rr(self):
        targets = [t for t in self.res.trades if t.exit_reason == "target"]
        self.assertTrue(targets)
        for t in targets:
            self.assertGreater(t.r_multiple, self.cfg.rr - 0.25)
            self.assertLessEqual(t.r_multiple, self.cfg.rr + 1e-6)

    def test_risk_per_trade_respects_the_budget(self):
        for t in self.res.trades:
            equity_before = t.equity_after - t.pnl
            budget = equity_before * self.cfg.risk_pct
            risked = t.r_price * t.lots * self.costs.contract_size
            self.assertLessEqual(risked, budget * 1.001 + 1e-9, f"over-risked: {t}")

    def test_one_position_at_a_time(self):
        spans = sorted((t.entry_bar, t.exit_bar) for t in self.res.trades)
        for (s1, e1), (s2, _) in zip(spans, spans[1:]):
            self.assertGreaterEqual(s2, e1 if e1 is not None else s1)

    def test_exits_are_never_before_entries(self):
        for t in self.res.trades:
            self.assertIsNotNone(t.exit_bar)
            self.assertGreaterEqual(t.exit_bar, t.entry_bar)

    def test_trades_only_start_in_session(self):
        for t in self.res.trades:
            minute = t.entry_ts.hour * 60 + t.entry_ts.minute
            self.assertTrue(
                any(s <= minute < e for s, e in self.cfg.sessions), f"out of session: {t.entry_ts}"
            )

    def test_equity_curve_is_aligned_with_bars(self):
        self.assertEqual(len(self.res.equity_curve), len(self.bars))

    def test_daily_trade_cap_holds(self):
        from collections import Counter

        per_day = Counter(t.entry_ts.date() for t in self.res.trades)
        self.assertLessEqual(max(per_day.values()), self.cfg.max_trades_per_day)

    def test_shifting_the_data_does_not_change_history(self):
        """Truncating the future must not change the past. If it does, there is
        a lookahead somewhere."""
        cut = 30_000
        res2 = backtest.run(self.bars[:cut], self.cfg, self.costs, 10_000.0)
        early = [t for t in self.res.trades if t.exit_bar is not None and t.exit_bar < cut - 200]
        early2 = {(t.entry_bar, round(t.entry, 3)) for t in res2.trades}
        missing = [t for t in early if (t.entry_bar, round(t.entry, 3)) not in early2]
        self.assertEqual(missing, [], f"{len(missing)} trades changed when the future was removed")


class TestStrategyGuards(unittest.TestCase):
    def test_config_validation(self):
        for bad in (
            {"rr": 0},
            {"retrace": 1.5},
            {"min_r_atr": 0},
            {"max_r_atr": 0.1},
            {"expire_bars": 0},
            {"atr_pct_floor": 0.99},
            {"sessions": ((100, 50),)},
        ):
            with self.assertRaises(ValueError, msg=f"accepted bad config {bad}"):
                from dataclasses import replace

                replace(StrategyConfig(), **bad).validate()

    def test_setup_geometry_is_always_consistent(self):
        bars = synthetic(30_000, seed=5)
        cfg = StrategyConfig()
        ctx = build_context(bars, cfg)
        found = 0
        for i in range(len(bars)):
            s = signal_at(ctx, i, cfg)
            if not s:
                continue
            found += 1
            if s.side is Side.LONG:
                self.assertLess(s.sl, s.entry)
                self.assertGreater(s.tp, s.entry)
                self.assertAlmostEqual(s.tp - s.entry, cfg.rr * (s.entry - s.sl), places=2)
            else:
                self.assertGreater(s.sl, s.entry)
                self.assertLess(s.tp, s.entry)
                self.assertAlmostEqual(s.entry - s.tp, cfg.rr * (s.sl - s.entry), places=2)
            self.assertGreaterEqual(s.r_price, cfg.min_r_atr * s.atr - 1e-6)
            self.assertLessEqual(s.r_price, cfg.max_r_atr * s.atr + 1e-6)
        self.assertGreater(found, 10)

    def test_limit_entry_is_never_a_chase(self):
        """The limit must sit behind price, never at or beyond it - otherwise it
        is a market order wearing a costume."""
        bars = synthetic(20_000, seed=9)
        cfg = StrategyConfig()
        ctx = build_context(bars, cfg)
        for i in range(len(bars)):
            s = signal_at(ctx, i, cfg)
            if not s:
                continue
            close = bars[i].close
            if s.side is Side.LONG:
                self.assertLess(s.entry, close, f"long limit above the signal close at bar {i}")
            else:
                self.assertGreater(s.entry, close, f"short limit below the signal close at bar {i}")


class TestMetrics(unittest.TestCase):
    def _trade(self, r: float, pnl: float) -> Trade:
        t = Trade(Side.LONG, 0.1, datetime(2024, 1, 1, tzinfo=UTC), 0, 2000, 1998, 2006, 2.0)
        t.exit_ts = datetime(2024, 1, 1, 1, tzinfo=UTC)
        t.exit_bar = 5
        t.r_multiple = r
        t.pnl = pnl
        t.exit_reason = "target" if r > 0 else "stop"
        return t

    def test_expectancy_and_streaks(self):
        trades = [self._trade(3, 60), self._trade(-1, -20), self._trade(-1, -20), self._trade(-1, -20)]
        st = compute(trades, 10_000, rr=3.0)
        self.assertEqual(st.trades, 4)
        self.assertAlmostEqual(st.win_rate, 0.25)
        self.assertAlmostEqual(st.expectancy_r, 0.0)
        self.assertEqual(st.max_consec_losses, 3)
        self.assertAlmostEqual(st.profit_factor, 1.0)
        self.assertAlmostEqual(st.max_dd_r, 3.0)

    def test_empty_is_not_a_crash(self):
        st = compute([], 10_000)
        self.assertEqual(st.trades, 0)
        self.assertEqual(st.expectancy_r, 0.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
