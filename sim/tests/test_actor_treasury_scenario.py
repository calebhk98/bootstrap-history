"""SCENARIO (Complaint 185): in a whole game the household pays into debt, the yearly life of the actors books taxation,
takings and upkeep through the ledger, the state's pressure on the founder reaches the government, and the ledgers
round-trip through save and load. The ledger's own rules are in test_actor_treasury."""
import copy
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents.api import ledger
from sim.engine.agents_port import SimWorld
from sim.engine.saveload import load_state, save_state

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and node["cap"] >= 0)


def make_node(node_id, traits=(), revenue=0.0, upkeep=0.0, hours=400.0, years=2.0):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=list(traits), pre=[], lab={"labourer": hours},
                mat={}, rev=revenue, up=upkeep, yrs=years, risk=0.0, ph=0.0,
                dev_years=None, dev_people=None)
    node.pop("gains", None)
    return node


def actor_sim(extra_nodes):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"))
    game.goal, game.done_year = GOAL, {}
    return game


def grown(civ, employees=2000.0, capital=1.0e10, eminence=100.0, events=False):
    """A household large enough that the state has noticed it."""
    game = sim(civ=civ, events=events)
    game.employees["artisan"] = employees
    game.labour._resync_pools()
    game.capital = capital
    game.eminence = eminence
    game.update_protection()
    return state_seeking(game)


class AlwaysFires(random.Random):
    def random(self):
        return 0.0


def government_of(game):
    return game.actors.government(str(game.civ["id"]))


def ledger_balances(actor, opening=0.0):
    income = sum(actor.record.income.values())
    outlays = sum(actor.record.outlays.values())
    return abs(actor.money - (opening + income - outlays)) <= 1e-6 * max(1.0, abs(actor.money))


# ---- scenario: the founder's household pays what it owes even into debt, exactly as its purse always did
game = actor_sim([])
treasury = game.actors.ensure_government("rome_100ad")
household = game.household
capital_before = household.money
ledger.transfer(household, treasury, capital_before * 3.0, "confiscation")
check("scenario: the household pays what it owes even into debt, and the treasury receives it",
      household.money < 0.0 and abs(treasury.money - capital_before * 3.0) < 1e-6 * capital_before, (household.money, treasury.money))

# ---- the yearly life of the actors goes through the ledger -------------------------
mill_id = "test_treasury_mill"
mill = make_node(mill_id, traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)
game = actor_sim([mill])
# a node earns only from output, which the game derives at its start; this fixture states the takings and upkeep it
# wants booked, in hours, so they survive the repricing when the economy opens
# its takings are a multiple of what its crew is paid, since the opening's pay for a trade is whatever that trade's
# scarcity makes it and a firm enters only where the niche pays its crew
hour = game.labour.money_per_labour_hour()
takings = max(5000.0, 10.0 * SimWorld(game).concern_wage_bill(mill_id))
game.nodes[mill_id].update(rev=takings, up=100.0, rev_hours=takings / hour, up_hours=100.0 / hour)
year = game.state.scenario.year
game.state.projects.done.add(mill_id)
game.state.projects.done_year[mill_id] = year - 6
game.state.projects.operating.add(mill_id)
game.state.projects.business.set_opened_year(mill_id, year - 6)
game._done_changed()
for _ in range(6):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)
treasury = government_of(game)
firms = game.actors.of_kind("firm")
check("scenario: over six years the state's revenue is booked as income from taxation, the firm that ran the mill has "
      "takings and upkeep in its books, every actor's copying spend is an outlay, and each actor's purse equals its ledger",
      treasury.record.income.get("taxation", 0.0) > 0.0 and bool(firms)
      and firms[0].record.income.get("takings", 0.0) > 0.0 and firms[0].record.outlays.get("upkeep", 0.0) > 0.0
      and all(actor.record.outlays.get("copying", 0.0) > 0.0 for actor in [treasury] + firms if actor.works or actor.knowledge)
      and ledger_balances(treasury) and all(ledger_balances(f) for f in firms),
      [(a.actor_id, a.money, a.record.income, a.record.outlays) for a in [treasury] + firms])

# ---- what the state takes from the founder reaches the government -------------------
levied = grown("rome_100ad")
treasury = government_of(levied)
capital_before, treasury_before = levied.capital, treasury.money
revenue = max(0.0, levied.revenue())
req_share, _why = levied.requisition_report()
off_share, _name = levied.office_report()
levied._state_pressure(levied.year)
paid = capital_before - levied.capital
quiet = sim(civ="rome_100ad")
quiet_treasury = government_of(quiet)
quiet._state_pressure(quiet.year)
check("scenario: the founder is charged requisition and the pressed office, the government receives exactly that and "
      "books the two separately; a household the state has not noticed pays nothing",
      abs(paid - (req_share + off_share) * revenue) < 1e-6 * max(1.0, paid) and paid > 0.0
      and abs((treasury.money - treasury_before) - paid) < 1e-6 * max(1.0, paid)
      and abs(treasury.record.income.get("requisition", 0.0) - req_share * revenue) < 1e-6 * max(1.0, paid)
      and abs(treasury.record.income.get("office", 0.0) - off_share * revenue) < 1e-6 * max(1.0, paid)
      and quiet_treasury.money == 0.0 and not quiet_treasury.record.income,
      (paid, req_share, off_share, revenue, treasury.record.income, quiet_treasury.record.income))

drawn = grown("rome_100ad", events=True)
drawn.rng = AlwaysFires(1)
drawn.military_demand_eligible = lambda: True  # the state can fight and has noticed the household
treasury = government_of(drawn)
treasury.record.unfunded = {"army": 1.0e5}  # the state could not pay for its army
treasury.record.levy_base = 1.0e6
capital_before, treasury_before = drawn.capital, treasury.money
drawn._state_pressure(drawn.year)
paid = capital_before - drawn.capital
check("scenario: military supply and confiscation, when they fall, are received too, and the founder's loss equals the "
      "treasury's gain",
      treasury.record.income.get("military supply", 0.0) > 0.0
      and treasury.record.income.get("confiscation by the state", 0.0) > 0.0
      and abs((treasury.money - treasury_before) - paid) < 1e-6 * max(1.0, paid),
      (treasury.record.income, treasury.money - treasury_before, paid))

# ---- the ledger is saved and loaded ---------------------------------------------------
game = levied
game._state_pressure(game.year)
game.advance_actors(game.state.scenario.year)
before = copy.deepcopy(game.state.actors.records)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = sim(civ="rome_100ad")
    load_state(revived, path)
check("scenario: the income and outlay ledgers round-trip through save and load",
      revived.state.actors.records == before and bool(
          revived.state.actors.records["government:rome_100ad"].income),
      revived.state.actors.records.get("government:rome_100ad"))
