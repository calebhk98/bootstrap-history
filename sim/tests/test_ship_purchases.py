"""Complaint 617: the navy buys durable ships made by shipwrights."""
QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.agents import budget_lines
from sim.book import Book, GoodsMove
from sim.economy.types import GoodSpec
from sim.engine import economy_port_actors as actors_port
from sim.engine.economy_port import EconomyPort
from sim.world import demand


METAL, FARMS = "metal", "farms"


def storage_economy(capital_asset):
    """A stand-in economy whose buyer account holds 2 units of a durable bought this year."""
    book = Book()
    book.move(GoodsMove("edge:legacy", actors_port.buy_account("state:a"), METAL, FARMS, 2.0, "test purchase"))
    specs = {METAL: GoodSpec(METAL, 1.0, 0.0, 20.0, "metal", capital_asset=capital_asset)}
    return SimpleNamespace(record=SimpleNamespace(book=book), setup=SimpleNamespace(currency_id="coin", specs=specs))


class ShipPurchases(unittest.TestCase):
    def test_fleet_planning_does_not_open_an_unopened_economy(self):
        world = SimpleNamespace(state=SimpleNamespace(
            projects=SimpleNamespace(granted={"sea_mortise_tenon"})))
        port = EconomyPort(world)
        port._opening = True
        goods = port.fleet_goods("state:a")
        self.assertEqual([good["material"] for good in goods], ["warship"])
        self.assertEqual(goods[0]["held"], 0.0)
        self.assertGreater(goods[0]["life"], 0.0)

    def test_a_new_good_without_a_curated_commodity_group_can_be_bought(self):
        world = SimpleNamespace(_material_commodity_map=lambda: {"iron_bar_kg": "iron"})
        port = EconomyPort(world)
        self.assertEqual(port.materials_in("warship"), ["warship"])
        self.assertEqual(port.materials_in("iron"), ["iron_bar_kg"])

    def test_navy_buys_missing_hulls_and_keeps_only_the_crew_on_payroll(self):
        world = SimpleNamespace(
            government=lambda: SimpleNamespace(record=SimpleNamespace(levers={})),
            territory=lambda: SimpleNamespace(coast_km=100.0),
            fleet_goods=lambda: [{"material": "test_hull", "life": 20.0,
                                  "held": 0.0, "crew": {"sailor": 60.0}}],
            trade_exists=lambda trade: True, national_people=lambda trade: 100000.0,
            pay_per_person_year=lambda trade: 10.0,
            commodity_of=lambda material: material,
            material_cost=lambda material, tonnes: tonnes * 1000000.0)
        line, = budget_lines.navy_line(world)
        self.assertEqual(line.labour, {"sailor": 60.0})
        self.assertAlmostEqual(line.materials.get("test_hull", 0.0), 0.001)
        self.assertGreater(line.material_cost, 0.0)
        world.fleet_goods = lambda: [{"material": "test_hull", "life": 20.0,
                                     "held": 1.0, "crew": {"sailor": 60.0}}]
        replacement, = budget_lines.navy_line(world)
        self.assertAlmostEqual(replacement.materials["test_hull"], 0.001 / 20.0)
        world.territory = lambda: SimpleNamespace(coast_km=0.0)
        self.assertEqual(budget_lines.navy_line(world), [])

    def test_bought_durables_are_retained_by_the_buyer_when_the_purchase_closes(self):
        economy = storage_economy(capital_asset=True)
        actors_port.close(economy, [], [{"buyer": "state:a"}])
        book = economy.record.book
        self.assertAlmostEqual(book.stock(actors_port.held_account("state:a"), METAL, FARMS), 2.0)
        self.assertEqual(book.stock(actors_port.buy_account("state:a"), METAL, FARMS), 0.0)

    def test_materials_bought_for_immediate_use_are_consumed_even_if_durable(self):
        economy = storage_economy(capital_asset=False)
        actors_port.close(economy, [], [{"buyer": "state:a"}])
        book = economy.record.book
        self.assertEqual(book.stock(actors_port.held_account("state:a"), METAL, FARMS), 0.0)
        self.assertEqual(book.stock(actors_port.buy_account("state:a"), METAL, FARMS), 0.0)

    def test_ship_recipes_take_shipwright_work_and_make_counted_goods(self):
        production = demand.production_data()
        for good in ("merchant_ship", "warship"):
            with self.subTest(good=good):
                entry = production.get(good, {})
                self.assertEqual(entry.get("unit_dimension"), "count")
                self.assertGreater(entry.get("unit_mass_kg", 0.0), 0.0)
                self.assertGreater(entry.get("labour_hours", {}).get("shipwright", 0.0), 0.0)
                self.assertEqual(entry.get("outputs"), {good: 1.0})


if __name__ == "__main__":
    unittest.main()
