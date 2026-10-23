"""SCENARIO (Complaint 640): Complaint 523: the opening checks are plain functions with structured results, and the `openings` gate
refuses an opening that fails them unless a reason is given."""
QUICK_TOPIC = True

import io
import unittest
from contextlib import redirect_stdout
from unittest import mock

from sim.economy.metal_stock import COIN_WEAR_PER_YEAR
from sim.engine import opening_checks, opening_checks_gate, opening_checks_table, shipped_openings_build


def _trace(first, last, years=30):
    """A trace whose money stock is `first` for the first decade, `last` for the last, and flat between."""
    rows = []
    for year in range(years):
        stock = first if year < opening_checks.DECADE_YEARS else last
        rows.append({"year": year, "money_supply": stock, "wear": stock * COIN_WEAR_PER_YEAR, "struck": 0.0})
    return rows


class PriceOverCostTests(unittest.TestCase):
    def test_a_ratio_beyond_the_band_either_way_fails_and_is_named(self):
        result = opening_checks.price_over_cost("ore", {"a": 2.0, "b": 50.0, "c": 0.01})
        self.assertFalse(result.passed)
        self.assertEqual(sorted(result.detail["outside"]), ["b", "c"])
        self.assertEqual(result.value, 0.01)    # the furthest from one, in either direction

    def test_ratios_inside_the_band_pass(self):
        self.assertTrue(opening_checks.price_over_cost("ore", {"a": 2.0, "b": 0.5}).passed)

    def test_no_ratio_is_not_a_pass(self):
        result = opening_checks.price_over_cost("ore", {})
        self.assertIsNone(result.value)
        self.assertFalse(result.passed)


class MoneyAgainstWearTests(unittest.TestCase):
    def test_a_stock_that_kept_up_passes_and_one_that_drained_fails(self):
        self.assertTrue(opening_checks.money_against_wear(_trace(100.0, 99.0)).passed)
        drained = opening_checks.money_against_wear(_trace(100.0, 50.0))
        self.assertFalse(drained.passed)
        self.assertAlmostEqual(drained.value, 0.5)
        self.assertAlmostEqual(drained.bound, (1.0 - COIN_WEAR_PER_YEAR) ** opening_checks.DECADE_YEARS)

    def test_a_trace_shorter_than_two_decades_is_not_a_pass(self):
        self.assertFalse(opening_checks.money_against_wear(_trace(100.0, 100.0, years=15)).passed)


class WageAndSettlingTests(unittest.TestCase):
    def test_wage_over_floor(self):
        self.assertTrue(opening_checks.wage_over_floor(0.3, 0.2).passed)
        below = opening_checks.wage_over_floor(0.1, 0.2)
        self.assertFalse(below.passed)
        self.assertAlmostEqual(below.value, 0.5)
        self.assertFalse(opening_checks.wage_over_floor(0.3, 0.0).passed)
        self.assertFalse(opening_checks.wage_over_floor(None, 0.2).passed)

    def test_spin_up_settled_reads_the_result(self):
        self.assertTrue(opening_checks.spin_up_settled({"settled": True, "years": 9, "gap": 0.01}, 0.02).passed)
        unsettled = opening_checks.spin_up_settled({"settled": False, "years": 30, "gap": 0.3}, 0.02)
        self.assertFalse(unsettled.passed)
        self.assertEqual(unsettled.value, 0.3)
        self.assertFalse(opening_checks.spin_up_settled({}, 0.02).passed)


class GateTests(unittest.TestCase):
    def _gate(self, passed, allow_failing=None):
        results = [opening_checks.CheckResult("c", 1.0, 2.0, "at most", passed, {})]
        gate = opening_checks_gate.OpeningGate("somewhere", allow_failing)
        patches = [mock.patch.object(opening_checks_gate.opening_checks_run, "check_game", return_value=results),
                   mock.patch.object(opening_checks_gate.opening_checks_run, "trace_entry", return_value=("ns", "k")),
                   mock.patch.object(opening_checks_gate.opening_checks_run, "opening_trace", return_value=[]),
                   mock.patch.object(opening_checks_gate.shipped_openings, "write")]
        return gate, patches

    def _call(self, gate, patches):
        output = io.StringIO()
        with redirect_stdout(output):
            for patch in patches:
                patch.start()
            try:
                gate(object())
            finally:
                mock.patch.stopall()
        return output.getvalue()

    def test_a_failing_opening_is_refused_and_writes_nothing(self):
        gate, patches = self._gate(False)
        with self.assertRaises(SystemExit) as refused:
            self._call(gate, patches)
        self.assertIn("c", str(refused.exception))
        self.assertEqual(gate.shipped, [])

    def test_a_failing_opening_ships_with_a_reason_and_the_reason_is_printed(self):
        gate, patches = self._gate(False, allow_failing="507 stage 2 regenerates it")
        self.assertIn("507 stage 2 regenerates it", self._call(gate, patches))
        self.assertEqual(gate.shipped, [("ns", "k")])

    def test_a_passing_opening_ships(self):
        gate, patches = self._gate(True)
        self._call(gate, patches)
        self.assertEqual(gate.shipped, [("ns", "k")])

    def test_the_build_calls_the_gate_with_the_opened_game_before_writing(self):
        calls = []
        with mock.patch.object(shipped_openings_build, "Sim", return_value="game"), \
                mock.patch.object(shipped_openings_build, "load", return_value=(0, 0, [], 0, 0)), \
                mock.patch.object(shipped_openings_build, "load_civ", return_value={}), \
                mock.patch.dict("os.environ", clear=False) as environment:
            environment.pop("ROME_SPIN_UP_YEARS", None)

            def refuse(game):
                calls.append(game)
                raise SystemExit("refused")
            with self.assertRaises(SystemExit):
                shipped_openings_build.build_reporting("somewhere", before_writing=refuse)
        self.assertEqual(calls, ["game"])


class TableTests(unittest.TestCase):
    def test_the_table_has_a_line_per_check_and_names_goods_outside_the_band(self):
        results = [opening_checks.price_over_cost("ore", {"iron_ore": 40.0}), opening_checks.wage_over_floor(0.3, 0.2)]
        lines = opening_checks_table.table({"rome": results})
        self.assertEqual(len(lines), 1 + 2 + 1)
        self.assertIn("iron_ore", lines[2])
        self.assertIn("FAIL", lines[1])


if __name__ == "__main__":
    unittest.main()
