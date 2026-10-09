"""The merchants' share of household funds reads the lenders' offers fixed at the year's meeting and nothing else, so
pricing a landed good before lenders first meet cannot loop back through society output to the landed price."""

QUICK_TOPIC = True

import types
import unittest

from sim.agents.api import EDGE_SAVERS, Purses
from sim.engine.foreign_traders import ForeignTradersMixin


def world_with(offers):
    purses = Purses()
    purses.set_offers(offers)

    def output_must_not_be_read():
        raise AssertionError("household saving read before lenders met")
    return types.SimpleNamespace(actors=types.SimpleNamespace(state=types.SimpleNamespace(purses=purses)),
                                 household_saving=output_must_not_be_read)


class FundsBeforeTheLendersMeet(unittest.TestCase):

    def test_no_offers_means_no_pooled_funds_and_no_call_into_output(self):
        self.assertEqual(ForeignTradersMixin._households_loanable_funds(world_with({})), 0.0)

    def test_after_the_meeting_the_households_offer_is_read(self):
        self.assertEqual(ForeignTradersMixin._households_loanable_funds(world_with({EDGE_SAVERS: 7.0, "state": 3.0})), 7.0)


if __name__ == "__main__":
    unittest.main()
