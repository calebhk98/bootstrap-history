"""The `commitments` screen (Complaints/94): the chosen goal, literacy against
its ceiling, the staff reserve target and which institutions are open or closed,
gathered from figures other screens already compute."""
from .screen_education import _fraction_of


def _goal(sim):
    if sim.fog:
        return {"id": None, "name": None, "reached": sim.goal_year is not None,
                "year_reached": sim.goal_year, "withheld": "the goal's name is fogged until you learn it"}
    if sim.goal not in sim.nodes:
        return {"id": sim.goal, "name": None, "reached": sim.goal_year is not None,
                "year_reached": sim.goal_year, "withheld": "no goal is set"}
    return {"id": sim.goal, "name": sim.nodes[sim.goal]["name"],
            "reached": sim.goal_year is not None, "year_reached": sim.goal_year}


def _literacy(sim):
    general = float(sim.civ.get("literacy_general", 0.0))
    elite = float(sim.civ.get("literacy_elite", 0.0))
    ceiling_general = sim.literacy_ceiling_general()
    ceiling_elite = sim.literacy_ceiling_elite()
    return {"general": round(general, 4), "general_ceiling": round(ceiling_general, 4),
            "share_of_ceiling_general": _fraction_of(general, ceiling_general),
            "elite": round(elite, 4), "elite_ceiling": round(ceiling_elite, 4),
            "share_of_ceiling_elite": _fraction_of(elite, ceiling_elite)}


def _reserve(sim):
    household = sim.state.household
    return {"craftsmen": household.reserve_craftsmen, "scholars": household.reserve_scholars,
            "policy_on": bool(sim.policy.get("reserve_staff", False))}


def _institutions(sim):
    rows = []
    for node_id in sorted(sim.done):
        node = sim.nodes.get(node_id)
        if not node or node.get("kind") != "INSTITUTION":
            continue
        if sim.fog and not sim.is_visible(node_id):
            continue
        rows.append({"id": node_id, "name": node["name"],
                     "state": "open" if sim.running(node_id) else "closed",
                     "units": round(sim.institution_units(node_id), 2)})
    return rows


def commitments_report(sim):
    return {"ok": True, "goal": _goal(sim), "literacy": _literacy(sim),
            "secondary_goals": [],
            "secondary_goals_note": "the game has one goal; there are no secondary goals to list",
            "reserve": _reserve(sim), "institutions": _institutions(sim)}
