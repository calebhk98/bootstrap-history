"""Scenario (Complaint 640): the default founder in a running game. The arithmetic of what the income can carry is in
test_founder_income_living_cost.py.

Complaint 524: a founder with no projects lives within what their own work earns, as a society household of the
same income does, instead of spending the purse down on a household the wage cannot keep."""

from .harness import *  # noqa: F401,F403

game = sim(manual=False)
revenue, upkeep = game.revenue(), game.upkeep()
living = game.living_cost()
shed = game.dependants_beyond_means(living, revenue, upkeep, game.mine_operating_cost())
paid = living - shed
base = game.household_bill_per_person()

check("the default founder earns a wage for their idle hours",
      game.labour.hours_for_sale() > 0 and game.founder_wage_income() > 0.0,
      (game.labour.hours_for_sale(), game.founder_wage_income()))
check("the wage covers one person's subsistence",
      game.founder_wage_income() > base, (game.founder_wage_income(), base))
check("the default founder with no projects pays no more than the income leaves after running costs",
      paid <= revenue - upkeep + 1e-6, (paid, revenue, upkeep))
check("what the income cannot carry is the dependants' cost, never subsistence",
      0.0 <= shed <= game.dependants_cost() + 1e-9 and paid >= base, (shed, game.dependants_cost(), paid, base))
check("the recurring net of the default founder is not negative",
      game.recurring_net() >= -1e-6, game.recurring_net())

game.charge_founder_for_theft = lambda keeping, keeping_owed: 0.0   # theft of held coin is its own mechanism
guard_fee = game.coin_hoard()["keeping_cost_per_year"]   # coin kept under guard is its own cost
capital_before = game.state.household.capital
game._step_money_seat()
check("a year of the money phase with no projects does not draw the purse down",
      game.state.household.capital >= capital_before - guard_fee - 1e-6,
      (capital_before, game.state.household.capital))
