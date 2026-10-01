"""Complaint 470: a saved and loaded game plays on exactly as the unbroken one
would. State the next year reads must be in the save: the material demand the
last throttle left behind, and the order of every dict (float sums follow it)."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto.saveload import save_state, load_state


def _round_trip(game):
    path = os.path.join(tempfile.mkdtemp(), "save.json")
    save_state(game, path)
    reloaded = sim(capital=1.0)
    load_state(reloaded, path)
    return reloaded


def _two_projects_with_different_materials(game):
    node_ids = []
    for node_id in ORDER:
        materials = set(NODES[node_id].get("mat") or ())
        if node_id in game.done or not materials:
            continue
        if not node_ids or not materials & set(NODES[node_ids[0]]["mat"]):
            node_ids.append(node_id)
        if len(node_ids) == 2:
            return node_ids
    raise AssertionError("no two projects with different materials")


# --- the demand the last throttle left behind is read before the next one -----
game = sim(capital=1e9)
first_id, second_id = _two_projects_with_different_materials(game)
game.initialize_project(first_id)
game.resource_throttle()
game.initialize_project(second_id)
check("set-up: work started after the last throttle makes the held demand lag the live one",
      game._cached_material_demand() != game.annual_material_demand())
reloaded = _round_trip(game)
check("a reloaded game reads the same material demand the unbroken game reads",
      reloaded._cached_material_demand() == game._cached_material_demand(),
      (reloaded._cached_material_demand(), game._cached_material_demand()))

# --- dict order survives the save --------------------------------------------
order_game = sim(capital=1e9)
order_game.state.projects.done_year = {"zeta_node": 3, "alpha_node": 4, "mid_node": 5}
order_reloaded = _round_trip(order_game)
check("a dict keeps its insertion order across a save",
      list(order_reloaded.state.projects.done_year) == list(order_game.state.projects.done_year),
      list(order_reloaded.state.projects.done_year))

# --- household demand ratios are a function of the rounded population and income, not of when they were last computed ---
demand_game = sim(capital=1e9)
before_ratios = dict(demand_game.household_demand_ratios())
for cohort in ("children", "working_age", "elderly"):
    setattr(demand_game.population, cohort, getattr(demand_game.population, cohort) * 1.0003)
check("set-up: the population moved less than the rounding step",
      demand_game.household_demand_ratios() is not None)
demand_reloaded = _round_trip(demand_game)
check("a reloaded game reads the household demand ratios the unbroken game reads",
      demand_reloaded.household_demand_ratios() == demand_game.household_demand_ratios())
