"""`LivingStockOpeningMixin.grant_opening_herds` credits the ledger with the head the economy's herd producers keep, held to the
pasture the held tiles carry, and records it as the society's herd. Called on a stand-in carrying only what the methods read; no game."""
import types
import unittest
from unittest import mock

from sim.engine import living_stock_opening
from sim.engine.living_stock_opening import LivingStockOpeningMixin

QUICK_TOPIC = True

PRODUCTION = {"keep_flock": {"herd_stock": {"sheep_kg": 2.0}}, "weave": {"outputs": {"cloth": 1.0}}}


def setUpModule():
    patcher = mock.patch.object(living_stock_opening, "production_data", lambda: PRODUCTION)
    patcher.start()
    unittest.addModuleCleanup(patcher.stop)


def stand_in(capacities, carried_kg, keeping=lambda material: 1.0):
    granted = []
    game = types.SimpleNamespace(
        economy=types.SimpleNamespace(producer_capacities=lambda: capacities),
        geography=types.SimpleNamespace(held_pasture_kg=lambda wild_stock: carried_kg),
        state=types.SimpleNamespace(economy=types.SimpleNamespace(wild_stock={}, society_herds={})),
        endemic_keeping=keeping, granted=granted,
        grant_stock=lambda material, units: granted.append((material, units)))
    game.society_herds = game.state.economy.society_herds
    game.opening_herd_units = lambda: LivingStockOpeningMixin.opening_herd_units(game)
    return game


class GrantOpeningHerdsTests(unittest.TestCase):
    def test_the_ledger_is_credited_the_head_the_herd_producers_keep(self):
        game = stand_in([("keep_flock", 10.0), ("weave", 5.0)], 1.0e12)
        units = game.opening_herd_units()
        self.assertTrue(units)
        LivingStockOpeningMixin.grant_opening_herds(game)
        self.assertEqual(dict(game.granted), units)
        self.assertEqual(game.state.economy.society_herds, units)

    def test_a_pasture_that_cannot_carry_the_head_scales_the_grant_down(self):
        roomy = stand_in([("keep_flock", 10.0)], 1.0e12)
        units = roomy.opening_herd_units()
        tight = stand_in([("keep_flock", 10.0)], 1.0)
        LivingStockOpeningMixin.grant_opening_herds(tight)
        for material, granted in tight.state.economy.society_herds.items():
            self.assertLess(granted, units[material])

    def test_no_herd_producers_credit_nothing(self):
        game = stand_in([("weave", 5.0)], 1.0e12)
        LivingStockOpeningMixin.grant_opening_herds(game)
        self.assertEqual(game.granted, [])
        self.assertEqual(game.state.economy.society_herds, {})


if __name__ == "__main__":
    unittest.main()
