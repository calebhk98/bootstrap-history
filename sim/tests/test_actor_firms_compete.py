"""Complaints 103 and 185: firms draw on the same labour pool as the founder,
the state assesses every actor by one rule, and firm output reaches the market."""
import copy
import random

from .harness import *  # noqa: F401,F403

from sim.engine.actors import SimWorld, ledger
from sim.engine.state import ActorRecord

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)


def make_node(node_id, category=None, revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0,
              lab=None):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=["commerce"], pre=[], lab=lab or {"labourer": hours},
                mat={}, rev=revenue, up=upkeep, yrs=years, risk=0.0, ph=0.0,
                dev_years=None, dev_people=None)
    node.pop("gains", None)
    if category:
        node["cat"] = category
    return node


def actor_sim(extra_nodes, civ="rome_100ad"):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
                 civ=S.load_civ(civ))
    game.goal, game.done_year = GOAL, {}
    return game


def founder_runs(game, node_id, opened_ago=0):
    year = game.state.scenario.year
    projects = game.state.projects
    projects.done.add(node_id)
    projects.done_year[node_id] = year - opened_ago
    projects.operating.add(node_id)
    projects.opened_year[node_id] = year - opened_ago
    game._done_changed()


def firm_runs(game, firm_id, node_id, money=1.0e6, opened_ago=5):
    firm = game.actors.add(firm_id, ActorRecord(kind="firm", money=money, target=node_id))
    firm.concerns.add(node_id)
    firm.knowledge.add(node_id)
    firm.record.opened_year[node_id] = game.state.scenario.year - opened_ago
    return firm


def next_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


HOURS = S.Sim.HOURS_PER_PERSON_YEAR

# ---- labour: a firm's staff come out of the pool the founder hires from ------------------
game = actor_sim([])
trade = "smith"
supply_before = game.market_supply(trade)
exist_before = game.people_who_exist(trade)
price_before = game.labour_price_factor(trade)
firm = game.actors.add("firm:smiths", ActorRecord(kind="firm", money=1.0e6))
firm.workforce[trade] = 5.0
game.actors.refresh_staff()
check("a firm's staff are counted against the same trade's pool",
      abs(game.actor_staff_fte(trade) - 5.0) < 1e-9, game.actor_staff_fte(trade))
check("the reachable pool the founder hires from shrinks by what a firm employs",
      game.market_supply(trade) < supply_before
      and abs((supply_before - game.market_supply(trade)) - 5.0 * HOURS) < 1e-6
      or game.market_supply(trade) == 0.0,
      (supply_before, game.market_supply(trade)))
check("a firm's employees are not available to the founder to hire",
      game.hire_check(trade, exist_before - 3.0)[2] is not None,
      game.hire_check(trade, exist_before - 3.0))
firm.workforce[trade] = 0.0
game.actors.refresh_staff()
check("when the firm lets them go the pool is the founder's again",
      abs(game.market_supply(trade) - supply_before) < 1e-6, (game.market_supply(trade), supply_before))

# ---- labour: a firm hiring bids up the wage the founder pays -----------------------------
mill = make_node("test_mill", revenue=5000.0, lab={"labourer": 100.0, "smith": 40.0, "artisan": 20.0})
game = actor_sim([mill])
founder_runs(game, "test_mill", opened_ago=6)
trade_held, _fte = game.venture_foreman("test_mill")
check("the test concern needs a skilled foreman trade", trade_held == "smith", trade_held)
price_before = game.labour_price_factor("smith")
firm = firm_runs(game, "firm:mill", "test_mill")
next_year(game)
check("a firm running a concern holds the staff that concern needs",
      firm.workforce.get("smith", 0.0) > 0.0, firm.workforce)
check("those staff count in the pool the founder competes in",
      game.actor_staff_fte("smith") >= firm.workforce["smith"] - 1e-9)
check("a firm hiring raises what the founder pays for the same trade",
      game.labour_price_factor("smith") > price_before,
      (game.labour_price_factor("smith"), price_before))
staff_year_one = dict(firm.workforce)
next_year(game)
check("keeping the same staff the next year is not hiring more",
      all(abs(firm.workforce.get(trade, 0.0) - people) < 1e-9 for trade, people in staff_year_one.items()),
      (firm.workforce, staff_year_one))

# ---- labour: with nobody left to hire the firm runs short and earns less -----------------
game = actor_sim([mill])
founder_runs(game, "test_mill", opened_ago=6)
well_staffed = firm_runs(game, "firm:full", "test_mill")
next_year(game)
full_takings = well_staffed.record.income.get("takings", 0.0)
game = actor_sim([mill])
founder_runs(game, "test_mill", opened_ago=6)
game.people_who_exist = lambda trade: 0.0
short = firm_runs(game, "firm:short", "test_mill")
next_year(game)
check("a firm that cannot find its staff in the pool earns less than one that can",
      0.0 <= short.record.income.get("takings", 0.0) < full_takings,
      (short.record.income.get("takings", 0.0), full_takings))

# ---- one rule assesses every actor -------------------------------------------------------
game = state_seeking(actor_sim([]))
treasury = game.state_treasury()
scale_of_founder = game.visible_scale(2000.0, 60000000.0, 0.0)
check("scale is one function of headcount, wealth and eminence for any taxpayer",
      abs(scale_of_founder - game.visible_scale(2000.0, 60000000.0, 0.0)) == 0.0
      and game.visible_scale(10.0, 100.0, 0.0) < scale_of_founder)
check("the founder's own scale is that same function",
      abs(game.household_scale() - game.visible_scale(
          game.headcount(), game.state.household.capital, game.state.household.eminence)) == 0.0)
rich_firm = game.actors.add("firm:rich", ActorRecord(kind="firm", money=60000000.0))
rich_firm.workforce["artisan"] = 2000.0
twin_firm = game.actors.add("firm:twin", ActorRecord(kind="firm", money=60000000.0))
twin_firm.workforce["artisan"] = 2000.0
world = SimWorld(game)
check("two firms of equal visible scale are assessed equally",
      treasury.assess(rich_firm, 1.0e6, world) == treasury.assess(twin_firm, 1.0e6, world)
      and treasury.assess(rich_firm, 1.0e6, world)[0] > 0.0, treasury.assess(rich_firm, 1.0e6, world))
check("a firm of the founder's visible scale is assessed at the founder's rate",
      abs(treasury.assess(rich_firm, 1.0e6, world)[0]
          - sum(game.levy_shares(game.visible_scale(2000.0, 60000000.0, 0.0))) * 1.0e6) < 1e-6)
small_firm = game.actors.add("firm:small", ActorRecord(kind="firm", money=1000.0))
small_firm.workforce["artisan"] = 2.0
check("a small firm the state has not noticed pays nothing", treasury.assess(small_firm, 1.0e6, world)[0] == 0.0)
game.state_capacity = 0.0
world = SimWorld(game)
check("a state with no capacity collects nothing from anyone",
      treasury.assess(rich_firm, 1.0e6, world)[0] == 0.0
      and sum(game.levy_shares(game.visible_scale(2000.0, 60000000.0, 0.0))) == 0.0)

game = state_seeking(actor_sim([mill]))
founder_runs(game, "test_mill", opened_ago=6)
taxed = firm_runs(game, "firm:taxed", "test_mill", money=60000000.0)
taxed.workforce["artisan"] = 2000.0
treasury = game.state_treasury()
income_before = dict(treasury.record.income)
taxed.operate(SimWorld(game))
paid = taxed.record.outlays.get("requisition", 0.0) + taxed.record.outlays.get("office", 0.0)
received = (treasury.record.income.get("requisition", 0.0) + treasury.record.income.get("office", 0.0)
            - income_before.get("requisition", 0.0) - income_before.get("office", 0.0))
check("a firm's margin pays the levy into the treasury and money is conserved",
      paid > 0.0 and abs(paid - received) < 1e-6 * max(1.0, paid), (paid, received))
check("the firm's purse still equals its ledger after paying the state",
      abs(taxed.money - (60000000.0 + sum(taxed.record.income.values())
                         - sum(taxed.record.outlays.values()))) < 1e-3)

# ---- firm output reaches the market -------------------------------------------------------
furnace_node = "blast_furnace"
check("the tree has a producer that declares physical output",
      NODES[furnace_node].get("annual_output_t", 0) > 0)
game = actor_sim([])
firm_world = SimWorld(game)
check("with no actors operating, nothing is supplied by actors", game.actor_supply("pig_iron_kg") == 0.0)
one = game.actors.add("firm:iron1", ActorRecord(kind="firm", money=1.0e6))
one.concerns.add(furnace_node)
one.record.opened_year[furnace_node] = game.state.scenario.year - 10
one.sell_output(firm_world)
supply_one = game.actor_supply("pig_iron_kg")
check("a firm running a furnace sells the material the furnace makes into the market", supply_one > 0.0, supply_one)
two = game.actors.add("firm:iron2", ActorRecord(kind="firm", money=1.0e6))
two.concerns.add(furnace_node)
two.record.opened_year[furnace_node] = game.state.scenario.year - 10
two.sell_output(firm_world)
check("actor supply sums every actor's output", abs(game.actor_supply("pig_iron_kg") - 2.0 * supply_one) < 1e-9,
      (game.actor_supply("pig_iron_kg"), supply_one))
one.concerns.clear()
two.concerns.clear()
check("a firm's output stands in the book into the next year until it deals again",
      game.state.scenario.__setattr__("year", game.state.scenario.year + 1) is None
      and abs(game.actor_supply("pig_iron_kg") - 2.0 * supply_one) < 1e-9)
for closed in (one, two):
    firm_world.market_forget(closed.actor_id)
    closed.sell_output(firm_world)
check("a closed concern stops supplying", game.actor_supply("pig_iron_kg") == 0.0)
check("a material nobody makes has no actor supply", game.actor_supply("no_such_material_kg") == 0.0)

loom = make_node("test_loom", category="textiles", revenue=8000.0)
game = actor_sim([loom])
founder_runs(game, "test_loom", opened_ago=6)
alone = game.goods_market_factor("test_loom")
firm = firm_runs(game, "firm:loom", "test_loom")
shared = game.goods_market_factor("test_loom")
check("a firm selling into the same category lowers the founder's share of its market",
      shared < alone, (shared, alone))
world = SimWorld(game)
ramped = game.concern_takings("test_loom", 1.0)
check("a firm's takings come out of the same shared market as the founder's",
      abs(world.concern_takings("test_loom", game.state.scenario.year - 5) - ramped * shared) < 1e-6 * ramped,
      (world.concern_takings("test_loom", game.state.scenario.year - 5), ramped * shared))
firm.concerns.clear()
check("when the firm closes the founder has the market back",
      abs(game.goods_market_factor("test_loom") - alone) < 1e-9)
