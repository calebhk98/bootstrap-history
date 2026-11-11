"""Complaint 492: a royalty on mined output is a revenue form on the ore the country's producers raised, whoever owns the
mine: the base is the tonnes raised, priced at the market. `revenue_bases.harvest` for a good other than the staple, no game."""
QUICK_TOPIC = True

import types
import unittest

from sim.agents import revenue_bases


def world_with(output_by_owner, price):
    """A stand-in world: the ore raised on the held tiles is the sum over owners, whoever they are."""
    return types.SimpleNamespace(
        quotes=types.SimpleNamespace(staple_material=lambda: "grain_kg", material_price=lambda material: price),
        revenue=types.SimpleNamespace(output_tonnes=lambda material, tiles=None: sum(output_by_owner.values())))


class MineRoyalty(unittest.TestCase):
    def test_the_base_is_the_tonnes_every_owner_raised_at_the_market_price(self):
        base = revenue_bases.harvest(world_with({"firm": 30.0, "state": 10.0, "founder": 5.0}, 4.0), None, "iron_ore_kg")
        self.assertAlmostEqual(base.tonnes, 45.0)
        self.assertAlmostEqual(base.value, 180.0)
        self.assertEqual(base.material, "iron_ore_kg")

    def test_an_ore_nobody_prices_is_not_assessed(self):
        self.assertIsNone(revenue_bases.harvest(world_with({"firm": 30.0}, None), None, "iron_ore_kg"))


if __name__ == "__main__":
    unittest.main()
