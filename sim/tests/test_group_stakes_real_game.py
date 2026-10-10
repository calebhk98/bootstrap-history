"""Complaint 110, the slow check against a real game: the church and academy a civilisation starts with run a year in
the live adapters (`SimWorld`), the servants and strata sectors are read from the real world's budget and labour core,
an unpaid army mutinies against the real treasury, and the founder's answers to a demand (negotiate, conceal,
confiscation) work on the real household. Builds whole games, so it is not in the quick tier."""
import random

from .harness import check, unopened_sim

from sim.agents import group_servants
from sim.agents.api import Sector
from sim.engine.agents_port import SimWorld
from sim.engine.state_demand import answer_confiscation, set_household_stance, settle_household_year


def a_year(game):
    game.advance_actors(game.state.scenario.year)


game = unopened_sim(civ="england_1300")
view = SimWorld(game)
check("the live world answers what a stake asks of it",
      isinstance(view.idle_hours_by_trade(), dict) and isinstance(view.land_rent_per_hectare(), float)
      and isinstance(view.running_techniques(), dict) and view.tithable_sales_value("food") >= 0.0
      and "maize_kg" in view.substitutes_of("wheat_kg"))

for _year in range(3):
    a_year(game)
check("the civilisation's file founded a church and an academy at the first actor year",
      len(game.actors.of_kind("church")) == 1 and len(game.actors.of_kind("academy")) == 1)
church = game.actors.of_kind("church")[0]
check("the church ran its years: it counted what it collected and what it owed its clergy",
      "stipends" in church.record.need and church.record.need["stipends"] > 0.0, church.record.need)
check("the groups screen still reads", isinstance(game.interest_groups(), list))

# ---- an unpaid army loses its loyalty and mutinies against the real treasury --------------------------------
treasury = game.state_treasury()
treasury.money = 1.0e9
soldiers_before = treasury.record.army
check("a state that pays its army as little as it always has is not mutinied against in a quiet game",
      "soldiers" not in {row["kind"] for row in game.interest_groups()} and treasury.record.loyalty == 1.0,
      (game.interest_groups(), treasury.record.loyalty))
# the army had come to expect its full pay, and then gets a fifth of it
treasury.record.income_reference["army_pay_share"] = 1.0
for _year in range(5):
    a_year(game)
    treasury.record.need["army"] = max(1.0, treasury.record.need.get("army", 1.0))
    treasury.record.unfunded["army"] = 0.8 * treasury.record.need["army"]
    group_servants.run_army_year(treasury, SimWorld(game))
sectors = {sector.kind for sector in Sector.of_servants(treasury, SimWorld(game))}
check("soldiers in arrears are a sector in the real game's budget", "soldiers" in sectors, sectors)
check("their loyalty fell and the army shrank", treasury.record.loyalty < 1.0 and treasury.record.army < soldiers_before,
      (treasury.record.loyalty, treasury.record.army, soldiers_before))
check("the mutiny is in the founder's log", any("MUTINY" in text for _year, text in game.state.household.log), game.state.household.log[-5:])

# ---- the founder's answers to a demand, on the real household ------------------------------------------------------
household = game.state.household
household.capital = 1.0e6
scale_open = game.household_scale()
set_household_stance(game, "conceal")
game.rng = random.Random(2)   # a first draw high enough that the state does not find the hoard
settle_household_year(game)
check("a founder who conceals holds part of his wealth out of sight, and the state assesses him as smaller",
      household.concealed > 0.0 and game.household_scale() <= scale_open, (household.concealed, scale_open, game.household_scale()))
household.demand_stance = "comply"
household.concealed = 0.0
capital_before = household.capital
_answer, demanded, taken = answer_confiscation(game, 0.4, "confiscation by the state")
check("a complying founder is confiscated from as before: the demanded share of his capital goes to the treasury",
      abs(taken - demanded) < 1e-6 * max(1.0, demanded) and household.capital < capital_before, (demanded, taken))
set_household_stance(game, "refuse")
defiance_before = household.defiance
scandal_before = household.scandal
answer_confiscation(game, 0.4, "confiscation by the state")
check("a refusal marks the real household and puts blame on it",
      household.defiance > defiance_before and household.scandal > scandal_before, (household.defiance, household.scandal))
check("a defiant household looks larger to the state", game.household_scale() >= scale_open - 1e-9)
