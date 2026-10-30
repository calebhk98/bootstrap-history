"""A node that makes something pays for what it takes to keep making it: its staff and its plant (`sim/engine/node_upkeep.py`,
`node_revenue._apply_output`). Each rule is called on a hand-made node and entry; no tree is loaded and no game is built."""
import unittest

from sim.production import node_revenue, node_upkeep
from sim.unit_conversions import HOURS_PER_PERSON_YEAR
from sim.tests.test_plant_figures import GOODS, WAGES, baskets, entry

QUICK_TOPIC = True

MONEY_PER_HOUR = 2.0


def derived_node(**fields):
    node = dict({"id": "kiln_works", "kind": "ENGINEERING"}, **fields)
    plant_baskets = baskets(entry(capacity=500.0))
    node_revenue._apply_output(node, plant_baskets, GOODS, WAGES, MONEY_PER_HOUR)
    return node, plant_baskets


class DerivedUpkeepTests(unittest.TestCase):
    def test_derived_upkeep_is_staff_wages_plus_plant_maintenance(self):
        node, plant_baskets = derived_node()
        parts = node["_upkeep_hours_parts"]
        staff = sum(WAGES[trade] * hours for trade, hours in plant_baskets.labour_hours.items()) / MONEY_PER_HOUR
        plant = node_upkeep.maintenance_hours(node, parts["plant_build_hours"], parts["plant_wear_hours"])
        self.assertGreater(staff, 0.0)
        self.assertGreater(plant, 0.0)
        self.assertAlmostEqual(parts["staff"], staff)
        self.assertAlmostEqual(node["up_hours"], staff + plant)
        self.assertEqual(node["_upkeep_basis"], "derived")

    def test_plant_is_the_capital_the_entry_states_priced_at_the_goods_prices(self):
        node, _baskets = derived_node()
        build = (100.0 * GOODS["brick"] + 50.0 * WAGES["mason"]) / MONEY_PER_HOUR
        self.assertAlmostEqual(node["_upkeep_hours_parts"]["plant_build_hours"], build)

    def test_an_entry_that_states_no_capital_keeps_no_plant_up(self):
        node = {"id": "reed_works", "kind": "ENGINEERING"}
        node_revenue._apply_output(node, baskets(entry(capacity=None), staff_people=1.0), GOODS, WAGES, MONEY_PER_HOUR)
        self.assertEqual(node["_upkeep_hours_parts"]["plant"], 0.0)
        self.assertEqual(node["up_hours"], node["_upkeep_hours_parts"]["staff"])

    def test_derived_upkeep_does_not_read_the_authored_figure(self):
        plain, _baskets = derived_node()
        stated, _baskets = derived_node(up_hours=1e9, _up_hours_authored=1e9)
        self.assertEqual(stated["up_hours"], plain["up_hours"])

    def test_plant_upkeep_is_never_more_than_the_wear_the_price_already_charges(self):
        parts = derived_node()[0]["_upkeep_hours_parts"]
        self.assertLessEqual(parts["plant"], parts["plant_wear_hours"] * (1 + 1e-9))


class ProgrammeUpkeepTests(unittest.TestCase):
    def test_a_programme_costs_what_its_labour_and_consumables_cost(self):
        node = {"annual_labour_hours": {"labourer": 10.0}, "annual_consumables": {"wheat_kg": 100.0}}
        wages, goods = {"labourer": 2.0}, {"wheat_kg": 0.5}
        self.assertAlmostEqual(node_upkeep.programme_spending_hours(node, goods, wages, 2.0), (20.0 + 50.0) / 2.0)
        self.assertTrue(node_upkeep.is_programme(node))
        self.assertFalse(node_upkeep.is_programme({}))

    def test_the_maintenance_share_is_a_fraction_of_the_build_cost(self):
        for kind in ("INFRASTRUCTURE", "ENGINEERING", "RESOURCE", None):
            hours = node_upkeep.maintenance_hours({"kind": kind}, 1000.0)
            self.assertGreater(hours, 0.0)
            self.assertLess(hours, 1000.0)
            self.assertAlmostEqual(node_upkeep.maintenance_hours({"kind": kind}, 2000.0), 2.0 * hours)

    def test_maintenance_is_capped_at_the_wear(self):
        self.assertEqual(node_upkeep.maintenance_hours({"kind": "ENGINEERING"}, 1000.0, 5.0), 5.0)
        self.assertGreater(node_upkeep.maintenance_hours({"kind": "ENGINEERING"}, 1000.0, 1e9), 5.0)

    def test_a_node_stating_no_upkeep_keeps_up_what_it_cost_to_build(self):
        node = {"kind": "RESOURCE"}
        self.assertEqual(node_upkeep.unstated_upkeep_hours(node, 800.0), node_upkeep.maintenance_hours(node, 800.0))

    def test_named_staff_places_are_paid_a_year_each(self):
        node = {"sch": 2.0, "art": 1.0}
        wages = {node_upkeep.SCHOLAR_STAFF_TRADE: 3.0, node_upkeep.CRAFT_STAFF_TRADE: 2.0}
        hours = node_upkeep.staff_places_hours_cost(node, wages, 1.0)
        self.assertAlmostEqual(hours, 8.0 * HOURS_PER_PERSON_YEAR)



if __name__ == "__main__":
    unittest.main()
