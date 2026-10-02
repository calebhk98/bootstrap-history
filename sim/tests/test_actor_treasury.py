"""Complaint 185: money moves between actors through a ledger, and the state's
takings from the founder are received by the government actor."""
import copy
import json
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents import Household, ledger
from sim.engine.saveload import load_state, save_state
from sim.engine.state import ActorRecord

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)


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
    game._resync_pools()
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


# ---- a transfer between any two actors conserves money ----------------------------
game = actor_sim([])
registry = game.actors
treasury = registry.ensure_government("rome_100ad")
firm = registry.add("firm:payer", ActorRecord(kind="firm", money=500.0))
household = game.household
capital_before = household.money
ledger.transfer(household, treasury, 40.0, "requisition")
check("a transfer debits the payer and credits the payee by the same amount",
      household.money == capital_before - 40.0 and treasury.money == 40.0,
      (household.money, treasury.money))
ledger.transfer(firm, treasury, 100.0, "taxation")
check("a recorded payer keeps an outlay and a recorded payee an income, by purpose",
      firm.record.outlays == {"taxation": 100.0}
      and treasury.record.income == {"requisition": 40.0, "taxation": 100.0},
      (firm.record.outlays, treasury.record.income))
check("a transfer never creates or destroys money",
      abs((household.money + treasury.money + firm.money) - (capital_before + 500.0)) < 1e-9,
      (household.money, treasury.money, firm.money))
ledger.transfer(household, treasury, capital_before * 3.0, "confiscation")
check("a household pays what it owes even into debt, exactly as its purse always did",
      household.money < 0.0 and treasury.money > capital_before, (household.money, treasury.money))
check("a recorded actor's purse is its opening money plus income less outlays",
      ledger_balances(treasury) and ledger_balances(firm, 500.0))

# ---- the yearly life of the actors goes through the ledger -------------------------
mill = make_node("test_treasury_mill", traits=["commerce"], revenue=5000.0, upkeep=100.0,
                 hours=100.0, years=1.0)
game = actor_sim([mill])
year = game.state.scenario.year
game.state.projects.done.add("test_treasury_mill")
game.state.projects.done_year["test_treasury_mill"] = year - 6
game.state.projects.operating.add("test_treasury_mill")
game.state.projects.opened_year["test_treasury_mill"] = year - 6
game._done_changed()
for _ in range(6):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)
treasury = government_of(game)
firms = game.actors.of_kind("firm")
check("the state's yearly revenue is booked as income from taxation",
      treasury.record.income.get("taxation", 0.0) > 0.0, treasury.record.income)
check("a firm was founded and ran, so its books have takings and upkeep",
      bool(firms) and firms[0].record.income.get("takings", 0.0) > 0.0
      and firms[0].record.outlays.get("upkeep", 0.0) > 0.0,
      [(f.actor_id, f.record.income, f.record.outlays) for f in firms])
check("every actor's copying spend is an outlay, so no money moves off the books",
      all(actor.record.outlays.get("copying", 0.0) > 0.0 for actor in [treasury] + firms
          if actor.works or actor.knowledge),
      [(a.actor_id, a.record.outlays) for a in [treasury] + firms])
check("across the years each actor's purse equals its ledger",
      ledger_balances(treasury) and all(ledger_balances(f) for f in firms),
      [(a.actor_id, a.money, sum(a.record.income.values()), sum(a.record.outlays.values()))
       for a in [treasury] + firms])

# ---- what the state takes from the founder reaches the government -------------------
levied = grown("rome_100ad")
treasury = government_of(levied)
capital_before, treasury_before = levied.capital, treasury.money
revenue = max(0.0, levied.revenue())
req_share, _why = levied.requisition_report()
off_share, _name = levied.office_report()
levied._state_pressure(levied.year)
paid = capital_before - levied.capital
check("the founder is charged requisition and the pressed office as before",
      abs(paid - (req_share + off_share) * revenue) < 1e-6 * max(1.0, paid) and paid > 0.0,
      (paid, req_share, off_share, revenue))
check("what the founder paid is what the government received",
      abs((treasury.money - treasury_before) - paid) < 1e-6 * max(1.0, paid),
      (treasury.money - treasury_before, paid))
check("the treasury books requisition and office separately",
      abs(treasury.record.income.get("requisition", 0.0) - req_share * revenue) < 1e-6 * max(1.0, paid)
      and abs(treasury.record.income.get("office", 0.0) - off_share * revenue) < 1e-6 * max(1.0, paid),
      treasury.record.income)

drawn = grown("rome_100ad", events=True)
drawn.rng = AlwaysFires(1)
drawn.military_demand_eligible = lambda: True  # the state can fight and has noticed the household
treasury = government_of(drawn)
treasury.record.unfunded = {"army": 1.0e5}  # the state could not pay for its army
treasury.record.levy_base = 1.0e6
capital_before, treasury_before = drawn.capital, treasury.money
drawn._state_pressure(drawn.year)
paid = capital_before - drawn.capital
check("military supply and confiscation, when they fall, are received too",
      treasury.record.income.get("military supply", 0.0) > 0.0
      and treasury.record.income.get("confiscation", 0.0) > 0.0, treasury.record.income)
check("with every levy the founder's loss equals the treasury's gain",
      abs((treasury.money - treasury_before) - paid) < 1e-6 * max(1.0, paid),
      (treasury.money - treasury_before, paid))

quiet = sim(civ="rome_100ad")
treasury = government_of(quiet)
quiet._state_pressure(quiet.year)
check("a household the state has not noticed pays nothing and the treasury is untouched",
      treasury.money == 0.0 and not treasury.record.income, treasury.record.income)

# ---- the ledger is saved and loaded ---------------------------------------------------
game = grown("rome_100ad")
game._state_pressure(game.year)
game.advance_actors(game.state.scenario.year)
before = copy.deepcopy(game.state.actors.records)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = sim(civ="rome_100ad")
    load_state(revived, path)
check("the income and outlay ledgers round-trip through save and load",
      revived.state.actors.records == before and bool(
          revived.state.actors.records["government:rome_100ad"].income),
      revived.state.actors.records.get("government:rome_100ad"))
