"""A project's materials are bought by the acting seat: the purchase pays the market edge, counts the tonnes in the year's
book and puts them in the seat's stock, in that order, each as the owner's command."""
import unittest

from sim.agents.api import edges
from sim.ledger.api import ChangeStock, PayEdge
from sim.markets.api import NotePurchase
from sim.tests import materials_stand_in, module_harness

QUICK_TOPIC = True


class MaterialsBoughtByTheActingSeat(unittest.TestCase):
    def test_purchase_is_settled_for_the_acting_seat(self):
        bill = {"rows": [{"material": "lead_kg", "deliverable_now_tonnes": 2.0, "priced": True, "cost_of_deliverable": 50.0}]}
        module = materials_stand_in.build()
        module.project_material_bill = lambda node_id: bill
        paid = module.buy_project_materials("any_node")
        self.assertEqual(paid, 50.0)
        self.assertEqual(module_harness.sent(module), [PayEdge(edges.EDGE_MARKET, 50.0, "materials bought for projects"),
                                                         NotePurchase("lead", 2.0), ChangeStock("lead", 2.0)])

    def test_a_row_with_nothing_deliverable_or_no_price_buys_nothing(self):
        bill = {"rows": [{"material": "lead_kg", "deliverable_now_tonnes": 0.0, "priced": True, "cost_of_deliverable": 0.0},
                         {"material": "tin_kg", "deliverable_now_tonnes": 3.0, "priced": False, "cost_of_deliverable": 9.0}]}
        module = materials_stand_in.build()
        module.project_material_bill = lambda node_id: bill
        self.assertEqual(module.buy_project_materials("any_node"), 0.0)
        self.assertEqual(module_harness.sent(module), [])


if __name__ == "__main__":
    unittest.main()
