"""`grant_opening_herds` of the living-stock module credits the ledger with the head the economy's herd producers keep, held
to the pasture the held tiles carry, and records it as the society's herd. The module is built by `module_harness` with the
producers and the pasture as plain values; no game."""
import unittest
from unittest import mock

from sim.ledger.api import ChangeStock
from sim.living_stock import holding
from sim.living_stock.api import GrantOpeningHerds
from sim.living_stock.module import LivingStock
from sim.living_stock.state import LivingStockWorld
from sim.tests import module_harness
from sim.world.material_units import tonnes_per_unit

QUICK_TOPIC = True

PRODUCTION = {"keep_flock": {"herd_stock": {"sheep_kg": 2.0}}, "weave": {"outputs": {"cloth": 1.0}}}


def setUpModule():
    patcher = mock.patch.object(holding, "production_data", lambda: PRODUCTION)
    patcher.start()
    unittest.addModuleCleanup(patcher.stop)


def stand_in(capacities, carried_kg, keeping=lambda material: 1.0):
    module = module_harness.build(LivingStock, world=LivingStockWorld(), views={
        "producer_capacities": lambda: capacities, "stock_land": {"place": "tile", "pasture_kg": carried_kg},
        "material_commodity": lambda material: material})
    module.endemic_keeping = keeping
    return module


def granted(module):
    """{material: units} the ledger was credited, read back from the tonnes sent."""
    return {sent.commodity: sent.tonnes / tonnes_per_unit(sent.commodity) for sent in module_harness.sent(module)
            if isinstance(sent, ChangeStock)}


class GrantOpeningHerdsTests(unittest.TestCase):
    def test_the_ledger_is_credited_the_head_the_herd_producers_keep(self):
        module = stand_in([("keep_flock", 10.0), ("weave", 5.0)], 1.0e12)
        units = module.opening_herd_units()
        self.assertTrue(units)
        module.grant_opening_herds(GrantOpeningHerds())
        self.assertEqual(granted(module).keys(), units.keys())
        for material, credited in granted(module).items():
            self.assertAlmostEqual(credited, units[material])
        self.assertEqual(module.world.society_herds, units)

    def test_a_pasture_that_cannot_carry_the_head_scales_the_grant_down(self):
        units = stand_in([("keep_flock", 10.0)], 1.0e12).opening_herd_units()
        tight = stand_in([("keep_flock", 10.0)], 1.0)
        tight.grant_opening_herds(GrantOpeningHerds())
        self.assertTrue(tight.world.society_herds)
        for material, kept in tight.world.society_herds.items():
            self.assertLess(kept, units[material])

    def test_no_herd_producers_credit_nothing(self):
        module = stand_in([("weave", 5.0)], 1.0e12)
        module.grant_opening_herds(GrantOpeningHerds())
        self.assertEqual(module_harness.sent(module), [])
        self.assertEqual(module.world.society_herds, {})


if __name__ == "__main__":
    unittest.main()
