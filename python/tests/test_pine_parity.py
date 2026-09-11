"""Parity checks between the Pine port and the reference implementation.

Pine has no ``math.erf``, so the indicator builds the normal integrals from an
Abramowitz & Stegun 7.1.26 rational approximation.  These tests re-implement that
approximation exactly as the Pine does and confirm the substitution does not
move the answer -- the one place the two ports genuinely differ in arithmetic.

They also re-derive the Pine's leg table straight from the .pine source, so the
two implementations cannot silently drift apart.
"""

import math
import os
import re
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from vfootprint.core import (  # noqa: E402
    Bar,
    FootprintConfig,
    Leg,
    build_profile,
    decompose,
    leg_mass_in_row,
)

PINE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "pine", "volume_footprint.pine"
)


# --- the Pine's own numerics, transcribed --------------------------------- #

def pine_erf(x: float) -> float:
    t = 1.0 / (1.0 + 0.3275911 * abs(x))
    p = t * (
        0.254829592
        + t * (-0.284496736 + t * (1.421413741 + t * (-1.453152027 + t * 1.061405429)))
    )
    y = 1.0 - p * math.exp(-x * x)
    return y if x >= 0 else -y


def pine_ncdf(z: float) -> float:
    return 0.5 * (1.0 + pine_erf(z / math.sqrt(2.0)))


def pine_npdf(z: float) -> float:
    return math.exp(-0.5 * z * z) / math.sqrt(2.0 * math.pi)


def pine_npsi(z: float) -> float:
    return z * pine_ncdf(z) + pine_npdf(z)


def pine_leg_mass(a, b, m, p1, p2, sigma):
    w = b - a
    if sigma <= 0.0:
        if w <= 1e-12:
            return m if p1 <= a < p2 else 0.0
        return m * max(0.0, min(p2, b) - max(p1, a)) / w
    if w <= 1e-12:
        return m * (pine_ncdf((p2 - a) / sigma) - pine_ncdf((p1 - a) / sigma))
    acc = (
        pine_npsi((p2 - a) / sigma)
        - pine_npsi((p1 - a) / sigma)
        - pine_npsi((p2 - b) / sigma)
        + pine_npsi((p1 - b) / sigma)
    )
    return m * sigma * acc / w


class TestErfApproximation(unittest.TestCase):
    def test_within_published_error_bound(self):
        z = -6.0
        while z <= 6.0:
            self.assertLess(abs(pine_erf(z) - math.erf(z)), 1.5e-7, msg=f"z={z}")
            z += 0.01

    def test_cdf_tails_are_sane(self):
        self.assertAlmostEqual(pine_ncdf(0.0), 0.5, places=7)
        self.assertLess(pine_ncdf(-8.0), 1e-6)
        self.assertGreater(pine_ncdf(8.0), 1.0 - 1e-6)

    def test_psi_is_the_antiderivative_of_the_cdf(self):
        # Numerically differentiate Psi and compare against Phi.  The tolerance
        # has to admit the 1.5e-7 erf error that Psi is built on, plus the
        # central-difference truncation term.
        h = 1e-5
        for z in (-2.5, -1.0, 0.0, 0.7, 3.0):
            slope = (pine_npsi(z + h) - pine_npsi(z - h)) / (2 * h)
            self.assertAlmostEqual(slope, pine_ncdf(z), delta=5e-6, msg=f"z={z}")

    def test_psi_is_exact_against_the_reference_antiderivative(self):
        # Independently of erf error, Psi must integrate Phi: compare a definite
        # integral from Psi against brute-force quadrature of the exact Phi.
        a, b, n = -1.5, 2.0, 200_000
        step = (b - a) / n
        quad = sum(
            0.5 * (1 + math.erf((a + (i + 0.5) * step) / math.sqrt(2))) * step
            for i in range(n)
        )
        self.assertAlmostEqual(pine_npsi(b) - pine_npsi(a), quad, places=6)


class TestLegMassParity(unittest.TestCase):
    def test_matches_reference_within_erf_error(self):
        leg = Leg(99.0, 101.5, 6.0, True)
        for sigma in (0.0, 0.1, 0.4, 1.2):
            p = 98.5
            while p < 102.0:
                got = pine_leg_mass(leg.lo, leg.hi, leg.mass, p, p + 0.25, sigma)
                want = leg_mass_in_row(leg, p, p + 0.25, sigma)
                self.assertAlmostEqual(got, want, places=6, msg=f"sigma={sigma} p={p}")
                p += 0.25


class TestFullProfileParity(unittest.TestCase):
    """Run the whole pipeline with the Pine's erf and compare row by row."""

    def _pine_profile(self, bar, cfg):
        legs = decompose(bar, cfg.action_exponent)
        sigma = cfg.sigma_for(bar.range)
        k_lo = math.floor(bar.l / cfg.row_size)
        k_hi = math.floor(bar.h / cfg.row_size)
        if k_hi > k_lo and abs(bar.h - k_hi * cfg.row_size) <= cfg.row_size * 1e-9:
            k_hi -= 1
        n = max(1, k_hi - k_lo + 1)
        buy = [0.0] * n
        sell = [0.0] * n
        up_mass = sum(l.mass for l in legs if l.up) or 1.0
        dn_mass = sum(l.mass for l in legs if not l.up) or 1.0
        share = up_mass / (up_mass + dn_mass)
        for leg in legs:
            scale = (
                bar.v * share / up_mass if leg.up else bar.v * (1 - share) / dn_mass
            )
            for k in range(n):
                p1 = (k_lo + k) * cfg.row_size
                q = pine_leg_mass(leg.lo, leg.hi, leg.mass, p1, p1 + cfg.row_size, sigma)
                if leg.up:
                    buy[k] += q * scale
                else:
                    sell[k] += q * scale
        # Pine rescales identically.
        tb, ts = bar.v * share, bar.v * (1 - share)
        buy = [x * tb / sum(buy) for x in buy] if sum(buy) > 0 else buy
        sell = [x * ts / sum(sell) for x in sell] if sum(sell) > 0 else sell
        return buy, sell

    def test_rows_agree(self):
        cfg = FootprintConfig(row_size=0.25, concentration=6.0)
        for bar in (
            Bar(100.0, 102.3, 99.1, 101.7, 5000),
            Bar(50.0, 50.4, 49.2, 49.3, 1200),
            Bar(10.0, 12.0, 9.0, 11.0, 800),
        ):
            ref = build_profile(bar, cfg)
            pine_buy, pine_sell = self._pine_profile(bar, cfg)
            self.assertEqual(len(pine_buy), len(ref.rows), msg=f"row count for {bar}")
            for i, row in enumerate(ref.rows):
                self.assertAlmostEqual(
                    pine_buy[i], row.buy, delta=bar.v * 1e-6, msg=f"buy row {i}"
                )
                self.assertAlmostEqual(
                    pine_sell[i], row.sell, delta=bar.v * 1e-6, msg=f"sell row {i}"
                )


class TestPineSourceStaysInSync(unittest.TestCase):
    """Guard the one table that must match the derivation exactly."""

    @classmethod
    def setUpClass(cls):
        with open(PINE_PATH) as fh:
            cls.src = fh.read()

    def test_leg_table_matches_the_derivation(self):
        # lLo / lHi spell out the six leg spans; they must match decompose().
        lo = re.search(r"lLo = array\.from\(([^)]*)\)", self.src).group(1)
        hi = re.search(r"lHi = array\.from\(([^)]*)\)", self.src).group(1)
        up = re.search(r"lUp = array\.from\(([^)]*)\)", self.src).group(1)
        norm = lambda s: [x.strip() for x in s.split(",")]
        self.assertEqual(norm(lo), ["o", "l", "l", "l", "l", "c"])
        self.assertEqual(norm(hi), ["h", "h", "c", "o", "h", "h"])
        self.assertEqual(
            norm(up), ["true", "false", "true", "false", "true", "false"]
        )

    def test_python_decompose_uses_the_same_spans(self):
        bar = Bar(10, 12, 9, 11, 100)
        spans = {(round(l.lo, 9), round(l.hi, 9), l.up) for l in decompose(bar, 0.0)}
        o, h, l_, c = bar.o, bar.h, bar.l, bar.c
        expected = {
            (o, h, True),
            (l_, h, False),
            (l_, c, True),
            (l_, o, False),
            (l_, h, True),
            (c, h, False),
        }
        self.assertEqual(spans, expected)

    def test_defaults_agree_across_ports(self):
        cfg = FootprintConfig()
        pairs = [
            (r'input\.float\(([\d.]+), "Volume concentration"', cfg.concentration),
            (r'input\.float\(([\d.]+), "Least-action exponent"', cfg.action_exponent),
            (r'input\.float\(([\d.]+),\s+"Value area %"', cfg.value_area_pct),
            (r'input\.float\(([\d.]+),\s+"Imbalance ratio"', cfg.imbalance_threshold),
            (r'input\.float\(([\d.]+),\s+"Balance tilt %"', cfg.balance_tilt_pct),
        ]
        for pattern, want in pairs:
            m = re.search(pattern, self.src)
            self.assertIsNotNone(m, msg=f"no Pine input matching {pattern}")
            self.assertAlmostEqual(float(m.group(1)), want, msg=pattern)

    def test_no_unsupported_pine_constructs(self):
        # Pine has no break/continue and no nested function definitions.
        self.assertNotRegex(self.src, r"(?m)^\s+(break|continue)\s*$")
        # Join wrapped signatures before checking indentation, so a parameter
        # list spilling onto a second line is not mistaken for a nested def.
        logical, buf, depth = [], "", 0
        for line in self.src.splitlines():
            code = line.split("//")[0]
            buf = line if not buf else buf + " " + line.strip()
            depth += code.count("(") - code.count(")")
            if depth <= 0:
                logical.append(buf)
                buf, depth = "", 0
        for line in logical:
            if "=>" in line and not line.lstrip().startswith("//"):
                indent = len(line) - len(line.lstrip())
                self.assertEqual(
                    indent, 0, msg=f"function must be declared at top level: {line!r}"
                )


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestPineStructure(unittest.TestCase):
    """Static checks for the Pine constraints that bite hardest at compile time."""

    @classmethod
    def setUpClass(cls):
        with open(PINE_PATH) as fh:
            cls.src = fh.read()
        cls.lines = cls.src.splitlines()

    def test_declares_version_6(self):
        self.assertIn("//@version=6", self.src)

    def test_no_tabs(self):
        for i, line in enumerate(self.lines, 1):
            self.assertNotIn("\t", line, msg=f"tab on line {i}; Pine wants spaces")

    def test_indentation_follows_pine_continuation_rules(self):
        """Pine keys blocks off 4-space indents, and distinguishes a wrapped
        line from a new block by that line NOT being a multiple of 4. So a
        statement must sit on a multiple of 4, and a continuation must not --
        getting either backwards silently reparses the script."""
        depth = 0
        for i, line in enumerate(self.lines, 1):
            code = line.split("//")[0]
            if not line.strip() or line.lstrip().startswith("//"):
                depth += code.count("(") - code.count(")")
                continue
            indent = len(line) - len(line.lstrip())
            if depth > 0:
                self.assertNotEqual(
                    indent % 4, 0,
                    msg=f"line {i} continues a wrapped call but sits on a "
                        f"multiple-of-4 indent, which Pine reads as a new block",
                )
            else:
                self.assertEqual(
                    indent % 4, 0, msg=f"statement at odd indent {indent} on line {i}"
                )
            depth = max(0, depth + code.count("(") - code.count(")"))

    def test_user_functions_are_defined_before_use(self):
        # Pine resolves top-down: calling a function declared further down the
        # file is a compile error, and is easy to introduce when reordering.
        defs = {}
        for i, line in enumerate(self.lines):
            m = re.match(r"^([a-zA-Z_]\w*)\s*\(.*=>\s*$", line)
            if m:
                defs[m.group(1)] = i
        self.assertIn("legMass", defs, msg="parser failed to find function defs")

        for name, def_line in defs.items():
            for i, line in enumerate(self.lines):
                if i <= def_line or line.lstrip().startswith("//"):
                    continue
                if re.search(rf"\b{name}\s*\(", line):
                    break
            # Now look for any *earlier* call.
            for i, line in enumerate(self.lines[:def_line]):
                if line.lstrip().startswith("//"):
                    continue
                self.assertIsNone(
                    re.search(rf"\b{name}\s*\(", line),
                    msg=f"{name}() called on line {i + 1}, defined on line {def_line + 1}",
                )

    def test_for_loops_over_arrays_are_guarded(self):
        # Pine iterates backwards when start > end, so `0 to size-1` on an empty
        # array steps to -1 and faults instead of skipping.
        for i, line in enumerate(self.lines, 1):
            m = re.search(r"for \w+ = 0 to (array\.size\([^)]*\)) - 1", line)
            if not m:
                continue
            window = "\n".join(self.lines[max(0, i - 14) : i])
            self.assertRegex(
                window,
                r"(size\([^)]*\) > 0|> EPS|if n > 0)",
                msg=f"unguarded array loop on line {i}: {line.strip()}",
            )

    def test_na_guards_are_nested_not_chained(self):
        # `and` does not reliably short-circuit, so array.size() must not sit in
        # the same condition as the na() check that protects it.
        for i, line in enumerate(self.lines, 1):
            if "array.size" in line and "na(" in line and " and " in line:
                self.fail(f"chained na/size guard on line {i}: {line.strip()}")

    def test_drawing_budget_is_capped(self):
        # TradingView hard-caps drawings; the window can ask for more.
        self.assertRegex(self.src, r"array\.size\(labs\) < \d+")
        for obj in ("max_boxes_count", "max_labels_count", "max_lines_count"):
            self.assertIn(obj, self.src)
