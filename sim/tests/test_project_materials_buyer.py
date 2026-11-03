"""A project's materials are ordered by the acting seat: each deliverable missing material becomes a buy order for the year's
clearing, tagged with the project and with the quote as its limit, and the tonnes reach the stock when the year clears."""
import unittest

from sim.markets.api import BuyMaterial
from sim.tests import materials_stand_in, module_harness

QUICK_TOPIC = True


class MaterialsOrderedByTheActingSeat(unittest.TestCase):
    def test_a_deliverable_material_is_ordered_at_its_quote(self):
        bill = {"rows": [{"material": "lead_kg", "deliverable_now_tonnes": 2.0, "priced": True, "cost_of_deliverable": 50.0}]}
        module = materials_stand_in.build(answers={BuyMaterial: {"tonnes": 2.0, "committed_money": 50.0, "order_id": 7}})
        module.project_material_bill = lambda node_id: bill
        ordered, awaited = module.order_project_materials("any_node")
        self.assertEqual(ordered, 50.0)
        self.assertEqual([(entry["material"], entry["tonnes"], entry["quoted"]) for entry in awaited], [("lead_kg", 2.0, 50.0)])
        self.assertEqual([entry["order_id"] for entry in awaited], [7])
        self.assertEqual(module_harness.sent(module), [BuyMaterial("lead_kg", 2.0, 25.0, "any_node", 1.0, True)])

    def test_a_row_with_nothing_deliverable_or_no_price_orders_nothing(self):
        bill = {"rows": [{"material": "lead_kg", "deliverable_now_tonnes": 0.0, "priced": True, "cost_of_deliverable": 0.0},
                         {"material": "tin_kg", "deliverable_now_tonnes": 3.0, "priced": False, "cost_of_deliverable": 9.0}]}
        module = materials_stand_in.build()
        module.project_material_bill = lambda node_id: bill
        self.assertEqual(module.order_project_materials("any_node"), (0.0, []))
        self.assertEqual(module_harness.sent(module), [])


if __name__ == "__main__":
    unittest.main()
