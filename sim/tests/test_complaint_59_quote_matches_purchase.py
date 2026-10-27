"""Complaints/59: a quoted affordable amount must be purchasable as quoted.

Every quote of an affordable amount and every purchase gate asks the finance module's purchase views, so the rule is tested
here on the module built for the purpose."""
QUICK_TOPIC = True

import unittest

from sim.finance import purchase_rules
from sim.refusal import cause_of, facts_of
from sim.tests import finance_host


def Actor(budget, capital=None, credit=0.0):
    """The finance module whose spending power, cash and credit line are given."""
    module = finance_host.build(acting_balance=budget if capital is None else capital)

    def spending_power(kind):
        assert kind == "buy"
        return budget
    module.spending_power = spending_power
    module.credit_limit = lambda revenue=None, upkeep=None, capital=None: credit
    return module


class AffordableUnitsTests(unittest.TestCase):
    def test_the_affordable_amount_is_always_payable(self):
        for budget in (0.37, 1.0, 3000.0, 2999.999999, 123456.789, 1.0e-7):
            for unit_cost in (0.013, 0.5, 7.0, 29.99, 3000.0, 1.0e6):
                for decimals in (0, 1, 2):
                    actor = Actor(budget)
                    units = actor.affordable_units(unit_cost, decimals)
                    self.assertTrue(actor.can_pay(units * unit_cost), (budget, unit_cost, decimals, units))

    def test_one_more_step_than_the_affordable_amount_is_refused(self):
        for budget, unit_cost in ((3000.0, 7.0), (3000.0, 29.99), (500.0, 3.0)):
            actor = Actor(budget)
            units = actor.affordable_units(unit_cost, 1)
            self.assertFalse(actor.can_pay((units + 0.2) * unit_cost), (budget, unit_cost))

    def test_twice_the_affordable_amount_is_refused(self):
        actor = Actor(3000.0)
        units = actor.affordable_units(12.0)
        self.assertFalse(actor.can_pay((units * 2 + 1) * 12.0))

    def test_the_amount_is_rounded_down_to_the_decimals_asked(self):
        actor = Actor(100.0)
        self.assertEqual(actor.affordable_units(30.0, 0), 3)
        self.assertEqual(actor.affordable_units(30.0, 1), 3.3)
        self.assertEqual(actor.affordable_units(30.0, 2), 3.33)

    def test_a_cost_exactly_the_budget_is_payable(self):
        self.assertTrue(Actor(90.0).can_pay(90.0))
        self.assertEqual(Actor(90.0).affordable_units(30.0, 0), 3)

    def test_nothing_is_affordable_with_no_budget_and_a_free_unit_does_not_divide_by_zero(self):
        self.assertEqual(Actor(0.0).affordable_units(5.0), 0.0)
        self.assertGreater(Actor(10.0).affordable_units(0.0), 0.0)

    def test_the_budget_is_the_actors_spending_power_not_its_cash(self):
        actor = Actor(budget=3000.0, capital=1000.0, credit=4000.0)
        self.assertEqual(actor.purchase_budget(), 3000.0)
        self.assertTrue(actor.can_pay(2500.0))
        self.assertEqual(actor.affordable_units(100.0, 0), 30)


class AffordableWholeUnitsTests(unittest.TestCase):
    """Units whose bill rises with the number taken (slaves): the amount quoted is payable and the next is not."""

    @staticmethod
    def bill(people):
        return 100.0 * people * (1.0 + 0.01 * people)

    def test_the_quoted_people_are_payable_and_one_more_is_not(self):
        for budget in (50.0, 1000.0, 3000.0, 25000.0):
            people = purchase_rules.affordable_whole_units(budget, 100.0, self.bill)
            self.assertLessEqual(self.bill(people), budget, budget)
            self.assertGreater(self.bill(people + 1), budget, budget)

    def test_a_budget_below_one_unit_buys_none(self):
        self.assertEqual(purchase_rules.affordable_whole_units(40.0, 100.0, self.bill), 0)

    def test_a_flat_price_gives_the_division(self):
        self.assertEqual(purchase_rules.affordable_whole_units(950.0, 100.0, lambda people: 100.0 * people), 9)


class RefusalTests(unittest.TestCase):
    def refusal(self, budget=3000.0, cost=5000.0):
        return Actor(budget, capital=1000.0, credit=4000.0).purchase_refusal("forest", cost)

    def test_the_refusal_states_cost_budget_and_shortfall_as_values(self):
        refusal = self.refusal()
        self.assertEqual(cause_of(refusal), "cash_short")
        self.assertEqual((facts_of(refusal)["cost"], facts_of(refusal)["budget"], facts_of(refusal)["short"]),
                         (5000.0, 3000.0, 2000.0))

    def test_the_refusal_cites_the_budget_the_quote_does(self):
        # presentation: the sentence that names what you could raise
        self.assertIn("you could raise", str(self.refusal()))
        self.assertIn(purchase_rules.afford_means(), str(self.refusal()))

    def test_a_cost_inside_the_budget_is_short_of_nothing(self):
        self.assertEqual(facts_of(self.refusal(budget=3000.0, cost=1000.0))["short"], 0.0)


if __name__ == "__main__":
    unittest.main()
