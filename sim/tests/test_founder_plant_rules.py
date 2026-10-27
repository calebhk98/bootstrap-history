"""The founder's business and a firm's are one object (stage 3a of docs/architecture/FIRMS_OWN_PLANTS_PLAN.md): the plant
keeps its size and age through a mothball and a restore (`Business.mothball`, `Business.restore`) and leaves its owner whole
(`release_plant`); the founder's verbs and quotes call the same rules a firm's do (`close_work`, `close_venture`,
`venture_hands`, `venture_upkeep_quote`, `venture_real_earnings`, `venture_ramp`, `ActorWorld.concern_takings`). Each is called
on a stand-in that holds only what it reads."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace
from unittest import mock

from sim.agents.business import Business
from sim.agents.business_closing import release_plant
from sim.agents.business_plant import MOTHBALLED, OPERATING, Plant
from sim.actors import world as actors_world
from sim.actors.world import ActorWorld
from sim.engine import projects_ventures, projects_venture_quotes
from sim.production import revenue as production_revenue
from sim.ledger.api import PayEdge
from sim.tests import module_harness, production_host, projects_host

from .world_stand_in import fake_needs
from sim.production.concern_earnings import quoted_ramp, quoted_units
from sim.engine.projects_venture_quotes import VentureQuotesMixin
from sim.engine.projects_ventures import VenturesMixin

NODE = "concern"


class PlantKeepsItsStateTests(unittest.TestCase):
    def test_mothballing_keeps_the_same_plant_with_its_size_and_age(self):
        plant = Plant(entry_key=NODE, size=2.5, opened_year=92)
        business = Business(plants=[plant])
        returned = business.mothball(NODE, 100, "by_choice")
        self.assertIs(returned, plant)
        self.assertEqual((plant.state, plant.since_year, plant.reason, plant.size, plant.opened_year),
                         (MOTHBALLED, 100, "by_choice", 2.5, 92))

    def test_restoring_returns_the_same_plant_operating_with_no_reason(self):
        plant = Plant(entry_key=NODE, size=2.5, opened_year=92, state=MOTHBALLED, since_year=100, reason="by_choice")
        business = Business(plants=[plant])
        self.assertIs(business.restore(NODE), plant)
        self.assertEqual((plant.state, plant.since_year, plant.reason, plant.size, plant.opened_year),
                         (OPERATING, None, "", 2.5, 92))


class ReleasePlantTests(unittest.TestCase):
    def test_a_released_plant_leaves_with_its_size_and_age_and_the_business_forgets_it(self):
        business = Business(plants=[Plant(entry_key=NODE, size=1.0, opened_year=92)])
        plant = release_plant(business, NODE, SimpleNamespace(year=100))
        self.assertEqual((plant.size, plant.opened_year), (1.0, 92))
        self.assertIsNone(business.plant_of(NODE))

    def test_a_plant_with_no_recorded_opening_is_dated_to_now(self):
        business = Business(plants=[Plant(entry_key=NODE)])
        self.assertEqual(release_plant(business, NODE, SimpleNamespace(year=100)).opened_year, 100)

    def test_releasing_a_plant_the_business_does_not_run_is_an_error(self):
        with self.assertRaises(KeyError):
            release_plant(Business(), NODE, SimpleNamespace(year=100))


class ClosingTests(unittest.TestCase):
    def test_close_work_mothballs_the_plant_for_the_reason_and_closes_what_depends_on_it(self):
        business = Business(plants=[Plant(entry_key=NODE)])
        module = projects_host.build(legacy_projects=SimpleNamespace(business=business), year=100)
        dependents_closed_in = []
        module.close_lapsed_dependents = dependents_closed_in.append
        module.close_work(NODE, "by_choice")
        self.assertEqual((business.state_of(NODE), business.plant_of(NODE).reason, dependents_closed_in),
                         (MOTHBALLED, "by_choice", [100]))

    def test_close_work_for_staff_is_remembered_and_cascade_can_be_turned_off(self):
        business = Business(plants=[Plant(entry_key=NODE)])
        projects = SimpleNamespace(business=business)
        module = projects_host.build(legacy_projects=projects, year=100)
        module.close_lapsed_dependents = lambda year: self.fail("cascade was off")
        module.close_work(NODE, module.CLOSED_FOR_STAFF, cascade=False)
        self.assertEqual(module.seat.ever_closed_for_staff, {NODE})

    def close_venture(self, operating):
        closed = []
        game = SimpleNamespace(state=SimpleNamespace(projects=SimpleNamespace(operating=operating)), CLOSED_BY_CHOICE="by_choice",
                               close_work=lambda node_id, reason: closed.append((node_id, reason)), nodes={NODE: {"up": 1.0, "rev": 2.0}})
        with mock.patch.object(projects_ventures, "money_text", return_value="m"):
            return VenturesMixin.close_venture(game, NODE)[0], closed

    def test_closing_a_concern_you_run_closes_it_by_choice(self):
        self.assertEqual(self.close_venture({NODE}), (True, [(NODE, "by_choice")]))

    def test_closing_a_concern_you_do_not_run_is_refused_and_closes_nothing(self):
        self.assertEqual(self.close_venture(set()), (False, []))


class RestoreWorkTests(unittest.TestCase):
    def restore(self, venture):
        business = Business(plants=[Plant(entry_key=NODE, state=MOTHBALLED, reason="by_choice", size=2.0, opened_year=92)])
        projects = SimpleNamespace(mothballed={NODE}, done={NODE}, business=business, closures=business.closures())
        module = projects_host.build(
            legacy_projects=projects, tree={NODE: {"pre": []}}, reopen_fee=lambda node_id: 5.0, spending_power=lambda kind: 10.0,
            acting_balance=0.0, is_venture=lambda node_id: venture, year=100)
        ok, _reply = module.restore_work(NODE)
        paid = [command.amount for command in module_harness.sent(module) if isinstance(command, PayEdge)]
        return ok, paid, business

    def test_restoring_a_concern_pays_the_fee_and_puts_the_same_plant_back_to_work(self):
        ok, paid, business = self.restore(venture=True)
        plant = business.plant_of(NODE)
        self.assertEqual((ok, paid, plant.state, plant.reason, plant.size, plant.opened_year), (True, [5.0], OPERATING, "", 2.0, 92))

    def test_restoring_a_work_that_is_not_a_concern_leaves_no_plant(self):
        ok, paid, business = self.restore(venture=False)
        self.assertEqual((ok, paid, business.plant_of(NODE)), (True, [5.0], None))


class QuoteWiringTests(unittest.TestCase):
    def test_hands_are_the_crew_rules_for_the_plants_own_figures(self):
        game = SimpleNamespace(crew_figures=lambda node_id: ("figures", node_id), concern_runs_without_founder=lambda node_id: False)
        with mock.patch.object(projects_ventures.business_crew_rule, "hands", lambda figures, runs: (figures, runs())):
            self.assertEqual(VenturesMixin.venture_hands(game, NODE), (("figures", NODE), False))

    def test_the_upkeep_quote_is_now_and_fully_staffed_at_the_price_level(self):
        calls = []
        game = SimpleNamespace(institution_upkeep=lambda node_id, units, fully_staffed=False: calls.append(fully_staffed) or (9.0 if fully_staffed else 4.0),
                               price_index=2.0)
        with mock.patch.object(projects_venture_quotes, "upkeep_quote", lambda now, full, index: {"now": now * index, "at_full_staffing": full * index}):
            self.assertEqual(VentureQuotesMixin.venture_upkeep_quote(game, NODE), {"now": 8.0, "at_full_staffing": 18.0})
        self.assertEqual(calls, [False, True])

    def earnings(self, running, **kwargs):
        seen = {}
        game = SimpleNamespace(
            state=SimpleNamespace(projects=SimpleNamespace(operating={NODE} if running else set()), acting_seat=0),
            SCALABLE_INSTITUTIONS={NODE}, venture_ramp=lambda node_id: 0.4, institution_units=lambda node_id: 3.0,
            node_output_market_factor=lambda node, seat: 0.9, nodes={NODE: {}},
            concern_takings=lambda node_id, ramp, with_output_factor=True: seen.update(ramp=ramp) or 100.0)
        with mock.patch.object(projects_venture_quotes.business_books, "takings_of_size",
                               lambda takings, units, market: seen.update(units=units, market=market) or takings):
            VentureQuotesMixin.venture_real_earnings(game, NODE, **kwargs)
        return seen

    def test_a_running_scalable_concern_is_quoted_at_its_own_ramp_and_units(self):
        self.assertEqual(self.earnings(True), {"ramp": 0.4, "units": 3.0, "market": 0.9})

    def test_a_concern_not_yet_open_is_quoted_at_full_ramp_and_one_unit(self):
        self.assertEqual(self.earnings(False), {"ramp": 1.0, "units": 1.0, "market": 0.9})


class QuotedFiguresTests(unittest.TestCase):
    def test_ramp_is_full_unless_the_concern_runs_and_the_full_one_was_not_asked_for(self):
        self.assertEqual((quoted_ramp(False, False, lambda: 0.4), quoted_ramp(True, True, lambda: 0.4), quoted_ramp(True, False, lambda: 0.4)),
                         (1.0, 1.0, 0.4))

    def test_units_are_those_asked_else_those_running_for_a_scalable_open_concern_else_one(self):
        self.assertEqual((quoted_units(True, True, lambda: 3.0, 2.0), quoted_units(True, True, lambda: 3.0),
                          quoted_units(True, False, lambda: 3.0), quoted_units(False, True, lambda: 3.0)), (2.0, 3.0, 1.0, 1.0))


class RampTests(unittest.TestCase):
    def ramp(self, opened_year, done_year=None):
        seen = {}
        projects = SimpleNamespace(business=Business(plants=[Plant(entry_key=NODE, opened_year=opened_year)] if opened_year is not None else []),
                                   done_year={NODE: done_year} if done_year is not None else {})
        module = production_host.build(SimpleNamespace(state=SimpleNamespace(projects=projects, scenario=SimpleNamespace(year=100)),
                                                       cfg={"revenue_ramp_years": 5}))
        module.industry_depth = lambda node_id: 0.5
        with mock.patch.object(production_revenue.plant_figures, "ramp",
                               lambda age, years, depth, share: seen.update(age=age, years=years, depth=depth) or 0.7):
            self.assertEqual(module.venture_ramp(NODE), 0.7)
        return seen

    def test_the_ramp_counts_from_the_year_it_was_opened(self):
        self.assertEqual(self.ramp(92, done_year=80), {"age": 8, "years": 5, "depth": 0.5})

    def test_without_an_opening_year_it_counts_from_the_year_the_work_was_learned(self):
        self.assertEqual(self.ramp(None, done_year=90)["age"], 10)


class FirmSideTests(unittest.TestCase):
    def test_a_firms_takings_go_through_the_same_size_arithmetic_as_the_founders(self):
        seen = {}
        needs = fake_needs(concern_takings=lambda node_id, ramp: 100.0, node_output_market_factor=lambda node: 0.9)
        world = SimpleNamespace(nodes={NODE: {"cat": "other"}}, needs=needs, goods_category_names=set(),
                                ramp=lambda opened_year, node_id=None: 0.5)
        with mock.patch.object(actors_world.business_books, "takings_of_size",
                               lambda takings, size, market: seen.update(takings=takings, size=size, market=market) or takings * size):
            result = ActorWorld.concern_takings(world, NODE, 90, rivals=1.0, capacity=2.0)
        self.assertEqual(seen, {"takings": 100.0, "size": 2.0, "market": 0.9})
        self.assertEqual(result, 200.0 / 3.0)

    def test_a_firms_crew_and_upkeep_are_the_engines_for_that_concern(self):
        needs = fake_needs(concern_staff=lambda node_id: {"smith": 2.0}, concern_upkeep=lambda node_id, capacity: 7.0 * capacity)
        world = SimpleNamespace(needs=needs)
        self.assertEqual(ActorWorld.concern_staff(world, NODE), {"smith": 2.0})
        self.assertEqual(ActorWorld.upkeep(world, NODE, 2.0), 14.0)


if __name__ == "__main__":
    unittest.main()
