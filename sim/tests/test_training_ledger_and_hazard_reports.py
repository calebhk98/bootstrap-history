"""The rules behind the Mexica, England, Rome and break testers' findings on a project's accounting, hazard advice, the
revenue ledger and how hazards are reported (Complaint 640: each rule is called on inputs built here; the checks that
need a played game are rule tests in test_bondage_training_lag, test_staffing_ceiling and test_explain_cost_factors).

Held elsewhere: a project can never be given back more hours than it has spent, and says it is in arrears when it is
(`fund_year`, test_arrears_hours); a failed attempt is announced as one project_failed line (test_completion_messaging);
interest on arrears counted in the net (test_arrears_interest_in_net)."""
QUICK_TOPIC = True

import unittest

from .harness import *  # noqa: F401,F403
from sim.hazards.capital_loss import capital_lost
from sim.engine.eminence_warning import eminence_band_to_announce
from sim.hazards.toll import sack_toll, staff_loss_toll
from sim.hazards.hedge_steps import hedge_wants, startable_first
from sim.projects.api import funding
year_bill = funding.year_bill
from sim.engine.revenue_ledger import assemble_ledger
from sim.engine.starting_techs import declared_starting_techs


class ProjectYearTests(unittest.TestCase):

    def test_a_year_asks_for_the_scaled_instalment_and_never_more_than_is_left(self):
        self.assertEqual(year_bill(1000.0, 400.0, 0.5), 200.0)
        self.assertEqual(year_bill(150.0, 400.0, 0.5), 150.0)

    def test_a_shortage_scales_the_instalment_and_not_what_is_left_so_a_small_bill_is_cleared(self):
        # The old rule paid a fraction of what was left every year, approaching zero without arriving.
        left = 1.0
        for _year in range(3):
            left -= year_bill(left, 400.0, 0.02)
        self.assertEqual(left, 0.0)


class HedgeAdviceTests(unittest.TestCase):
    nodes = {"counter": {"pre": ["near", "held"]}, "near": {"pre": []}, "held": {"pre": []},
             "other": {"pre": ["near"]}}
    rows = [("counter", 0.3, "a counter"), ("missing_node", 0.1, "unknown"), ("other", 0.1, "another")]

    def test_the_hedges_are_the_counters_and_their_unfinished_prerequisites(self):
        wants, leads_to, counters = hedge_wants(self.rows, self.nodes, {"held"})
        self.assertEqual(counters, {"counter", "other"})
        self.assertEqual(sorted(node_id for _distance, node_id in wants), ["counter", "near", "near", "other"])
        self.assertNotIn("held", leads_to)

    def test_a_node_that_is_done_or_unknown_is_no_hedge(self):
        wants, _leads_to, counters = hedge_wants(self.rows, self.nodes, {"counter", "other"})
        self.assertEqual((wants, counters), ([], set()))

    def test_a_prerequisite_says_what_it_leads_to_and_a_counter_says_what_it_is(self):
        _wants, leads_to, _counters = hedge_wants(self.rows, self.nodes, set())
        self.assertEqual(leads_to["counter"], "a counter")
        self.assertEqual(leads_to["near"], "a step toward a counter")

    def test_what_can_begin_now_comes_first_and_the_order_within_a_group_is_kept(self):
        entries = [{"id": "a", "can_begin_now": False}, {"id": "b", "can_begin_now": True},
                   {"id": "c", "can_begin_now": False}, {"id": "d", "can_begin_now": True}]
        self.assertEqual([entry["id"] for entry in startable_first(entries)], ["b", "d", "a", "c"])


class CatastropheTests(unittest.TestCase):

    def test_a_catastrophe_never_pays_off_a_debt(self):
        self.assertEqual(capital_lost(-1000.0, 0.60), 0.0)
        self.assertEqual(capital_lost(0.0, 0.60), 0.0)

    def test_a_catastrophe_takes_its_share_of_what_is_held(self):
        self.assertAlmostEqual(capital_lost(1000.0, 0.60), 600.0)

    def test_a_share_outside_zero_to_one_is_clamped(self):
        self.assertEqual(capital_lost(1000.0, 3.0), 1000.0)
        self.assertEqual(capital_lost(1000.0, -1.0), 0.0)

    def test_a_plague_that_met_no_people_and_no_takings_took_nothing(self):
        self.assertEqual(staff_loss_toll(0.0, 0.0), (False, False))
        self.assertEqual(staff_loss_toll(12.0, 0.0), (True, False))
        self.assertEqual(staff_loss_toll(0.0, 300.0), (False, True))

    def test_a_sack_reports_each_part_it_took_and_none_when_there_was_nothing(self):
        self.assertEqual(sack_toll(0.0, 0.0, 0), (False, False, False))
        self.assertEqual(sack_toll(620.0, 4.5, 2), (True, True, True))
        self.assertEqual(sack_toll(0.0, 0.0, 3), (False, False, True))


class EminenceWarningTests(unittest.TestCase):

    def test_nothing_is_said_until_eminence_nears_the_danger_line(self):
        self.assertIsNone(eminence_band_to_announce(70.0, 100.0, 0))

    def test_a_band_is_said_once_and_a_higher_one_is_said_again(self):
        band = eminence_band_to_announce(80.0, 100.0, 0)
        self.assertIsNotNone(band)
        self.assertIsNone(eminence_band_to_announce(80.0, 100.0, band))
        self.assertGreater(eminence_band_to_announce(95.0, 100.0, band), band)


class LedgerTests(unittest.TestCase):

    def _total(self, ledger):
        return sum(ledger.values())

    def test_the_parts_add_up_to_the_revenue_it_states_with_the_market_gap_a_row_of_its_own(self):
        ledger = assemble_ledger({"inn": 100.0, "mill": 60.0}, 20.0, 30.0, 10.0, 200.0)
        self.assertAlmostEqual(self._total(ledger), 200.0, places=6)
        self.assertEqual(ledger["_what_the_market_will_not_absorb"], -20.0)

    def test_only_the_largest_rows_are_listed_and_the_rest_are_summed_not_dropped(self):
        rows = {"concern_%02d" % index: float(100 - index) for index in range(20)}
        ledger = assemble_ledger(rows, 0.0, 0.0, None, sum(rows.values()))
        listed = [key for key in ledger if key.startswith("concern_")]
        self.assertEqual(len(listed), 15)
        self.assertIn("_and_5_smaller_concerns", ledger)
        self.assertAlmostEqual(self._total(ledger), sum(rows.values()), places=1)

    def test_a_gap_too_small_to_show_is_pushed_into_the_largest_row_so_the_rows_still_add_up(self):
        ledger = assemble_ledger({"inn": 100.04, "mill": 60.0}, 0.0, 0.0, None, 160.5)
        self.assertNotIn("_what_the_market_will_not_absorb", ledger)
        self.assertAlmostEqual(self._total(ledger), 160.5, places=6)

    def test_a_row_below_the_floor_is_left_out_and_its_money_is_the_market_gap(self):
        ledger = assemble_ledger({"inn": 100.0}, 0.2, 0.1, None, 100.0)
        self.assertEqual(set(ledger), {"inn"})


class StrategyOrderTests(unittest.TestCase):
    """The strategy order is data, checked without a game."""

    @classmethod
    def setUpClass(cls):
        _labour, cls.order, _bonus = S.load_strategy("recommended", NODES, GOAL)
        cls.index = {node_id: place for place, node_id in enumerate(cls.order)}

    def test_no_technology_is_ordered_before_something_it_requires(self):
        violations = [(node_id, prerequisite) for node_id in self.order for prerequisite in NODES[node_id]["pre"]
                      if self.index.get(prerequisite, -1) > self.index[node_id]]
        self.assertEqual(violations[:3], [])

    def test_everything_the_goal_needs_is_near_the_front(self):
        needed = S.closure(NODES, GOAL)
        last = max(self.index[node_id] for node_id in needed if node_id in self.index)
        self.assertLess(last, 400, "the last goal-critical node sits at index %d of %d" % (last, len(self.order)))


class OpeningGrantTests(unittest.TestCase):

    def test_a_society_is_not_granted_the_route_another_society_would_take_to_it(self):
        # Maize hangs off crossing the Atlantic; closing the grant over prerequisites would hand over steel and clocks.
        civ = json.load(open(os.path.join(ROOT, "data", "civilizations", "mexica_1500.json"), encoding="utf-8"))
        granted = set(declared_starting_techs(civ, NODES))
        self.assertIn("fud_maize", granted)
        self.assertFalse({"cementation_steel", "clock_pendulum"} & granted)


if __name__ == "__main__":
    unittest.main()
