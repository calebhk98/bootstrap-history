"""Rent and lease terms follow labour scarcity, and a landless cohort leases land in the market (Complaints 538,
551). Each test builds the inputs and calls the rule."""

QUICK_TOPIC = True

import math
import unittest

from sim.economy import land_bid, land_tenancy, titles, titles_worked
from sim.economy.record import EconomyRecord
from sim.economy.types import Recipe, ToolFallback, Transfer
from sim.tests.test_economy_titles import LANDLORD, MONEY, PEASANT, RENT_PER_HECTARE, TILE, make_world

WHEAT = Recipe("wheat", {"grain": 10.0}, {}, {"hand": 100.0})
PRICES = {"grain": 2.0}
HECTARES = 100.0


def margin_at(wage, fertility=1.0):
    return land_bid.crop_margin_per_hectare(WHEAT, 1.0, fertility, PRICES, wage)


class RentFollowsLabourScarcityTests(unittest.TestCase):
    def test_a_higher_wage_lowers_the_most_tenants_can_bear_and_so_the_ask(self):
        posted = 5.0
        slack = land_tenancy.rent_ask(posted, margin_at(0.05), 0.0)
        scarce = land_tenancy.rent_ask(posted, margin_at(0.17), 0.0)
        self.assertLess(scarce, slack)
        self.assertAlmostEqual(slack, min(posted, margin_at(0.05)))

    def test_the_ask_never_exceeds_the_posted_rent_or_falls_below_nothing(self):
        self.assertEqual(land_tenancy.rent_ask(3.0, margin_at(0.0), 0.0), 3.0)
        self.assertEqual(land_tenancy.rent_ask(3.0, margin_at(0.5), 0.0), 0.0)       # the wage eats the crop: no rent

    def test_better_land_to_take_elsewhere_lowers_the_ask(self):
        margin = margin_at(0.05)
        alone = land_tenancy.rent_ask(20.0, margin, land_tenancy.outside_option([]))
        competed = land_tenancy.rent_ask(20.0, margin, land_tenancy.outside_option([1.0, 4.0, math.nan]))
        self.assertAlmostEqual(alone - competed, 4.0)

    def test_a_tenant_pays_its_lessor_less_after_a_labour_shock_than_before(self):
        paid = []
        for wage in (0.05, 0.19):
            _setup, record = make_world()
            record.titles[TILE][PEASANT] -= 0.1
            record.titles[TILE][LANDLORD] += 0.1
            record.tenancies = {TILE: [{"tenant": PEASANT, "lessor": LANDLORD, "share": 0.1, "arrears": 0.0}]}
            record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, 1000.0, "harvest"))
            ask = land_tenancy.rent_ask(RENT_PER_HECTARE, margin_at(wage), 0.0)
            payments = titles.settle_tenancies(record, MONEY, {TILE: HECTARES}, ask_by_tile={TILE: ask})
            paid.append(sum(payment.amount for payment in payments if payment.purpose == "tenant_rent"))
        self.assertLess(paid[1], paid[0])
        self.assertAlmostEqual(paid[0], 0.1 * HECTARES * RENT_PER_HECTARE)      # slack labour: the posted rent

    def test_without_an_ask_the_posted_rent_is_paid(self):
        _setup, record = make_world()
        record.titles[TILE][PEASANT] -= 0.1
        record.titles[TILE][LANDLORD] += 0.1
        record.tenancies = {TILE: [{"tenant": PEASANT, "lessor": LANDLORD, "share": 0.1, "arrears": 0.0}]}
        record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, 1000.0, "harvest"))
        payments = titles.settle_tenancies(record, MONEY, {TILE: HECTARES})
        self.assertAlmostEqual(sum(payment.amount for payment in payments), 0.1 * HECTARES * RENT_PER_HECTARE)


class LeasingInTheMarketTests(unittest.TestCase):
    def landless_world(self):
        setup, record = make_world()
        record.titles[TILE][LANDLORD] += record.titles[TILE].pop(PEASANT)       # the peasant cohort has no land
        return setup, record

    def test_a_landless_cohort_leases_from_a_holder_with_no_hands_at_the_ask(self):
        _setup, record = self.landless_world()
        held = titles.holding(record, TILE, LANDLORD) * HECTARES
        leases = land_tenancy.match([land_tenancy.Offer(PEASANT, TILE, 10.0, 4.0)],
                                    [land_tenancy.Lot(LANDLORD, TILE, held)], {TILE: RENT_PER_HECTARE}, {TILE: 1.5})
        self.assertEqual([(lease.tenant, lease.lessor, lease.hectares, lease.rent_per_hectare) for lease in leases],
                         [(PEASANT, LANDLORD, 10.0, 1.5)])

    def test_the_lease_is_a_tenancy_and_the_own_plot_rule_reads_it(self):
        _setup, record = self.landless_world()
        self.assertEqual(titles_worked.worked_share(record, TILE, PEASANT), 0.0)
        held = titles.holding(record, TILE, LANDLORD)
        let = titles.lease(record, TILE, PEASANT, LANDLORD, 0.1)
        self.assertAlmostEqual(let, 0.1)
        self.assertAlmostEqual(titles_worked.worked_share(record, TILE, PEASANT), 0.1)
        self.assertAlmostEqual(titles.holding(record, TILE, LANDLORD), held)       # the title stays with the lessor
        self.assertAlmostEqual(titles_worked.worked_share(record, TILE, LANDLORD), held - 0.1)
        allocated = titles_worked.allocate_hectares({PEASANT: 0.1 * HECTARES}, HECTARES)
        self.assertAlmostEqual(allocated[PEASANT], 10.0)

    def test_the_lease_pays_rent_like_any_tenancy(self):
        _setup, record = self.landless_world()
        titles.lease(record, TILE, PEASANT, LANDLORD, 0.1)
        record.book.transfer(Transfer("edge:harvest", PEASANT, MONEY, 1000.0, "harvest"))
        payments = titles.settle_tenancies(record, MONEY, {TILE: HECTARES})
        self.assertAlmostEqual(sum(payment.amount for payment in payments if payment.purpose == "tenant_rent"),
                               0.1 * HECTARES * RENT_PER_HECTARE)

    def test_no_lease_when_the_tenant_cannot_bear_the_ask(self):
        leases = land_tenancy.match([land_tenancy.Offer(PEASANT, TILE, 10.0, 0.5)],
                                    [land_tenancy.Lot(LANDLORD, TILE, 50.0)], {TILE: 2.0}, {TILE: 1.5})
        self.assertEqual(leases, [])

    def test_the_tenant_that_bears_most_is_served_first_when_land_is_short(self):
        leases = land_tenancy.match([land_tenancy.Offer("a", TILE, 8.0, 2.0), land_tenancy.Offer("b", TILE, 8.0, 3.0)],
                                    [land_tenancy.Lot(LANDLORD, TILE, 10.0)], {TILE: 1.0}, {TILE: 1.0})
        self.assertEqual([(lease.tenant, lease.hectares) for lease in leases], [("b", 8.0), ("a", 2.0)])

    def test_a_lessor_cannot_let_more_than_its_free_title_nor_to_itself(self):
        _setup, record = self.landless_world()
        held = titles.holding(record, TILE, LANDLORD)
        self.assertEqual(titles.lease(record, TILE, LANDLORD, LANDLORD, 0.1), 0.0)
        self.assertAlmostEqual(titles.lease(record, TILE, PEASANT, LANDLORD, 5.0), held)
        self.assertEqual(titles.lease(record, TILE, "other", LANDLORD, 0.1), 0.0)       # all of it is let already

    def test_holders_let_only_what_their_hands_cannot_work(self):
        self.assertEqual(land_tenancy.lettable_hectares(50.0, 0.0, 0.0), 50.0)          # no hands: a rent-only holder
        self.assertEqual(land_tenancy.lettable_hectares(50.0, 10.0, 30.0), 10.0)
        self.assertEqual(land_tenancy.lettable_hectares(50.0, 0.0, 80.0), 0.0)
        self.assertEqual(land_tenancy.wanted_hectares(30.0, 12.0), 18.0)
        self.assertEqual(land_tenancy.wanted_hectares(10.0, 12.0), 0.0)

    def test_a_lease_survives_a_save_and_load(self):
        _setup, record = self.landless_world()
        titles.lease(record, TILE, PEASANT, LANDLORD, 0.1)
        self.assertEqual(EconomyRecord.from_record(record.to_record()).tenancies, record.tenancies)


class ToolsCheckTests(unittest.TestCase):
    TOOLED = Recipe("wheat", {"grain": 10.0}, {"hoe": 1.0}, {"hand": 100.0}, tool_wear={"hoe": 1.0},
                    tool_fallbacks={"hoe": (ToolFallback("", 0.0, 2.0, ("hand",)),)})

    def test_a_cohort_with_the_tools_works_as_many_hectares_as_its_hours_cover(self):
        self.assertAlmostEqual(land_tenancy.hectares_workable(self.TOOLED, 1.0, {"hoe": 100.0}, 1000.0), 10.0)

    def test_without_tools_it_works_by_hand_at_the_longer_hours(self):
        self.assertAlmostEqual(land_tenancy.hectares_workable(self.TOOLED, 1.0, {}, 1000.0), 5.0)

    def test_some_tools_cover_some_hectares_and_the_rest_is_by_hand(self):
        with_four = land_tenancy.hectares_workable(self.TOOLED, 1.0, {"hoe": 4.0}, 1000.0)
        self.assertGreater(with_four, 5.0)
        self.assertLess(with_four, 10.0)
        self.assertAlmostEqual(with_four, 4.0 + (1000.0 - 400.0) / 200.0)

    def test_no_hours_work_no_hectares_and_a_recipe_without_hours_is_not_limited_by_hands(self):
        self.assertEqual(land_tenancy.hectares_workable(self.TOOLED, 1.0, {"hoe": 9.0}, 0.0), 0.0)
        self.assertEqual(land_tenancy.hectares_workable(Recipe("ground", {"x": 1.0}, {}, {}), 1.0, {}, 10.0), math.inf)


if __name__ == "__main__":
    unittest.main()
