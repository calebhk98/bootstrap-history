"""Complaint 147: `why` says which owned supply covers tonnes of the materials a project still has to buy, so it has fewer to buy."""
import unittest

from .harness import sim
from sim.ui.proto.techtree import _material_row

_NODE = "case_hardening"
_MATERIAL = "charcoal_kg"


def _row(game):
    return next(row for row in game.project_material_bill(_NODE)["rows"] if row["material"] == _MATERIAL)


class OwnedSupplyNoteTests(unittest.TestCase):
    def test_no_note_without_owned_supply(self):
        game = sim(capital=5e7)
        shown = _material_row(_row(game), game)
        self.assertEqual(shown["own_supply_tonnes_per_year"], 0)
        self.assertNotIn("scarcity_note", shown)

    def test_owned_supply_is_named_and_lowers_the_bill(self):
        bare, owner = sim(capital=5e7), sim(capital=5e7)
        owner.state.holdings.forest_ha += 500
        before, after = _row(bare), _row(owner)
        # the price a tonne fetches is the economy's on the founder's tile, so owned supply no longer cheapens it
        # (Merge 507-stage-3-prices-to-pay removed the scarcity premium); it lowers the bill by covering tonnes
        self.assertLessEqual(after["price_per_tonne"], before["price_per_tonne"])
        self.assertGreater(after["held_from_own_output_tonnes"], 0.0)
        self.assertLess(after["missing_tonnes"], before["missing_tonnes"])
        self.assertLess(after["cost_of_missing"], before["cost_of_missing"])
        shown = _material_row(after, owner)
        self.assertGreater(shown["own_supply_tonnes_per_year"], 0)
        self.assertIn("own", shown["scarcity_note"])
        self.assertIn(_MATERIAL, shown["scarcity_note"])


if __name__ == "__main__":
    unittest.main()
