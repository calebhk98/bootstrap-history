"""Complaints 103 and 185: firms draw on the same labour pool as the founder,
the state assesses every actor by one rule, and firm output reaches the market.

The state's assessment is tested between actors built here with a stand-in for the world's levy rule; the pool,
the wage, the market and the shared category are named scenarios on a game."""
from types import SimpleNamespace

import copy
import random

from .harness import *  # noqa: F401,F403

from sim.agents.api import ActorRegistry, ActorsState, ledger
from sim.engine.agents_port import SimWorld
from sim.engine.state import ActorRecord

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if not node["pre"] and node["cap"] >= 0)


def make_node(node_id, category=None, revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0,
              lab=None):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=["commerce"], pre=[], lab=lab or {"labourer": hours},
                mat={}, rev=revenue, up=upkeep, yrs=years, risk=0.0, ph=0.0,
                dev_years=None, dev_people=None, sch=0.0)
    node.pop("gains", None)
    if category:
        node["cat"] = category
    return node


def actor_sim(extra_nodes, civ="rome_100ad"):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    game = build_unopened(lambda: S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
                 civ=S.load_civ(civ)))
    game.goal, game.done_year = GOAL, {}
    return game


def founder_runs(game, node_id, opened_ago=0):
    year = game.state.scenario.year
    projects = game.state.projects
    projects.done.add(node_id)
    projects.done_year[node_id] = year - opened_ago
    projects.operating.add(node_id)
    projects.business.set_opened_year(node_id, year - opened_ago)
    game._done_changed()


def firm_runs(game, firm_id, node_id, money=1.0e6, opened_ago=5):
    firm = game.actors.add(firm_id, ActorRecord(kind="firm", money=money, target=node_id))
    firm.business.open_plant(node_id, game.state.scenario.year - opened_ago)
    firm.knowledge.add(node_id)
    return firm


def next_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


from sim.unit_conversions import HOURS_PER_PERSON_YEAR as HOURS

# ---- labour: a firm's staff come out of the pool the founder hires from ------------------
game = actor_sim([])
trade = "smith"
supply_before = game.labour.market_supply(trade)
exist_before = game.labour.people_who_exist(trade)
price_before = game.labour.market.price_factor(trade)
firm = game.actors.add("firm:smiths", ActorRecord(kind="firm", money=1.0e6))
firm.workforce[trade] = 5.0
game.actors.refresh_staff()
staffed_fte = game.actor_staff_fte(trade)
staffed_supply = game.labour.market_supply(trade)
staffed_hire = game.labour.hire_check(trade, exist_before - 3.0)
firm.workforce[trade] = 0.0
game.actors.refresh_staff()
check("scenario: a firm's staff are counted against the same trade's pool, shrink the reachable pool the founder hires "
      "from by what the firm employs and are not available to the founder to hire; when the firm lets them go the pool "
      "is the founder's again",
      abs(staffed_fte - 5.0) < 1e-9
      and (staffed_supply < supply_before and abs((supply_before - staffed_supply) - 5.0 * HOURS) < 1e-6 or staffed_supply == 0.0)
      and staffed_hire[2] is not None
      and abs(game.labour.market_supply(trade) - supply_before) < 1e-6,
      (staffed_fte, supply_before, staffed_supply, staffed_hire, game.labour.market_supply(trade)))

# ---- labour: a firm hiring bids up the wage the founder pays -----------------------------
mill = make_node("test_mill", revenue=5000.0, lab={"labourer": 100.0, "smith": 40.0, "artisan": 20.0})
game = actor_sim([mill])
founder_runs(game, "test_mill", opened_ago=6)
trade_held, _fte = game.venture_foreman("test_mill")
price_before = game.labour.market.price_factor("smith")
firm = firm_runs(game, "firm:mill", "test_mill")
next_year(game)
priced_after_hiring = game.labour.market.price_factor("smith")
staff_year_one = dict(firm.workforce)
next_year(game)
check("scenario: a firm running a concern needing a skilled foreman holds the staff the concern needs, counted in the "
      "pool the founder competes in, hiring raises what the founder pays for that trade, and keeping the same staff the "
      "next year is not hiring more",
      trade_held == "smith" and firm.workforce.get("smith", 0.0) > 0.0
      and game.actor_staff_fte("smith") >= firm.workforce["smith"] - 1e-9
      and priced_after_hiring > price_before
      and all(abs(firm.workforce.get(trade, 0.0) - people) < 1e-9 for trade, people in staff_year_one.items()),
      (trade_held, firm.workforce, price_before, priced_after_hiring, staff_year_one))

# ---- labour: with nobody left to hire the firm runs short and earns less -----------------
game = actor_sim([mill])
founder_runs(game, "test_mill", opened_ago=6)
well_staffed = firm_runs(game, "firm:full", "test_mill")
next_year(game)
full_takings = well_staffed.record.income.get("takings", 0.0)
game = actor_sim([mill])
founder_runs(game, "test_mill", opened_ago=6)
game.labour.people_who_exist = lambda trade: 0.0
short = firm_runs(game, "firm:short", "test_mill")
next_year(game)
check("scenario: a firm that cannot find its staff in the pool earns less than one that can",
      0.0 <= short.record.income.get("takings", 0.0) < full_takings,
      (short.record.income.get("takings", 0.0), full_takings))

# ---- one rule assesses every actor (actors built here; the world answers the levy rule)
registry = ActorRegistry(ActorsState(home_country="home"))
state_actor = registry.ensure_government("home")
scales = {}
SCALE_LINE = 0.5


def levy_world():
    return SimpleNamespace(
        visible_scale_of=lambda payer: scales[payer.actor_id],
        levy_shares=lambda scale, protection: (0.10 * scale, 0.05 * scale) if scale > SCALE_LINE else (0.0, 0.0))


def taxpayer(actor_id, scale):
    scales[actor_id] = scale
    return registry.add(actor_id, ActorRecord(kind="firm", money=1.0e6))


rich = taxpayer("firm:rich", 0.8)
twin = taxpayer("firm:twin", 0.8)
small = taxpayer("firm:small", 0.1)
levy_of = lambda payer, taxable=1.0e6: state_actor.assess(payer, taxable, levy_world())
check("two taxpayers of equal visible scale are assessed equally, and by the levy rule of that scale",
      levy_of(rich) == levy_of(twin) and levy_of(rich)[0] > 0.0
      and abs(levy_of(rich)[0] - (0.10 + 0.05) * 0.8 * 1.0e6) < 1e-6, levy_of(rich))
check("a taxpayer the state has not noticed pays nothing", levy_of(small)[0] == 0.0, levy_of(small))
check("a levy is by purpose: requisition and office, each a share of the taxable income",
      abs(levy_of(rich)[1]["requisition"] - 0.08 * 1.0e6) < 1e-6 and abs(levy_of(rich)[1]["office"] - 0.04 * 1.0e6) < 1e-6
      and levy_of(rich, -5.0)[0] == 0.0, levy_of(rich))
treasury_before = state_actor.money
payer_before = rich.money
collected = state_actor.collect(rich, 1.0e6, levy_world())
check("collecting a levy moves exactly what it took from the payer to the treasury, booked by purpose",
      collected > 0.0 and abs((payer_before - rich.money) - collected) < 1e-6
      and abs((state_actor.money - treasury_before) - collected) < 1e-6
      and abs(sum(rich.record.outlays.values()) - collected) < 1e-6, (collected, rich.record.outlays))

# ---- scenario: the game's levy rule is one function of headcount, wealth and eminence for any taxpayer
game = state_seeking(actor_sim([]))
treasury = game.state_treasury()
scale_of_founder = game.visible_scale(2000.0, 60000000.0, 0.0)
rich_firm = game.actors.add("firm:rich", ActorRecord(kind="firm", money=60000000.0))
rich_firm.workforce["labourer"] = 2000.0
small_firm = game.actors.add("firm:small", ActorRecord(kind="firm", money=1000.0))
small_firm.workforce["labourer"] = 2.0
world = SimWorld(game)
rich_levy = treasury.assess(rich_firm, 1.0e6, world)[0]
small_levy = treasury.assess(small_firm, 1.0e6, world)[0]
founder_scale_matches = abs(game.household_scale() - game.visible_scale(
    game.labour.headcount(), game.state.household.capital, game.state.household.eminence)) == 0.0
founder_rate = sum(game.levy_shares(scale_of_founder))
game.state_reach = lambda: 0.0
world = SimWorld(game)
check("scenario: in a game the scale is one function for any taxpayer and the founder's own, a firm of the founder's "
      "visible scale is assessed at the founder's rate, a small firm pays nothing, and a state with no capacity collects "
      "nothing from anyone",
      game.visible_scale(10.0, 100.0, 0.0) < scale_of_founder and founder_scale_matches
      and abs(rich_levy - founder_rate * 1.0e6) < 1e-6 and rich_levy > 0.0
      and small_levy == 0.0
      and treasury.assess(rich_firm, 1.0e6, world)[0] == 0.0 and sum(game.levy_shares(scale_of_founder)) == 0.0,
      (rich_levy, small_levy, scale_of_founder))

game = state_seeking(actor_sim([mill]))
founder_runs(game, "test_mill", opened_ago=6)
taxed = firm_runs(game, "firm:taxed", "test_mill", money=60000000.0)
taxed.workforce["labourer"] = 2000.0
treasury = game.state_treasury()
income_before = dict(treasury.record.income)
taxed.operate(SimWorld(game))
paid = taxed.record.outlays.get("requisition", 0.0) + taxed.record.outlays.get("office", 0.0)
received = (treasury.record.income.get("requisition", 0.0) + treasury.record.income.get("office", 0.0)
            - income_before.get("requisition", 0.0) - income_before.get("office", 0.0))
check("scenario: a firm's margin pays the levy into the treasury, money is conserved and the firm's purse still equals its ledger",
      paid > 0.0 and abs(paid - received) < 1e-6 * max(1.0, paid)
      and abs(taxed.money - (60000000.0 + sum(taxed.record.income.values())
                             - sum(taxed.record.outlays.values()))) < 1e-3, (paid, received))

# ---- firm output reaches the market -------------------------------------------------------
furnace_node = "blast_furnace"
game = actor_sim([])
firm_world = SimWorld(game)
nothing_supplied = noted_sale_tonnes(game, "pig_iron_kg") == 0.0
one = game.actors.add("firm:iron1", ActorRecord(kind="firm", money=1.0e6))
one.business.open_plant(furnace_node, game.state.scenario.year - 10)
one.sell_output(firm_world)
supply_one = noted_sale_tonnes(game, "pig_iron_kg")
two = game.actors.add("firm:iron2", ActorRecord(kind="firm", money=1.0e6))
two.business.open_plant(furnace_node, game.state.scenario.year - 10)
two.sell_output(firm_world)
supply_two = noted_sale_tonnes(game, "pig_iron_kg")
one.concerns.clear()
two.concerns.clear()
game.state.scenario.year += 1
supply_next_year = noted_sale_tonnes(game, "pig_iron_kg")
for closed in (one, two):
    firm_world.market_forget(closed.actor_id)
    closed.sell_output(firm_world)
check("scenario: firms running a furnace that declares physical output note the material for the year's market, "
      "the noted supply sums every actor's output and stands into the next year until the firm deals again, a closed "
      "concern stops supplying, and a material nobody makes has no noted supply",
      NODES[furnace_node].get("annual_output_t", 0) > 0 and nothing_supplied and supply_one > 0.0
      and abs(supply_two - 2.0 * supply_one) < 1e-9 and abs(supply_next_year - 2.0 * supply_one) < 1e-9
      and noted_sale_tonnes(game, "pig_iron_kg") == 0.0 and noted_sale_tonnes(game, "no_such_material_kg") == 0.0,
      (nothing_supplied, supply_one, supply_two, supply_next_year))

loom = make_node("test_loom", category="textiles", revenue=8000.0)
game = actor_sim([loom])
founder_runs(game, "test_loom", opened_ago=6)
alone = game.goods_category_factor("textiles")
firm = firm_runs(game, "firm:loom", "test_loom")
shared = game.goods_category_factor("textiles")
world = SimWorld(game)
ramped = game.concern_takings("test_loom", 1.0)
shared_takings = world.concern_takings("test_loom", game.state.scenario.year - 5)
firm.concerns.clear()
check("scenario: a firm selling into the same category lowers the founder's share of its market, a firm's takings come "
      "out of the same shared market as the founder's, and when the firm closes the founder has the market back",
      shared < alone and abs(shared_takings - ramped * shared) < 1e-6 * ramped
      and abs(game.goods_category_factor("textiles") - alone) < 1e-9,
      (shared, alone, shared_takings, ramped * shared))
