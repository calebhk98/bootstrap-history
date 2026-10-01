"""Complaint 109: the government keeps a budget. Revenue is what the economy yields, spending is what
the state maintains (an army, officials), a deficit is financed from the reserve and then cut, the
spending reaches the labour pool and the goods market, and the levy on visible actors follows the
shortfall."""
import copy
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld
from sim.engine.actors import budget
from sim.engine.proto.saveload import load_state, save_state
from sim.engine.state import ActorRecord


def budget_sim(civ="rome_100ad", army=None, purse=None):
    game = sim(civ=civ)
    if army is not None:
        game.civ["standing_army"] = army
    treasury = game.state_treasury()
    if purse is not None:
        treasury.money = purse
    return game, treasury


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def grown(game, employees=2000.0, capital=60000000.0, eminence=25.0):
    game.employees["artisan"] = employees
    game._resync_pools()
    game.capital = capital
    game.eminence = eminence
    game.update_protection()
    return game


# ---- the standing need comes from the army and the officials --------------------------------
game, treasury = budget_sim()
world = SimWorld(game)
lines = {line.name: line for line in budget.standing_lines(world)}
check("the state's standing need has an army line and an administration line",
      set(lines) == {"army", "administration"}, sorted(lines))
soldiers = lines["army"].labour.get("labourer", 0.0)
check("the army is the civilisation's opening standing force, held at the same share of the people",
      abs(soldiers - game.civ["standing_army"]) < 1e-6 * soldiers, (soldiers, game.civ.get("standing_army")))
check("army pay is the soldiers' hours at the labourer's wage",
      abs(lines["army"].wages - soldiers * game.HOURS_PER_PERSON_YEAR * game.wage_per_hour("labourer"))
      < 1e-6 * lines["army"].wages, lines["army"].wages)
check("the army's iron comes from military logistics: tonnes follow the soldiers and their equipment",
      lines["army"].materials and all(tonnes > 0.0 for tonnes in lines["army"].materials.values()),
      lines["army"].materials)
check("administration is paid officials, who are scribes",
      lines["administration"].labour.get("scribe", 0.0) > 0.0 and not lines["administration"].materials,
      lines["administration"])
bigger, _t = budget_sim()
bigger.population.total *= 2.0
check("a larger population keeps a larger army",
      budget.standing_lines(SimWorld(bigger))[0].labour["labourer"] > soldiers, soldiers)
unarmed, _t = budget_sim(army=0.0)
check("a civilisation that opens with no standing force has no army line",
      "army" not in {line.name for line in budget.standing_lines(SimWorld(unarmed))})

# ---- revenue is the economy's yield, spending is the standing need ----------------------------
game, treasury = budget_sim()
revenue = SimWorld(game).state_revenue()
one_year(game)
income, outlays = treasury.record.income, treasury.record.outlays
check("the whole of the state's revenue is booked as income from taxation",
      abs(income.get("taxation", 0.0) - revenue) < 1e-6 * revenue, (income, revenue))
need = sum(line.money for line in budget.standing_lines(SimWorld(game)))
check("the state spends its standing need, by purpose",
      outlays.get("army", 0.0) > 0.0 and outlays.get("administration", 0.0) > 0.0
      and abs(outlays["army"] + outlays["administration"] - need) < 0.02 * need, (outlays, need))
check("a state in surplus keeps the difference as reserve and the ledger balances",
      abs(treasury.money - (sum(income.values()) - sum(outlays.values()))) < 1e-6 * revenue
      and treasury.money > 0.0, (treasury.money, income, outlays))
check("a state that paid all it needs records no unfunded need",
      not any(treasury.record.unfunded.values()), treasury.record.unfunded)

# ---- a deficit is financed from the reserve first, then spending is cut ----------------------
heavy, treasury = budget_sim(army=1.0e8)  # a force the revenue cannot carry
revenue = SimWorld(heavy).state_revenue()
need = sum(line.money for line in budget.standing_lines(SimWorld(heavy)))
check("the heavy army is a real deficit", need > 2.0 * revenue, (need, revenue))
reserve = 0.4 * (need - revenue)
treasury.money = reserve
one_year(heavy)
check("a reserve that covers part of the deficit is spent down to nothing, not below",
      abs(treasury.money) < 1e-6 * need and treasury.money >= 0.0, treasury.money)
spent = sum(treasury.record.outlays.get(name, 0.0) for name in ("army", "administration"))
check("spending is cut to what revenue and reserve afford",
      abs(spent - (revenue + reserve)) < 1e-6 * need, (spent, revenue, reserve))
check("the cut is recorded as unfunded need, by line",
      abs(sum(treasury.record.unfunded.values()) - (need - spent)) < 1e-6 * need
      and all(amount > 0.0 for amount in treasury.record.unfunded.values()),
      treasury.record.unfunded)
rich, treasury_rich = budget_sim(army=1.0e8)
treasury_rich.money = 10.0 * need
one_year(rich)
check("a reserve big enough finances the whole deficit and leaves nothing unfunded",
      not any(treasury_rich.record.unfunded.values())
      and treasury_rich.money < 10.0 * need, (treasury_rich.money, treasury_rich.record.unfunded))

# ---- spending reaches the labour pool --------------------------------------------------------
game, treasury = budget_sim()
free_before = game.market_supply("labourer")
scribes_before = game.actor_staff_fte("scribe")
one_year(game)
check("the army's and the officials' staff are held in the government's workforce",
      treasury.workforce.get("labourer", 0.0) > 0.0 and treasury.workforce.get("scribe", 0.0) > 0.0,
      treasury.workforce)
local = game.home_town_population_estimate() / game.population.total
check("the state draws on the founder's local pool in proportion to the people it has there",
      abs(treasury.workforce["labourer"] - game.civ["standing_army"] * local) < 0.02 * treasury.workforce["labourer"],
      (treasury.workforce, local))
check("what the state employs is no longer on offer to the founder",
      game.actor_staff_fte("scribe") > scribes_before and game.market_supply("labourer") < free_before,
      (game.actor_staff_fte("scribe"), game.market_supply("labourer"), free_before))
unfunded_game, unfunded_treasury = budget_sim(army=1.0e8, purse=0.0)
one_year(unfunded_game)
check("a state that cut its spending employs correspondingly fewer people",
      unfunded_treasury.workforce["labourer"]
      < unfunded_game.civ["standing_army"] * local, unfunded_treasury.workforce)

# ---- spending reaches the goods market -------------------------------------------------------
game, treasury = budget_sim()
check("before the state buys anything it adds no demand", game.actor_demand("iron") == 0.0)
quoted_before = game.market_price_ratio("iron_bar_kg")
one_year(game)
tonnes = game.actor_demand("iron")
check("the state's iron purchases are demand in the commodity's market", tonnes > 0.0, tonnes)
check("the demand is what the army's equipment needs, funded",
      abs(tonnes - sum(budget.standing_lines(SimWorld(game))[0].materials.values())) < 1e-6 * tonnes, tonnes)
state = game.market_state("iron_bar_kg")
check("the market report shows the state's demand", state["actor_demand_tonnes"] == tonnes, state)
huge, huge_treasury = budget_sim(army=3.0e8, purse=1.0e18)
one_year(huge)
check("a state buying a great deal of iron raises its price",
      huge.market_price_ratio("iron_bar_kg") > quoted_before, (huge.market_price_ratio("iron_bar_kg"), quoted_before))

# ---- the levy follows the state's need -------------------------------------------------------
content = grown(budget_sim()[0])
one_year(content)
check("a state with no unfunded need levies nothing, however visible the household",
      content.levy_shares(content.household_scale(), 0.0) == (0.0, 0.0),
      content.levy_shares(content.household_scale(), 0.0))
needy = grown(budget_sim(army=1.0e8, purse=0.0)[0])
one_year(needy)
requisition, office = needy.levy_shares(needy.household_scale(), 0.0)
check("a state with unfunded need levies the household it can see: army need as requisition, "
      "officials as office", requisition > 0.0 and office > 0.0, (requisition, office))
small_gap = grown(budget_sim(army=1.0e8, purse=0.0)[0])
small_gap_treasury = small_gap.state_treasury()
small_gap_treasury.money = 0.97 * (sum(line.money for line in budget.standing_lines(SimWorld(small_gap)))
                                   - SimWorld(small_gap).state_revenue())
one_year(small_gap)
check("a smaller shortfall asks less of the same household",
      sum(small_gap.levy_shares(small_gap.household_scale(), 0.0)) < sum(needy.levy_shares(needy.household_scale(), 0.0)),
      (small_gap.levy_shares(small_gap.household_scale(), 0.0), (requisition, office)))
check("the levy never exceeds the ceiling on any one taxpayer's income",
      requisition + office <= budget.LEVY_RATE_CEILING + 1e-12, (requisition, office))
below = sim()
below.civ["standing_army"] = 1.0e8
one_year(below)
check("a household below the notice line pays nothing even when the state is short",
      below.levy_shares(below.household_scale(), 0.0) == (0.0, 0.0), below.levy_shares(below.household_scale(), 0.0))
treasury_needy = needy.state_treasury()
paid_before = needy.capital
needy._state_pressure(needy.year)
check("the founder is charged the need-driven levy and the treasury receives it",
      needy.capital < paid_before and treasury_needy.record.income.get("requisition", 0.0) > 0.0,
      (needy.capital, paid_before, treasury_needy.record.income))
spread = grown(budget_sim(army=1.0e8, purse=0.0)[0])
spread.actors.add("firm:big", ActorRecord(kind="firm", money=60000000.0)).workforce["artisan"] = 2000.0
one_year(spread)
check("the same shortfall spread over more visible taxpayers asks less of each",
      sum(spread.levy_shares(spread.household_scale(), 0.0)) < sum(needy.levy_shares(needy.household_scale(), 0.0)),
      (spread.levy_shares(spread.household_scale(), 0.0), (requisition, office)))

# ---- the books survive save and load ----------------------------------------------------------
before = copy.deepcopy(needy.state.actors.records)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(needy, path)
    revived = sim()
    load_state(revived, path)
check("need, unfunded need, demand and levy rates round-trip through save and load",
      revived.state.actors.records == before
      and revived.state.actors.records["government:rome_100ad"].unfunded, before.keys())
