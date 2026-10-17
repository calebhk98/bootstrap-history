"""A recipe whose makers start too small grows when buyers keep bidding above its cost, though the market
traded little (Complaint 559). Margin and trial entry are taken out so only the sized entry is measured."""

QUICK_TOPIC = False   # builds whole games

import dataclasses
import unittest
from unittest import mock

from sim.economy import entry_year
from sim.economy.economy import Economy
from sim.tests import economy_fixture as fixture

YEARS = 6
SHRUNK_SHARE = 0.05


def grown_capacity(unfilled_counts):
    """Smelter capacity, with plant to come, after the years; `unfilled_counts` False sizes entry to the trade alone."""
    setup = fixture.small_setup()
    economy = Economy(setup)
    for producer_id, producer in list(economy.record.producers.items()):
        if producer.recipe_id == fixture.SMELT:
            economy.record.producers[producer_id] = dataclasses.replace(
                producer, capacity_runs=producer.capacity_runs * SHRUNK_SHARE)
    with mock.patch.object(entry_year, "margin_entry_plans", return_value=[]), \
            mock.patch.object(entry_year, "trial_entry_plans", return_value=[]):
        if not unfilled_counts:
            with mock.patch.object(entry_year, "unfilled_at_cost", return_value=None):
                return _run(economy, setup)
        return _run(economy, setup)


def _run(economy, setup):
    for _year in range(YEARS):
        economy.step(fixture.quiet_year(setup))
    return sum(producer.capacity_runs + economy.record.expansion_runs.get(producer_id, 0.0)
               for producer_id, producer in economy.record.producers.items() if producer.recipe_id == fixture.SMELT)


class StarvedMakersGrowTests(unittest.TestCase):
    def setUp(self):
        fixture.households_with_a_surplus(self)

    def test_makers_too_small_grow_faster_when_unfilled_bids_count(self):
        self.assertGreater(grown_capacity(True), grown_capacity(False))


if __name__ == "__main__":
    unittest.main()
