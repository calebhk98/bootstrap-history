"""spin_up_moved: the first and last year's figures of a spin-up and the last over the first."""

QUICK_TOPIC = True

import unittest

from sim.ui.spin_up_moved import format_moved, moved

FIRST = {"hired_hours": 80.0, "idle_hours": 20.0, "wage": 1.0, "price_level": 1.0, "real_output": 500.0, "rate": 0.05,
         "money_supply": 1000.0, "money_households": 600.0, "money_producers": 350.0, "money_merchants": 50.0,
         "inventory_value": 100.0, "unmet_need": 0.0, "food_need": 40.0}
LAST = {"hired_hours": 95.0, "idle_hours": 5.0, "wage": 0.5, "price_level": 0.8, "real_output": 550.0, "rate": 0.04,
        "money_supply": 900.0, "money_households": 450.0, "money_producers": 400.0, "money_merchants": 50.0,
        "inventory_value": 220.0, "unmet_need": 2.0, "food_need": 40.0}


def by_name(table):
    return {name: (before, after, ratio) for name, before, after, ratio in table}


class Moved(unittest.TestCase):
    def setUp(self):
        self.table = by_name(moved([FIRST, {"hired_hours": 1.0}, LAST]))

    def test_the_share_of_offered_hours_hired_in_the_first_and_last_year(self):
        before, after, ratio = self.table["hours hired over hours offered"]
        self.assertAlmostEqual(before, 0.8)
        self.assertAlmostEqual(after, 0.95)
        self.assertAlmostEqual(ratio, 0.95 / 0.8)

    def test_the_wage_over_the_price_level(self):
        before, after, ratio = self.table["wage over price level"]
        self.assertAlmostEqual(before, 1.0)
        self.assertAlmostEqual(after, 0.625)
        self.assertAlmostEqual(ratio, 0.625)

    def test_a_plain_column_is_read_from_the_first_and_last_rows_only(self):
        self.assertEqual(self.table["coin of households"], (600.0, 450.0, 0.75))
        self.assertEqual(self.table["hours hired"][:2], (80.0, 95.0))

    def test_a_first_value_of_nothing_gives_no_ratio(self):
        before, after, ratio = self.table["unmet need over food need"]
        self.assertEqual(before, 0.0)
        self.assertAlmostEqual(after, 0.05)
        self.assertIsNone(ratio)

    def test_a_figure_a_row_does_not_carry_is_none(self):
        table = by_name(moved([{"hired_hours": 80.0, "idle_hours": 20.0}, {"hired_hours": 90.0, "idle_hours": 10.0}]))
        self.assertEqual(table["wage"], (None, None, None))
        self.assertAlmostEqual(table["hours hired over hours offered"][2], 0.9 / 0.8)

    def test_no_rows_give_no_table(self):
        self.assertEqual(moved([]), [])


class FormatMoved(unittest.TestCase):
    # presentation: the table's layout is what is under test
    def test_one_line_a_figure_under_a_heading_with_a_dash_for_no_value(self):
        text = format_moved([("wage", 1.0, 0.5, 0.5), ("rate", None, None, None)])
        lines = text.splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("wage", lines[1])
        self.assertIn("0.5", lines[1])
        self.assertEqual(lines[2].split()[1:], ["-", "-", "-"])


if __name__ == "__main__":
    unittest.main()
