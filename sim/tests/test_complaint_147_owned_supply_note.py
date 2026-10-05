"""Complaint 147: `why` says which owned supply lowers the scarcity premium on the materials a project still has to buy."""
import unittest

from .harness import sim
from sim.ui.proto.techtree import _material_row

_NODE = "case_hardening"
_MATERIAL = "charcoal_kg"


def _row(game):
    return next(row for row in game.project_material_bill(_NODE)["rows"] if row["material"] == _MATERIAL)


class OwnedSupplyNoteTests(unittest.TestCase):
    def test_no_note_without_owned_supply(self):
        shown = _material_row(_row(sim(capital=5e7)))
        self.assertEqual(shown["own_supply_tonnes_per_year"], 0)
        self.assertNotIn("scarcity_note", shown)

    def test_owned_supply_is_named_and_lowers_the_price(self):
        bare, owner = sim(capital=5e7), sim(capital=5e7)
        owner.state.economy.forest_ha += 500
        before, after = _row(bare), _row(owner)
        self.assertLess(after["price_per_tonne"], before["price_per_tonne"])
        shown = _material_row(after)
        self.assertGreater(shown["own_supply_tonnes_per_year"], 0)
        self.assertIn("own", shown["scarcity_note"])
        self.assertIn(_MATERIAL, shown["scarcity_note"])


if __name__ == "__main__":
    unittest.main()
