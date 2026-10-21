"""Scenario, Complaint 564: in a running game the seat's need floors are the economy's floors at its tile, and a founder
and a cohort household of the same size pay the same. The arithmetic of the bill is in test_one_living_cost_model."""

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

check("the seat's floors are the economy's floors at its tile",
      abs(sum(floors.values()) - cohort_floor_per_person) <= 1e-9 * cohort_floor_per_person, (floors, cohort_floor_per_person))
check("a founder and a cohort household of the same size pay the same for their needs",
      abs((game.household_bill_per_person() + game.dependants_cost()) - people * cohort_floor_per_person)
      <= 1e-9 * people * cohort_floor_per_person,
      (game.household_bill_per_person(), game.dependants_cost(), cohort_floor_per_person))
