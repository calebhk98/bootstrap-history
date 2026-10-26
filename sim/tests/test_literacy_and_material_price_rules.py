"""The literate-trade hiring ceiling and the premium on a material the market barely sells, each a method called on a
stand-in with its inputs written out (Complaints 640; FINDINGS_ROUND2 sections Q and R). The labour price pressure is
test_literacy_market_pricing, the scarcity curve is test_material_freight, the wall is test_staff_moves_rules."""
QUICK_TOPIC = True

import collections
import types
import unittest
from unittest import mock

from sim.engine import economy_mining
from sim.engine.economy_freight import FreightMixin
from sim.labour import labour_capacity
from sim.labour.labour_capacity import CapacityMixin


class _Society(CapacityMixin):
    LITERATE_TRADES = ("scribe", "scholar")
    LITERATE_CAPACITY_FLOOR = 1.5
    POP_SCALE_FLOOR_SHARE = 0.5
    POP_SCALE_VARIABLE_SHARE = 0.5
    SCHOLAR_MARKET_SHARE = 0.4

    def __init__(self, literacy, institutional=0.0, existing=1e9):
        self._world = types.SimpleNamespace(
            cfg={"hired_hours_cap_base": 1000.0}, pop_scale=1.0, HOURS_PER_PERSON_YEAR=10.0, trades_absent=())
        self.literacy, self.institutional, self.existing = literacy, institutional, existing

    def local_market_share(self):
        return 1.0

    def literacy_factor(self, trade):
        return self.literacy

    def staff_capacity(self):
        return (self.institutional, 0.0)

    def people_who_exist(self, trade):
        return self.existing


class LiterateCapacity(unittest.TestCase):
    def capacity(self, society, trade="scribe"):
        with mock.patch.object(labour_capacity.trade_data, "scholar_trade", lambda: "scholar"):
            return society.literate_capacity(trade)

    def test_a_trade_that_needs_no_letters_has_no_ceiling(self):
        self.assertEqual(self.capacity(_Society(0.5), "smith"), float("inf"))

    def test_the_ceiling_is_a_floor_of_findable_people_plus_a_literacy_scaled_pool(self):
        pool = 1000.0 * 1.0 * (0.5 + 0.5) * 0.4 / 10.0
        self.assertAlmostEqual(self.capacity(_Society(0.5)), 1.5 + pool * 0.5)

    def test_more_literacy_widens_the_pool_but_never_removes_the_floor(self):
        low, high = self.capacity(_Society(0.0)), self.capacity(_Society(1.0))
        self.assertEqual(low, 1.5)
        self.assertGreater(high, low)

    def test_scholars_add_the_institutional_pool_and_scribes_do_not(self):
        society = _Society(0.5, institutional=7.0)
        self.assertAlmostEqual(self.capacity(society, "scholar") - self.capacity(society, "scribe"), 7.0)

    def test_the_ceiling_never_exceeds_the_people_who_exist(self):
        self.assertEqual(self.capacity(_Society(1.0, existing=3.0)), 3.0)


class _Market(FreightMixin):
    MATERIAL_PRICE_DEMAND_SHARE_CAP = 1.5
    MATERIAL_PRICE_PRESSURE_SCALE = 0.9

    def __init__(self, market_tonnes, demands, own_supply, freight=1.0):
        self.market_tonnes, self.demands, self.own_supply, self.freight = market_tonnes, demands, own_supply, freight

    def _material_market_tonnes(self, key):
        return self.market_tonnes

    def _demand_by_emp_key(self):
        return {"saltpetre": self.demands}

    def _own_material_supply(self, tag):
        return self.own_supply

    def view(self, name):
        assert name == "material_freight_factor"
        return collections.defaultdict(lambda: self.freight)


class MaterialPriceFactor(unittest.TestCase):
    def test_demand_on_a_material_the_market_does_not_sell_costs_a_premium(self):
        self.assertGreater(_Market(0.0, [("nitre", 10.0)], 0.0).material_price_factor("saltpetre"), 1.5)

    def test_own_supply_covering_the_need_relieves_the_premium(self):
        bare = _Market(0.0, [("nitre", 10.0)], 0.0).material_price_factor("saltpetre")
        own = _Market(0.0, [("nitre", 10.0)], 1000.0).material_price_factor("saltpetre")
        self.assertLess(own, bare)
        self.assertAlmostEqual(own, 1.0 + 0.9 * (10.0 / 1000.0) ** 2)

    def test_no_demand_leaves_the_price_at_the_freight_factor_alone(self):
        self.assertAlmostEqual(_Market(5.0, [], 0.0, freight=1.3).material_price_factor("saltpetre"), 1.3)

    def test_the_freight_factor_multiplies_the_scarcity_premium(self):
        cheap = _Market(5.0, [("nitre", 5.0)], 0.0, freight=1.0).material_price_factor("saltpetre")
        far = _Market(5.0, [("nitre", 5.0)], 0.0, freight=2.0).material_price_factor("saltpetre")
        self.assertAlmostEqual(far, cheap * 2.0)


class MineableMaterials(unittest.TestCase):
    def test_a_name_that_prices_nothing_is_not_mineable_and_has_no_quote(self):
        stand_in = types.SimpleNamespace(_normalize_material_name=lambda name: name,
                                         _mine_capex=lambda name: None, _mine_capex_opex=lambda name: (None, None))
        self.assertFalse(economy_mining.MiningMixin.mineable(stand_in, "not_a_real_material"))
        self.assertIsNone(economy_mining.MiningMixin.mine_quote(stand_in, "not_a_real_material", 100.0))

    def test_a_priced_material_is_mineable(self):
        stand_in = types.SimpleNamespace(_normalize_material_name=lambda name: name, _mine_capex=lambda name: 5.0)
        self.assertTrue(economy_mining.MiningMixin.mineable(stand_in, "aluminium_kg"))


if __name__ == "__main__":
    unittest.main()
