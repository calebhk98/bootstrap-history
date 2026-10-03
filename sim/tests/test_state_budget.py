"""Complaint 105: the government keeps a budget. Revenue is what the economy yields, spending is what
the state maintains (an army, officials), a deficit is financed from the reserve and then cut, the
spending reaches the labour pool and the goods market, and the levy on visible actors follows the
shortfall."""
import copy
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403
from functools import partial

sim = partial(sim, agent_economy=False)   # these checks pin the engine's own loanable-funds market, wage table and state budget


from sim.engine.agents_port import SimWorld
from sim.agents import budget
from sim.engine.saveload import load_state, save_state
from sim.engine.state import ActorRecord


def budget_sim(civ="rome_100ad", army=None, purse=None):
    """A game whose lenders advance the state nothing, so a deficit beyond the reserve is cut (borrowing
    is covered by test_capital_market)."""
    game = sim(civ=civ)
    game.market_credit_room = lambda actor_id: 0.0
    # revenue in coin only, so a deficit is measured against money (in-kind revenue: test_state_revenue_forms)
    game.civ["state_revenue"] = [form for form in game.civ["state_revenue"] if "paid_in" not in form]
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
check("the state's standing need has an army line and an administration line among its others",
      {"army", "administration"} <= set(lines), sorted(lines))
soldiers = lines["army"].labour.get("soldier", 0.0)
check("the army is the civilisation's opening standing force, held at the same share of the people",
      abs(soldiers - game.civ["standing_army"]) < 1e-6 * soldiers, (soldiers, game.civ.get("standing_army")))
check("army pay is the soldiers' hours at the soldier trade's wage",
      abs(lines["army"].wages - soldiers * game.HOURS_PER_PERSON_YEAR * game.labour_market.quote("soldier"))
      < 1e-6 * lines["army"].wages, lines["army"].wages)
check("the army's iron comes from military logistics: tonnes follow the soldiers and their equipment",
      lines["army"].materials and all(tonnes > 0.0 for tonnes in lines["army"].materials.values()),
      lines["army"].materials)
check("administration is paid officials, who are scribes",
      lines["administration"].labour.get("scribe", 0.0) > 0.0 and not lines["administration"].materials,
      lines["administration"])
bigger, _t = budget_sim()
for cohort in ("children", "working_age", "elderly"):
    setattr(bigger.population, cohort, getattr(bigger.population, cohort) * 2.0)
check("a larger population keeps more officials; the garrison follows the frontier, not the head count",
      budget.standing_lines(SimWorld(bigger))[1].labour["scribe"] > lines["administration"].labour["scribe"]
      and abs(budget.standing_lines(SimWorld(bigger))[0].labour["soldier"] - soldiers) < 1e-6 * soldiers, soldiers)
unarmed, _t = budget_sim(army=0.0)
check("a civilisation that opens with no standing force has no army line",
      "army" not in {line.name for line in budget.standing_lines(SimWorld(unarmed))})

# ---- revenue is the economy's yield, spending is the standing need ----------------------------
game, treasury = budget_sim()
revenue = SimWorld(game).state_revenue()
need = sum(line.money for line in budget.standing_lines(SimWorld(game)))
one_year(game)
income, outlays = treasury.record.income, treasury.record.outlays
check("the state's revenue is booked as income from taxation, less what it took in kind",
      abs(income.get("taxation", 0.0) + sum(treasury.record.revenue_in_kind.values()) - revenue) < 1e-6 * revenue,
      (income, treasury.record.revenue_in_kind, revenue))
check("the state spends its standing need, by purpose",
      outlays.get("army", 0.0) > 0.0 and outlays.get("administration", 0.0) > 0.0
      and abs(sum(outlays.values()) - need) < 0.02 * need, (outlays, need))
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
      abs(treasury.money) < 1e-6 * need, treasury.money)
spent = sum(treasury.record.outlays.values())
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
soldiers_free_before = game.market_supply("soldier")
scribes_before = game.actor_staff_fte("scribe")
one_year(game)
check("the army's and the officials' staff are held in the government's workforce",
      treasury.workforce.get("soldier", 0.0) > 0.0 and treasury.workforce.get("scribe", 0.0) > 0.0,
      treasury.workforce)
reach = game.reachable_trade_population("soldier") + game.actor_staff_fte("soldier")
labour_reach = game.reachable_trade_population("labourer") + game.actor_staff_fte("labourer")
share_of_nation = game.civ["standing_army"] / game.civ["population"] * game.population.total / game.population.working_age
army_share = lines["army"].labour["soldier"] / game.population.working_age
other_labourers = sum(line.labour.get("labourer", 0.0) for line in budget.standing_lines(SimWorld(game))[1:])
check("the state takes the same share of the founder's local pool as of the nation's working people",
      abs(treasury.workforce["soldier"] - army_share * reach) < 1e-6 * reach
      and abs(treasury.workforce["labourer"] - other_labourers / game.population.working_age * labour_reach) < 1e-6 * labour_reach,
      (treasury.workforce, share_of_nation, reach))
check("what the state employs is no longer on offer to the founder",
      game.actor_staff_fte("scribe") > scribes_before and game.market_supply("soldier") < soldiers_free_before,
      (game.actor_staff_fte("scribe"), game.market_supply("soldier"), soldiers_free_before))
unfunded_game, unfunded_treasury = budget_sim(army=1.0e8, purse=0.0)
one_year(unfunded_game)
check("a state that cut its spending employs correspondingly fewer people",
      unfunded_treasury.workforce["soldier"] < 0.5 * (unfunded_game.reachable_trade_population("soldier")
                                                     + unfunded_game.actor_staff_fte("soldier")),
      unfunded_treasury.workforce)

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
INCOME = 1.0e6


def short_of(unfunded, firms=0, protection=None):
    """A visible household (and `firms` equally visible firms), each earning INCOME, under a state
    that went a year short of exactly `unfunded` money."""
    game = grown(budget_sim()[0])
    game.revenue = lambda: INCOME
    if protection is not None:
        game.protection = protection
    for number in range(firms):
        firm = game.actors.add("firm:visible%d" % number, ActorRecord(kind="firm", money=60000000.0,
                                                                      last_margin=INCOME))
    world = SimWorld(game)
    while sum(line.money for line in budget.standing_lines(world)) < 1.5 * world.state_revenue():
        game.civ["standing_army"] *= 2.0  # a need above revenue, so the purse that falls short is positive, not a debt
        world = SimWorld(game)  # soldiers leave production, so revenue is read afresh
    need = sum(line.money for line in budget.standing_lines(world))
    game.state_treasury().money = need - world.state_revenue() - unfunded
    one_year(game)
    for firm in game.actors.active_firms():
        firm.workforce["artisan"] = 2000.0  # a firm with a visible staff (its year clears it)
    world = SimWorld(game)
    game.state_treasury().seek_shortfall(budget.standing_lines(world), world)
    return game


def ordinary(game):
    """The share of income the society pays the state, as it falls on a visible taxpayer."""
    return game.civ["starting_tax_share"] * game.state_capacity * game.notice_over(game.household_scale())


def charged(game):
    """What the state's shortfall adds to the ordinary share."""
    return sum(game.levy_shares(game.household_scale(), 0.0)) - ordinary(game)


content = grown(budget_sim()[0])
one_year(content)
check("a state with no unfunded need levies only the ordinary share, however visible the household",
      abs(sum(content.levy_shares(content.household_scale(), 0.0)) - ordinary(content)) < 1e-12
      and ordinary(content) > 0.0, content.levy_shares(content.household_scale(), 0.0))
small, large = short_of(1.0e4), short_of(2.0e4)
record = small.state_treasury().record
check("the state seeks its shortfall from the income it can see: the rate is shortfall over visible income",
      0.0 < record.levy_base and abs(charged(small) - 1.0e4 / record.levy_base * small.notice_over(small.household_scale())) < 1e-9
      and 1.0e4 / record.levy_base < budget.LEVY_RATE_CEILING, (charged(small), record.levy_base))
check("a bigger shortfall asks more of the same household", charged(large) > 1.5 * charged(small),
      (charged(large), charged(small)))
check("the same shortfall spread over a second equally visible taxpayer asks half as much of each",
      abs(charged(short_of(1.0e4, firms=1)) - 0.5 * charged(small)) < 0.05 * charged(small),
      (charged(short_of(1.0e4, firms=1)), charged(small)))
ruinous = short_of(1.0e12)
requisition, office = ruinous.levy_shares(ruinous.household_scale(), 0.0)
requisition -= ordinary(ruinous)
check("however large the shortfall the levy stops at the ceiling on one taxpayer's income",
      abs(requisition + office - budget.LEVY_RATE_CEILING * ruinous.notice_over(ruinous.household_scale())) < 1e-9,
      (requisition, office))
check("army need is claimed as requisition and the officials' as office",
      requisition > 0.0 and office > 0.0 and requisition > office, (requisition, office))
bargained = short_of(1.0e12, protection=0.85)
check("protection bargains requisition down and leaves the office alone",
      bargained.levy_shares(bargained.household_scale(), 0.85)[0] < requisition
      and abs(bargained.levy_shares(bargained.household_scale(), 0.85)[1] - office) < 1e-12,
      (bargained.levy_shares(bargained.household_scale(), 0.85), (requisition, office)))
below = sim()
below.civ["standing_army"] = 1.0e8
one_year(below)
check("a household below the notice line pays nothing even when the state is short",
      below.levy_shares(below.household_scale(), 0.0) == (0.0, 0.0), below.levy_shares(below.household_scale(), 0.0))
needy = ruinous
treasury_needy = needy.state_treasury()
paid_before = needy.capital
needy._state_pressure(needy.year)
check("the founder is charged the need-driven levy and the treasury receives it",
      needy.capital < paid_before and treasury_needy.record.income.get("requisition", 0.0) > 0.0,
      (needy.capital, paid_before, treasury_needy.record.income))
asked = treasury_needy.military_ask(INCOME, needy.household_scale(), SimWorld(needy))
check("the arms it asks of a militarily useful taxpayer are its unfunded army need, shared by visible income",
      0.0 < asked <= budget.LEVY_RATE_CEILING * INCOME, asked)
check("a state that paid for its army asks no arms",
      content.state_treasury().military_ask(INCOME, content.household_scale(), SimWorld(content)) == 0.0)

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

# ---- the founder pays the ordinary share the society pays ------------------------------------
ordinary_game = grown(budget_sim()[0])
ordinary_game.revenue = lambda: INCOME
one_year(ordinary_game)
before_capital = ordinary_game.capital
expected = INCOME * sum(ordinary_game.levy_shares(
    ordinary_game.household_scale(), ordinary_game.state.household.protection))
ordinary_game._state_pressure(ordinary_game.year)
check("a visible founder in a state with no shortfall still pays the ordinary share of his income",
      abs((before_capital - ordinary_game.capital) - expected) < 1e-6 * INCOME and ordinary(ordinary_game) > 0.0,
      (before_capital - ordinary_game.capital, expected))

# ---- the army follows what the state can pay -------------------------------------------------
from sim.agents.tuning import ARMY_ADJUSTMENT_RATE

army_game, army_treasury = budget_sim()
wanted = SimWorld(army_game).army_wanted()
one_year(army_game)
check("a state that pays for its army keeps the force it wants", abs(army_treasury.record.army - wanted) < 1e-6 * wanted,
      (army_treasury.record.army, wanted))
poor, poor_treasury = budget_sim(purse=0.0)
poor.civ["standing_army"] = 1.0e8
sizes = []
for _year in range(4):
    one_year(poor)
    sizes.append(poor_treasury.record.army)
wanted_poor = SimWorld(poor).army_wanted()
check("a state that cannot pay for its army shrinks it, by at most the adjustment rate a year",
      sizes[0] < wanted_poor and all(later <= earlier * (1.0 + 1e-9) for earlier, later in zip(sizes, sizes[1:]))
      and abs(sizes[0] - wanted_poor * (1.0 - ARMY_ADJUSTMENT_RATE)) < 1e-6 * wanted_poor, (sizes, wanted_poor))
for _year in range(3):
    poor_treasury.money = 1.0e30  # a purse that covers whatever the army costs, restored as the state sweeps its surplus
    one_year(poor)
check("when it can pay again the army regrows toward the force it wants, at the same bounded rate",
      sizes[-1] < poor_treasury.record.army <= sizes[-1] * (1.0 + ARMY_ADJUSTMENT_RATE) ** 3 + 1e-6, poor_treasury.record.army)
