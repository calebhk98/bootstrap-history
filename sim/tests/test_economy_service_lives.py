"""A durable good households buy is held, wears by one service life's share a year, and is not
bought again in full."""

QUICK_TOPIC = True

import unittest
from unittest import mock

from sim.economy import opening
from sim.economy.economy import Economy
from sim.economy.types import Transfer
from sim.tests import economy_fixture as fixture

SERVICE_LIFE_YEARS = 20.0


def durable_setup():
    return fixture.small_setup(specs=fixture.specs({fixture.METAL: SERVICE_LIFE_YEARS}))


def household_stock(economy):
    book = economy.record.book
    return sum(quantity for agent in book.holders_of(fixture.METAL) if agent.startswith("household")
               for quantity in book.holdings(agent)["goods"][fixture.METAL].values())


# The fixture opens with margins no competition has worked on; entry and the wage floor take them away over
# decades, with incomes and the wanted stock swinging while they do (Complaint 398). The real game also
# measures from a spun-up economy, so the durable path is read after the fixture has settled.
SPIN_UP_YEARS = 60


def economy_opening_empty(setup):
    """An economy whose households open holding none of the durable, as when a good is new to a society:
    the opening's seeding of in-use stocks (opening._seed_durable_stocks) is switched off."""
    with mock.patch.object(opening, "_seed_durable_stocks", lambda *_arguments: None):
        return Economy(setup)


def years_of(setup, years, spin_up=0, empty=False):
    """(household stock after the year, wear that year, units sold that year, households' income that
    year) for each of `years` years after `spin_up` years that are not reported. Households open holding
    the stock they keep in use, unless `empty`."""
    economy = economy_opening_empty(setup) if empty else Economy(setup)
    rows = []
    for year in range(spin_up + years):
        economy.step(fixture.quiet_year(setup))
        if year < spin_up:
            continue
        flow = economy.record.book.goods_flow(fixture.METAL)
        income = sum(cohort.last_year_income for cohort in economy.record.cohorts.values())
        rows.append((household_stock(economy), flow.get("wear", 0.0), flow["output"], income))
    return rows


class ServiceLifeTests(unittest.TestCase):
    def test_a_durable_bought_is_held_into_the_next_year(self):
        rows = years_of(durable_setup(), 3)
        self.assertGreater(rows[1][0], 0.0)
        self.assertGreater(rows[2][0], 0.0)

    def test_it_wears_by_one_service_life_share_of_what_is_in_use(self):
        stock, wear, _sold, _income = years_of(durable_setup(), 3)[2]
        self.assertAlmostEqual(wear, (stock + wear) / SERVICE_LIFE_YEARS, delta=1e-6 * (stock + wear))

    def test_a_good_without_a_service_life_is_not_held(self):
        rows = years_of(fixture.small_setup(), 3)
        self.assertEqual(rows[2][0], 0.0)

    def test_the_stock_is_filled_over_years_of_income(self):
        # a durable new to a society starts from no stock and is built up by many times the wear
        rows = years_of(durable_setup(), 3, empty=True)
        self.assertGreater(rows[1][0] - rows[0][0] + rows[1][1], 8.0 * rows[1][1])

    def test_households_open_holding_the_stock_they_keep_in_use_and_so_build_less(self):
        # the real opening seeds the in-use stock, so the first year builds less than from nothing; the
        # fixture's income still grows while its margins close, so what is bought is not just the wear
        # (the settled tests below hold it to that), but it is never the stock built from scratch
        seeded = years_of(durable_setup(), 3)
        empty = years_of(durable_setup(), 3, empty=True)
        self.assertGreater(seeded[0][0], 0.0)
        bought_seeded = seeded[1][0] - seeded[0][0] + seeded[1][1]
        bought_empty = empty[1][0] - empty[0][0] + empty[1][1]
        self.assertLess(bought_seeded, bought_empty)

    def test_it_is_not_bought_again_in_full(self):
        # once the fixture has settled its income is level with lumps (competition has taken the margins
        # that made it grow), so households buy about the wear: never a year's purchase beyond twice the
        # wear, where buying the stock again would be as many times the wear as the service life
        rows = years_of(durable_setup(), 13, SPIN_UP_YEARS)
        for year in range(1, 13):
            bought = rows[year][0] - rows[year - 1][0] + rows[year][1]
            self.assertGreaterEqual(bought, 0.0)
            self.assertLess(bought, 2.0 * rows[year][1], "year %d buys the stock again" % year)

    def test_settled_holdings_move_by_less_than_one_years_wear(self):
        # with a level income the wanted stock is level, so the holding rises or falls by less than the wear
        # a lumpy year of income can account for; it is neither sold out nor refilled in a year
        rows = years_of(durable_setup(), 13, SPIN_UP_YEARS)
        for year in range(1, 13):
            self.assertLess(abs(rows[year][0] - rows[year - 1][0]), rows[year][1], "the stock jumps in year %d" % year)


class BadYearTests(unittest.TestCase):
    """One bad year must not sell the durable stock off and then rebuy it (Complaint 468's swing): the
    stock is sized on smoothed spending and a smoothed surplus, not on what one year's floors leave."""

    def test_the_unspun_fixtures_income_crash_does_not_sell_the_stock(self):
        # the fixture's own income falls by a fifth in its seventh year as margins close; the holding
        # used to go from 33 thousand to 8 thousand units that year
        rows = years_of(durable_setup(), 14)
        for year in range(1, 14):
            self.assertGreater(rows[year][0], 0.9 * rows[year - 1][0], "year %d sells a tenth of the stock" % year)

    def test_a_year_of_cash_shortage_sells_at_most_a_third_of_the_stock_and_rebuys_near_the_wear(self):
        # the economy is read after the fixture has settled, as in the other settled tests: the stock then
        # stands at the level its income wants, so a rise in what the households want is not mistaken for a
        # rebuy after the shortage
        setup = durable_setup()
        economy = Economy(setup)
        for _year in range(SPIN_UP_YEARS):
            economy.step(fixture.quiet_year(setup))
        before = household_stock(economy)
        for cohort in economy.record.cohorts.values():          # households lose nine tenths of their cash
            cash = economy.record.book.balance(cohort.agent_id, setup.currency_id)
            economy.record.book.transfer(Transfer(cohort.agent_id, setup.state_agent, setup.currency_id,
                                                  0.9 * cash, "levy"))
        previous = before
        for _year in range(4):
            economy.step(fixture.quiet_year(setup))
            wear = economy.record.book.goods_flow(fixture.METAL).get("wear", 0.0)
            stock = household_stock(economy)
            self.assertGreater(stock, 0.6 * before, "the stock is sold off")
            self.assertLess(stock - previous + wear, 3.0 * wear, "the stock is bought again")
            previous = stock


if __name__ == "__main__":
    unittest.main()
