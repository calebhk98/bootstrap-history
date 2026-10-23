"""Complaints 605 and 607: household saving finds a use. A household counts what it owns of the firms among the
wealth it wants to hold, so it does not also keep that wealth as idle cash; more of its income reaches a spender
(goods, or a producer's loan). Values are read from the economy's records, not from text.

Rules (Complaint 640): `EquityTests` (in test_saving_finds_a_use_rule.py) calls `equity.firm_net_worth`, `equity_of` and `goods_orders` on built inputs.
The old paired whole-run comparison (with and without the equity read, lent share at least double) is deleted: the
fixture run no longer separates the two, and its rule is the one `goods_orders` test above. One baseline validation
remains (`BaselineValidationSavingReachesAProducerTests`)."""
import unittest

from sim.economy import api as economy_api
from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture
from sim.tests.test_saving_finds_a_use_rule import plant_setup

YEARS = 40
WARM_UP_YEARS = 5


def _lent_share(years=YEARS, warm_up=WARM_UP_YEARS):
    """Lent over offered, summed over the warmed-up years of the plant fixture's quiet run."""
    setup = plant_setup()
    economy = Economy(setup)
    economy_api.begin_spin_up(economy)
    lent = offered = 0.0
    for year in range(years):
        economy.step(fixture.quiet_year(setup))
        if year >= warm_up:
            lent += sum(economy.record.lent_by_borrower.values())
            offered += economy.record.funds_offered
    return lent, offered


class BaselineValidationSavingReachesAProducerTests(unittest.TestCase):
    """Baseline validation (CLAUDE.md 4.2, Complaint 640), slow only: in a quiet economy with plant on its farms and
    mines, some of the savings on offer are lent to producers. It reads the whole run, so a failure names no rule;
    the rules (equity counts as wealth held, so less cash is offered idle) are held by EquityTests.
    The households have a surplus to save: the settled opening leaves none (Complaint 607), and the question here is
    whether a surplus finds a use."""

    def setUp(self):
        fixture.households_with_a_surplus(self)

    def test_validation_some_savings_on_offer_are_lent_to_producers(self):
        lent, offered = _lent_share()
        self.assertGreater(offered, 0.0)
        self.assertGreater(lent / offered, 0.0, "no savings reached a producer in %d quiet years" % YEARS)


if __name__ == "__main__":
    unittest.main()
