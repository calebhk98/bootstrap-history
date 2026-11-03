"""Complaints 103 and 185, Complaint 640: the callers that make actors compete with the founder, each over a stand-in:
what firms and governments employ is off the pool the founder's market supplies and hires from; the state sees
any actor by one visible-scale function; a concern's takings are shared with the other sellers of its goods category.
The levy and crew rules are in test_actor_firms_compete and test_firm_crew_rule."""
QUICK_TOPIC = True

import types
import unittest

from sim.actors.world import ActorWorld
from sim.labour.labour import Labour
from sim.refusal import cause_of
from sim.tests.labour_stand_in import stand_in_world
from sim.tests.world_stand_in import fake_needs

HOURS = 2000.0


def labour_of(actor_staff=0.0):
    world = stand_in_world("rome_100ad")
    world.people.home_tiles_held_version = lambda: 0
    world.knowledge.effect_factor = lambda channel, value, exponent=None: value
    world.actors.actor_staff_fte = lambda trade: actor_staff
    labour = Labour(world)
    labour.book.core_people_by_trade = lambda: {"smith": 1000.0}
    labour.book.core_people_by_tile_and_trade = lambda: {labour.settlement.base_tile(): {"smith": 100.0}}
    return labour


class SharedPool(unittest.TestCase):
    def test_what_actors_employ_is_off_the_hours_the_market_supplies(self):
        free = labour_of(0.0).supply.market_supply("smith")
        taken = labour_of(5.0).supply.market_supply("smith")
        self.assertAlmostEqual(free - taken, 5.0 * HOURS, delta=1e-6)

    def test_hiring_everyone_the_actors_have_not_taken_is_refused_for_want_of_people(self):
        labour = labour_of(0.0)
        exist = labour.supply.people_who_exist("smith")
        labour.supply._world.actors.actor_staff_fte = lambda trade: exist - 3.0
        count, fee, refusal = labour.hiring.hire_check("smith", 5)
        self.assertEqual((count, fee), (None, None))
        self.assertEqual(cause_of(refusal), "nobody_left")


class VisibleScale(unittest.TestCase):
    def test_any_actor_is_seen_by_its_staff_its_wealth_and_its_prominence(self):
        seen = []
        module = types.SimpleNamespace(needs=fake_needs(visible_scale=lambda *args: seen.append(args) or 0.4))
        actor = types.SimpleNamespace(workforce={"smith": 3.0, "mason": 2.0}, money=500.0, concealed_wealth=lambda: 100.0,
                                      prominence=lambda: 0.25, defiance=lambda: 0.5)
        self.assertEqual(ActorWorld(module.needs).taxpayers.visible_scale_of(actor), 0.4)
        headcount, wealth, eminence, defiance = seen[0]
        self.assertEqual((headcount, eminence, defiance), (5.0, 0.25, 0.5))
        self.assertLess(wealth, 500.0)      # what is hidden is not counted


class ConcernTakings(unittest.TestCase):
    def test_a_concern_splits_its_takings_with_its_rivals_capacity(self):
        module = types.SimpleNamespace(needs=fake_needs(
            tree_nodes={"loom": {"cat": "textiles"}}, game_setting={"revenue_ramp_years": 5}, year=10, ramp_share_at_full_depth=0.5,
            industry_depth=lambda node_id: 0.0, concern_takings=lambda node_id, ramp: 1000.0, node_output_market_factor=lambda node: 1.0))
        self.assertEqual(ActorWorld(module.needs).concerns.concern_takings("loom", 10, rivals=2.0, capacity=2.0), 2000.0 / 4.0)


if __name__ == "__main__":
    unittest.main()
