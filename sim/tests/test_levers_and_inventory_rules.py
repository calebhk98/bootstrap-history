"""Food, housing, trade schools, demographics and the material report, each rule called on a stand-in `self` that carries only
what the method reads. The typed-command parse is a rule in test_typed_front_end; the stock accounting of the material throttle
is a rule in test_material_throttle_rules; a purchase or sale of material is test_purchase_limited_by_offered_volume and
test_one_goods_market_wiring."""
QUICK_TOPIC = True

import types
import unittest

from sim.engine.economy_goods import GoodsMixin
from sim.labour.labour_capacity import CapacityMixin
from sim.labour.labour_population import PopulationMixin
from sim.ledger.api import rules as ledger_rules
from sim.tests import materials_stand_in
from sim.ui.proto.render import render_pretty


def household(**fields):
    return types.SimpleNamespace(**{"capital": 1_000_000.0, "trades_created": set(), **fields})


class FarmlandTests(unittest.TestCase):
    def test_farmland_lowers_the_essential_price_ratio_below_neutral(self):
        def ratio(farm_hectares):
            stand_in = types.SimpleNamespace(
                ESSENTIAL_CATEGORIES=frozenset(), goods_category_price_ratio=lambda category: None,
                household=types.SimpleNamespace(farm_hectares=farm_hectares),
                HOUSEHOLD_FARM_PRICE_RATIO_FLOOR=GoodsMixin.HOUSEHOLD_FARM_PRICE_RATIO_FLOOR,
                HOUSEHOLD_FARM_HECTARES_HALF_EFFECT=GoodsMixin.HOUSEHOLD_FARM_HECTARES_HALF_EFFECT)
            return GoodsMixin.essential_price_ratio(stand_in)
        self.assertEqual(ratio(0.0), 1.0)
        self.assertLess(ratio(120.0), 1.0)


class HousingTests(unittest.TestCase):
    def test_worker_housing_adds_its_places_and_pays_its_price(self):
        paid = []
        held = household(worker_housing_places=2.0)
        stand_in = types.SimpleNamespace(
            housing_price_per_place=lambda: 100.0, state=types.SimpleNamespace(household=held),
            pay_edge=lambda edge, cost, note: paid.append(cost))
        self.assertEqual(GoodsMixin.build_worker_housing(stand_in, 5), 5.0)
        self.assertEqual(held.worker_housing_places, 7.0)
        self.assertEqual(paid, [500.0])

    def test_supervision_room_grows_by_the_worker_housing_places(self):
        def room(places):
            stand_in = types.SimpleNamespace(
                SUPERVISION_ROOM_SELF=6.0, SUPERVISION_ROOM_PER_DIRECTOR_EXTRA=1.0,
                _world=types.SimpleNamespace(state=types.SimpleNamespace(household=household(directors_extra=0.0, worker_housing_places=places)),
                                             effect_sum=lambda effect, base: base))
            return CapacityMixin.supervision_room(stand_in)
        self.assertEqual(room(5.0), room(0.0) + 5.0)


class TradeSchoolTests(unittest.TestCase):
    def test_a_school_for_an_existing_trade_adds_seats_and_marks_the_trade_created(self):
        held = household()
        paid = []
        stand_in = types.SimpleNamespace(
            trade_available=lambda trade: True,
            _world=types.SimpleNamespace(wages={"chemist": 1.0}, trade_school_price_per_seat=lambda: 50.0,
                                         state=types.SimpleNamespace(household=held), EDGE_WORKERS="workers",
                                         pay_edge=lambda edge, cost, note: paid.append(cost)))
        self.assertEqual(PopulationMixin.found_trade_school(stand_in, "chemist", 2), (True, None))
        self.assertEqual(held.trade_schools, {"chemist": 2.0})
        self.assertEqual(held.trades_created, {"chemist"})
        self.assertEqual(paid, [100.0])


class PopulationReportTests(unittest.TestCase):
    def test_each_trade_row_carries_national_reachable_and_employed_figures(self):
        stand_in = types.SimpleNamespace(
            _world=types.SimpleNamespace(civ={"population": 1000.0, "short_name": "Rome"}, population=types.SimpleNamespace(total=1500.0),
                                         urban_fraction=lambda: 0.1, wages={"smith": 1.0}, plain_number=lambda number: "%g" % number),
            national_trade_population=lambda trade: 900.0, reachable_trade_population=lambda trade: 40.0,
            trade_available=lambda trade: True, employed=lambda trade: 4.0, _density_is_placeholder=lambda trade: False,
            home_town_population_estimate=lambda: 5000.0)
        report = PopulationMixin.population_report(stand_in)
        self.assertEqual(report["trades"][0]["estimated_in_the_country"], 900.0)
        self.assertEqual(report["trades"][0]["within_your_reach"], 40.0)
        self.assertEqual(report["trades"][0]["you_employ"], 4.0)
        self.assertEqual(report["trades"][0]["share_of_the_reachable_pool_you_employ"], 0.1)


class MaterialsReportTests(unittest.TestCase):
    def stand_in(self):
        module = materials_stand_in.build(
            held_goods=ledger_rules.StockLedger({"iron": 50.0}), goods_stock=lambda material: {"iron": 50.0}.get(material, 0.0),
            goods_quote=lambda material: {"material": material, "buy_per_tonne": 9.0, "sell_per_tonne": 7.0} if material == "iron" else None)
        module.demand_by_commodity = lambda: {"iron": [("tag", 10.0)]}
        module.own_production_tags = lambda: [("iron", "mine:iron")]
        module.own_material_supply = lambda tag: 3.0
        return module

    def test_a_row_reports_stock_flow_demand_and_cover(self):
        rows = self.stand_in().materials_report()
        self.assertEqual(rows, [{"material": "iron", "buy_per_tonne": 9.0, "sell_per_tonne": 7.0, "stock_on_hand_tonnes": 50.0,
                                 "own_production_tonnes_per_year": 3.0, "current_demand_tonnes_per_year": 10.0,
                                 "stock_covers_years_at_current_demand": 5.0}])

    def test_the_readable_screen_carries_its_heading(self):
        # presentation: the materials screen's heading
        self.assertIn("MATERIAL STOCKS", render_pretty("materials", {"ok": True, "materials": self.stand_in().materials_report()}))


if __name__ == "__main__":
    unittest.main()
