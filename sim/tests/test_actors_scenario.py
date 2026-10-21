"""SCENARIO (actors): in a whole game the founder's household is an Actor on the game's own state, the government copies
what it values through the years the game keeps and leaves the founder's purse alone, firms enter a proven concern and
leave when it loses, and actor records round-trip through save and load. What an actor values, copies and fails at is in
test_actors."""
import copy
import json
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents.api import Actor
from sim.agents.policy import IdlePolicy
from sim.engine.state import ActorRecord
from sim.engine.saveload import load_state, save_state

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if not node["pre"] and node["cap"] >= 0)


def make_node(node_id, traits=(), gains=None, revenue=0.0, upkeep=0.0, hours=400.0,
              years=2.0, prerequisites=(), risk=0.0):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=list(traits), pre=list(prerequisites),
                lab={"labourer": hours}, mat={}, rev=revenue, up=upkeep, yrs=years,
                risk=risk, ph=0.0, dev_years=None, dev_people=None, cap=0.0, art=0.2, sch=0.0)
    node.pop("gains", None)
    if gains is not None:
        node["gains"] = gains
    return node


def actor_sim(extra_nodes):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    game = build_unopened(lambda: S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad")))
    game.goal, game.done_year = GOAL, {}
    return game


def founder_completes(game, node_id, operating=False, opened_ago=0):
    year = game.state.scenario.year
    game.state.projects.done.add(node_id)
    game.state.projects.done_year[node_id] = year - opened_ago
    if operating:
        game.state.projects.operating.add(node_id)
        game.state.projects.business.set_opened_year(node_id, year - opened_ago)
    game._done_changed()


def next_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


# ---- scenario: the household is an Actor on the game's own state ---------------------------------------------------
game = actor_sim([])
household = game.household
household.money = 1234.0
check("scenario: the founder's household is an Actor whose money, staff, knowledge and concerns are its existing state, "
      "and which never chooses through a policy of its own",
      isinstance(household, Actor) and household.capital == 1234.0
      and household.workforce is household.employees and household.knowledge is household.done
      and household.concerns is household.operating and isinstance(household.decision_policy, IdlePolicy)
      and all(hasattr(household, name) for name in ("money", "workforce", "knowledge", "concerns", "works", "decision_policy")))

# ---- scenario: the state copies through the years the game keeps, and the founder's purse is left alone -------------
gun = make_node("test_gun", traits=["military"])
cartoons = make_node("test_cartoons", traits=["information"])
game = actor_sim([gun, cartoons])
for node_id in ("test_gun", "test_cartoons"):
    founder_completes(game, node_id, operating=True)
government = game.actors.ensure_government("rome_100ad")
government.money = 0.0
founder_purse = game.state.household.capital
next_year(game)
begun_after_one = (set(government.works), "test_gun" in government.knowledge)
next_year(game)
check("scenario: over the game's years the government begins copying what it values, finishes after the planned time "
      "and the founder's own purse is left alone",
      "test_gun" in begun_after_one[0] and "test_cartoons" not in government.works and not begun_after_one[1]
      and "test_gun" in government.knowledge and "test_gun" not in government.works
      and game.state.household.capital == founder_purse,
      (begun_after_one, sorted(government.knowledge), sorted(government.works)))

# ---- scenario: firms enter when a concern proves profitable, copy it, share its market and leave when it loses -------
profitable = make_node("test_mill", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)
losing = make_node("test_loss", traits=["commerce"], revenue=10.0, upkeep=400.0, hours=100.0, years=1.0)
fresh = make_node("test_fresh", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)
game = actor_sim([profitable, losing, fresh])
founder_completes(game, "test_mill", operating=True, opened_ago=6)
founder_completes(game, "test_loss", operating=True, opened_ago=6)
founder_completes(game, "test_fresh", operating=True, opened_ago=0)
game.advance_actors(game.state.scenario.year)   # the cast is seeded at the first actor year
ready_for_entry(game)
game.state.scenario.year += 1
game.advance_actors(game.state.scenario.year)
firms = game.actors.of_kind("firm")
entered_only_proven = bool(firms) and all(f.record.target == "test_mill" for f in firms)
next_year(game)
# the first entrant: ids sort as text, so the earliest founded is not always the first in id order
firm = min(game.actors.of_kind("firm"), key=lambda entrant: (entrant.record.founded_year, int(entrant.actor_id.split(":")[1])))
copied_and_running = "test_mill" in firm.knowledge and "test_mill" in firm.concerns
shares_market = game.actors.rivals_of("test_mill", firm.actor_id) >= 1
next_year(game)
check("scenario: a firm enters only a concern that has proved profitable, copies it by the ordinary rules and runs it, "
      "shares the market with the founder, earns takings less upkeep and leaves the founder's own concerns untouched",
      entered_only_proven and copied_and_running and shares_market and firm.record.last_margin != 0.0
      and "test_mill" in game.state.projects.operating,
      ([f.record.target for f in firms], firm.record.works, firm.concerns))

game = actor_sim([losing])
founder_completes(game, "test_loss", operating=True, opened_ago=6)
loser = game.actors.add("firm:loser", ActorRecord(kind="firm", money=1000.0, target="test_loss"))
loser.business.open_plant("test_loss", game.state.scenario.year - 6)
loser.knowledge.add("test_loss")
for _ in range(4):
    next_year(game)
check("scenario: a firm that keeps losing money closes", loser.record.exited_year is not None and not loser.concerns,
      (loser.record.loss_years, loser.record.exited_year))

# ---- scenario: persistence --------------------------------------------------------------------------------------------
extra_nodes = [make_node("test_gun", traits=["military"]), profitable,
               make_node("test_save_mill", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)]
game = actor_sim(extra_nodes)
founder_completes(game, "test_gun", operating=True)
founder_completes(game, "test_mill", operating=True, opened_ago=6)
game.state.scenario.year += 1
game.advance_actors(game.state.scenario.year)
next_year(game)
before = copy.deepcopy(game.state.actors.records)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    with open(path) as handle:
        saved = json.load(handle)
    revived = actor_sim(extra_nodes)
    load_state(revived, path)
kinds_after_load = [(a.actor_id, a.kind) for a in (revived.actors.of_kind("government") + revived.actors.of_kind("firm"))]
kinds_before = [(a.actor_id, a.kind) for a in (game.actors.of_kind("government") + game.actors.of_kind("firm"))]
next_year(revived)
next_year(game)
check("scenario: actor records are written to the save automatically, round-trip through save and load, rebuild the same "
      "kinds, and a loaded game goes on exactly as the original would",
      "actors" in saved and "government:rome_100ad" in saved["actors"]["records"]
      and revived.state.actors.records != {} and kinds_after_load == kinds_before
      and revived.state.actors.records == game.state.actors.records,
      (sorted(revived.state.actors.records), sorted(before)))

