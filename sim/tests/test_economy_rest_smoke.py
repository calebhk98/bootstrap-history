"""SMOKE: the hand-built three-tile economy on the clearing rule set comes to rest, stays close to a copy a rounding error
apart and moves to a new rest after a shock; that it ends in the same place from a start five per cent different is what
the owner asks and does not hold yet (the three checks expected to fail say why) (Complaint 473).
Whole economies are stepped for decades, so this is an integration check of the rule set as a whole; its rules are tested
one function at a time in test_labour_symmetric_wage, test_labour_hires_at_wage, test_labour_clear_at_one_wage,
test_labour_demand_schedule, test_stock_supply, test_goods_one_price_clearing and test_rule_sets. The same figures print
with `python3 sim/simulator.py spin-up-trace --fixture stationary --rules clearing --twin --years 90`."""
import statistics
import unittest

from sim.economy.api import RULE_SET_CLEARING
from sim.economy.fixture_setups import FARM, FARMS, GRAIN, HILLS, LABOURER, METAL, MINER, ORE, SMITH, TOWN, stationary_setup
from sim.markets.spin_up import SPIN_UP_TOLERANCE
from sim.tests.economy_fixture import quiet_year, run
from sim.ui.spin_up_fixture_trace import nudged

TOPIC_SECONDS = 900          # seven economies of ninety to a hundred and ten years each
YEARS = 90
RESTING_FROM = 60            # the years from here on are read as the rest state
SHOCK_YEAR = 60
SHOCK_YEARS = 110
OPENING_PRICES = {GRAIN: 0.3, ORE: 0.05, METAL: 95.0}       # the fixture's own, restated so a start can be moved off them
OPENING_WAGES = {LABOURER: 1.0, MINER: 1.2, SMITH: 1.5}
MOVED = 1.05


def figures(outcome):
    """A year's figures: price level, labourers' wage, that wage in grain, hours hired, the grain price, grain made."""
    wage, grain = outcome.wages[LABOURER], outcome.prices[GRAIN]
    return {"price_level": outcome.basket_price_level, "wage": wage, "wage_in_grain": wage / grain,
            "hired_hours": outcome.hired_hours, "grain_price": grain, "grain_made": outcome.output.get(GRAIN, 0.0)}


def series(years=YEARS, inputs_for_year=None, setup=None, **changes):
    setup = setup or stationary_setup(rule_set=RULE_SET_CLEARING, **changes)
    _economy, outcomes = run(setup, years, inputs_for_year)
    return [figures(outcome) for outcome in outcomes]


def yearly_moves(rows, name, first, last=None):
    """Each year's change of a figure over the years from `first`, as a share of the year before."""
    window = rows[first:last]
    return [abs(after[name] - before[name]) / abs(before[name]) for before, after in zip(window, window[1:])]


def resting(rows, name, first=RESTING_FROM, last=None):
    return statistics.mean(row[name] for row in rows[first:last])


def scaled(figures_by_name, factor):
    return {name: value * factor for name, value in figures_by_name.items()}


def fewer_people(economy, year):
    setup = economy.setup
    if year < SHOCK_YEAR:
        return quiet_year(setup)
    return quiet_year(setup, population_by_tile={tile: people * 0.9 for tile, people in setup.opening_population_by_tile.items()})


def better_farm_yield(economy, year):
    if year < SHOCK_YEAR:
        return quiet_year(economy.setup)
    farms = {producer_id: 1.2 for producer_id in economy.record.producers if economy.record.producers[producer_id].recipe_id == FARM}
    return quiet_year(economy.setup, yield_factor_by_producer=farms)


class ClearingRuleSetOnTheThreeTileEconomy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = series()
        cls.twin = series(setup=nudged(stationary_setup(rule_set=RULE_SET_CLEARING)))
        cls.moved_starts = {
            "prices": series(opening_prices=scaled(OPENING_PRICES, MOVED)),
            "wages": series(opening_wages=scaled(OPENING_WAGES, MOVED)),
            "prices and wages": series(opening_prices=scaled(OPENING_PRICES, MOVED), opening_wages=scaled(OPENING_WAGES, MOVED)),
        }
        cls.fewer = series(SHOCK_YEARS, fewer_people)
        cls.better = series(SHOCK_YEARS, better_farm_yield)

    def test_no_year_of_the_rest_state_moves_a_quantity_by_half_the_settle_tolerance(self):
        for name in ("price_level", "wage", "hired_hours"):
            self.assertLess(max(yearly_moves(self.base, name, RESTING_FROM)), SPIN_UP_TOLERANCE / 2.0, name)

    def test_the_rest_state_moves_a_fifth_of_the_settle_tolerance_a_year_on_average(self):
        for name in ("price_level", "wage", "hired_hours"):
            self.assertLess(statistics.mean(yearly_moves(self.base, name, RESTING_FROM)), SPIN_UP_TOLERANCE / 5.0, name)

    def rests_where_the_base_does(self, start):
        for name in ("wage_in_grain", "hired_hours"):
            self.assertLess(abs(resting(self.moved_starts[start], name) / resting(self.base, name) - 1.0), 0.01, (start, name))

    # The three below state the owner's requirement (an economy started five per cent off settles close to the same thing).
    # They fail because a producer's capacity depends on the path taken: it grows toward what its sales call for and is cut
    # on a year's loss (close_kernel.close_rows), so the share of its workplaces that work at rest, and with it the wage in
    # grain, differ by start; and a producer stands for every workplace of a recipe on a tile, so one bankruptcy idles them
    # all for a year and the economy restarts smaller. Both rules are shared by the rule sets.
    @unittest.expectedFailure
    def test_a_start_with_prices_five_per_cent_higher_rests_at_the_same_real_wage_and_hours(self):
        self.rests_where_the_base_does("prices")

    @unittest.expectedFailure
    def test_a_start_with_wages_five_per_cent_higher_rests_at_the_same_real_wage_and_hours(self):
        self.rests_where_the_base_does("wages")

    @unittest.expectedFailure
    def test_a_start_with_prices_and_wages_five_per_cent_higher_rests_at_the_same_real_wage_and_hours(self):
        self.rests_where_the_base_does("prices and wages")

    def test_a_copy_a_rounding_error_apart_stays_within_the_settle_tolerance(self):
        for name in ("price_level", "wage", "hired_hours"):
            gaps = [abs(ours[name] - theirs[name]) / abs(ours[name]) for ours, theirs in zip(self.base, self.twin)]
            self.assertLess(max(gaps), SPIN_UP_TOLERANCE, name)

    def test_a_better_farm_yield_gives_more_and_cheaper_grain_and_a_higher_real_wage(self):
        before = lambda name: resting(self.better, name, SHOCK_YEAR - 10, SHOCK_YEAR)
        after = lambda name: resting(self.better, name, SHOCK_YEARS - 20)
        self.assertGreater(after("grain_made") / before("grain_made"), 1.1)
        self.assertLess(after("grain_price") / before("grain_price"), 0.9)
        self.assertGreater(after("wage_in_grain") / before("wage_in_grain"), 1.1)

    def test_the_economy_rests_again_after_the_better_yield(self):
        for name in ("price_level", "wage", "hired_hours"):
            self.assertLess(max(yearly_moves(self.better, name, SHOCK_YEARS - 20)), SPIN_UP_TOLERANCE, name)

    def test_a_tenth_fewer_people_hire_about_a_tenth_fewer_hours_at_a_higher_real_wage(self):
        before = lambda name: resting(self.fewer, name, SHOCK_YEAR - 10, SHOCK_YEAR)
        after = lambda name: resting(self.fewer, name, SHOCK_YEARS - 20)
        self.assertLess(after("hired_hours") / before("hired_hours"), 0.95)
        self.assertGreater(after("hired_hours") / before("hired_hours"), 0.85)
        self.assertGreater(after("wage_in_grain"), before("wage_in_grain"))


if __name__ == "__main__":
    unittest.main()
