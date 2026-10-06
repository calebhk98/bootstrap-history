"""Complaint 336: a near-zero-cost technique enters a market served by dearer incumbents. Relationships,
never target values: the price starts near the incumbents', falls as the entrant's capacity grows, the
dearer incumbents leave, and the entrant's takings stay within what demand allows. A property the
economy does not yet produce is an expected failure, so the build that makes it hold flips the test."""
import unittest

from sim.tests import economy_innovator_scenario as scenario

BOOK_MERGE_TOLERANCE = 1.25     # the summarised book merges buyers, so its ceiling is approximate
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
        table = rows()
        early = mean(row["price"] for row in table[scenario.ENTRY_YEAR:scenario.ENTRY_YEAR + 4])
        late = mean(row["price"] for row in table[-4:])
        self.assertLess(late, 0.8 * early)

    @unittest.expectedFailure
    def test_the_price_path_falls_steadily_without_a_swing_between_years(self):
        table = rows()[scenario.ENTRY_YEAR:]
        pairs = [mean(row["price"] for row in table[i:i + 2]) for i in range(0, len(table) - 1, 2)]
        for earlier, later in zip(pairs, pairs[1:]):
            self.assertLessEqual(later, 1.1 * earlier)

    @unittest.expectedFailure
    def test_dearer_incumbents_leave_once_the_entrant_can_serve_the_market(self):
        table = rows()
        quantity_before = table[scenario.ENTRY_YEAR - 1]["volume"]
        served = next(row for row in table if row["entrant_runs"] * scenario.CHEAP.outputs[scenario.COFFEE]
                      >= quantity_before)
        later = [row for row in table if row["year"] >= served["year"] + 2]
        self.assertTrue(later and later[0]["incumbent_runs"] <= 0.5 * table[0]["incumbent_runs"])

    def test_the_entrants_takings_stay_within_what_demand_allows(self):
        for row in rows()[scenario.ENTRY_YEAR:]:
            self.assertLessEqual(row["price"] * row["volume"], BOOK_MERGE_TOLERANCE * row["revenue_ceiling"])


if __name__ == "__main__":
    unittest.main()
