"""Scenario: a new node that declares a mechanic gets the effect in a game, and removing the declaration from a node's data
removes it from the engine's arithmetic (CLAUDE.md 4.7: the engine reads node `mechanics`, never node ids). The scan for node
ids in the engine's source is `test_engine_content_ids`."""
from .harness import *  # noqa: F401,F403

# --- A node that is not one of the old ids gets the effect by declaring the mechanic.
def _sim_with(extra_nodes=(), drop=()):
    nodes = copy.deepcopy(NODES)
    for node in extra_nodes:
        nodes[node["id"]] = node
    for node_id, mechanic in drop:
        nodes[node_id]["mechanics"].pop(mechanic)
    built = build_unopened(lambda: S.Sim(nodes, ORDER, random.Random(1), events=False, manual=True,
                                         civ=S.load_civ("rome_100ad")))
    built.goal, built.done_year = GOAL, {}
    return built


def _new_node(node_id, mechanics):
    node = copy.deepcopy(NODES["workshop_first"])
    node.update(id=node_id, name=node_id, pre=[], req_any=[], mechanics=mechanics)
    return node


_plain = _sim_with()
_control = _sim_with([_new_node("mod_x:hall", {"standing": {"flat": 0.0}})])
run_it(_control, "mod_x:hall")
_modded = _sim_with([_new_node("mod_x:hall", {"standing": {"flat": 7.0}})])
run_it(_modded, "mod_x:hall")
check("a new node declaring a `standing` effect raises standing_floor by exactly its flat value",
      abs(_modded.standing_floor() - _control.standing_floor() - 7.0) < 1e-9,
      (_modded.standing_floor(), _control.standing_floor()))

_credit_before = _plain.credit_limit()
_credit_sim = _sim_with([_new_node("mod_x:bank", {"credit_line": {"flat": 1234.0}})])
run_it(_credit_sim, "mod_x:bank")
check("a new node declaring a `credit_line` effect widens the credit limit",
      _credit_sim.credit_limit() > _credit_before, (_credit_sim.credit_limit(), _credit_before))

_no_tag = _sim_with(drop=[("patron_imperial", "standing")])
run_it(_no_tag, "patron_imperial")
run_it(_plain, "patron_imperial")
check("removing the `standing` effect from patron_imperial's data removes it from the engine's arithmetic",
      _no_tag.standing_floor() < _plain.standing_floor(), (_no_tag.standing_floor(), _plain.standing_floor()))

_life = _sim_with([_new_node("mod_x:clinic", {"founder_life_extension": True})])
_life.founder_alive, _life.life_left = True, 10
run_it(_life, "mod_x:clinic")
_life._step_founder_mortality()
check("a new node declaring `founder_life_extension` extends the founder's life like sanitation does",
      _life.life_left == 10 - 1 + _life.SANITATION_LIFE_EXTENSION_YEARS, _life.life_left)

_hedge = _sim_with([_new_node("mod_x:archive", {"corpus": {"rank": 9, "dispersed": True, "loss_chance": 0.01, "fraction_lost": 0.01, "diffusion_pace": 2.0}})])
_hedge.done.add("mod_x:archive")
check("corpus_hedge names a new node declaring the best `corpus` tier",
      _hedge.corpus_hedge()[2] == "mod_x:archive" and _hedge.best_corpus_node() == "mod_x:archive",
      _hedge.corpus_hedge())

_capable = _sim_with([_new_node("mod_x:guild", {"capability": {"scalable": "population", "lost_benefit": "Guild pay"}})])
check("a new node declaring `capability` is a capability institution, scalable, with its lost-benefit text",
      "mod_x:guild" in _capable.CAPABILITY_INSTITUTIONS and "mod_x:guild" in _capable.SCALABLE_INSTITUTIONS
      and _capable.NOT_OPERATING_BENEFIT["mod_x:guild"] == "Guild pay", None)

_burden_before = _plain._disease_burden()
_sans_germ = _sim_with(drop=[("germ_theory", "disease_burden")])
_sans_germ.done.add("germ_theory")
_with_germ = _sim_with()
_with_germ.done.add("germ_theory")
check("disease burden counts exactly the nodes declaring `disease_burden`",
      _with_germ._disease_burden() < _sans_germ._disease_burden() <= 1.0
      and "germ_theory" not in _sans_germ.DISEASE_BURDEN_TECH_IDS, None)
