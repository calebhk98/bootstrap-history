"""Complaint 186: names that had no live caller stay deleted.

Each name was checked by grep across sim, data, mods and tools; none is
reached by getattr, a dispatch table or a mod hook.

sim/tests: dead-code removal guard (unittest-style).
"""
import importlib

import sim.engine.cli  # noqa: F401  (loads cli_analysis in the order the app does)
import unittest

# (module, dotted attribute path) that must no longer exist.
DELETED = (
    ("sim.agents.household", "MineWorking"),
    ("sim.engine.economy_materials", "MaterialSupplyMixin.capacity_reserves"),
    ("sim.engine.commodities", "Ledger.on_hand"),
    ("sim.world.demography", "Population.working_age_population"),
    ("sim.world.demand", "consumers_of"),
    ("sim.world.demand", "joint_output_value_shares_for_recipe"),
    ("sim.world.demand", "aggregate_household_demand_all_goods"),
    ("sim.world.military_logistics", "pack_animals_required_for_daily_delivery"),
    ("sim.engine.cli_analysis", "granary_projection"),
)


def _resolve(module_name, dotted):
    target = importlib.import_module(module_name)
    for part in dotted.split("."):
        target = getattr(target, part)
    return target


class DeadCodeStaysDeleted(unittest.TestCase):
    def test_deleted_names_are_gone(self):
        still_present = []
        for module_name, dotted in DELETED:
            try:
                _resolve(module_name, dotted)
            except AttributeError:
                continue
            still_present.append("%s.%s" % (module_name, dotted))
        self.assertEqual(still_present, [])


if __name__ == "__main__":
    unittest.main()
