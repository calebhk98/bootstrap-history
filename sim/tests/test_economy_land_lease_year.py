"""The year's leasing and rent asks read the economy's record and view (land_lease_year.py): a landless cohort takes a
tenancy from a holder with no hands, the ask falls when the wage rises, and the tools it holds limit what it works."""

QUICK_TOPIC = True

import types
import unittest

from sim.economy import land_lease_year, titles, titles_worked
from sim.economy.households_cohort import Cohort
from sim.economy.households_own import own_production_options
from sim.economy.types import Recipe, TileSpec, ToolFallback

TILE = "t"
LANDLORD = "firm:landlord"
POOR = "household:t:0"
GRAIN_RECIPE = Recipe("grow_grain", {"grain": 10.0}, {"hoe": 1.0}, {"hand": 4.0}, climate_classes=("Cfb",),
                      tool_wear={"hoe": 1.0}, tool_fallbacks={"hoe": (ToolFallback("", 0.0, 2.0, ("hand",)),)})
LAND = {"grow_grain": 2.0}
BASKET = types.SimpleNamespace(needs=[types.SimpleNamespace(need_id="food", subsistence_per_person=1.0, goods=(("grain", 1.0),))])


class View:
    def __init__(self, wage, tools=0.0):
        self.wage_per_hour, self.tools = wage, tools

    def wage(self, trade, area):
        return self.wage_per_hour

    def price(self, good, area):
        return 5.0 if good == "grain" else None

    def area_of(self, good, tile):
        return "area"

    def stock(self, agent, good, tile):
        return self.tools if good == "hoe" else 0.0


def world(people=10.0, working=10.0):
    tile = TileSpec(TILE, 40.0, 10.0, 1.0, False, (), 1.0, 1.0, climate_class="Cfb")       # a hundred hectares
    setup = types.SimpleNamespace(tiles={TILE: tile}, recipes={"grow_grain": GRAIN_RECIPE}, land_per_run=LAND,
                                  servant_trade="servant", working_hours_per_year=2000.0,
                                  basket_for=lambda tile_id: BASKET)
    record = types.SimpleNamespace(cohorts={POOR: Cohort(POOR, TILE, 0, people, working, 0.0)},
                                   titles={TILE: {LANDLORD: 1.0}}, tenancies={}, loans=[], land_rent={TILE: 24.0},
                                   cleared_hectares={})
    return setup, record, own_production_options(setup.recipes, LAND, BASKET)


class AskTests(unittest.TestCase):
    def test_the_ask_falls_when_the_wage_rises(self):
        setup, record, options = world()
        slack = land_lease_year.asks(setup, record, View(0.2, tools=100.0), options)[TILE]
        scarce = land_lease_year.asks(setup, record, View(5.0, tools=100.0), options)[TILE]
        self.assertGreater(slack, scarce)
        self.assertLessEqual(slack, record.land_rent[TILE])

    def test_a_wage_that_eats_the_crop_leaves_no_rent_to_ask(self):
        setup, record, options = world()
        self.assertEqual(land_lease_year.asks(setup, record, View(15.0), options)[TILE], 0.0)


class LeaseInTheMarketTests(unittest.TestCase):
    def test_a_landless_cohort_takes_the_hectares_its_floors_need_from_a_holder_with_no_hands(self):
        setup, record, options = world()
        self.assertEqual(titles_worked.worked_share(record, TILE, POOR), 0.0)
        leases = land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)
        self.assertEqual([(lease.tenant, lease.lessor) for lease in leases], [(POOR, LANDLORD)])
        # ten people, a floor of one need unit each, grown at ten units a two-hectare run of four hours: two hectares
        self.assertAlmostEqual(leases[0].hectares, 2.0)
        self.assertAlmostEqual(titles_worked.worked_share(record, TILE, POOR) * 100.0, 2.0)
        self.assertAlmostEqual(titles.holding(record, TILE, LANDLORD), 1.0)

    def test_a_second_year_leases_nothing_more_it_already_works_what_it_needs(self):
        setup, record, options = world()
        land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)
        self.assertEqual(land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options), [])

    def test_no_lease_when_the_wage_leaves_no_margin_over_the_outside_option(self):
        setup, record, options = world()
        self.assertEqual(land_lease_year.lease_in_market(setup, record, View(15.0), options), [])
        self.assertEqual(record.tenancies, {})

    def test_a_cohort_with_too_few_hands_leases_only_what_its_hours_work(self):
        setup, record, options = world(people=100.0, working=0.01)      # 20 hours: five four-hour runs of two hectares
        leases = land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)
        self.assertAlmostEqual(leases[0].hectares, 10.0)               # its floors need twenty hectares

    def test_without_tools_the_same_hours_work_fewer_hectares(self):
        setup, record, options = world(people=100.0, working=0.01)
        tooled = land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)[0].hectares
        setup, record, options = world(people=100.0, working=0.01)
        bare = land_lease_year.lease_in_market(setup, record, View(0.2, tools=0.0), options)[0].hectares
        self.assertAlmostEqual(bare, tooled / 2.0)

    def test_a_holder_that_works_its_own_floors_lets_only_the_rest(self):
        setup, record, options = world()
        record.cohorts["household:t:1"] = Cohort("household:t:1", TILE, 1, 10.0, 10.0, 0.5)
        record.titles[TILE] = {"household:t:1": 1.0}
        leases = land_lease_year.lease_in_market(setup, record, View(0.2, tools=100.0), options)
        self.assertEqual([lease.lessor for lease in leases], ["household:t:1"])
        self.assertAlmostEqual(titles_worked.worked_share(record, TILE, "household:t:1") * 100.0, 98.0)


if __name__ == "__main__":
    unittest.main()
