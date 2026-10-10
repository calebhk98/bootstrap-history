"""A project's materials are bought by the acting seat: the purchase names `market.acting`, so an
automatic founder that starts a project is not stopped by a missing attribute."""
import unittest
from types import SimpleNamespace

from sim.engine.project_materials import ProjectMaterialsMixin

QUICK_TOPIC = True


class RecordingMarket:
    """Only the seat attribute the engine names, and the one call that settles the purchase."""

    def __init__(self):
        self.acting = "seat:one"
        self.settled = []

    def settle_purchase(self, buyer, stock_key, tonnes, money, purpose):
        self.settled.append((buyer, stock_key, tonnes, money, purpose))


class MaterialsBoughtByTheActingSeat(unittest.TestCase):
    def test_purchase_is_settled_for_the_acting_seat(self):
        market = RecordingMarket()
        bill = {"rows": [{"material": "lead_kg", "deliverable_now_tonnes": 2.0, "priced": True,
                          "cost_of_deliverable": 50.0}]}
        stub = SimpleNamespace(
            opposition_factor=lambda node_id: 1.0, geography=SimpleNamespace(material_cost_factor=lambda node_id: 1.0),
            goods_market=market, project_material_bill=lambda node_id: bill,
            _material_tag=lambda material: ("lead", "tag"))
        paid = ProjectMaterialsMixin.buy_project_materials(stub, "any_node")
        self.assertEqual(paid, 50.0)
        self.assertEqual(market.settled, [("seat:one", "lead", 2.0, 50.0, "materials bought for projects")])


if __name__ == "__main__":
    unittest.main()
