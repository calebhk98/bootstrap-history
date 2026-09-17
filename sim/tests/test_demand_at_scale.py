"""Pins three properties of sim/world/demand.py's Stone-Geary household
demand system found while answering docs/architecture/DEMAND_AT_SCALE.md's
three questions - read that document for the full analysis, the literature
each claim rests on, and the ranked recommendation for what to build next.
This file only pins the numbers so nobody has to re-derive them before
checking a fix.

TWO CLASSES HERE PIN DEFECTS, WRITTEN AS PASSING PINS ON THE WRONG
BEHAVIOUR, NOT AS FAILING TESTS - the pattern sim/tests/test_price_solver_
cycles.py established for Complaints/31 (see that file's own git history:
commit 355e9ef pinned the wrong answer with instructions to invert rather
than delete, and 66e2c94 did exactly that once the defect was fixed). Each
assertion below states what sim/world/demand.py does TODAY, with a comment
saying what a fix should change it to, so whoever builds the fix
DEMAND_AT_SCALE.md recommends finds this file immediately, flips the
assertion, and does not mistake the fix for a regression. Do not delete
these when a fix lands - invert them.

A third class is NOT a defect pin. It confirms a property
DEMAND_AT_SCALE.md's third question needed checked rather than assumed -
that the demand system needs no currency at all - and is kept as ordinary
regression coverage, because there is nothing here to invert.

Written as unittest.TestCase, like sim/tests/test_demand.py and sim/tests/
test_price_solver_cycles.py, importing sim.world.demand directly rather
than sim/tests/harness.py - see demand.py's own STANDALONE section for why
a module with no dependency on sim/engine/ should not be tested through a
harness built for the engine.

NOT YET REGISTERED IN sim/tests/__main__.py's TOPICS list, so `python3
sim/test_regressions.py` does not run this file yet - see
DEMAND_AT_SCALE.md's own closing section for why that file was left
untouched here and what line adds it.
"""
import unittest

from sim.world import demand


class HardSubsistenceFloorZerosOutEveryOtherGoodTests(unittest.TestCase):
    """household_quantity_demanded_per_capita's below-subsistence branch
    (its own docstring calls this a "starvation regime") pays every good's
    committed floor down by the SAME proportional scale factor, including a
    good whose own subsistence_quantity_per_capita_per_year is zero. A zero
    floor scaled by any factor is still zero, so a household below its food
    floor demands EXACTLY zero of a good like a phone, at ANY price however
    cheap. See DEMAND_AT_SCALE.md SS1 for why Banerjee and Duflo's household
    survey evidence says real below-subsistence households do not behave
    this way, and for the three ways this could be fixed.
    """

    def setUp(self):
        # A two-good household: FOOD (a real subsistence floor, taken from
        # demand.py's own default good) and a cheap PHONE (no biological
        # floor at all, priced far below a year's committed food spending).
        self.food = demand.Good(
            "wheat_kg", demand.FOOD.subsistence_quantity_per_capita_per_year, 0.95)
        self.phone = demand.Good("phone", 0.0, 0.05)
        self.basket = (self.food, self.phone)
        demand.validate_basket(self.basket)
        wheat_price_per_kg = demand._illustrative_recursive_labour_content_price_per_kg(
            "wheat_kg")
        self.prices = {"wheat_kg": wheat_price_per_kg, "phone": 0.01}
        self.committed_food_cost_per_capita = (
            wheat_price_per_kg * self.food.subsistence_quantity_per_capita_per_year)

    def test_below_subsistence_household_buys_zero_phones_at_any_income_shortfall(self):
        # Three income levels, all below the food floor by different
        # amounts (99%, 80%, 30% of the committed food cost) - every one
        # of them demands exactly zero phones, not merely fewer phones.
        for income_fraction_of_committed_food in (0.99, 0.80, 0.30):
            income_per_capita = (
                income_fraction_of_committed_food * self.committed_food_cost_per_capita)
            phone_quantity = demand.household_quantity_demanded_per_capita(
                self.phone, self.prices, income_per_capita, self.basket)
            self.assertEqual(
                phone_quantity, 0.0,
                "a below-subsistence household now buys a nonzero quantity "
                "of a gamma=0 good - if this is because the hard floor was "
                "softened (DEMAND_AT_SCALE.md SS1's recommendation), invert "
                "this assertion to check the quantity is POSITIVE and grows "
                "with income fraction, update this class's docstring, and "
                "do not delete the test")

    def test_phone_demand_jumps_discontinuously_the_instant_food_floor_clears(self):
        # The two incomes below straddle the food floor by one percent in
        # each direction. Real household spending has no step
        # discontinuity at any single income level; this model's does,
        # because the below- and above-floor formulas in household_
        # quantity_demanded_per_capita are two different pieces of algebra
        # glued together at one point.
        income_just_below_floor = 0.99 * self.committed_food_cost_per_capita
        income_just_above_floor = 1.01 * self.committed_food_cost_per_capita
        phone_quantity_below = demand.household_quantity_demanded_per_capita(
            self.phone, self.prices, income_just_below_floor, self.basket)
        phone_quantity_above = demand.household_quantity_demanded_per_capita(
            self.phone, self.prices, income_just_above_floor, self.basket)

        self.assertEqual(phone_quantity_below, 0.0)
        # A two-percent change in income takes phone demand from zero to a
        # specific positive quantity - pinned as an exact figure so a fix
        # that smooths this transition shows up here as a changed number,
        # not just as "still passes".
        self.assertAlmostEqual(
            phone_quantity_above, 3.069328, places=5,
            msg="the discontinuity's size at the subsistence line has "
                "moved - if it is smaller or gone, DEMAND_AT_SCALE.md SS1 "
                "is being addressed; recompute this figure for the fixed "
                "module rather than deleting the test")


class EngelCurveFloorsAtTheMarginalBudgetShareTests(unittest.TestCase):
    """A linear expenditure system's budget share for a good with a
    positive subsistence floor is that good's own marginal_budget_share
    PLUS a term that shrinks toward zero as income grows - see
    market_clearing_price's own module-docstring derivation for the same
    A + B/income shape applied to a fixed-supply good's price instead of a
    budget share. That means food's budget share can fall a long way as
    income rises (Engel's Law holds in DIRECTION), but it can never fall
    below FOOD's own marginal_budget_share (0.30, read from demand.FOOD
    rather than hardcoded here, since the constant that sets it is being
    renamed elsewhere in this same branch - see DEMAND_AT_SCALE.md's own
    closing note) at ANY income, however large - see
    DEMAND_AT_SCALE.md SS2 for the closed form and why this is a structural
    property of every linear expenditure system, not a calibration miss.
    Real modern-US food budget shares run roughly 10-13% of household
    spending (source and citation: DEMAND_AT_SCALE.md SS2), a share this
    functional form cannot reach at any income multiple - the model does
    not merely need a bigger number here, 0.30 is a floor no income level
    lets it cross.
    """

    def setUp(self):
        self.basket = demand.DEFAULT_BASKET
        wheat_price_per_kg = demand._illustrative_recursive_labour_content_price_per_kg(
            "wheat_kg")
        self.prices = {"wheat_kg": wheat_price_per_kg, "manufactures": 1.0,
                        "silver_kg": 50.0}
        self.committed_cost_per_capita = sum(
            self.prices[good.name] * good.subsistence_quantity_per_capita_per_year
            for good in self.basket)

    def _food_budget_share_at_income_multiple(self, income_multiple_of_committed_cost):
        income_per_capita = income_multiple_of_committed_cost * self.committed_cost_per_capita
        single_bin = (demand.IncomeBin(
            population=1.0, income_per_capita_per_year=income_per_capita,
            population_percentile_from_top=(0.0, 1.0)),)
        return demand.household_budget_share(
            demand.FOOD, self.prices, single_bin, self.basket)

    def test_food_share_keeps_falling_across_industrial_and_modern_income_multiples(self):
        # The DIRECTION is right - Engel's Law holds qualitatively across
        # six orders of magnitude of income.
        shares = [self._food_budget_share_at_income_multiple(multiple)
                  for multiple in (2.0, 10.0, 100.0, 10_000.0, 1_000_000.0)]
        for earlier_share, later_share in zip(shares, shares[1:]):
            self.assertGreater(earlier_share, later_share)

    def test_food_share_never_falls_below_its_own_marginal_budget_share(self):
        # The MAGNITUDE is wrong: at a full million times the committed
        # subsistence cost - an income scale far beyond anything needed to
        # stand in for a modern economy - food's share is still barely
        # above 30%, not the roughly 10-13% real modern economies show.
        food_share_at_extreme_income = self._food_budget_share_at_income_multiple(1_000_000.0)
        food_marginal_budget_share = demand.FOOD.marginal_budget_share
        self.assertGreater(food_share_at_extreme_income, food_marginal_budget_share)
        self.assertAlmostEqual(
            food_share_at_extreme_income, food_marginal_budget_share, delta=0.001,
            msg="food's budget share at an extreme income multiple is no "
                "longer converging on its own marginal budget share - if a "
                "richer functional form with an income-varying share (AIDS "
                "or QUAIDS; see DEMAND_AT_SCALE.md SS2) has replaced the "
                "fixed-share linear expenditure system, this whole class is "
                "checking a property the new form does not have and should "
                "be replaced rather than inverted")


class NumeraireInvarianceConfirmsTheAtlantisCaseTests(unittest.TestCase):
    """NOT a defect pin. This class protects a property DEMAND_AT_SCALE.md
    SS3 confirms is already correct, rather than assumed: a Stone-Geary /
    linear expenditure system is homogeneous of degree zero in prices and
    income taken together (standard microeconomic theory - see any
    treatment of "no money illusion" in consumer demand), so a
    civilisation that prices everything in cowrie shells rather than
    labour-hours needs no change to this module at all, PROVIDED income
    and every price are expressed in the same unit of account. If either
    test below ever fails, something in this module has started reading a
    price or an income figure's absolute size rather than a ratio between
    them, which would be a real and immediate regression against
    DEMAND_AT_SCALE.md's Atlantis finding.
    """

    def test_quantities_demanded_are_unchanged_by_a_uniform_unit_of_account_change(self):
        basket = demand.DEFAULT_BASKET
        wheat_price_per_kg = demand._illustrative_recursive_labour_content_price_per_kg(
            "wheat_kg")
        prices_in_labour_hours = {
            "wheat_kg": wheat_price_per_kg, "manufactures": 1.0, "silver_kg": 50.0}
        income_in_labour_hours = 400.0

        # An arbitrary, non-round conversion factor - a round factor like
        # 1.0 or 10.0 could hide a bug that only shows up away from the
        # "natural" scale the module's own illustrative numbers use.
        shells_per_labour_hour = 17.3
        prices_in_shells = {name: price * shells_per_labour_hour
                             for name, price in prices_in_labour_hours.items()}
        income_in_shells = income_in_labour_hours * shells_per_labour_hour

        for good in basket:
            quantity_priced_in_hours = demand.household_quantity_demanded_per_capita(
                good, prices_in_labour_hours, income_in_labour_hours, basket)
            quantity_priced_in_shells = demand.household_quantity_demanded_per_capita(
                good, prices_in_shells, income_in_shells, basket)
            self.assertAlmostEqual(
                quantity_priced_in_hours, quantity_priced_in_shells, places=6,
                msg="%s's demanded quantity changed when every price and "
                    "the income figure were rescaled by the same factor - "
                    "the module has started depending on the choice of "
                    "numeraire" % good.name)

    def test_market_clearing_price_rescales_exactly_with_the_unit_of_account(self):
        wheat_price_per_kg = demand._illustrative_recursive_labour_content_price_per_kg(
            "wheat_kg")
        other_prices_in_labour_hours = {"wheat_kg": wheat_price_per_kg, "manufactures": 1.0}
        shells_per_labour_hour = 17.3
        other_prices_in_shells = {name: price * shells_per_labour_hour
                                   for name, price in other_prices_in_labour_hours.items()}

        bins_in_labour_hours = demand.income_bins(1_000_000.0, 400.0, gini=0.4)
        bins_in_shells = demand.income_bins(
            1_000_000.0, 400.0 * shells_per_labour_hour, gini=0.4)
        supply_quantity = 500.0

        price_in_labour_hours = demand.market_clearing_price(
            demand.SILVER, supply_quantity, other_prices_in_labour_hours,
            bins_in_labour_hours, demand.DEFAULT_BASKET)
        price_in_shells = demand.market_clearing_price(
            demand.SILVER, supply_quantity, other_prices_in_shells,
            bins_in_shells, demand.DEFAULT_BASKET)

        self.assertAlmostEqual(
            price_in_shells / price_in_labour_hours, shells_per_labour_hour, places=6)


if __name__ == "__main__":
    unittest.main()
