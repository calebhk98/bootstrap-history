"""The effect channels a work declares in its `mechanics` (Complaint 190's benefactions use them): `MechanicsMixin`'s
`effect_values`, `effect_sum` and `effect_factor` over a stand-in that holds nodes, which are running and how many units; and
the readers that ask a channel (`standing_floor`, `goods_reach_factor`, `_schooling_flow`) called on that stand-in. No game is
built. What the benefactions branch declares is test_complaint_190_benefactions."""
import unittest
from types import SimpleNamespace

from sim.engine.core import Sim
from sim.engine.mechanics import MechanicsMixin

QUICK_TOPIC = True

NODES = {
    "school_a": {"mechanics": {"schooling_flow": {"per_unit": 0.5, "order": 1, "required": True, "reaches": ["general"]}}},
    "school_b": {"mechanics": {"schooling_flow": {"flat": 0.25, "order": 2}}},
    "patron_a": {"mechanics": {"standing": {"flat": 1.0, "order": 1, "group": "patron"}}},
    "patron_b": {"mechanics": {"standing": {"flat": 2.0, "order": 2, "group": "patron"}}},
    "charter": {"mechanics": {"standing": {"flat": 4.0, "order": 3, "gate": "has"}}},
    "road": {"mechanics": {"reach": {"factor": 1.5}}},
    "canal": {"mechanics": {"reach": {"factor": 1.6}}},
    "hall": {"mechanics": {"supervision_room": {"per_unit": 3.0}}},
}


class Channels(MechanicsMixin):
    """What the channel readers ask of a game: the nodes, which are running or built, the units of each, and a household."""

    REACH_CEILING = Sim.REACH_CEILING

    def __init__(self, running=(), built=(), units=1.0, scandal=0.0):
        self.nodes = NODES
        self.labour = SimpleNamespace(money_per_labour_hour=lambda: 1.0)
        self._running, self._built, self._units = set(running), set(built) | set(running), units
        self.state = SimpleNamespace(projects=SimpleNamespace(done=set(), granted=set()),
                                     household=SimpleNamespace(scandal=scandal))

    def running(self, node_id):
        return node_id in self._running

    def has(self, node_id):
        return node_id in self._built

    def institution_units(self, node_id):
        return self._units


class EffectValues(unittest.TestCase):

    def test_a_closed_work_contributes_nothing_and_an_open_one_its_declared_value(self):
        self.assertEqual(Channels().effect_values("schooling_flow"), [])
        self.assertEqual(Channels(running=["school_b"]).effect_values("schooling_flow"), [("school_b", 0.25)])

    def test_a_per_unit_work_scales_with_its_units(self):
        self.assertEqual(Channels(running=["hall"], units=1.0).effect_sum("supervision_room"), 3.0)
        self.assertEqual(Channels(running=["hall"], units=4.0).effect_sum("supervision_room"), 12.0)

    def test_the_sum_starts_from_the_base_and_adds_each_open_work(self):
        self.assertEqual(Channels(running=["school_a", "school_b"]).effect_sum("schooling_flow", 10.0), 10.75)

    def test_a_group_counts_once_for_its_first_holder_in_declared_order(self):
        both = Channels(running=["patron_a", "patron_b"]).effect_values("standing")
        self.assertEqual(both, [("patron_a", 1.0)])
        self.assertEqual(Channels(running=["patron_b"]).effect_values("standing"), [("patron_b", 2.0)])

    def test_a_has_gated_work_counts_when_built_though_not_running(self):
        self.assertEqual(Channels(built=["charter"]).effect_sum("standing"), 4.0)

    def test_factors_multiply(self):
        self.assertAlmostEqual(Channels(running=["road", "canal"]).effect_factor("reach"), 2.4)
        self.assertEqual(Channels().effect_factor("reach"), 1.0)


class ReadersAskTheirChannel(unittest.TestCase):

    def test_standing_rises_by_the_open_works_declared_amount(self):
        shut = Sim.standing_floor(Channels())
        opened = Sim.standing_floor(Channels(running=["patron_a"]))
        self.assertAlmostEqual(opened - shut, 1.0)

    def test_standing_is_lower_with_scandal(self):
        self.assertLess(Sim.standing_floor(Channels(scandal=3.0)), Sim.standing_floor(Channels()))

    def test_goods_reach_widens_with_an_open_work_and_is_capped(self):
        self.assertEqual(Sim.goods_reach_factor(Channels()), 1.0)
        self.assertAlmostEqual(Sim.goods_reach_factor(Channels(running=["road"])), 1.5)
        many = Channels(running=["road", "canal"])
        many.REACH_CEILING = 2.0
        self.assertEqual(Sim.goods_reach_factor(many), 2.0)

    def test_schooling_flow_is_nothing_with_no_school_and_grows_with_an_open_one(self):
        self.assertEqual(Sim._schooling_flow(Channels()), 0.0)
        self.assertGreater(Sim._schooling_flow(Channels(running=["school_a"])), 0.0)

    def test_schooling_flow_is_nothing_when_the_required_school_is_shut(self):
        self.assertEqual(Sim._schooling_flow(Channels(running=["school_b"])), 0.0)

    def test_a_school_that_names_fields_teaches_only_those(self):
        game = Channels(running=["school_a"])
        self.assertGreater(Sim._schooling_flow(game, "general"), 0.0)
        self.assertEqual(Sim._schooling_flow(game, "scientific"), 0.0)


class FurtherUnitsCostMore(unittest.TestCase):
    """`institution_unit_cost` over a stand-in that holds the founding cost and the convexity."""

    def cost(self, have_units, add_units, convexity=0.5, capex=1000.0):
        game = SimpleNamespace(venture_capex=lambda node_id: capex, INSTITUTION_EXPANSION_CONVEXITY=convexity)
        return Sim.institution_unit_cost(game, "college", have_units, add_units)

    def test_the_first_unit_costs_exactly_what_founding_costs(self):
        self.assertEqual(self.cost(0.0, 1.0), 1000.0)

    def test_a_second_unit_costs_more_than_the_first(self):
        self.assertGreater(self.cost(1.0, 1.0), self.cost(0.0, 1.0))

    def test_each_further_unit_costs_more_than_the_one_before(self):
        costs = [self.cost(units, 1.0) for units in range(5)]
        self.assertEqual(costs, sorted(costs))
        self.assertEqual(len(set(costs)), 5)

    def test_with_no_convexity_every_unit_costs_the_same(self):
        self.assertEqual(self.cost(3.0, 1.0, convexity=0.0), 1000.0)

    def test_adding_nothing_costs_nothing(self):
        self.assertEqual(self.cost(2.0, 0.0), 0.0)


if __name__ == "__main__":
    unittest.main()
