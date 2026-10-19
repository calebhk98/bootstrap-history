"""Complaint 564: the founder's household buys its needs through the economy's need basket and floors at the prices
on its tile, so its living cost is a read of that bill and a cohort household of the same size pays the same."""

from .harness import *  # noqa: F401,F403
from sim.economy import households
from sim.economy.api import country_figures

game = sim(manual=False)
economy = game.economy.agent._economy
tile = game.economy.acting_tile()
coin = economy.setup.coin_per_unit
view = country_figures._floor_view(economy)
cohort_floor_per_person = coin * sum(need.price_index * need.spec.subsistence_per_person
                                     for need in households.need_prices(economy.setup.basket_for(tile), view, tile))
floors = game.economy.agent_need_floor_costs_at()
people = 1.0 + game.household_dependant_people()
state = game.state.household

check("the seat's floors are the economy's floors at its tile",
      abs(sum(floors.values()) - cohort_floor_per_person) <= 1e-9 * cohort_floor_per_person, (floors, cohort_floor_per_person))
check("a founder and a cohort household of the same size pay the same for their needs",
      abs((game.household_bill_per_person() + game.dependants_cost()) - people * cohort_floor_per_person)
      <= 1e-9 * people * cohort_floor_per_person,
      (game.household_bill_per_person(), game.dependants_cost(), cohort_floor_per_person))
check("the dependants are people with the founder's needs, one bill each",
      abs(game.dependants_cost() - game.household_dependant_people() * game.household_bill_per_person()) <= 1e-9,
      game.dependants_cost())
state.freedmen, state.slaves = 2, 3
check("freedmen and slaves are people too",
      game.household_dependant_people() == game.HOUSEHOLD_DEPENDANT_PEOPLE + 5, game.household_dependant_people())
state.freedmen, state.slaves = 0, 0

game.LIVING_COST_STATUS_PER_CAPITAL = 0.0
state.capital = 0.0
check("with no tax, status or wages, the living cost is the household's need bill",
      abs(game.living_cost(_rev=0.0, _upkeep=0.0) - (game.labour.wage_bill() + people * game.household_bill_per_person()))
      <= 1e-6, (game.living_cost(_rev=0.0, _upkeep=0.0), people * game.household_bill_per_person()))
