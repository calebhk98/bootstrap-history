"""Complaints 103, 185, 287: an actor chooses what to do with an invention (keep it secret, license
it, publish it), and the state's military adoption is what the government actually holds."""
import copy
import json
import os
import random
import tempfile

from .harness import *  # noqa: F401,F403

from sim.agents import SimWorld
from sim.agents.tuning import PROOF_YEARS, SECRET_EXPOSURE
from sim.engine.saveload import load_state, save_state
from sim.engine.state import ActorRecord

_TEMPLATE_ID = next(node_id for node_id, node in NODES.items()
                    if node["rev"] > 0 and not node["pre"] and node["cap"] >= 0)


def make_node(node_id, lab=None, traits=("commerce",), revenue=5000.0, upkeep=100.0, years=1.0):
    node = copy.deepcopy(NODES[_TEMPLATE_ID])
    node.update(id=node_id, name=node_id, traits=list(traits), pre=[], lab=lab or {"labourer": 100.0},
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


def founder_runs(game, node_id, opened_ago=0):
    year = game.state.scenario.year
    projects = game.state.projects
    projects.done.add(node_id)
    projects.done_year[node_id] = year - opened_ago
    projects.operating.add(node_id)
    projects.opened_year[node_id] = year - opened_ago
    game._done_changed()


EASY = make_node("zz_easy", lab={"labourer": 100.0})
HARD = make_node("zz_hard", lab={"smith": 50.0, "carpenter": 50.0, "mason": 50.0, "labourer": 50.0})
EXTRA = [EASY, HARD]

# ---- the default is today's behaviour ----------------------------------------------------
game = actor_sim(EXTRA)
founder_runs(game, "zz_easy", opened_ago=PROOF_YEARS)
founder_runs(game, "zz_hard", opened_ago=PROOF_YEARS)
world = SimWorld(game)
check("an invention with no choice made is on the default, which is today's rule",
      game.disclosure_of("zz_easy")["mode"] == "default")
default_exposure = world.exposure("zz_easy", None)
check("the default exposure is full visibility for a concern in public use",
      abs(default_exposure - 1.0) < 1e-9, default_exposure)
check("a proven concern is believed after the proof years on the default",
      "zz_easy" in world.proven_concerns(), world.proven_concerns())

# ---- keep secret: slowed by how hard the know-how is to copy -----------------------------
check("choosing secret is accepted for an invention the founder holds",
      game.disclose("zz_easy", "secret")["ok"])
check("choosing secret for something the founder has not made is refused",
      not game.disclose("not_a_node", "secret")["ok"])
game.disclose("zz_hard", "secret")
world = SimWorld(game)
easy_secret, hard_secret = world.exposure("zz_easy", None), world.exposure("zz_hard", None)
check("a secret is copied more slowly than the same concern kept on the default",
      easy_secret < default_exposure, (easy_secret, default_exposure))
check("a secret needing more trades is harder to copy than a simple one",
      hard_secret < easy_secret, (hard_secret, easy_secret))
check("a secret concern is not believed by outsiders as soon as the default would believe it",
      "zz_easy" not in world.proven_concerns(), world.proven_concerns())
founder_runs(game, "zz_easy", opened_ago=PROOF_YEARS + 60)
check("...but it is believed in the end, after the delay its difficulty sets",
      "zz_easy" in SimWorld(game).proven_concerns())

# ---- publish: anyone copies, the publisher gains standing --------------------------------
game = actor_sim(EXTRA)
founder_runs(game, "zz_easy", opened_ago=PROOF_YEARS - 1)
reputation_before = game.reputation
result = game.disclose("zz_easy", "publish")
check("publishing is accepted and raises the publisher's reputation",
      result["ok"] and game.reputation > reputation_before, (result, reputation_before, game.reputation))
reputation_after = game.reputation
game.disclose("zz_easy", "publish")
check("publishing again earns nothing more", abs(game.reputation - reputation_after) < 1e-9)
check("a published concern is believed without waiting out the proof years",
      "zz_easy" in SimWorld(game).proven_concerns())
game.state.projects.operating.discard("zz_easy")
check("a published invention is fully visible even when the founder runs no concern from it",
      abs(SimWorld(game).exposure("zz_easy", None) - 1.0) < 1e-9, SimWorld(game).exposure("zz_easy", None))
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "save.json")
    save_state(game, path)
    revived = actor_sim(EXTRA)
    load_state(revived, path)
check("the choice survives a save and load", revived.disclosure_of("zz_easy")["mode"] == "publish")

# ---- license: a named firm or the state pays through the ledger and copies at once -------
game = actor_sim(EXTRA)
founder_runs(game, "zz_easy", opened_ago=5)
firm = game.actors.add("firm:licensee", ActorRecord(kind="firm", money=1.0e6, target="zz_easy"))
capital_before, firm_before = game.household.capital, firm.money
result = game.disclose("zz_easy", "license", licensee="firm:licensee", fee=1000.0)
check("a licence to a named firm is accepted", result["ok"], result)
check("the firm paid the fee and the founder received it, nothing created or destroyed",
      abs((firm_before - firm.money) - 1000.0) < 1e-6
      and abs((game.household.capital - capital_before) - 1000.0) < 1e-6,
      (firm_before - firm.money, game.household.capital - capital_before))
check("the licensee can make it at once: the know-how and the concern are its own",
      "zz_easy" in firm.knowledge and "zz_easy" in firm.concerns)
check("the licence is on the founder's record",
      "firm:licensee" in game.disclosure_of("zz_easy")["licensees"])
poor = game.actors.add("firm:poor", ActorRecord(kind="firm", money=10.0, target="zz_easy"))
check("a licensee that cannot pay the fee is refused and learns nothing",
      not game.disclose("zz_easy", "license", licensee="firm:poor", fee=1000.0)["ok"]
      and "zz_easy" not in poor.knowledge)
check("a licence to nobody is refused",
      not game.disclose("zz_easy", "license", licensee="firm:nobody", fee=1.0)["ok"])

government = game.state_treasury()
government.credit(1.0e6, "taxation")
treasury_before = government.money
result = game.disclose("zz_easy", "license", licensee=government.actor_id, fee=2000.0)
check("the state can be the licensee, paying from its treasury",
      result["ok"] and abs((treasury_before - government.money) - 2000.0) < 1e-6
      and "zz_easy" in government.knowledge, result)

# ---- a royalty is paid from the licensee's takings every year ---------------------------
game = actor_sim(EXTRA)
founder_runs(game, "zz_easy", opened_ago=5)
firm = game.actors.add("firm:royal", ActorRecord(kind="firm", money=1.0e6, target="zz_easy"))
game.disclose("zz_easy", "license", licensee="firm:royal", fee=0.0, royalty=0.1)
capital_before = game.household.capital
game.state.scenario.year += 1
game.advance_actors(game.state.scenario.year)
check("a licensed firm pays the founder its royalty on takings",
      game.household.capital > capital_before and firm.record.outlays.get("licence", 0.0) > 0.0,
      (game.household.capital - capital_before, firm.record.outlays))

# ---- the command ------------------------------------------------------------------------
replies, _, _ = proto([{"cmd": "disclose"}, {"cmd": "disclose", "id": "no_such_node", "mode": "publish"},
                 {"cmd": "help", "topic": "disclose"}])
check("the disclose command lists the inventions and says what it takes",
      replies and replies[0].get("ok") and "inventions" in replies[0], replies[:1])
check("a bad node is refused with a reason", replies[1].get("ok") is False and replies[1].get("error"))
check("help documents it", replies[2].get("ok") is not False, replies[2])

# ---- increment 3: the state's military adoption is what the government holds -------------
military = sorted(node_id for node_id, node in NODES.items()
                  if "military" in (node.get("traits") or ()) and node_id != "patron_imperial")[:2]
game = sim(civ="rome_100ad")
run_it(game, "patron_imperial")
for node_id in military:
    game.done.add(node_id)
    game.done_year[node_id] = game.year - 200
check("the founder's military work does not reach the state however long it has had",
      game.state_military_diffusion() == 0.0, game.state_military_diffusion())
check("no half-life curve for the state's armies remains",
      not hasattr(game, "DIFFUSION_HALF_LIFE_MILITARY_YEARS"))
government = game.state_treasury()
government.knowledge.add(military[0])
held = game.state_military_diffusion()
check("what the government holds is the state's adoption", 0.0 < held < 1.0 + 1e-9, held)
government.knowledge.update(military)
check("holding all of it is full adoption", abs(game.state_military_diffusion() - 1.0) < 1e-9)
relief, why = game.hazard_relief("sack_chance")
check("war relief follows what the state holds",
      relief < 1.0 and any("state's own armies" in line for line in why), (relief, why))
