"""The occupational measure counts every kind of work once (Complaint 619): own-plot farming, hired work, the
unskilled pool, staff of firms, merchants and states, and the standing army. Rule tests on built inputs; and the
named crafts' recipes bill their own trade, not only the generic labourer (Complaint 530)."""
QUICK_TOPIC = True

import json
import os
import unittest

from sim.engine.ui_port import ROOT
from sim.labour.api import hours_by_trade, shares_by_group

POOL = "labourer"
ARMY = frozenset({"soldier"})
# recipes of crafts that have a trade of their own: none may bill only the generic labourer
NAMED_CRAFT_RECIPES = ("waste_haulage_on_foot", "waste_haulage_by_pack_animal", "waste_haulage_by_cart", "natron_kg",
                       "wool_kg", "linen_kg", "thread_kg", "fabric_kg", "cloth_kg", "flour_kg", "bread_kg", "brick_1000",
                       "ceramic_kg", "leather_kg", "wine_common_kg", "olive_oil_kg", "charcoal_kg", "lime_kg", "salt_solar_kg")


class HoursByTrade(unittest.TestCase):
    def test_shares_are_each_groups_hours_over_all_hours(self):
        society = {"farmer": 600.0, POOL: 300.0, "weaver": 100.0}
        held = {"weaver": 150.0, "merchant": 50.0, "scribe": 20.0, "soldier": 200.0}
        hours = hours_by_trade(society, held, ARMY, POOL)
        total = 600.0 + 300.0 + 100.0 + 200.0
        self.assertAlmostEqual(sum(hours.values()), total)
        shares = shares_by_group(hours)
        self.assertAlmostEqual(shares["agriculture"], 600.0 / total)
        self.assertAlmostEqual(shares["textiles"], 150.0 / total)
        self.assertAlmostEqual(shares["services_state"], 270.0 / total)
        self.assertAlmostEqual(shares["unattributed"], 180.0 / total)
        self.assertAlmostEqual(sum(shares.values()), 1.0)

    def test_staff_already_in_the_society_hours_are_not_counted_twice(self):
        hours = hours_by_trade({"farmer": 500.0, "baker": 100.0, POOL: 400.0}, {"baker": 60.0}, ARMY, POOL)
        self.assertEqual(hours, {"farmer": 500.0, "baker": 100.0, POOL: 400.0})

    def test_staff_taken_from_the_pool_cannot_exceed_the_pool(self):
        hours = hours_by_trade({"farmer": 500.0, POOL: 30.0}, {"merchant": 80.0}, ARMY, POOL)
        self.assertEqual(hours[POOL], 0.0)
        self.assertEqual(hours["merchant"], 30.0)

    def test_own_plot_farm_hours_are_agriculture(self):
        shares = shares_by_group(hours_by_trade({"farmer": 80.0, POOL: 20.0}, {}, ARMY, POOL))
        self.assertAlmostEqual(shares["agriculture"], 0.8)

    def test_no_hours_gives_zero_shares(self):
        self.assertEqual(set(shares_by_group(hours_by_trade({}, {}, ARMY, POOL)).values()), {0.0})


class NamedCraftsBillTheirTrade(unittest.TestCase):
    def test_no_named_craft_bills_only_labourer(self):
        recipes = {}
        directory = os.path.join(ROOT, "data", "production")
        for name in sorted(os.listdir(directory)):
            if name.endswith(".json"):
                with open(os.path.join(directory, name), encoding="utf-8") as handle:
                    recipes.update(json.load(handle)["materials"])
        for material in NAMED_CRAFT_RECIPES:
            entries = recipes[material]
            for entry in (entries if isinstance(entries, list) else [entries]):
                with self.subTest(material=material):
                    trades = set(entry["labour_hours"])
                    self.assertTrue(trades and trades != {POOL}, "%s bills only %s" % (material, trades))


if __name__ == "__main__":
    unittest.main()
