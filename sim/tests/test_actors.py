"""Actors: the shared base, the government's imitation, failure and stalling, policies, and a mod's declared gains.

What a government values, copies and fails at is tested between actors built here on the agents' stand-in world
(`agents_fake_world`). The household as an actor and the save of the actors' records are in test_household_actor_save,
the seeded cast in test_cast_seeding; firms entering and leaving are in test_firm_entry_capital and test_business_review."""

QUICK_TOPIC = True
import copy
import json
import os
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents.api import (Actor, ActorRegistry, ActorsState, CallbackPolicy, Firm, Government,
                               RecordedActor, shipped_extensions)
from sim.agents import imitation
from sim.agents.policy import IdlePolicy
from sim.engine.state import ActorRecord
from sim.engine.mods import get_ordered_mods, load_mod_tree

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


def state_with(world, aware=True):
    """A government with a treasury; aware of every invention shown in `world` unless `aware` is False (an actor takes up
    only what it knows exists, awareness.py)."""
    state_registry = ActorRegistry(ActorsState(home_country="home"))
    government = state_registry.ensure_government("home")
    government.money = 1.0e6
    if aware:
        government.record.aware.update({node_id: world.year for node_id in world.demonstrated()})
    return government


gun = make_node("test_gun", traits=["military"])
cartoons = make_node("test_cartoons", traits=["information"])
faint = make_node("test_faint", gains={"military": 1e-12})
modded = make_node("test_mod:cannon", gains={"military": 0.9})
world = valued_world(gun, cartoons, faint, modded)
unaware_government = state_with(world, aware=False)
check("a government that has not come to know of a shown invention is not offered it",
      not unaware_government.imitation_options(world), sorted(option.subject for option in unaware_government.imitation_options(world)))
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
chooser.record.aware.update({node_id: policy_world.year for node_id in policy_world.demonstrated()})
chooser.decision_policy = IdlePolicy()
chooser.consider_imitation(policy_world)
check("an idle policy copies nothing however valuable the invention", not chooser.works)
chooser.decision_policy = CallbackPolicy(lambda actor, decision: ["test_visible", "not_on_offer"])
chooser.consider_imitation(policy_world)
check("a callback policy chooses for the actor and cannot pick what is not on offer",
      set(chooser.works) == {"test_visible"})
policy_extensions = shipped_extensions()
policy_extensions.policies["test_never"] = IdlePolicy
chooser.record.policy_kind = "test_never"
check("a provided policy is restored by name",
      isinstance(ActorRegistry(policy_registry.state, policy_extensions).get("government:home").decision_policy, IdlePolicy))


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
