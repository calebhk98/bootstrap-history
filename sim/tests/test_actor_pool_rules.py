"""Complaints 103 and 185, Complaint 640: the callers that make actors compete with the founder, each over a stand-in:
what firms and governments employ is off the pool the founder's market supplies and hires from; an actor taking on
people presses the labour market and one shedding them eases it; a hire raises the price of its trade; the state sees
any actor by one visible-scale function; a concern's takings are shared with the other sellers of its goods category.
The levy and crew rules are in test_actor_firms_compete and test_firm_crew_rule."""
QUICK_TOPIC = True

import types
import unittest
from sim.tests import workforce_stand_in

from sim.agents.base import Actor
from sim.actors.world import ActorWorld
from sim.labour.labour import Labour
from sim.labour.labour_market_api import LabourMarket
from sim.refusal import cause_of
from sim.tests.labour_stand_in import stand_in_world
from sim.tests.world_stand_in import fake_needs

HOURS = 2000.0


def labour_of(actor_staff=0.0):
    world = stand_in_world("rome_100ad")
    world.shared_answer = lambda key, inputs, compute, standalone=False: compute()
    world.home_tiles_held_version = lambda: 0
    world.cfg = {"hired_hours_cap_base": 25000}
    world.effect_factor = lambda channel, value, exponent=None: value
    world.actor_staff_fte = lambda trade: actor_staff
    return Labour(world)


class SharedPool(unittest.TestCase):
    def test_what_actors_employ_is_off_the_hours_the_market_supplies(self):
        free = labour_of(0.0).market_supply("smith")
        taken = labour_of(5.0).market_supply("smith")
        self.assertAlmostEqual(free - taken, 5.0 * HOURS, delta=1e-6)

    def test_hiring_everyone_the_actors_have_not_taken_is_refused_for_want_of_people(self):
        labour = labour_of(0.0)
        exist = labour.people_who_exist("smith")
        labour._world.actor_staff_fte = lambda trade: exist - 3.0
        count, fee, refusal = labour.hire_check("smith", 5)
        self.assertEqual((count, fee), (None, None))
        self.assertEqual(cause_of(refusal), "nobody_left")


class Market:
    def __init__(self):
        self.hired, self.released = [], []

    def hire(self, employer, trade, hours):
        self.hired.append((trade, hours))

    def release(self, employer, trade, hours):
        self.released.append((trade, hours))


class HiringRaisesThePrice(unittest.TestCase):
    def _market(self):
        household = types.SimpleNamespace(labour_pressure_records={}, employees={})
        world = types.SimpleNamespace(
            workforce=household, view=workforce_stand_in.view_of(household), year=0, state=types.SimpleNamespace(household=household, scenario=types.SimpleNamespace(year=0)),
            HOURS_PER_PERSON_YEAR=HOURS, wages={"smith": 1}, trade_family=lambda trade: "craft", price_index=1.0,
            wage_index=1.0, actor_staff_fte=lambda trade: 0.0, economy=types.SimpleNamespace(agent_wage_per_hour=lambda trade: 0.05))
        labour = types.SimpleNamespace(_world=world, market_supply=lambda trade: 20.0 * HOURS,
                                       wage_schedule=lambda: types.SimpleNamespace(training_years={"smith": 1.0}),
                                       base_annual_wage=lambda trade: 100.0, wage_cost_factors=lambda trade: {"weighted": 1.0},
                                       employed=lambda trade: 0.0)
        return LabourMarket(labour)

    def test_hours_taken_on_by_an_employer_raise_what_the_trade_costs_and_letting_them_go_eases_it(self):
        market = self._market()
        before = market.price_factor("smith")
        market.hire(object(), "smith", 10.0 * HOURS)
        pressed = market.price_factor("smith")
        market.release(object(), "smith", 10.0 * HOURS)
        self.assertGreater(pressed, before)
        self.assertEqual(market.price_factor("smith"), before)


class PressNewStaff(unittest.TestCase):
    def test_people_taken_on_press_the_market_and_people_let_go_ease_it(self):
        market = Market()
        world = types.SimpleNamespace(labour_market=market, hours_per_person_year=HOURS)
        actor = types.SimpleNamespace(workforce={"smith": 7.0, "mason": 1.0, "scribe": 2.0})
        Actor.press_new_staff(actor, {"smith": 4.0, "mason": 3.0, "scribe": 2.0}, world)
        self.assertEqual(market.hired, [("smith", 3.0 * HOURS)])
        self.assertEqual(market.released, [("mason", 2.0 * HOURS)])


class VisibleScale(unittest.TestCase):
    def test_any_actor_is_seen_by_its_staff_its_wealth_and_its_prominence(self):
        seen = []
        module = types.SimpleNamespace(needs=fake_needs(visible_scale=lambda *args: seen.append(args) or 0.4))
        actor = types.SimpleNamespace(workforce={"smith": 3.0, "mason": 2.0}, money=500.0, concealed_wealth=lambda: 100.0,
                                      prominence=lambda: 0.25, defiance=lambda: 0.5)
        self.assertEqual(ActorWorld(module).visible_scale_of(actor), 0.4)
        headcount, wealth, eminence, defiance = seen[0]
        self.assertEqual((headcount, eminence, defiance), (5.0, 0.25, 0.5))
        self.assertLess(wealth, 500.0)      # what is hidden is not counted


class ConcernTakings(unittest.TestCase):
    def _world(self, category, factor=0.5):
        module = types.SimpleNamespace(needs=fake_needs(
            tree_nodes={"loom": {"cat": category}}, legacy_constant={"GOODS_CATEGORIES": ("textiles",)},
            game_setting={"revenue_ramp_years": 5}, year=10, ramp_share_at_full_depth=0.5,
            industry_depth=lambda node_id: 0.0, concern_takings=lambda node_id, ramp: 1000.0,
            node_output_market_factor=lambda node: 1.0, goods_category_factor=lambda cat: factor))
        return ActorWorld(module)

    def test_a_goods_category_shares_one_market_among_every_seller(self):
        self.assertEqual(self._world("textiles", 0.5).concern_takings("loom", 10, rivals=3.0, capacity=2.0), 2000.0 * 0.5)

    def test_a_concern_with_no_market_model_splits_with_its_rivals_capacity(self):
        self.assertEqual(self._world("metals").concern_takings("loom", 10, rivals=2.0, capacity=2.0), 2000.0 / 4.0)


if __name__ == "__main__":
    unittest.main()
