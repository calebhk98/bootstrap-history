"""A state that prints a bigger real programme gets a higher price level and a bigger money supply than one that prints
a smaller one, with money conserved. Fiat fixture economy, engine-free; the figures compared are the two runs' own, never a
fixed magnitude."""
QUICK_TOPIC = True
import unittest

from sim.tests import economy_fixture as fixture
from sim.tests.test_economy_agent_state import COIN, opened

YEARS = 4


def printed(times_the_opening_supply):
    supply = opened().record.book.money_supply(COIN)
    economy = opened(("issue",), real_spending_target=times_the_opening_supply * supply)
    levels = [economy.step(fixture.quiet_year(economy.setup)).basket_price_level for _ in range(YEARS)]
    return economy, levels


class PrintingScaleTests(unittest.TestCase):
    def test_printing_more_leaves_a_higher_price_level_and_more_money(self):
        smaller, smaller_levels = printed(0.5)
        bigger, bigger_levels = printed(2.0)
        self.assertGreater(bigger_levels[-1], smaller_levels[-1])
        self.assertGreater(bigger.record.book.money_supply(COIN), smaller.record.book.money_supply(COIN))
        self.assertGreater(bigger.record.state_budget.issued_total, smaller.record.state_budget.issued_total)

    def test_printing_at_either_scale_raises_the_level_above_a_state_that_prints_nothing(self):
        _control, control_levels = printed(0.0)
        for scale in (0.5, 2.0):
            economy, levels = printed(scale)
            self.assertGreater(levels[-1], control_levels[-1])
            self.assertGreater(economy.record.state_budget.issued_total, 0.0)

    def test_money_is_conserved_when_the_state_prints(self):
        economy, _levels = printed(2.0)
        self.assertTrue(economy.record.book.check_conservation(1e-9).ok)


if __name__ == "__main__":
    unittest.main()
