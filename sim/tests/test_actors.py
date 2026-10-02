"""Actors: the shared base, the government and firm, imitation, and persistence."""
import copy
import json
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents import (Actor, ActorRegistry, CallbackPolicy, Firm, Government,
                               Household, RecordedActor, SimWorld, register_policy)
from sim.agents import imitation
from sim.agents.policy import IdlePolicy
from sim.agents.tuning import SECRET_EXPOSURE
from sim.engine.state import ActorRecord
from sim.engine.mods import get_ordered_mods, load_mod_tree
from sim.engine.saveload import load_state, save_state
from sim.geography import settlement

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)


def make_node(node_id, traits=(), gains=None, revenue=0.0, upkeep=0.0, hours=400.0,
              years=2.0, prerequisites=(), risk=0.0):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=list(traits), pre=list(prerequisites),
                lab={"labourer": hours}, mat={}, rev=revenue, up=upkeep, yrs=years,
                risk=risk, ph=0.0, dev_years=None, dev_people=None)
    node.pop("gains", None)
    if gains is not None:
        node["gains"] = gains
    return node


def actor_sim(extra_nodes):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    game = S.Sim(nodes, list(ORDER), random.Random(1), events=False, manual=True,
                 civ=S.load_civ("rome_100ad"), cfg={"agent_economy": False})
    game.goal, game.done_year = GOAL, {}
    return game


def founder_completes(game, node_id, operating=False, opened_ago=0):
    year = game.state.scenario.year
    game.state.projects.done.add(node_id)
    game.state.projects.done_year[node_id] = year - opened_ago
    if operating:
        game.state.projects.operating.add(node_id)
        game.state.projects.opened_year[node_id] = year - opened_ago
    game._done_changed()


def next_year(game):
    game.state.scenario.year += 1
    game.advance_actors(game.state.scenario.year)


# ---- the base class holds the shared state -------------------------------
game = actor_sim([])
household = game.household
check("the founder's household is an Actor", isinstance(household, Actor))
check("a firm and a government are Actors too",
      issubclass(Firm, RecordedActor) and issubclass(Government, RecordedActor)
      and issubclass(RecordedActor, Actor))
check("household money, staff, knowledge and concerns are its existing state",
      household.money == household.capital and household.workforce is household.employees
      and household.knowledge is household.done and household.concerns is household.operating,
      (household.money, household.capital))
household.money = 1234.0
check("setting actor money moves the household purse", household.capital == 1234.0)
registry = game.actors
firm = registry.add("firm:test", ActorRecord(kind="firm", money=50.0))
check("every actor kind exposes the same shared surface",
      all(hasattr(actor, name) for actor in (household, firm, registry.ensure_government("rome_100ad"))
          for name in ("money", "workforce", "knowledge", "concerns", "works", "decision_policy")))
check("recorded actor state lives on its record", firm.money == 50.0 and firm.record.money == 50.0)
check("the household never chooses through a policy of its own", isinstance(household.decision_policy, IdlePolicy))

# ---- government imitation is derived from values, not ids ------------------
gun = make_node("test_gun", traits=["military"])
cartoons = make_node("test_cartoons", traits=["information"])
faint = make_node("test_faint", gains={"military": 1e-12})
modded = make_node("test_mod:cannon", gains={"military": 0.9})
game = actor_sim([gun, cartoons, faint, modded])
for node_id in ("test_gun", "test_cartoons", "test_faint", "test_mod:cannon"):
    founder_completes(game, node_id, operating=True)
world = SimWorld(game)
government = game.actors.ensure_government("rome_100ad")
government.money = 1.0e6
subjects = {option.subject: option for option in government.imitation_options(world)}
check("a militarily valuable invention is on offer to the government", "test_gun" in subjects, sorted(subjects))
check("an invention the state weighs negatively is not", "test_cartoons" not in subjects, sorted(subjects))
check("a mod invention with a declared military value is on offer without code changes",
      "test_mod:cannon" in subjects and subjects["test_mod:cannon"].worth > subjects["test_gun"].worth * 0.5,
      sorted(subjects))
check("a real but negligible gain is worth less than it costs",
      "test_faint" not in subjects or subjects["test_faint"].net <= 0)
game.value_weights["w_military"] = -0.5
flipped = {option.subject for option in government.imitation_options(SimWorld(game))}
check("changing what the state values changes what it wants, ids unchanged",
      "test_gun" not in flipped and "test_mod:cannon" not in flipped, sorted(flipped))
game.value_weights["w_military"] = 0.9

# ---- imitation takes time and consumes resources ----------------------------
government.money = 0.0
founder_purse = game.state.household.capital
next_year(game)
check("the government begins copying what it values and ignores the rest",
      set(government.works) == {"test_gun", "test_mod:cannon"}
      and "test_cartoons" not in government.works and "test_faint" not in government.works,
      sorted(government.works))
check("the copy is not finished in the first year", "test_gun" not in government.knowledge
      and "test_gun" in government.works)
check("copying spends the treasury and puts trades to work",
      government.workforce.get("labourer", 0.0) > 0 and government.money < government.record.money + 1 and government.money >= 0)
next_year(game)
check("the copy finishes after its planned time and the state then knows the technique",
      "test_gun" in government.knowledge and "test_gun" not in government.works,
      (sorted(government.knowledge), sorted(government.works)))
check("copying leaves the founder's own purse alone", game.state.household.capital == founder_purse)

# ---- failure and stalling ---------------------------------------------------
class DoomedWorld(SimWorld):
    def copy_risk(self, node_id):
        return 5.0


game = actor_sim([make_node("test_doomed", traits=["military"])])
founder_completes(game, "test_doomed", operating=True)
world = DoomedWorld(game)
government = game.actors.ensure_government("rome_100ad")
government.money = 1.0e6
government.decision_policy = CallbackPolicy(lambda actor, decision: [o.subject for o in decision.options])
plan = imitation.copy_plan(government, ["test_doomed"], world)
government.works["test_doomed"] = imitation.start_work("test_doomed", ["test_doomed"], plan, world.year)
government.work_on_copies(world)
finished = government.work_on_copies(world)
check("a copy that fails teaches nothing, costs what was spent and is counted",
      not finished and "test_doomed" not in government.knowledge
      and government.record.failed_copies.get("test_doomed") == 1
      and government.money < 1.0e6)
government.money = 0.0
government.works["test_doomed"] = imitation.start_work("test_doomed", ["test_doomed"], plan, world.year)
government.work_on_copies(world)
check("a purse that cannot pay stalls the work instead of forgiving it",
      government.works["test_doomed"]["progress"] < 1.0 and government.works["test_doomed"]["stalled"] > 0)

# ---- exposure: how visible, how far ----------------------------------------
game = actor_sim([make_node("test_visible", traits=["military"]), make_node("test_hidden", traits=["military"])])
founder_completes(game, "test_visible", operating=True)
founder_completes(game, "test_hidden", operating=False)
world = SimWorld(game)
government = game.actors.ensure_government("rome_100ad")
offers = {option.subject: option for option in government.imitation_options(world)}
check("an invention kept out of public use is less exposed",
      abs(offers["test_hidden"].worth / offers["test_visible"].worth - SECRET_EXPOSURE) < 1e-9,
      (offers["test_hidden"].worth, offers["test_visible"].worth))
homes = game.civ.get("home_regions") or []
farthest = max(settlement.tile_ids(homes), key=game.distance_to_tile_km)
government.record.location = farthest
far_offer = {option.subject: option for option in government.imitation_options(world)}["test_visible"]
check("a distant observer sees less of what the founder does", far_offer.worth < offers["test_visible"].worth)

# ---- policies drive any actor --------------------------------------------------
government.record.location = None
government.money = 1.0e6
game.state.projects.done.discard("test_hidden")
world = SimWorld(game)
government.decision_policy = IdlePolicy()
government.consider_imitation(world)
check("an idle policy copies nothing however valuable the invention", not government.works)
government.decision_policy = CallbackPolicy(lambda actor, decision: ["test_visible", "not_on_offer"])
government.consider_imitation(world)
check("a callback policy chooses for the actor and cannot pick what is not on offer",
      set(government.works) == {"test_visible"})
register_policy("test_never", IdlePolicy)
government.record.policy_kind = "test_never"
check("a registered policy is restored by name", isinstance(ActorRegistry(game.state.actors).get(
    "government:rome_100ad").decision_policy, IdlePolicy))

# ---- firms enter when a concern proves profitable -------------------------------
profitable = make_node("test_mill", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)
losing = make_node("test_loss", traits=["commerce"], revenue=10.0, upkeep=400.0, hours=100.0, years=1.0)
fresh = make_node("test_fresh", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)
game = actor_sim([profitable, losing, fresh])
founder_completes(game, "test_mill", operating=True, opened_ago=6)
founder_completes(game, "test_loss", operating=True, opened_ago=6)
founder_completes(game, "test_fresh", operating=True, opened_ago=0)
game.state.scenario.year += 1
game.advance_actors(game.state.scenario.year)
firms = game.actors.of_kind("firm")
check("a firm enters a concern that has proved profitable",
      len(firms) == 1 and firms[0].record.target == "test_mill", [f.record.target for f in firms])
check("no firm enters a losing concern or one not yet proved",
      all(f.record.target not in ("test_loss", "test_fresh") for f in firms))
next_year(game)
firm = game.actors.of_kind("firm")[0]
check("the firm copies the concern with the ordinary rules and then runs it",
      "test_mill" in firm.knowledge and "test_mill" in firm.concerns, (firm.record.works, firm.concerns))
check("the entrant shares the market with the founder", game.actors.rivals_of("test_mill", firm.actor_id) == 1)
next_year(game)
check("a running firm earns takings less upkeep", firm.record.last_margin != 0.0)
check("the founder's own concerns and purse are untouched by the firm's existence",
      "test_mill" in game.state.projects.operating)

game = actor_sim([losing])
founder_completes(game, "test_loss", operating=True, opened_ago=6)
loser = game.actors.add("firm:loser", ActorRecord(kind="firm", money=1000.0, target="test_loss"))
loser.concerns.add("test_loss")
loser.knowledge.add("test_loss")
loser.record.opened_year["test_loss"] = game.state.scenario.year - 6
for _ in range(4):
    next_year(game)
check("a firm that keeps losing money closes", loser.record.exited_year is not None and not loser.concerns,
      (loser.record.loss_years, loser.record.exited_year))

# ---- persistence --------------------------------------------------------------------
game = actor_sim([make_node("test_gun", traits=["military"]), profitable, make_node("test_save_mill", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)])
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
    check("actor records are written to the save automatically", "actors" in saved
          and "government:rome_100ad" in saved["actors"]["records"])
    revived = actor_sim([make_node("test_gun", traits=["military"]), profitable, make_node("test_save_mill", traits=["commerce"], revenue=5000.0, upkeep=100.0, hours=100.0, years=1.0)])
    load_state(revived, path)
check("every actor record round-trips through save and load", revived.state.actors.records == before,
      (sorted(revived.state.actors.records), sorted(before)))
check("a loaded game rebuilds its actors with the same kinds",
      [(a.actor_id, a.kind) for a in (revived.actors.of_kind("government") + revived.actors.of_kind("firm"))]
      == [(a.actor_id, a.kind) for a in (game.actors.of_kind("government") + game.actors.of_kind("firm"))])
next_year(revived)
next_year(game)
check("a loaded game goes on exactly as the original would",
      revived.state.actors.records == game.state.actors.records)

# ---- a mod can declare gains -----------------------------------------------------------
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
