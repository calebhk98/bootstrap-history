"""Complaint 336: a near-zero-cost technique enters a market served by dearer incumbents. Relationships,
never target values: the price starts near the incumbents', falls as the entrant's capacity grows, the
dearer incumbents leave, and the entrant's takings stay within what demand allows. A property the
economy does not yet produce is marked an expected failure, so the build that makes it hold flips the test."""
import math
import unittest

from sim.economy import producers, producers_close
from sim.tests import economy_innovator_scenario as scenario

BOOK_MERGE_TOLERANCE = 1.25     # the summarised book merges buyers, so its ceiling is approximate
YEAR_TO_YEAR_RISE_LIMIT = 1.2   # a year's price against the year before, in the years after entry
_ROWS = []


def rows():
    if not _ROWS:
        _ROWS.extend(scenario.run_scenario())
    return _ROWS


def mean(values):
    values = list(values)
    return sum(values) / len(values)


class InnovatorPricingTests(unittest.TestCase):
    def test_the_price_starts_near_the_incumbents_price(self):
        table = rows()
        before = mean(row["price"] for row in table[:scenario.ENTRY_YEAR])
        first = table[scenario.ENTRY_YEAR]["price"]
        self.assertGreater(first, 0.5 * before)
        self.assertLess(first, 2.0 * before)

    def test_the_price_falls_as_the_entrants_capacity_grows(self):
        # Against the years before entry, not the few years just after it: sellers that move the price may
        # raise or withhold, so the entry years are a swing, and the property is the level the market
        # settles at once the entrant can serve it.
        table = rows()
        before = mean(row["price"] for row in table[:scenario.ENTRY_YEAR])
        late = mean(row["price"] for row in table[-4:])
        self.assertLess(late, 0.8 * before)

    def test_the_price_path_falls_steadily_without_a_swing_between_years(self):
        # Spending is smoothed across years (households_orders.SPENDING_CUT_LIMIT), so a low price one year
        # does not send a larger budget to the next year's market; the bound is on each year against the last.
        table = rows()[scenario.ENTRY_YEAR:]
        for earlier, later in zip(table, table[1:]):
            self.assertLessEqual(later["price"], YEAR_TO_YEAR_RISE_LIMIT * earlier["price"],
                                 msg="year %d" % later["year"])

    def test_dearer_incumbents_leave_once_the_price_stops_covering_their_cost(self):
        # They stay while the price covers what they cost to run, then go at the pace a market loses makers:
        # the loss years a producer waits, then the share of its workplaces that close a year. The entrant's
        # capacity need not have caught up with the old volume: demand grows as the price falls.
        table = rows()
        before = table[0]["incumbent_runs"]
        unpaid = next(row for row in table if row["price"] < row["incumbent_cost"])
        for row in table:
            if row["year"] < unpaid["year"]:
                self.assertAlmostEqual(row["incumbent_runs"], before, msg="left while the price covered the cost")
        shedding_years = math.ceil(math.log(0.5) / math.log(1.0 - producers.OUTPUT_CHANGE_SHARE_PER_YEAR))
        later = [row for row in table
                 if row["year"] >= unpaid["year"] + producers_close.LOSS_YEARS_BEFORE_EXIT + shedding_years]
        self.assertTrue(later and later[0]["incumbent_runs"] <= 0.5 * before)

    def test_the_entrants_takings_stay_within_what_demand_allows(self):
        for row in rows()[scenario.ENTRY_YEAR:]:
            self.assertLessEqual(row["port_price"] * row["volume"], BOOK_MERGE_TOLERANCE * row["revenue_ceiling"])


if __name__ == "__main__":
    unittest.main()
