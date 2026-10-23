"""Rush fiscal controls: a bulk start can be capped by total cost, yearly draw and a cash reserve, and refuses option values it
cannot read. The cap reader, the cap test and the typed spellings are called on inputs the test builds; the command on a game
(preview, rollback, agreement with the real run) is in test_rush_fiscal_controls_scenario."""
import unittest
from types import SimpleNamespace

from sim.ui.proto.dispatch_ventures import _rush_cap_refusal, _rush_caps
from sim.ui.protocol import parse_typed

QUICK_TOPIC = True

GAME = SimpleNamespace(civ={"id": "rome_100ad"})
BUDGET = 1000.0


def refusal(caps, cost, draw=0.0, cost_so_far=0.0, draw_so_far=0.0, budget=BUDGET):
    return _rush_cap_refusal(GAME, _rush_caps(caps, GAME)[0], budget, cost, draw, cost_so_far, draw_so_far)


class CapTests(unittest.TestCase):
    def test_no_caps_refuse_nothing(self):
        self.assertIsNone(refusal({}, 1.0e9, 1.0e9))

    def test_a_total_cost_cap_refuses_what_would_pass_it_and_says_which_cap(self):
        self.assertIsNone(refusal({"max_total_cost": 100}, 40.0, cost_so_far=60.0))
        reason = refusal({"max_total_cost": 100}, 41.0, cost_so_far=60.0)
        self.assertIn("max_total_cost", reason)

    def test_a_yearly_draw_cap_refuses_what_would_pass_it_and_says_which_cap(self):
        self.assertIsNone(refusal({"max_annual_draw": 30}, 500.0, draw=10.0, draw_so_far=20.0))
        self.assertIn("max_annual_draw", refusal({"max_annual_draw": 30}, 500.0, draw=11.0, draw_so_far=20.0))

    def test_a_cash_reserve_stays_out_of_the_budget(self):
        self.assertIsNone(refusal({"reserve_cash": 200}, 300.0, cost_so_far=500.0))
        self.assertIn("reserve_cash", refusal({"reserve_cash": 200}, 301.0, cost_so_far=500.0))

    def test_each_cap_is_checked_beside_the_others(self):
        caps = {"max_total_cost": 1000, "max_annual_draw": 10}
        self.assertIn("max_annual_draw", refusal(caps, 50.0, draw=11.0))


class ReadingTests(unittest.TestCase):
    def test_a_cap_not_given_is_none(self):
        self.assertEqual(_rush_caps({}, GAME)[0]["max_total_cost"], None)

    def test_caps_are_numbers_and_may_be_text(self):
        caps, error = _rush_caps({"max_total_cost": "20000", "reserve_cash": 5}, GAME)
        self.assertIsNone(error)
        self.assertEqual((caps["max_total_cost"], caps["reserve_cash"]), (20000.0, 5.0))

    def test_a_non_numeric_cap_is_refused_for_each_option(self):
        for option in ("max_total_cost", "max_annual_draw", "reserve_cash"):
            caps, error = _rush_caps({option: "lots"}, GAME)
            self.assertIsNone(caps, option)
            self.assertIn(option, error)

    def test_a_negative_cap_is_refused(self):
        self.assertIsNone(_rush_caps({"max_total_cost": -5}, GAME)[0])


class TypedTests(unittest.TestCase):
    def test_typed_rush_parses_every_fiscal_option(self):
        parsed, error = parse_typed("rush limit:5 max_total_cost:20000 max_annual_draw:5,000 reserve_cash:10000 preview")
        self.assertIsNone(error)
        self.assertEqual((parsed.get("max_total_cost"), parsed.get("max_annual_draw"), parsed.get("reserve_cash"),
                          parsed.get("preview"), parsed.get("limit")), (20000, 5000, 10000, True, 5))

    def test_typed_rush_refuses_an_unparseable_cap(self):
        parsed, error = parse_typed("rush max_total_cost:abc")
        self.assertIsNone(parsed)
        self.assertTrue(error)

    def test_start_all_is_the_rush_alias_and_keeps_its_options(self):
        parsed, error = parse_typed("start all max_total_cost:500")
        self.assertIsNone(error)
        self.assertEqual((parsed.get("cmd"), parsed.get("max_total_cost")), ("rush", 500))

    def test_start_of_one_id_is_still_start(self):
        self.assertEqual((parse_typed("start scientific_method")[0] or {}).get("cmd"), "start")


if __name__ == "__main__":
    unittest.main()
