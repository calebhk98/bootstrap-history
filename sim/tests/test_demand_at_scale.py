"""Pins three properties of sim/world/demand.py's Stone-Geary household
demand system found while answering docs/architecture/DEMAND_AT_SCALE.md's
three questions - read that document for the full analysis, the literature
each claim rests on, and the ranked recommendation for what to build next.
This file only pins the numbers so nobody has to re-derive them before
checking a fix.

ONE CLASS BELOW USED TO PIN A DEFECT AS A PASSING TEST ON THE WRONG
BEHAVIOUR, in the style sim/tests/test_price_solver_cycles.py established
for Complaints/31 (commit 355e9ef pinned the wrong answer with instructions
to invert rather than delete, and 66e2c94 did exactly that once the defect
was fixed). `SubsistenceFloorIsNowTradeableTests` below is that inversion:
docs/architecture/DEMAND_AT_SCALE.md SS1's recommended fix (a). The hard
floor is gone - a household short of its own subsistence bundle now
demands a POSITIVE, price-sensitive quantity of a good with no
subsistence floor of its own, exactly the property Banerjee and Duflo's
survey evidence (see this class's own docstring) said the old model could
not represent at all. THE CLASS NAME AND EVERY ASSERTION IN IT CHANGED;
nothing here still checks the old zero-demand behaviour, so there is
nothing left in this class to invert a second time - a future change to
the mechanism should update this class's numbers directly rather than
hunting for an "old" version to flip.

EngelCurveFloorsAtTheMarginalBudgetShareTests below is UNCHANGED and still
pins the second, separate defect DEMAND_AT_SCALE.md SS2 found (the Engel
curve's floor at food's own fixed marginal budget share) - out of scope for
this task, per the task's own instruction to leave it pinned.

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


class SubsistenceFloorIsNowTradeableTests(unittest.TestCase):
    """Formerly HardSubsistenceFloorZerosOutEveryOtherGoodTests, inverted:
    household_quantity_demanded_per_capita's below-subsistence branch used
    to pay every good's committed floor down by the SAME proportional scale
    factor, including a good whose own subsistence_quantity_per_capita_per_
    year is zero - a zero floor scaled by any factor is still zero, so a
    household below its food floor demanded EXACTLY zero of a good like a
    phone, at ANY price however cheap, with a step jump to a specific
    positive quantity the instant income crossed the floor. See
    DEMAND_AT_SCALE.md SS1 for why Banerjee and Duflo's household survey
    evidence (extremely poor, calorie-short households still spending on
    festivals, tobacco and alcohol) and Jack and Suri's M-Pesa adoption
    evidence say real below-subsistence households do not behave this way.

    The fix (sim/world/demand.py's own _below_subsistence_quantity_
    demanded_per_capita, and FLOOR_TRADEABLE_SHARE) treats part of a
    below-subsistence household's shortfall as flexible spending rather
    than forcing every good down by the same scale factor. Four properties
    are checked below, matching the ones the task that built this fix was
    handed: no discontinuity at the old cliff, price actually mattering
    below the line (the sharpest test - a good made 1000x cheaper must
    draw MORE demand even from a household that cannot feed itself), food
    still dominating a poor household's spending, and a comfortable
    household's demand staying exactly what the untouched formula above
    the line always gave it.
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

    def _phone_quantity_at(self, income_fraction_of_committed_food, phone_price=None):
        income_per_capita = (
            income_fraction_of_committed_food * self.committed_food_cost_per_capita)
        prices = dict(self.prices)
        if phone_price is not None:
            prices["phone"] = phone_price
        return demand.household_quantity_demanded_per_capita(
            self.phone, prices, income_per_capita, self.basket)

    def test_below_subsistence_household_now_buys_a_positive_quantity_of_the_phone(self):
        # Three income levels, all below the food floor by different
        # amounts (99%, 80%, 30% of the committed food cost) - every one
        # of them now demands a POSITIVE quantity of phones, the property
        # the old hard floor could not represent at any price.
        for income_fraction_of_committed_food in (0.99, 0.80, 0.30):
            phone_quantity = self._phone_quantity_at(income_fraction_of_committed_food)
            self.assertGreater(
                phone_quantity, 0.0,
                "a below-subsistence household demands zero phones at "
                "income fraction %.2f - the hard floor is back; see this "
                "class's own docstring and sim/world/demand.py's "
                "_below_subsistence_quantity_demanded_per_capita"
                % income_fraction_of_committed_food)

    def test_price_cut_below_the_subsistence_line_raises_demand(self):
        # THE test: a household earning 99% of its own committed food cost
        # - calorie-short by construction - is offered the SAME phone at
        # 1000x the price and at ordinary price. Demand must be higher at
        # the lower price. Under the old hard floor both quantities were
        # exactly zero, so price had NO effect at all below the line; this
        # is the specific behaviour the old model could not produce at any
        # price, however cheap.
        normal_price_quantity = self._phone_quantity_at(0.99, phone_price=0.01)
        cheap_price_quantity = self._phone_quantity_at(0.99, phone_price=0.01 / 1000.0)
        self.assertGreater(normal_price_quantity, 0.0)
        self.assertGreater(
            cheap_price_quantity, normal_price_quantity,
            "cutting a below-subsistence household's phone price 1000x did "
            "not raise its phone demand - price has stopped mattering "
            "below the subsistence line again")
        # The elastic (flexible-spending) term is linear in 1/price, exactly
        # like the formula above the line - so the 1000x price cut should
        # raise quantity by (almost) exactly 1000x, not some smaller amount.
        self.assertAlmostEqual(
            cheap_price_quantity / normal_price_quantity, 1000.0, places=6)

    def test_no_step_discontinuity_walking_income_across_the_old_cliff(self):
        # Walk income in 1000 small, even steps from half the committed
        # food cost to 1.5x it - straddling the old cliff at exactly 1.0 -
        # and check no single step changes phone demand by more than a
        # bound comfortably below the OLD cliff's own jump size (which was
        # the pinned 3.069328, in one step, however finely income was
        # sampled either side of it - see this class's own docstring).
        # This bound is not tuned to just barely pass: sampled this finely,
        # every step observed while building this fix stayed under 0.31,
        # itself no larger than this model's ordinary elastic response to
        # an equivalent income step well away from the old cliff (this
        # basket's own PHONE has marginal_budget_share / price = 5.0, so an
        # income step of this size moves ordinary demand by a comparable
        # amount everywhere, not just near the old cliff).
        number_of_steps = 1000
        low_income_fraction, high_income_fraction = 0.5, 1.5
        max_single_step_change = 0.0
        previous_quantity = None
        for step_index in range(number_of_steps + 1):
            income_fraction = low_income_fraction + (
                (high_income_fraction - low_income_fraction)
                * step_index / number_of_steps)
            income_per_capita = income_fraction * self.committed_food_cost_per_capita
            quantity = demand.household_quantity_demanded_per_capita(
                self.phone, self.prices, income_per_capita, self.basket)
            if previous_quantity is not None:
                max_single_step_change = max(
                    max_single_step_change, abs(quantity - previous_quantity))
            previous_quantity = quantity
        self.assertLess(
            max_single_step_change, 1.0,
            "a single fine step in income moved phone demand by %.6f - "
            "comparable to the old cliff's own jump size (3.069328) rather "
            "than an ordinary, continuous response" % max_single_step_change)

    def test_meets_the_formula_above_the_line_with_no_jump_at_the_boundary(self):
        # At income exactly equal to the committed food cost, the surplus
        # is exactly zero, so the (untouched) formula above the line
        # returns exactly the phone's own subsistence quantity (0.0, since
        # the phone has none). Approaching that same income from just
        # below must land on the same value, not jump past it.
        income_just_below = 0.999 * self.committed_food_cost_per_capita
        quantity_just_below = demand.household_quantity_demanded_per_capita(
            self.phone, self.prices, income_just_below, self.basket)
        quantity_at_the_line = demand.household_quantity_demanded_per_capita(
            self.phone, self.prices, self.committed_food_cost_per_capita, self.basket)
        self.assertEqual(quantity_at_the_line, 0.0)
        self.assertLess(quantity_just_below, 0.2)

    def test_food_still_dominates_a_household_at_half_the_subsistence_floor(self):
        # A household at HALF its own committed food cost - severely
        # calorie-short - must still spend most of its income on food, not
        # spread it evenly with the phone. Softening the floor must not
        # turn into "the poor spend like the rich": every unit of flexible
        # spending is split by the SAME marginal budget shares used above
        # the line (food's own share here is 0.95, deliberately food-heavy
        # like a real subsistence basket), so food keeps the large
        # majority of spending for any FLOOR_TRADEABLE_SHARE below 1 - see
        # _below_subsistence_quantity_demanded_per_capita's own docstring
        # for why this does not depend on tuning that number.
        income_per_capita = 0.5 * self.committed_food_cost_per_capita
        food_quantity = demand.household_quantity_demanded_per_capita(
            self.food, self.prices, income_per_capita, self.basket)
        phone_quantity = demand.household_quantity_demanded_per_capita(
            self.phone, self.prices, income_per_capita, self.basket)
        food_spending = self.prices["wheat_kg"] * food_quantity
        phone_spending = self.prices["phone"] * phone_quantity
        food_budget_share = food_spending / (food_spending + phone_spending)
        self.assertGreater(
            food_budget_share, 0.5,
            "a household at half its own subsistence floor spends less "
            "than half its income on food - the softened floor has gone "
            "too far")
        # Report the actual share rather than just clearing 0.5, so a
        # change to FLOOR_TRADEABLE_SHARE or the mechanism shows up here as
        # a moved number even while this bound keeps passing. This
        # basket's own food marginal budget share is already 0.95 (a
        # deliberately food-heavy two-good basket - see setUp), so almost
        # all of the newly-flexible spending goes to food too.
        self.assertAlmostEqual(food_budget_share, 0.9875, places=3)

    def test_budget_is_exactly_exhausted_below_the_subsistence_line(self):
        # The re-allocation is real spending moved between goods, not
        # spending invented from nowhere: total spending across the whole
        # basket must still equal income exactly, the same identity the
        # formula above the line satisfies.
        income_per_capita = 0.5 * self.committed_food_cost_per_capita
        total_spending = sum(
            self.prices[good.name] * demand.household_quantity_demanded_per_capita(
                good, self.prices, income_per_capita, self.basket)
            for good in self.basket)
        self.assertAlmostEqual(total_spending, income_per_capita, places=6)

    def test_a_comfortable_household_is_unaffected_to_within_floating_point_noise(self):
        # Well above the floor, the untouched formula must give exactly
        # what it always gave - the old model was not wrong there (see
        # this class's own docstring). Computed independently here from
        # the textbook closed form rather than by calling demand.py's own
        # function twice, so this is a genuine check against the documented
        # algebra, not a tautology.
        income_per_capita = 50.0 * self.committed_food_cost_per_capita
        surplus_per_capita = income_per_capita - self.committed_food_cost_per_capita
        expected_phone_quantity = (
            self.phone.subsistence_quantity_per_capita_per_year
            + (self.phone.marginal_budget_share / self.prices["phone"])
            * surplus_per_capita)
        actual_phone_quantity = demand.household_quantity_demanded_per_capita(
            self.phone, self.prices, income_per_capita, self.basket)
        self.assertAlmostEqual(
            actual_phone_quantity, expected_phone_quantity, places=9)


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


class SoftenedFloorOnTheRealDefaultBasketTests(unittest.TestCase):
    """SubsistenceFloorIsNowTradeableTests exercises a deliberately
    food-heavy two-good basket (food's own marginal budget share there is
    0.95, so food dominating a poor household's spending is close to
    automatic). This class runs the same "food still dominates when poor"
    property against demand.py's own DEFAULT_BASKET, where food's marginal
    budget share is only 0.30 and MANUFACTURES takes 0.65 of every
    flexible unit spent - the harder version of the same check, because
    food no longer wins the flexible pool almost by default.
    """

    def setUp(self):
        self.basket = demand.DEFAULT_BASKET
        wheat_price_per_kg = demand._illustrative_recursive_labour_content_price_per_kg(
            "wheat_kg")
        self.prices = {"wheat_kg": wheat_price_per_kg, "manufactures": 1.0,
                        "silver_kg": 50.0}
        self.committed_per_capita = sum(
            self.prices[good.name] * good.subsistence_quantity_per_capita_per_year
            for good in self.basket)

    def test_food_still_dominates_at_half_the_floor_even_with_a_low_marginal_share(self):
        income_per_capita = 0.5 * self.committed_per_capita
        spending = {
            good.name: self.prices[good.name] * demand.household_quantity_demanded_per_capita(
                good, self.prices, income_per_capita, self.basket)
            for good in self.basket}
        total_spending = sum(spending.values())
        food_budget_share = spending["wheat_kg"] / total_spending
        self.assertGreater(
            food_budget_share, 0.5,
            "food's own marginal budget share (0.30) is not enough to keep "
            "it the majority of a half-floor household's spending once "
            "MANUFACTURES (0.65) and SILVER (0.05) share the flexible pool")
        # Reported rather than just bounded, so a change to
        # FLOOR_TRADEABLE_SHARE shows up here as a moved number - see
        # _below_subsistence_quantity_demanded_per_capita's own docstring
        # for why this stays comfortably above 0.5 for ANY
        # FLOOR_TRADEABLE_SHARE strictly less than 1, not because 0.5 was
        # picked to make this particular number come out this way.
        self.assertAlmostEqual(food_budget_share, 0.825, places=3)

    def test_total_spending_still_equals_income_on_the_default_basket(self):
        income_per_capita = 0.5 * self.committed_per_capita
        total_spending = sum(
            self.prices[good.name] * demand.household_quantity_demanded_per_capita(
                good, self.prices, income_per_capita, self.basket)
            for good in self.basket)
        self.assertAlmostEqual(total_spending, income_per_capita, places=6)


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
