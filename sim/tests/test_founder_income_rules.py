"""What the founder is charged and paid, each rule called on a stand-in that holds only what it reads (Complaints 518, 524):
a derived upkeep leaves out the crew's pay (`institution_upkeep`), the living cost charged nets off the dependants the income
cannot carry and the wages paid in advance (`dependants_beyond_means_of`, `_step_money_seat`), and the founder's job is the
hours not spoken for sold in the held trade (`held_trade`, `founder_wage_income`, `revenue_sources`, `revenue`). The share rule
on nodes is in test_founder_crew_paid_once, the job's arithmetic in test_founder_job."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.engine import economy_production
from sim.engine.economy_debt_service import dependants_beyond_means_of
from sim.engine.economy_production import ProductionMixin
from sim.engine.step_phase_money import MoneyPhaseMixin

NODE = "workshop"


class InstitutionUpkeepTests(unittest.TestCase):
    def upkeep(self, node, scalable=False, capability=False, headcount=0.0, units=None, fully_staffed=False, places=10.0, full=False):
        game = SimpleNamespace(
            nodes={NODE: node}, state=SimpleNamespace(projects=SimpleNamespace(operating={NODE})),
            SCALABLE_INSTITUTIONS={NODE} if scalable else set(), CAPABILITY_INSTITUTIONS={NODE} if capability else set(),
            institution_units=lambda node_id: 3.0, institution_places=lambda node_id: places, INSTITUTION_FLOOR=0.2,
            mechanic=lambda node_id, name: full, labour=SimpleNamespace(headcount=lambda: headcount))
        return ProductionMixin.institution_upkeep(game, NODE, units, fully_staffed)

    def test_the_crews_pay_is_left_out_because_the_payroll_already_has_it(self):
        node = {"up": 100.0, "_upkeep_hours_parts": {"staff": 3.0, "plant": 1.0}}
        self.assertAlmostEqual(self.upkeep(node), 25.0)

    def test_a_node_with_no_stated_crew_keeps_its_whole_upkeep(self):
        self.assertEqual(self.upkeep({"up": 100.0}), 100.0)

    def test_a_scalable_institution_costs_what_is_open_and_a_stated_size_costs_that_size(self):
        self.assertEqual(self.upkeep({"up": 10.0}, scalable=True), 30.0)
        self.assertEqual(self.upkeep({"up": 10.0}, scalable=True, units=2), 20.0)
        self.assertEqual(self.upkeep({"up": 10.0}, scalable=False, units=2), 10.0)

    def test_a_capability_institution_costs_the_floor_when_empty_and_all_when_full(self):
        node = {"up": 100.0}
        self.assertAlmostEqual(self.upkeep(node, capability=True, headcount=0.0), 20.0)
        self.assertAlmostEqual(self.upkeep(node, capability=True, headcount=5.0), 60.0)
        self.assertAlmostEqual(self.upkeep(node, capability=True, headcount=50.0), 100.0)

    def test_fully_staffed_and_a_full_upkeep_mechanic_skip_the_occupancy_scaling(self):
        node = {"up": 100.0}
        self.assertEqual(self.upkeep(node, capability=True, fully_staffed=True), 100.0)
        self.assertEqual(self.upkeep(node, capability=True, full=True), 100.0)


class DependantsBeyondMeansTests(unittest.TestCase):
    GRID = [(capital, dependants, living, revenue, upkeep)
            for capital in (-500.0, 0.0, 500.0) for dependants in (0.0, 40.0, 100.0)
            for living in (100.0, 300.0) for revenue in (0.0, 150.0, 600.0, 5000.0) for upkeep in (0.0, 80.0)
            if dependants <= living]

    def shed(self, capital, dependants, living, revenue, upkeep):
        return dependants_beyond_means_of(capital, dependants, living, revenue, upkeep, 0.0, 0.05, 0.5)

    def test_what_is_shed_is_never_subsistence_and_never_more_than_the_dependants_cost(self):
        for case in self.GRID:
            capital, dependants, living, _revenue, _upkeep = case
            self.assertTrue(0.0 <= self.shed(*case) <= dependants, case)
            self.assertGreaterEqual(living - self.shed(*case), living - dependants, case)

    def test_the_cost_paid_is_no_more_than_the_income_leaves_unless_subsistence_alone_exceeds_it(self):
        for case in self.GRID:
            capital, dependants, living, revenue, upkeep = case
            paid = living - self.shed(*case)
            interest_free_room = revenue - upkeep
            self.assertTrue(paid <= max(interest_free_room, living - dependants) + 1e-9, (case, paid))


class MoneySeatChargeTests(unittest.TestCase):
    def run_phase(self, living, shed, prepaid):
        household = SimpleNamespace(wages_prepaid=prepaid, capital=1000.0, log=[], slaves=0)
        founder = SimpleNamespace(living_cost_paid=0.0, policy={"auto_mothball": False, "auto_open": False,
                                                                 "auto_buy_people": False, "auto_manumit": False})
        game = mock.MagicMock()
        game.state = SimpleNamespace(household=household, founder=founder, holdings=SimpleNamespace(mine_cost_paid=0.0),
                                     scenario=SimpleNamespace(year=100))
        game.living_cost.return_value = living
        game.dependants_beyond_means.return_value = shed
        game.view.return_value = lambda *call: (0.0, 0.0)    # the coin module's coin_keeping_due quote
        game.reopen_restaffed_ventures.return_value = []
        game.revenue.return_value = game.upkeep.return_value = game.mine_operating_cost.return_value = 0.0
        game.manual = True
        MoneyPhaseMixin._step_money_seat(game)
        return game, household, founder

    def test_the_wages_paid_are_the_living_cost_less_the_dependants_shed_and_the_advance(self):
        game, household, founder = self.run_phase(living=100.0, shed=30.0, prepaid=20.0)
        game.pay_wages.assert_called_once_with(50.0, "living costs")
        self.assertEqual((founder.living_cost_paid, household.wages_prepaid), (50.0, 0.0))

    def test_an_advance_larger_than_the_cost_nets_it_to_nothing_and_is_used_up(self):
        game, household, founder = self.run_phase(living=100.0, shed=0.0, prepaid=500.0)
        game.pay_wages.assert_called_once_with(0.0, "living costs")
        self.assertEqual(household.wages_prepaid, 0.0)


class FoundersJobTests(unittest.TestCase):
    def held(self, nodes, practice):
        game = SimpleNamespace(nodes=nodes, _practice_set=lambda: practice)
        return ProductionMixin.held_trade(game)

    def test_a_founder_who_holds_no_skill_sells_no_trade(self):
        self.assertIsNone(self.held({}, set()))

    def test_a_skill_that_asks_for_scholars_makes_the_trade_scholar_else_artisan(self):
        nodes = {"reading": {"sch": 1}, "smithing": {"sch": 0}}
        self.assertEqual(self.held(nodes, {"reading", "smithing"}), "scholar")
        self.assertEqual(self.held(nodes, {"smithing"}), "artisan")

    def test_the_income_is_the_standing_jobs_pay_in_the_held_trade(self):
        game = SimpleNamespace(held_trade=lambda: "artisan", labour=SimpleNamespace(standing_job_pay=lambda trade: {"artisan": 42.0}[trade]))
        self.assertEqual(ProductionMixin.founder_wage_income(game), 42.0)

    def test_revenue_sources_carry_the_wages_once_after_the_output_factor_and_no_practice_line(self):
        seen = {}
        game = SimpleNamespace(
            output_factor=0.5, state_funding=lambda: 0.0,
            ledger_concern_rows=lambda: {"inn": 10.0}, workshop_output=lambda: 4.0, founder_wage_income=lambda: 20.0,
            revenue=lambda: 99.0)
        with mock.patch.object(economy_production, "assemble_ledger",
                               lambda rows, workshop, wages, funding, revenue: seen.update(rows=rows, workshop=workshop, wages=wages,
                                                                                         funding=funding, revenue=revenue) or {}):
            ProductionMixin.revenue_sources(game)
        self.assertEqual(seen, {"rows": {"inn": 10.0}, "workshop": 2.0, "wages": 10.0, "funding": None, "revenue": 99.0})


class RevenueCacheTests(unittest.TestCase):
    def game(self):
        household = SimpleNamespace(operating_version=0, done_version=0, workforce_version=0, institution_units_version=0,
                                    wage_hours_this_year=0.0, directors_extra=0.0, bondage_years_left=0, reputation=1.0,
                                    freedmen=0, slaves=0)
        state = SimpleNamespace(
            scenario=SimpleNamespace(year=100), economy=SimpleNamespace(output_per_head=1.0),
            projects=None, household=household,
            governance=SimpleNamespace())
        game = SimpleNamespace(state=state, household=household, founder_alive=True, output_factor=1.0, view=lambda name: (lambda: {"governance": 0.0, "reputation": 1.0, "hectares": 0.0}), pop_scale=1.0, real_output_per_head=lambda: 1.0, state_funding=lambda: 0.0, home_price_level=lambda: 1.0,
                               signature=1.0, committed=0.0, computed=[], _compute_revenue_uncached=None)
        game.labour = SimpleNamespace(director_hours_committed=lambda: game.committed, wage_signature=lambda: game.signature)
        game._compute_revenue_uncached = lambda: game.computed.append(1) or (10.0 * len(game.computed), 0.0)
        return game

    def test_an_unchanged_year_is_computed_once(self):
        game = self.game()
        ProductionMixin.revenue(game)
        ProductionMixin.revenue(game)
        self.assertEqual(len(game.computed), 1)

    def test_a_change_in_the_market_wage_the_job_is_paid_recomputes_revenue(self):
        game = self.game()
        before = ProductionMixin.revenue(game)
        game.signature = 2.0
        self.assertNotEqual(ProductionMixin.revenue(game), before)

    def test_hours_taken_up_supervising_recompute_revenue(self):
        game = self.game()
        ProductionMixin.revenue(game)
        game.committed = 100.0
        ProductionMixin.revenue(game)
        self.assertEqual(len(game.computed), 2)


if __name__ == "__main__":
    unittest.main()
