"""The one crossing wiring sim/world/military_logistics.py into the engine: the per-soldier equipment burden follows
the founder's military leverage between the melee floor and the modern-rifle ceiling, and leverage counts only the
founder's own military nodes. The polity module over a set of nodes done. Soldier iron and ammunition supply is derived in
kilograms and never converted to money."""

QUICK_TOPIC = True

import unittest
from sim.polity import constants
from sim.tests import polity_host
from sim.world import military_logistics as logistics

MELEE_KG = logistics.annual_iron_and_ammunition_burden_kg_per_soldier()


def founder_with(military_done=0, granted=0, other_done=0):
    """The polity module over a set of nodes done, some granted free: the real leverage and burden arithmetic."""
    nodes, done, granted_nodes = {}, set(), set()
    for index in range(military_done + granted):
        node_id = "military_%d" % index
        nodes[node_id] = {"traits": ("military",)}
        done.add(node_id)
        if index >= military_done:
            granted_nodes.add(node_id)
    for index in range(other_done):
        node_id = "other_%d" % index
        nodes[node_id] = {"traits": ("trade",)}
        done.add(node_id)
    return polity_host.build(tree_nodes=nodes, techniques_held=done, techniques_granted=granted_nodes)


def rifle_kg(founder):
    return logistics.annual_iron_and_ammunition_burden_kg_per_soldier(
        firearm=logistics.MODERN_SERVICE_RIFLE,
        engagements_per_year=constants.MILITARY_EQUIPMENT_ERA_CAMPAIGN_TEMPO_ENGAGEMENTS_PER_YEAR)


class Leverage(unittest.TestCase):

    def test_a_founder_with_no_military_node_has_none(self):
        self.assertEqual(founder_with(other_done=5).military_leverage(), 0.0)

    def test_leverage_saturates_at_one_however_much_more_is_built(self):
        saturates = constants.MILITARY_LEVERAGE_SATURATES_AT
        self.assertEqual(founder_with(military_done=int(saturates)).military_leverage(), 1.0)
        self.assertEqual(founder_with(military_done=int(saturates) + 10).military_leverage(), 1.0)

    def test_leverage_rises_with_each_military_node_built(self):
        values = [founder_with(military_done=count).military_leverage() for count in (0, 1, 5, 10)]
        self.assertEqual(values, sorted(values))
        self.assertEqual(len(set(values)), 4)

    def test_nodes_the_society_already_had_do_not_count(self):
        self.assertEqual(founder_with(granted=10).military_leverage(), 0.0)


class Burden(unittest.TestCase):

    def test_at_zero_leverage_the_burden_is_the_melee_only_figure_exactly(self):
        self.assertEqual(founder_with().military_equipment_burden_kg_per_soldier_per_year(), MELEE_KG)

    def test_at_full_leverage_the_burden_is_the_modern_rifle_figure_at_the_declared_tempo(self):
        founder = founder_with(military_done=int(constants.MILITARY_LEVERAGE_SATURATES_AT))
        self.assertAlmostEqual(founder.military_equipment_burden_kg_per_soldier_per_year(), rifle_kg(founder), places=9)

    def test_partial_leverage_lies_strictly_between_the_floor_and_the_ceiling(self):
        founder = founder_with(military_done=5)
        self.assertLess(MELEE_KG, founder.military_equipment_burden_kg_per_soldier_per_year())
        self.assertLess(founder.military_equipment_burden_kg_per_soldier_per_year(), rifle_kg(founder))

    def test_more_military_nodes_never_report_a_lighter_burden(self):
        burdens = [founder_with(military_done=count).military_equipment_burden_kg_per_soldier_per_year()
                   for count in (0, 1, 5, 25)]
        self.assertEqual(burdens, sorted(burdens))
        self.assertGreater(burdens[-1], burdens[0])

    def test_an_army_s_own_adoption_stands_in_for_the_founder_s_leverage(self):
        founder = founder_with()
        self.assertAlmostEqual(founder.military_equipment_burden_kg_per_soldier_per_year(adoption=1.0), rifle_kg(founder))

    def test_the_burden_is_a_function_of_the_done_set_alone(self):
        first, second = founder_with(military_done=3), founder_with(military_done=3)
        self.assertEqual(first.military_equipment_burden_kg_per_soldier_per_year(),
                         second.military_equipment_burden_kg_per_soldier_per_year())


if __name__ == "__main__":
    unittest.main()
