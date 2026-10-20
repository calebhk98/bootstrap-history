"""Actors: the shared base, the government and firm, imitation, and persistence.

What a government values, copies and fails at is tested between actors built here on the agents' stand-in world
(`agents_fake_world`); named scenarios run the household, the state's copying through the years, firms entering and
leaving, and persistence on a game."""
import copy
import json
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents.api import (Actor, ActorRegistry, ActorsState, CallbackPolicy, Firm, Government,
                               RecordedActor, register_policy)
from sim.engine.agents_port import SimWorld
from sim.agents import imitation
from sim.agents.policy import IdlePolicy
from sim.engine.state import ActorRecord
from sim.engine.mods import get_ordered_mods, load_mod_tree
from sim.engine.saveload import load_state, save_state

from .agents_fake_world import FakeWorld

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


# ---- the actor kinds share one base, and a recorded actor's money is an account in the purses book -----------------
registry = ActorRegistry(ActorsState(home_country="home"))
firm = registry.add("firm:test", ActorRecord(kind="firm", money=50.0))
state_actor = registry.ensure_government("home")
check("a firm and a government are Actors too",
      issubclass(Firm, RecordedActor) and issubclass(Government, RecordedActor) and issubclass(RecordedActor, Actor))
check("every recorded actor kind exposes the same shared surface",
      all(hasattr(actor, name) for actor in (firm, state_actor)
          for name in ("money", "workforce", "knowledge", "concerns", "works", "decision_policy")))
check("a recorded actor keeps its money as an account in the purses book, the rest of its state on its record",
      firm.money == 50.0 and firm.record.money == 0.0 and registry.state.purses.purse("firm:test") == 50.0)

# ---- government imitation is derived from values, not ids (the stand-in world answers what the state weighs) -------


class StateWorld(FakeWorld):
    def __init__(self):
        super().__init__(year=100)
        self.weights = {"military": 0.9, "information": -0.5}
        self.revenue = 1.0e9

    def state_weights(self):
        return self.weights

    def state_revenue(self):
        return self.revenue


def valued_world(*nodes):
    world = StateWorld()
    for node in nodes:
        world.nodes[node["id"]] = node
        world.demonstrated_nodes.add(node["id"])
    return world


def state_with(world):
    state_registry = ActorRegistry(ActorsState(home_country="home"))
    government = state_registry.ensure_government("home")
    government.money = 1.0e6
    return government


gun = make_node("test_gun", traits=["military"])
cartoons = make_node("test_cartoons", traits=["information"])
faint = make_node("test_faint", gains={"military": 1e-12})
modded = make_node("test_mod:cannon", gains={"military": 0.9})
world = valued_world(gun, cartoons, faint, modded)
government = state_with(world)
subjects = {option.subject: option for option in government.imitation_options(world)}
check("a militarily valuable invention is on offer to the government", "test_gun" in subjects, sorted(subjects))
check("an invention the state weighs negatively is not", "test_cartoons" not in subjects, sorted(subjects))
check("a mod invention with a declared military value is on offer without code changes",
      "test_mod:cannon" in subjects and subjects["test_mod:cannon"].worth > subjects["test_gun"].worth * 0.5,
      sorted(subjects))
check("a real but negligible gain is worth less than it costs",
      "test_faint" not in subjects or subjects["test_faint"].net <= 0)
world.weights["military"] = -0.5
flipped = {option.subject for option in government.imitation_options(world)}
check("changing what the state values changes what it wants, ids unchanged",
      "test_gun" not in flipped and "test_mod:cannon" not in flipped, sorted(flipped))
world.weights["military"] = 0.9
world.revenue = 0.0
check("a state with no revenue values nothing", not government.imitation_options(world))
world.revenue = 1.0e9

# ---- a policy chooses, and an actor begins and carries on copies ----------------------------------------------------
begun = government.consider_imitation(world)
check("the government begins copying what it values and ignores the rest",
      set(begun) == set(government.works) and "test_gun" in begun and "test_mod:cannon" in begun
      and "test_cartoons" not in government.works and "test_faint" not in government.works, sorted(government.works))
government.money = 1.0e6
finished = government.work_on_copies(world)
check("the copy is not finished in the first year, spends the treasury and puts trades to work",
      "test_gun" not in finished and "test_gun" in government.works
      and government.workforce.get("labourer", 0.0) > 0 and government.money < 1.0e6, (finished, government.money))
for _ in range(imitation.copy_years(gun)):
    finished = government.work_on_copies(world)
check("the copy finishes after its planned time and the state then knows the technique",
      "test_gun" in government.knowledge and "test_gun" not in government.works,
      (sorted(government.knowledge), sorted(government.works)))

# ---- failure and stalling -------------------------------------------------------------------------------------------
doomed_world = valued_world(make_node("test_doomed", traits=["military"], risk=5.0))
doomed = state_with(doomed_world)
doomed.decision_policy = CallbackPolicy(lambda actor, decision: [o.subject for o in decision.options])
plan = imitation.copy_plan(doomed, ["test_doomed"], doomed_world)
doomed.works["test_doomed"] = imitation.start_work("test_doomed", ["test_doomed"], plan, doomed_world.year)
doomed.work_on_copies(doomed_world)
finished = doomed.work_on_copies(doomed_world)
check("a copy that fails teaches nothing, costs what was spent and is counted",
      not finished and "test_doomed" not in doomed.knowledge
      and doomed.record.failed_copies.get("test_doomed") == 1 and doomed.money < 1.0e6)
doomed.money = 0.0
doomed.works["test_doomed"] = imitation.start_work("test_doomed", ["test_doomed"], plan, doomed_world.year)
doomed.work_on_copies(doomed_world)
check("a purse that cannot pay stalls the work instead of forgiving it",
      doomed.works["test_doomed"]["progress"] < 1.0 and doomed.works["test_doomed"]["stalled"] > 0)

# ---- policies drive any actor ---------------------------------------------------------------------------------------
policy_world = valued_world(make_node("test_visible", traits=["military"]))
policy_registry = ActorRegistry(ActorsState(home_country="home"))
chooser = policy_registry.ensure_government("home")
chooser.money = 1.0e6
chooser.decision_policy = IdlePolicy()
chooser.consider_imitation(policy_world)
check("an idle policy copies nothing however valuable the invention", not chooser.works)
chooser.decision_policy = CallbackPolicy(lambda actor, decision: ["test_visible", "not_on_offer"])
chooser.consider_imitation(policy_world)
check("a callback policy chooses for the actor and cannot pick what is not on offer",
      set(chooser.works) == {"test_visible"})
register_policy("test_never", IdlePolicy)
chooser.record.policy_kind = "test_never"
check("a registered policy is restored by name",
      isinstance(ActorRegistry(policy_registry.state).get("government:home").decision_policy, IdlePolicy))

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

# ---- a mod can declare gains ----------------------------------------------------------------------------------------
with tempfile.TemporaryDirectory() as folder:
    mod = os.path.join(folder, "mods", "test_arms_k3f9")
    os.makedirs(os.path.join(mod, "data", "branches"))
    with open(os.path.join(mod, "mod.json"), "w") as handle:
        json.dump({"id": "test_arms_k3f9", "name": "Arms", "version": "1",
                   "dependencies": [], "conflicts": []}, handle)
    with open(os.path.join(mod, "data", "branches", "arms.json"), "w") as handle:
        json.dump({"nodes": [{"id": "test_arms_k3f9:culverin", "name": "Culverin",
                              "gains": {"military": 0.8}}]}, handle)
    tree = load_mod_tree({"nodes": [], "meta": {"goals": []}},
                         get_ordered_mods(os.path.join(folder, "mods")))
    loaded = {node["id"]: node for node in tree["nodes"]}["test_arms_k3f9:culverin"]
check("a mod node's declared gains survive loading", loaded.get("gains") == {"military": 0.8}, loaded)
