"""Complaint 327 (and 412): a state's surplus is not swept out of the economy. Reserve beyond the need it
holds against risk is lent through the loanable-funds market (the state as a saver, earning interest) and
spent on works, a named purchase that hires people; no outlay of the state goes to nobody."""
from .harness import *  # noqa: F401,F403




def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


# ---- no outlay without a recipient --------------------------------------------------------------
rich = unopened_sim()
rich_treasury = rich.state_treasury()
rich_treasury.money = 1.0e12
for _year in range(4):
    one_year(rich)
check("no state outlay is the sweep that paid no one",
      "discretionary" not in rich_treasury.record.outlays, rich_treasury.record.outlays)
check("the purse still equals what it held plus income less outlays",
      abs(rich_treasury.money - (1.0e12 + sum(rich_treasury.record.income.values())
                                 - sum(rich_treasury.record.outlays.values()))) < 1e-6 * 1.0e12, rich_treasury.money)

# ---- the state is a saver on the loanable market ------------------------------------------------
saver = unopened_sim()
saver_treasury = saver.state_treasury()
saver_treasury.money = 1.0e12
one_year(saver)
check("a state with a reserve beyond its need is a source of funds on the market",
      saver.actors.state.purses.offers.get(saver_treasury.actor_id, 0.0) > 0.0, saver.actors.state.purses.offers)
