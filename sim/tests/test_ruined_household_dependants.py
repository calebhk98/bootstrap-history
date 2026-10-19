"""Complaint 524: a household in arrears whose income does not cover its costs cannot keep every dependant, so
debt stops growing past the credit limit. Read on a game with its economy unopened, one year's money phase."""

from .harness import *  # noqa: F401,F403

game = unopened_sim()
household = game.state.household
dependants = game.dependants_cost()
revenue = game.revenue()
upkeep = game.upkeep()

check("the dependants' cost is part of the living cost",
      0.0 < dependants < game.living_cost(),
      (dependants, game.living_cost()))
household.capital = 1000.0
check("a household with money and an income that covers its costs keeps every dependant",
      game.dependants_beyond_means(game.living_cost(), revenue=1.0e9, upkeep=upkeep) == 0.0,
      game.dependants_beyond_means(game.living_cost(), revenue=1.0e9, upkeep=upkeep))
check("a household with money but no income sheds all its dependants and leaves its savings alone",
      abs(game.dependants_beyond_means(game.living_cost(), revenue=0.0, upkeep=upkeep) - dependants) < 1e-9,
      game.dependants_beyond_means(game.living_cost(), revenue=0.0, upkeep=upkeep))
household.capital = -10.0
check("a household in arrears whose income covers its costs keeps every dependant",
      game.dependants_beyond_means(game.living_cost(), revenue=1.0e9, upkeep=upkeep) == 0.0,
      game.dependants_beyond_means(game.living_cost(), revenue=1.0e9, upkeep=upkeep))
living = game.living_cost()
shed = game.dependants_beyond_means(living, revenue=0.0, upkeep=upkeep)
check("a household in arrears with no income sheds all its dependants and no more",
      abs(shed - dependants) < 1e-9, (shed, dependants))
creditors_keep = game.DEBT_SERVICE_SHARE_OF_SURPLUS
income_for_half = (living - dependants + dependants / 2.0 / (1.0 - creditors_keep)
                   + upkeep + 10.0 * game.debt_interest_rate())
half = game.dependants_beyond_means(living, revenue=income_for_half, upkeep=upkeep)
check("a household in arrears keeps the dependants its surplus carries once the creditors have their share",
      abs(half - dependants / 2.0) < 1e-6, (half, dependants))

# One year's money phase with no income at all: the dependants are not paid for.
game.revenue = lambda: 0.0
game.revenue_capacity = lambda: 0.0
household.capital = -0.5 * game.credit_limit()
living_without_income = game.living_cost()
paid_before = game.state.founder.living_cost_paid
game._step_money_seat()
paid = game.state.founder.living_cost_paid - paid_before
check("a year in arrears charges living costs without the dependants its income cannot carry",
      abs(paid - (living_without_income - dependants)) < 1e-6, (paid, living_without_income, dependants))
