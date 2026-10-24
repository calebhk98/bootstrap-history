"""Wage work shows in the `money` text; the shortage remedy tells the truth about the player's own workings (complaints 144
and 171). Complaint 640: the remedy is called on a stub founder and the text is rendered from a hand-written reply; the
books and the command are test_wage_work_books."""
QUICK_TOPIC = True

import unittest

from sim.engine import purchase_rule  # noqa: F401  (first: the engine modules import each other in a fixed order)
from sim.ui.proto.render_screens_economy import _money_wage_work_lines

from .test_material_production_commands import _Founder


class _Miner(_Founder):
    MINE_OPEX_MATERIALS = ("gold",)

    def material_shortfall_t(self, material, by_tag=None):
        return 0.0


class ShortageRemedyTests(unittest.TestCase):

    def test_no_workings_and_no_shortfall_says_to_sink_one(self):
        plan = _Miner(cash=0.0).shortage_remedy_plan("gold")
        self.assertEqual(plan["kind"], "dig_mine")
        self.assertFalse(plan["has_working"])
        self.assertIn("buy mine gold 1", plan["commands"])

    def test_workings_that_cover_demand_say_so_with_no_shortfall(self):
        founder = _Miner(cash=0.0)
        founder.mine_capacity = {"gold": 5.0}
        plan = founder.shortage_remedy_plan("gold")
        self.assertEqual(plan["kind"], "dig_mine")
        self.assertTrue(plan["has_working"])
        self.assertLess(plan["short_tonnes"], 1.0)


class WageWorkLinesTests(unittest.TestCase):

    def test_the_money_text_shows_the_wage_rows_and_does_not_claim_they_add_up_to_revenue(self):
        text = "\n".join(_money_wage_work_lines({"wage_work_last_year": {"hours": 1000, "wage_income": 240.0}}))
        # presentation: the rows' labels and the note that wages are outside the revenue
        self.assertIn("wage work last year", text)
        self.assertNotIn("(these add up to the revenue above)", text)

    def test_no_wage_work_gives_no_lines(self):
        self.assertEqual(_money_wage_work_lines({}), [])


if __name__ == "__main__":
    unittest.main()
