"""Property tests for the footprint reconstruction.

These check the *derivation*, not just that the code runs: the closed forms in
docs/DERIVATION.md are re-derived numerically and compared against the
implementation.
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vfootprint.core import (  # noqa: E402
    Bar,
    FootprintConfig,
    Leg,
    build_profile,
    buy_share,
    decompose,
    leg_mass_in_row,
    overlap_coefficient,
    path_weights,
    session_profile,
    value_area,
)


def _centre_of_mass(rows, side):
    w = sum(getattr(r, side) for r in rows)
    if w <= 0:
        return float("nan")
    return sum(r.mid * getattr(r, side) for r in rows) / w


class TestPathWeights(unittest.TestCase):
    def test_weights_sum_to_one(self):
        for bar in (
            Bar(10, 12, 9, 11, 100),
            Bar(10, 10.5, 9.5, 9.7, 100),
            Bar(10, 10, 10, 10, 100),
        ):
            wa, wb = path_weights(bar)
            self.assertAlmostEqual(wa + wb, 1.0, places=12)

    def test_up_bar_prefers_down_first_path(self):
        # An up bar that also printed the low must have gone down first, or else
        # taken a longer journey.  Least action prefers the shorter one.
        wa, wb = path_weights(Bar(10, 12, 9, 11.8, 100))
        self.assertLess(wa, wb)

    def test_alpha_zero_is_agnostic(self):
        wa, wb = path_weights(Bar(10, 12, 9, 11.8, 100), alpha=0.0)
        self.assertAlmostEqual(wa, 0.5)
        self.assertAlmostEqual(wb, 0.5)

    def test_closed_form_weights_at_alpha_one(self):
        bar = Bar(10, 12, 9, 11, 100)
        r, d = bar.range, bar.body
        wa, wb = path_weights(bar, alpha=1.0)
        self.assertAlmostEqual(wa, (2 * r - d) / (4 * r), places=12)
        self.assertAlmostEqual(wb, (2 * r + d) / (4 * r), places=12)


class TestBuyShare(unittest.TestCase):
    cfg = FootprintConfig(engine="path")

    def test_matches_closed_form(self):
        # buyShare = (4 + 2x - x^2) / (8 - 2x^2),  x = body / range
        for o, h, l, c in [
            (10, 12, 9, 11),
            (10, 11, 8, 8.5),
            (100, 105, 95, 100),
            (50, 51, 49, 50.9),
        ]:
            bar = Bar(o, h, l, c, 1000)
            x = bar.body / bar.range
            expect = (4 + 2 * x - x * x) / (8 - 2 * x * x)
            self.assertAlmostEqual(buy_share(bar, self.cfg), expect, places=12)

    def test_doji_is_neutral(self):
        self.assertAlmostEqual(buy_share(Bar(10, 12, 9, 10, 100), self.cfg), 0.5, places=12)

    def test_marubozu_bounds(self):
        up = Bar(9, 12, 9, 12, 100)      # x = +1
        dn = Bar(12, 12, 9, 9, 100)      # x = -1
        self.assertAlmostEqual(buy_share(up, self.cfg), 5 / 6, places=12)
        self.assertAlmostEqual(buy_share(dn, self.cfg), 1 / 6, places=12)

    def test_mirror_symmetry(self):
        # Reflecting a bar through a price axis must swap the two sides exactly.
        bar = Bar(10, 12, 9, 11.2, 500)
        mirror = Bar(-10, -9, -12, -11.2, 500)
        self.assertAlmostEqual(
            buy_share(bar, self.cfg), 1.0 - buy_share(mirror, self.cfg), places=12
        )

    def test_close_engine_saturates_where_path_does_not(self):
        cfg_close = FootprintConfig(engine="close")
        up = Bar(9, 12, 9, 12, 100)
        self.assertAlmostEqual(buy_share(up, cfg_close), 1.0, places=12)
        self.assertLess(buy_share(up, self.cfg), 1.0)

    def test_zero_range_is_neutral(self):
        self.assertAlmostEqual(buy_share(Bar(10, 10, 10, 10, 100), self.cfg), 0.5)


class TestLegDecomposition(unittest.TestCase):
    def test_leg_mass_identity(self):
        # M_buy - M_sell should equal the body times the weight normalisation,
        # and total leg mass should equal 2R at alpha = 0.
        bar = Bar(10, 12, 9, 11, 100)
        legs = decompose(bar, alpha=0.0)
        up = sum(l.mass for l in legs if l.up)
        dn = sum(l.mass for l in legs if not l.up)
        self.assertAlmostEqual(up + dn, 2 * bar.range, places=10)
        self.assertAlmostEqual(up - dn, bar.body, places=10)

    def test_legs_are_within_range(self):
        bar = Bar(10, 12, 9, 11, 100)
        for leg in decompose(bar):
            self.assertGreaterEqual(leg.lo, bar.l - 1e-12)
            self.assertLessEqual(leg.hi, bar.h + 1e-12)
            self.assertGreater(leg.mass, 0.0)


class TestKernelIntegral(unittest.TestCase):
    """The Psi closed form must match brute-force numerical integration."""

    @staticmethod
    def _numeric(leg, p1, p2, sigma, n=20000):
        # Convolution of Uniform[a,b] with N(0, sigma^2), integrated over [p1,p2].
        a, b = leg.lo, leg.hi
        step = (p2 - p1) / n
        acc = 0.0
        for i in range(n):
            x = p1 + (i + 0.5) * step
            # density of the smoothed uniform at x
            d = (
                0.5 * math.erf((x - a) / (sigma * math.sqrt(2)))
                - 0.5 * math.erf((x - b) / (sigma * math.sqrt(2)))
            ) / (b - a)
            acc += d * step
        return leg.mass * acc

    def test_smoothed_matches_numeric(self):
        leg = Leg(9.0, 12.0, 7.5, True)
        sigma = 0.4
        for p1, p2 in [(9.0, 9.25), (10.0, 10.5), (11.75, 12.0), (8.5, 8.75)]:
            got = leg_mass_in_row(leg, p1, p2, sigma)
            want = self._numeric(leg, p1, p2, sigma)
            self.assertAlmostEqual(got, want, places=7, msg=f"row {p1}-{p2}")

    def test_unsmoothed_is_exact_overlap(self):
        leg = Leg(10.0, 12.0, 4.0, True)
        # Half the leg's span -> half its mass.
        self.assertAlmostEqual(leg_mass_in_row(leg, 10.0, 11.0, 0.0), 2.0, places=12)
        self.assertAlmostEqual(leg_mass_in_row(leg, 8.0, 9.0, 0.0), 0.0, places=12)
        self.assertAlmostEqual(leg_mass_in_row(leg, 9.0, 13.0, 0.0), 4.0, places=12)

    def test_smoothing_conserves_mass_over_the_real_line(self):
        leg = Leg(10.0, 12.0, 3.0, True)
        self.assertAlmostEqual(leg_mass_in_row(leg, -50.0, 70.0, 0.5), 3.0, places=9)


class TestProfile(unittest.TestCase):
    cfg = FootprintConfig(row_size=0.25, concentration=3.0)

    def test_volume_is_conserved(self):
        for bar in (
            Bar(10, 12, 9, 11, 1000),
            Bar(100, 100.4, 99.1, 99.2, 777),
            Bar(5, 5, 5, 5, 42),
            Bar(10, 10.01, 9.99, 10.005, 13),
        ):
            prof = build_profile(bar, self.cfg)
            self.assertAlmostEqual(sum(r.total for r in prof.rows), bar.v, places=9)
            self.assertLess(prof.residual_ppm, 1.0)

    def test_delta_matches_bar_level_split(self):
        bar = Bar(10, 12, 9, 11, 1000)
        prof = build_profile(bar, self.cfg)
        share = buy_share(bar, self.cfg)
        self.assertAlmostEqual(prof.buy_volume, bar.v * share, places=8)
        self.assertAlmostEqual(prof.delta, bar.v * (2 * share - 1), places=8)

    def test_buy_and_sell_shapes_differ(self):
        # The whole point of the leg model: buying concentrates where price rose.
        # If these centres coincided, the footprint would carry no information
        # the candle did not already have.
        bar = Bar(10, 12, 9, 11.5, 1000)
        prof = build_profile(bar, self.cfg)
        self.assertGreater(_centre_of_mass(prof.rows, "buy"), _centre_of_mass(prof.rows, "sell"))
        self.assertLess(prof.ovl, 1.0)

    def test_ovl_is_bounded(self):
        for bar in (Bar(10, 12, 9, 11, 500), Bar(10, 10.2, 9.8, 9.9, 500)):
            ovl = build_profile(bar, self.cfg).ovl
            self.assertGreaterEqual(ovl, 0.0)
            self.assertLessEqual(ovl, 1.0 + 1e-12)

    def test_doji_is_symmetric(self):
        # A perfectly symmetric bar must produce equal sides and near-total overlap.
        bar = Bar(10, 11, 9, 10, 1000)
        prof = build_profile(bar, self.cfg)
        self.assertAlmostEqual(prof.buy_volume, prof.sell_volume, places=8)
        self.assertAlmostEqual(prof.tilt_pct, 0.0, places=8)
        self.assertGreater(prof.ovl, 0.85)

    def test_rows_align_across_bars(self):
        # Absolute grid anchoring: two different bars covering the same price
        # must produce rows at identical indices, or diagonals are meaningless.
        a = build_profile(Bar(10, 12, 9, 11, 100), self.cfg)
        b = build_profile(Bar(11, 13, 10, 12, 100), self.cfg)
        shared = {r.index for r in a.rows} & {r.index for r in b.rows}
        self.assertTrue(shared)
        for idx in shared:
            self.assertAlmostEqual(a.row(idx).price_low, b.row(idx).price_low, places=12)

    def test_rows_span_the_bar_range(self):
        bar = Bar(10, 12, 9, 11, 100)
        prof = build_profile(bar, self.cfg)
        self.assertLessEqual(prof.rows[0].price_low, bar.l)
        self.assertGreaterEqual(prof.rows[-1].price_high, bar.h)

    def test_poc_is_the_modal_row(self):
        prof = build_profile(Bar(10, 12, 9, 11, 1000), self.cfg)
        self.assertEqual(prof.poc.total, max(r.total for r in prof.rows))

    def test_value_area_reaches_target(self):
        prof = build_profile(Bar(10, 12, 9, 11, 1000), self.cfg)
        total = sum(r.total for r in prof.rows)
        inside = sum(r.total for r in prof.rows[prof.val_index : prof.vah_index + 1])
        self.assertGreaterEqual(inside / total, 0.70 - 1e-9)
        self.assertLessEqual(prof.val_index, prof.poc_index)
        self.assertGreaterEqual(prof.vah_index, prof.poc_index)

    def test_value_area_is_minimal_ish(self):
        # Dropping the outermost row of the band must break the 70% target,
        # otherwise the band was grown too far.
        prof = build_profile(Bar(10, 12, 9, 11, 1000), self.cfg)
        rows = prof.rows
        total = sum(r.total for r in rows)
        band = rows[prof.val_index : prof.vah_index + 1]
        if len(band) > 1:
            self.assertLess(sum(r.total for r in band[:-1]) / total, 0.70 + 1e-9)

    def test_high_concentration_approaches_exact_uniform(self):
        bar = Bar(10, 12, 9, 11, 1000)
        smooth = build_profile(bar, FootprintConfig(row_size=0.25, concentration=200.0))
        exact = build_profile(bar, FootprintConfig(row_size=0.25, concentration=math.inf))
        for a, b in zip(smooth.rows, exact.rows):
            self.assertAlmostEqual(a.total, b.total, delta=bar.v * 2e-2)

    def test_degenerate_bar(self):
        prof = build_profile(Bar(5, 5, 5, 5, 42), self.cfg)
        self.assertAlmostEqual(sum(r.total for r in prof.rows), 42.0, places=9)
        self.assertAlmostEqual(prof.delta, 0.0, places=9)

    def test_zero_volume_bar(self):
        prof = build_profile(Bar(10, 12, 9, 11, 0), self.cfg)
        self.assertAlmostEqual(sum(r.total for r in prof.rows), 0.0, places=12)
        self.assertEqual(prof.residual_ppm, 0.0)

    def test_rejects_impossible_bar(self):
        with self.assertRaises(ValueError):
            Bar(o=13, h=12, l=9, c=11, v=100)
        with self.assertRaises(ValueError):
            Bar(o=10, h=12, l=9, c=11, v=-1)


class TestImbalance(unittest.TestCase):
    def test_diagonal_rule_fires_on_a_one_sided_bar(self):
        cfg = FootprintConfig(row_size=0.25, imbalance_threshold=3.0)
        prof = build_profile(Bar(9.0, 12.0, 9.0, 11.9, 5000), cfg)
        self.assertTrue(prof.buy_imbalances, "an aggressive up bar should show buy imbalances")

    def test_threshold_is_monotone(self):
        bar = Bar(9.0, 12.0, 9.0, 11.9, 5000)
        lo = build_profile(bar, FootprintConfig(row_size=0.25, imbalance_threshold=1.5))
        hi = build_profile(bar, FootprintConfig(row_size=0.25, imbalance_threshold=9.0))
        self.assertGreaterEqual(len(lo.buy_imbalances), len(hi.buy_imbalances))

    def test_balance_label(self):
        self.assertEqual(
            build_profile(Bar(10, 11, 9, 10, 1000)).balance_label(5.0), "balanced"
        )
        self.assertEqual(
            build_profile(Bar(9, 12, 9, 12, 1000)).balance_label(5.0), "buyers"
        )
        self.assertEqual(
            build_profile(Bar(12, 12, 9, 9, 1000)).balance_label(5.0), "sellers"
        )


class TestLtfEngine(unittest.TestCase):
    def test_measured_split_overrides_model(self):
        cfg = FootprintConfig(engine="ltf", row_size=0.25)
        bar = Bar(10, 12, 9, 11, 1000, buy_volume=800)
        self.assertAlmostEqual(buy_share(bar, cfg), 0.8, places=12)

    def test_sub_bars_conserve_volume_and_shift_the_split(self):
        cfg = FootprintConfig(engine="ltf", row_size=0.25)
        bar = Bar(10, 12, 9, 11, 1000)
        subs = [
            Bar(10, 10.5, 9.0, 9.2, 400),   # sold off hard
            Bar(9.2, 12.0, 9.2, 11.8, 400),  # rallied hard
            Bar(11.8, 12.0, 10.9, 11.0, 200),
        ]
        prof = build_profile(bar, cfg, sub_bars=subs)
        self.assertAlmostEqual(sum(r.total for r in prof.rows), 1000.0, places=8)
        # The sub-bars visit price unevenly, so the composite must differ from
        # the single-bar reconstruction.
        plain = build_profile(bar, FootprintConfig(row_size=0.25))
        self.assertNotAlmostEqual(prof.ovl, plain.ovl, places=6)


class TestSessionProfile(unittest.TestCase):
    def test_merge_conserves_total_volume(self):
        cfg = FootprintConfig(row_size=0.25)
        bars = [
            Bar(10, 12, 9, 11, 1000),
            Bar(11, 13, 10.5, 12.5, 800),
            Bar(12.5, 12.8, 11.0, 11.2, 600),
        ]
        profs = [build_profile(b, cfg) for b in bars]
        rows, poc, val, vah = session_profile(profs, cfg.row_size)
        self.assertAlmostEqual(sum(r.total for r in rows), 2400.0, places=7)
        self.assertLessEqual(val, poc)
        self.assertGreaterEqual(vah, poc)

    def test_empty_merge(self):
        rows, poc, val, vah = session_profile([], 0.25)
        self.assertEqual(rows, [])


class TestValueAreaHelper(unittest.TestCase):
    def test_empty_rows(self):
        self.assertEqual(value_area([], 0), (0, 0))

    def test_overlap_of_disjoint_profiles_is_zero(self):
        from vfootprint.core import Row

        rows = [Row(0, 0, 1, buy=10, sell=0), Row(1, 1, 2, buy=0, sell=10)]
        self.assertAlmostEqual(overlap_coefficient(rows), 0.0, places=12)

    def test_overlap_of_identical_profiles_is_one(self):
        from vfootprint.core import Row

        rows = [Row(0, 0, 1, buy=5, sell=7), Row(1, 1, 2, buy=5, sell=7)]
        self.assertAlmostEqual(overlap_coefficient(rows), 1.0, places=12)


if __name__ == "__main__":
    unittest.main(verbosity=2)
