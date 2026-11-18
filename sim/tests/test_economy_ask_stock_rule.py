"""Complaint 473: a seller's ask moves with its unsold stock against a target stock (ask_adjust.stepped_by_stock),
and a plain loop over that one rule against a written-out linear demand and fixed supply settles."""

QUICK_TOPIC = True

import unittest

from sim.economy import ask_adjust

COST = 10.0
SUPPLY, TARGET = 100.0, 10.0


def next_ask(ask, stock, target=TARGET):
    return ask_adjust.stepped_by_stock(ask, COST, stock, target)


def unsold_at(ask):
    """Linear demand 200 - 100 * ask against a fixed supply: what is left over."""
    return max(0.0, SUPPLY - max(0.0, 200.0 - 100.0 * ask / COST))


class StockAgainstTargetTests(unittest.TestCase):
    def test_no_stock_raises_stock_over_target_cuts_stock_at_target_holds(self):
        self.assertGreater(next_ask(15.0, 0.0), 15.0)
        self.assertLess(next_ask(15.0, 5.0 * TARGET), 15.0)
        self.assertEqual(next_ask(15.0, TARGET), 15.0)

    def test_the_step_grows_with_the_gap(self):
        self.assertGreater(next_ask(15.0, 0.0), next_ask(15.0, 0.5 * TARGET))
        self.assertGreater(next_ask(15.0, 1.5 * TARGET), next_ask(15.0, 3.0 * TARGET))

    def test_a_cut_stops_at_the_cost_that_covers_a_unit_and_a_raise_has_no_ceiling(self):
        self.assertEqual(next_ask(COST, 100.0 * TARGET), COST)
        self.assertGreater(next_ask(30.0 * COST, 0.0), 30.0 * COST)

    def test_an_ask_below_cost_is_not_raised_toward_cost_by_a_cut(self):
        self.assertEqual(next_ask(0.5 * COST, 100.0 * TARGET), 0.5 * COST)

    def test_no_cost_to_anchor_on_means_no_move(self):
        self.assertEqual(ask_adjust.stepped_by_stock(15.0, None, 0.0, TARGET), 15.0)

    def test_a_cobweb_around_the_stock_target_shrinks(self):
        ask, errors = 25.0, []
        for _year in range(40):
            errors.append(abs(ask - 11.0))     # the ask at which demand leaves exactly the target unsold
            ask = next_ask(ask, unsold_at(ask))
        self.assertLess(errors[-1], 0.05 * errors[0])
        self.assertLess(max(errors[20:]), max(errors[:20]))


if __name__ == "__main__":
    unittest.main()
