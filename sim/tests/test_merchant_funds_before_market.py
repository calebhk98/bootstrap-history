"""The merchants' share of household funds (the `households_loanable_funds` view) reads the lenders' offers fixed at the year's meeting and nothing else, so
pricing a landed good before lenders first meet cannot loop back through society output to the landed price."""

QUICK_TOPIC = True

import unittest

from sim.tests import finance_host


def world_with(listing):
    """The finance module over the economy's lender listing as the markets view answers it (`(answered, listing)`)."""
    return finance_host.build(agent_lender_listing=lambda: listing)


class FundsBeforeTheLendersMeet(unittest.TestCase):

    def test_no_lenders_listed_means_no_pooled_funds(self):
        self.assertEqual(world_with((False, None)).households_loanable_funds(), 0.0)
        self.assertEqual(world_with((True, {"coin_per_unit": 2.0, "lenders": []})).households_loanable_funds(), 0.0)

    def test_after_the_meeting_what_the_economys_lenders_offered_is_read_in_coin(self):
        listing = {"coin_per_unit": 2.0, "lenders": [("cohort:a", 3.0, 3.0, 3.0, 0.05), ("bank:b", 4.0, 1.0, 1.0, 0.06)]}
        self.assertEqual(world_with((True, listing)).households_loanable_funds(), 14.0)

    def test_the_full_offer_is_read_not_the_capacity_the_years_loans_have_left(self):
        listing = {"coin_per_unit": 2.0, "lenders": [("cohort:a", 10.0, 2.0, 10.0, 0.05)]}
        self.assertEqual(world_with((True, listing)).households_loanable_funds(), 20.0)

    def test_what_is_lent_is_the_offer_less_what_the_account_still_holds_of_it(self):
        listing = {"coin_per_unit": 2.0, "lenders": [("cohort:a", 10.0, 2.0, 6.0, 0.05)]}
        self.assertEqual(world_with((True, listing)).economy_lending(), (20.0, 8.0))


if __name__ == "__main__":
    unittest.main()
