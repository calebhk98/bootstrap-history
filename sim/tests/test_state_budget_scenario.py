"""SCENARIO: Complaint 105: the government keeps a budget. Revenue is what the economy yields, spending is what
the state maintains (an army, officials), a deficit is financed from the reserve and then cut, the
spending reaches the labour pool and the goods market, and the levy on visible actors follows the
shortfall."""
import copy
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents.policy import IdlePolicy



from sim.engine.agents_port import SimWorld
from sim.agents import budget
from sim.engine.saveload import load_state, save_state
from sim.engine.state import ActorRecord


# a force the revenue cannot carry, yet within the working-age people who could serve (Complaint 602)
HEAVY_ARMY = 1.0e7


def budget_sim(civ="rome_100ad", army=None, purse=None, cut_when_short=False):
    """A game whose lenders advance the state nothing, so a deficit beyond the reserve is cut (borrowing
    is covered by test_capital_market)."""
    game = unopened_sim(civ=civ)
    game.market_credit_room = lambda actor_id: 0.0
    # revenue in coin only, so a deficit is measured against money (in-kind revenue: test_state_revenue_forms)
    record = game.state_treasury().record   # the state's own forms, copied from the civilisation's file at setup
    record.revenue_forms = [{key: value for key, value in form.items() if key != "paid_in"} for form in record.revenue_forms]
    # the goods the state buys are bid for in the agent economy's book and paid when the year clears, not booked as outlays
    game.bids = []   # (buyer, commodity, tonnes, money)
    real_note_purchase = game.economy.note_actor_purchase
    game.economy.note_actor_purchase = lambda buyer, commodity, tonnes, budget_money: (
        game.bids.append((buyer, commodity, tonnes, budget_money)), real_note_purchase(buyer, commodity, tonnes, budget_money))[1]
    if army is not None:
        game.civ["standing_army"] = army
    treasury = game.state_treasury()
    if purse is not None:
        treasury.money = purse
    if cut_when_short:
        treasury.decision_policy = IdlePolicy()   # a state that chooses no other response cuts its lines
    return game, treasury


def one_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


def grown(game, employees=2000.0, capital=60000000.0, eminence=25.0):
    game.employees["artisan"] = employees
    game.labour._resync_pools()
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
      abs(lines["army"].wages - soldiers * game.HOURS_PER_PERSON_YEAR * game.labour.market.quote("soldier"))
      < 1e-6 * lines["army"].wages, lines["army"].wages)
check("the army's iron comes from military logistics: tonnes follow the soldiers and their equipment",
      lines["army"].materials and all(tonnes > 0.0 for tonnes in lines["army"].materials.values()),
      lines["army"].materials)
# the opening game is read and then changed one thing at a time, each put back, before it runs its first year below
opening_population = {cohort: getattr(game.population, cohort) for cohort in ("children", "working_age", "elderly")}
for cohort, people in opening_population.items():
    setattr(game.population, cohort, people * 2.0)
check("a larger population keeps more officials; the garrison follows the frontier, not the head count",
      budget.standing_lines(SimWorld(game))[1].labour["scribe"] > lines["administration"].labour["scribe"]
      and abs(budget.standing_lines(SimWorld(game))[0].labour["soldier"] - soldiers) < 1e-6 * soldiers, soldiers)
for cohort, people in opening_population.items():
    setattr(game.population, cohort, people)
opening_army = game.civ["standing_army"]
game.civ["standing_army"] = 0.0
check("a civilisation that opens with no standing force has no army line",
      "army" not in {line.name for line in budget.standing_lines(SimWorld(game))})
game.civ["standing_army"] = opening_army

# ---- revenue is the economy's yield, spending is the standing need ----------------------------
# (this one year also serves the labour-pool and goods-market sections below, which read the same year's result)
revenue = SimWorld(game).state_revenue()
standing = budget.standing_lines(SimWorld(game))
standing_purposes = {line.name for line in standing}
soldiers_free_before = game.labour.market_supply("soldier")
scribes_before = game.actor_staff_fte("scribe")
iron_demand_before_buying = sum(1 for bid in game.bids if bid[1] == "iron")
one_year(game)
income, outlays = treasury.record.income, treasury.record.outlays
need = sum(treasury.record.need.values())   # the year's standing need after the state's stores drew on it (a store-fed line asks the purse for nothing)
check("the state's revenue is booked as income from taxation, less what it took in kind",
      abs(income.get("taxation", 0.0) + sum(treasury.record.revenue_in_kind.values()) - revenue) < 1e-6 * revenue,
      (income, treasury.record.revenue_in_kind, revenue))
bid_money = sum(money for buyer, _commodity, _tonnes, money in game.bids if buyer == treasury.actor_id)
check("the state spends its standing need, by purpose: outlays now, and bids for the goods it buys",
      outlays.get("army", 0.0) > 0.0 and outlays.get("administration", 0.0) > 0.0
      # a surplus also raises named works (building ...), and thieves and coin guards take their cut: none is a standing need
      and abs(sum(money for purpose, money in outlays.items() if purpose in standing_purposes) + bid_money - need) < 0.02 * need,
      (outlays, bid_money, need))
check("a state in surplus keeps the difference as reserve and the ledger balances",
      abs(treasury.money - (sum(income.values()) - sum(outlays.values()))) < 1e-6 * revenue
      and treasury.money > 0.0, (treasury.money, income, outlays))
check("a state that paid all it needs records no unfunded need",
      not any(treasury.record.unfunded.values()), treasury.record.unfunded)

# ---- a deficit is financed from the reserve first, then spending is cut ----------------------
heavy, heavy_treasury = budget_sim(army=HEAVY_ARMY, cut_when_short=True)  # a force the revenue cannot carry
revenue = SimWorld(heavy).state_revenue()
heavy_lines = budget.standing_lines(SimWorld(heavy))
need = sum(line.money for line in heavy_lines)
check("the heavy army is a real deficit", need > 2.0 * revenue, (need, revenue))
reserve = 0.4 * (need - revenue)
heavy_treasury.money = reserve
one_year(heavy)
need = sum(heavy_treasury.record.need.values())   # the year's need after the state's stores drew on it
heavy_bids = sum(money for buyer, _commodity, _tonnes, money in heavy.bids if buyer == heavy_treasury.actor_id)
heavy_outlays = heavy_treasury.record.outlays
on_lines = sum(heavy_outlays.get(line.name, 0.0) for line in heavy_lines)
off_lines = sum(heavy_outlays.values()) - on_lines   # lending, theft and the guards of coin are not the lines it keeps up
check("a reserve that covers part of the deficit is all committed: the purse keeps only the bids not yet paid, "
      "less what left outside the lines",
      abs(heavy_treasury.money - heavy_bids + off_lines) < 1e-6 * need, (heavy_treasury.money, heavy_bids, off_lines))
spent = on_lines + heavy_bids
check("spending on the lines is cut to what revenue and reserve afford",
      abs(spent - (heavy_treasury.record.income.get("taxation", 0.0) + reserve)) < 1e-6 * need,
      (spent, heavy_treasury.record.income, reserve))
check("the cut is recorded as unfunded need, by line",
      abs(sum(heavy_treasury.record.unfunded.values()) - (need - spent)) < 1e-6 * need
      and all(heavy_treasury.record.unfunded[name] > 0.0 for name, owed in heavy_treasury.record.need.items() if owed > 0.0),
      heavy_treasury.record.unfunded)
rich, treasury_rich = budget_sim(army=HEAVY_ARMY)
treasury_rich.money = 10.0 * need
one_year(rich)
check("a reserve big enough finances the whole deficit and leaves nothing unfunded",
      not any(treasury_rich.record.unfunded.values())
      and treasury_rich.money < 10.0 * need, (treasury_rich.money, treasury_rich.record.unfunded))

# ---- spending reaches the labour pool --------------------------------------------------------
check("the army's and the officials' staff are held in the government's workforce",
      treasury.workforce.get("soldier", 0.0) > 0.0 and treasury.workforce.get("scribe", 0.0) > 0.0,
      treasury.workforce)
reach = game.labour.reachable_trade_population("soldier") + game.actor_staff_fte("soldier")
labour_reach = game.labour.reachable_trade_population("labourer") + game.actor_staff_fte("labourer")
share_of_nation = game.civ["standing_army"] / game.civ["population"] * game.population.total / game.population.working_age
army_share = lines["army"].labour["soldier"] / game.population.working_age
other_labourers = sum(line.labour.get("labourer", 0.0) for line in budget.standing_lines(SimWorld(game))[1:])
check("the state takes the same share of the founder's local pool as of the nation's working people",
      abs(treasury.workforce["soldier"] - army_share * reach) < 1e-6 * reach
      and abs(treasury.workforce["labourer"] - other_labourers / game.population.working_age * labour_reach) < 1e-6 * labour_reach,
      (treasury.workforce, share_of_nation, reach))
check("what the state employs is no longer on offer to the founder",
      game.actor_staff_fte("scribe") > scribes_before and game.labour.market_supply("soldier") < soldiers_free_before,
      (game.actor_staff_fte("scribe"), game.labour.market_supply("soldier"), soldiers_free_before))
unfunded_game, unfunded_treasury = budget_sim(army=HEAVY_ARMY, purse=0.0)
one_year(unfunded_game)
check("a state that cut its spending employs correspondingly fewer people",
      unfunded_treasury.workforce["soldier"] < 0.5 * (unfunded_game.labour.reachable_trade_population("soldier")
                                                     + unfunded_game.actor_staff_fte("soldier")),
      unfunded_treasury.workforce)

# ---- spending reaches the goods market -------------------------------------------------------
check("before the state buys anything it bids for nothing", iron_demand_before_buying == 0.0)
tonnes = sum(bid_tonnes for buyer, commodity, bid_tonnes, _money in game.bids
             if buyer == treasury.actor_id and commodity == "iron")
check("the state's iron purchases are bids in the agent economy's book", tonnes > 0.0, tonnes)
check("the demand is what the army's equipment needs, funded",
      abs(tonnes - sum(budget.standing_lines(SimWorld(game))[0].materials.values())) < 1e-6 * tonnes, tonnes)
huge, huge_treasury = budget_sim(army=3.0e8, purse=1.0e18)
one_year(huge)
huge_tonnes = sum(bid_tonnes for buyer, commodity, bid_tonnes, _money in huge.bids
                  if buyer == huge_treasury.actor_id and commodity == "iron")
check("a state with a great army bids for a great deal more iron (the price it raises is the economy's, "
      "test_economy_agent_state.py)", huge_tonnes > 10.0 * tonnes, (huge_tonnes, tonnes))

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
    one_year(game)
    world = SimWorld(game)
    household_scale = world.visible_taxpayers()[0][0]
    for firm in game.actors.active_firms():
        firm.workforce["artisan"] = 2000.0  # a firm with a visible staff (its year clears it)
        # the year spends part of the purse, so set the purse to what makes the firm exactly as visible as the household
        low, high = 0.0, 1.0e12
        for _ in range(100):
            firm.money = (low + high) / 2.0
            if world.visible_scale_of(firm) < household_scale:
                low = firm.money
            else:
                high = firm.money
    world = SimWorld(game)
    # the state went short of `unfunded` and chose to raise it all by levy: the year's need is split across its lines
    record = game.state_treasury().record
    owed = sum(record.need.values())
    record.unfunded = {name: unfunded * amount / owed for name, amount in record.need.items()}
    record.fiscal_response = {"levy": unfunded}
    game.state_treasury().seek_shortfall(budget.standing_lines(world), world)
    return game


def ordinary(game):
    """The share of income the society pays the state, as it falls on a visible taxpayer."""
    return game.civ["starting_tax_share"] * game.state_reach() * game.notice_over(game.household_scale())


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
ruinous = short_of(1.0e3 * INCOME)   # far past what the visible income could raise, yet less than the whole need, so officials are still partly paid
requisition, office = ruinous.levy_shares(ruinous.household_scale(), 0.0)
requisition -= ordinary(ruinous)
check("army need is claimed as requisition and the officials' as office",
      requisition > 0.0 and office > 0.0 and requisition > office, (requisition, office))
below = unopened_sim()
below.civ["standing_army"] = HEAVY_ARMY
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
# ---- the books survive save and load ----------------------------------------------------------
before = copy.deepcopy(needy.state.actors.records)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(needy, path)
    revived = below   # any game takes a load: the save replaces its state
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
army_game, army_treasury = budget_sim()
wanted = SimWorld(army_game).army_wanted()
one_year(army_game)
check("a state that pays for its army keeps the force it wants", abs(army_treasury.record.army - wanted) < 1e-6 * wanted,
      (army_treasury.record.army, wanted))
