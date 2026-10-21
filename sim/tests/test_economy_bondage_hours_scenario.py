"""SCENARIO: a bonded cohort in a stepped economy works part of its owed hours in its creditor's works. The creditor owns
the tile's farms; the bond is large enough that the term, not the debt, ends it."""
import unittest

from sim.economy.economy import Economy
from sim.tests import economy_fixture

DEBT = 1e6


def bonded_economy():
    setup = economy_fixture.small_setup()
    economy = Economy(setup)
    record = economy.record
    economy.step(economy_fixture.quiet_year(setup))
    creditor = "household:farms:2"
    bonded = "household:farms:0"
    record.bondage[bonded] = {"creditor": creditor, "debt": DEBT, "years_left": 5.0}
    return setup, economy, creditor, bonded


class BondedHoursScenarioTests(unittest.TestCase):
    def test_the_bonded_cohorts_debt_falls_by_hours_worked_for_the_creditor_as_well_as_cash(self):
        setup, economy, creditor, bonded = bonded_economy()
        economy.step(economy_fixture.quiet_year(setup))
        debt = economy.record.bondage[bonded]["debt"]
        self.assertLess(debt, DEBT)
        self.assertEqual(economy.record.bondage[bonded]["creditor"], creditor)

    def test_the_creditors_works_are_credited_the_bonded_hours(self):
        setup, economy, creditor, bonded = bonded_economy()
        from sim.economy import bondage_hours
        record = economy.record
        view = economy.view()
        offers = [offer for offer in economy_offers(setup, record, view) if offer.worker == bonded]
        self.assertTrue(offers)
        bids = [bid for bid in economy_bids(setup, record, view)]
        placement = bondage_hours.place(record.bondage, offers, bids, bondage_hours.works_of_producers(record), 0.75)
        self.assertTrue(placement.hired)
        for employer in placement.hired:
            self.assertEqual(record.producers[employer].owner, creditor)


def economy_offers(setup, record, view):
    from sim.economy.year_labour import labour_offers, outside_option_by_tile
    return labour_offers(setup, record, view, outside_option_by_tile(setup, record, view))


def economy_bids(setup, record, view):
    from sim.economy import producers
    plans = [producers.plan(producer, setup.recipes[producer.recipe_id], view, record.book.balance(producer_id, setup.currency_id))
             for producer_id, producer in sorted(record.producers.items())]
    return [bid for plan in plans for bid in plan.labour_bids]


if __name__ == "__main__":
    unittest.main()
