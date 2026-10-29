"""`RepriceOpeningMoney`, applied by the markets module: when the economy opens and settles its own wage, every seat's money is
rescaled by the ratio of the new figure to the one it was counted at, the money is marked as the economy's, and the root is asked to
count the tree afresh. One handler over written-out figures; the port's decision to send it is in test_open_agent_reprices_money."""

QUICK_TOPIC = True

import contextlib
import unittest

from sim.assembly.api import RepriceTree
from sim.ledger.api import RescaleHouseholdMoney
from sim.markets.commands import RepriceOpeningMoney
from sim.markets.module import Markets
from sim.markets.state import MarketsWorld
from sim.tests import module_harness


def markets_over(wage_after, seats):
    """The markets module reading `wage_after` as the money an hour of work is worth now and `seats` as the registry; the seats
    it acted as are kept in `module.acted_as`."""
    acted_as = []

    @contextlib.contextmanager
    def act_as(seat_id):
        acted_as.append(seat_id)
        yield
    module = module_harness.build(Markets, views={"money_per_labour_hour": wage_after, "registered_seats": list(seats), "act_as": act_as},
                                  world=MarketsWorld(), module_id="markets")
    module.acted_as = acted_as
    return module


class RepriceOpeningMoneyCommand(unittest.TestCase):
    def test_every_seat_is_sent_the_one_ratio_of_the_figures_in_the_order_the_registry_lists_them(self):
        module = markets_over(0.25, ["founder", "second"])
        module.reprice_opening_money(RepriceOpeningMoney(1.0))
        self.assertEqual(module_harness.sent(module), [RescaleHouseholdMoney(0.25), RescaleHouseholdMoney(0.25), RepriceTree()])
        self.assertEqual(module.acted_as, ["founder", "second"])

    def test_a_purse_holds_the_same_hours_of_unskilled_work_after_repricing(self):
        wage_before, wage_after, purse = 0.80, 0.08, 6000.0
        module = markets_over(wage_after, ["founder"])
        module.reprice_opening_money(RepriceOpeningMoney(wage_before))
        rescaling, = [command for command in module_harness.sent(module) if isinstance(command, RescaleHouseholdMoney)]
        self.assertAlmostEqual(purse * rescaling.ratio / wage_after, purse / wage_before)

    def test_the_economy_is_marked_as_the_source_of_money_so_a_second_open_does_not_reprice_again(self):
        module = markets_over(0.5, ["founder"])
        self.assertFalse(module.world.money_from_economy)
        module.reprice_opening_money(RepriceOpeningMoney(1.0))
        self.assertTrue(module.world.money_from_economy)


if __name__ == "__main__":
    unittest.main()
