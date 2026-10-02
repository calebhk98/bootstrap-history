"""Complaint 314: soldiers are a trade in the one labour market. The state's army is people of that trade
at its wage, conscription moves the wage, and soldiers taken out of the unskilled pool make unskilled
labour scarcer."""
from .harness import *  # noqa: F401,F403

from sim.agents import SimWorld
from sim.agents import budget


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def with_army(share_of_working_age):
    game = sim()
    game.civ["standing_army"] = share_of_working_age * game.population.working_age
    return game


game = with_army(0.001)
world = SimWorld(game)
check("soldier is a trade the labour market prices and the founder could hire", "soldier" in game.available_trades(),
      game.available_trades())
army = {line.name: line for line in budget.standing_lines(world)}["army"]
check("the army is people of the soldier trade, not labourers", set(army.labour) == {"soldier"}, army.labour)
check("army pay is the soldier trade's wage in the one labour market",
      abs(army.wages - army.labour["soldier"] * world.pay_per_person_year("soldier")) < 1e-6 * army.wages, army.wages)
check("soldiers come from the whole working age, as unskilled labour does",
      world.national_people("soldier") == game.population.working_age, world.national_people("soldier"))

# ---- conscription moves the soldier wage ------------------------------------------------------------
small, large = with_army(0.002), with_army(0.2)
wage_small, wage_large = (g.labour_market.quote_annual("soldier") for g in (small, large))
check("before the state hires, the soldier wage does not depend on the army it will raise",
      abs(wage_small - wage_large) < 1e-9 * wage_small, (wage_small, wage_large))
for funded in (small, large):
    funded.state_treasury().money = 1.0e15  # both states pay in full, so the levy size is the only difference
one_year(small)
one_year(large)
check("soldiers hired by the state raise the soldier wage", small.labour_market.quote_annual("soldier") > wage_small,
      (small.labour_market.quote_annual("soldier"), wage_small))
check("a larger levy raises it further",
      large.labour_market.quote_annual("soldier") / wage_large > small.labour_market.quote_annual("soldier") / wage_small,
      (large.labour_market.quote_annual("soldier"), small.labour_market.quote_annual("soldier")))
check("the state's soldiers are in its workforce under their own trade",
      large.state_treasury().workforce.get("soldier", 0.0) > 0.0, large.state_treasury().workforce)

# ---- soldiers under arms are drawn from the unskilled pool ------------------------------------------
unarmed, armed = with_army(0.0), with_army(0.2)
for funded in (unarmed, armed):
    funded.state_treasury().money = 1.0e15  # both states pay every line, so only the army differs
one_year(unarmed)
one_year(armed)
check("with a fifth of the working age under arms, unskilled labour costs more",
      armed.labour_market.quote_annual("labourer") > unarmed.labour_market.quote_annual("labourer"),
      (armed.labour_market.quote_annual("labourer"), unarmed.labour_market.quote_annual("labourer")))
