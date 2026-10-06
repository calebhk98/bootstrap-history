"""Complaint 382 step 1: every money posting names a counterparty or a named edge.

Money changes a purse only through `ledger.transfer`; where the other side is not an actor the
simulation models, it is a named edge held in `state.actors.edges`. So all purses together plus all
edges together stay what they were, and a new one-sided posting fails the scan below."""
import os
import re

from .harness import *  # noqa: F401,F403

from sim.agents import ledger

SIM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCANNED = ("engine", "agents", "labour", "geography", "economy")
# the ledger itself, the purse's own methods, and the actors that delegate to the founder's purse
POSTING_WRITERS = {os.path.join("agents", "ledger.py"), os.path.join("engine", "state.py"),
                   os.path.join("agents", "household.py"), os.path.join("agents", "household_party.py")}
ONE_SIDED = re.compile(r"\.(credit|debit|add_capital|cost_capital|costCapital|reset_cash)\(")

offenders = []
for package in SCANNED:
    for folder, _dirs, files in os.walk(os.path.join(SIM_DIR, package)):
        for name in sorted(files):
            path = os.path.join(folder, name)
            relative = os.path.relpath(path, SIM_DIR)
            if not name.endswith(".py") or relative in POSTING_WRITERS:
                continue
            with open(path, encoding="utf-8") as source:
                for number, line in enumerate(source, 1):
                    if ONE_SIDED.search(line.split("#", 1)[0]):
                        offenders.append("%s:%d" % (relative, number))
check("no engine or agent code posts money to one side only", not offenders, offenders[:20])


def purses(game):
    return game.state.household.capital + sum(record.money for record in game.state.actors.records.values())


def edges(game):
    return sum(game.state.actors.edges.values())


def ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


for label, capital in (("a rich household", 300_000.0), ("a poor household", 2_000.0)):
    game = sim(capital=capital, manual=False, events=True)
    game.end_year = game.cfg["start_year"] + game.cfg["horizon_years"]
    opening = purses(game) + edges(game)
    years = 0
    for _year in range(6):
        ask(game, cmd="step", years=1)
        years += 1
        total = purses(game) + edges(game)
        if abs(total - opening) > 1e-6 * max(1.0, abs(opening)):
            break
        if not game.state.founder.founder_alive:
            break
    total = purses(game) + edges(game)
    check("%s: all purses and all named edges together stay what they were over %d years" % (label, years),
          abs(total - opening) <= 1e-6 * max(1.0, abs(opening)), (opening, total))
    check("%s: money moved through named edges" % label, bool(game.state.actors.edge_volume),
          game.state.actors.edge_volume)
    check("%s: every edge is named" % label, all(name.startswith("edge:") for name in game.state.actors.edges),
          sorted(game.state.actors.edges))

# an edge takes what a payer loses and gives what a payee gains, and keeps its volume
from sim.engine.state import ActorsState

state = ActorsState()
payer = type("Purse", (), {"money": 10.0})()
payer.debit = lambda amount, purpose: setattr(payer, "money", payer.money - amount)
payer.credit = lambda amount, purpose: setattr(payer, "money", payer.money + amount)
ledger.transfer(payer, state.edge("edge:test"), 4.0, "a payment")
ledger.transfer(state.edge("edge:test"), payer, 1.0, "a refund")
check("a payer's loss is the edge's gain", payer.money == 7.0 and state.edges["edge:test"] == 3.0, state.edges)
check("an edge keeps the volume that crossed it", state.edge_volume["edge:test"] == 5.0, state.edge_volume)
