"""Property income paid to a tile's owner cohort is shared across the tile's cohorts by what each owns."""

QUICK_TOPIC = True

import unittest
from types import SimpleNamespace

from sim.economy import ownership
from sim.economy.households_cohort import cohort_id, cohorts_for_tile
from sim.economy.types import Transfer


def record_with_three_cohorts():
    cohorts = (cohorts_for_tile("t", 3000.0, 0.5, 0.4, class_count=3)
               + cohorts_for_tile("u", 1000.0, 0.5, 0.4, class_count=3))
    return SimpleNamespace(cohorts={cohort.agent_id: cohort for cohort in cohorts})


class SpreadTests(unittest.TestCase):
    def test_a_dividend_to_the_richest_cohort_is_split_by_ownership_share(self):
        record = record_with_three_cohorts()
        richest = cohort_id("t", 2)
        spread = ownership.spread(record, [Transfer("producer:a", richest, "coin", 100.0, "dividend")])
        paid = {transfer.payee: transfer.amount for transfer in spread}
        self.assertEqual(set(paid), {cohort_id("t", index) for index in range(3)})
        self.assertAlmostEqual(sum(paid.values()), 100.0)
        for index in range(3):
            share = record.cohorts[cohort_id("t", index)].ownership_share
            self.assertAlmostEqual(paid[cohort_id("t", index)], 100.0 * share)
        self.assertLess(paid[richest], 100.0)            # today the richest alone gets all of it

    def test_every_split_payment_keeps_payer_and_currency(self):
        record = record_with_three_cohorts()
        spread = ownership.spread(record, [Transfer("producer:a", cohort_id("t", 2), "coin", 10.0, "rent")])
        self.assertTrue(all(transfer.payer == "producer:a" and transfer.currency == "coin"
                            and transfer.purpose == "rent" for transfer in spread))

    def test_payments_to_other_payees_or_for_other_purposes_pass_through(self):
        record = record_with_three_cohorts()
        interest = Transfer("lender", cohort_id("t", 2), "coin", 5.0, "interest")
        to_state = Transfer("producer:a", "state", "coin", 5.0, "dividend")
        self.assertEqual(ownership.spread(record, [interest, to_state]), [interest, to_state])

    def test_the_tiles_owner_is_its_richest_cohort(self):
        record = record_with_three_cohorts()
        self.assertEqual(ownership.owner_cohort(record, "t"), cohort_id("t", 2))
        self.assertIsNone(ownership.owner_cohort(record, "nowhere"))


if __name__ == "__main__":
    unittest.main()
