"""The merchants' share of household funds (the `households_loanable_funds` view) reads the lenders' offers fixed at the year's meeting and nothing else, so
pricing a landed good before lenders first meet cannot loop back through society output to the landed price."""

QUICK_TOPIC = True

from sim.tests.agents_fake_world import flat_namespace
import unittest

from sim.tests import finance_host


def world_with(listing):
    """The finance module over the economy's lender listing as the markets view answers it (`(answered, listing)`)."""
    def output_must_not_be_read():
        raise AssertionError("household saving read before lenders met")
    return finance_host.build(agent_lender_listing=lambda: listing,
                              actor_world=flat_namespace(household_saving=output_must_not_be_read))


class FundsBeforeTheLendersMeet(unittest.TestCase):

    def test_no_lenders_listed_means_no_pooled_funds_and_no_call_into_output(self):
        self.assertEqual(world_with((False, None)).households_loanable_funds(), 0.0)
        self.assertEqual(world_with((True, {"coin_per_unit": 2.0, "lenders": []})).households_loanable_funds(), 0.0)

    def test_after_the_meeting_what_the_economys_lenders_offered_is_read_in_coin(self):
        listing = {"coin_per_unit": 2.0, "lenders": [("cohort:a", 3.0, 3.0, 0.05), ("bank:b", 4.0, 1.0, 0.06)]}
        self.assertEqual(world_with((True, listing)).households_loanable_funds(), 14.0)


if __name__ == "__main__":
    unittest.main()
