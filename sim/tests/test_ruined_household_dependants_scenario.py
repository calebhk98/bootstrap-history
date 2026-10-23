"""SCENARIO (Complaint 524): one year's money phase of a game in arrears with no income charges living costs without the
dependants its income cannot carry. The rule is in test_ruined_household_dependants."""

from .harness import *  # noqa: F401,F403

game = unopened_sim()
dependants = game.dependants_cost()
check("the dependants' cost is part of the living cost", 0.0 < dependants < game.living_cost(), (dependants, game.living_cost()))
game.revenue = lambda: 0.0
game.revenue_capacity = lambda: 0.0
game.state.household.capital = -0.5 * game.credit_limit()
living_without_income = game.living_cost()
paid_before = game.state.founder.living_cost_paid
game._step_money_seat()
paid = game.state.founder.living_cost_paid - paid_before
check("a year in arrears charges living costs without the dependants its income cannot carry",
      abs(paid - (living_without_income - dependants)) < 1e-6, (paid, living_without_income, dependants))
