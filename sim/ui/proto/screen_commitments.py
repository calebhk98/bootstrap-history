"""The `commitments` screen (Complaints/94): the chosen goal, literacy against
its ceiling, the staff reserve target and which institutions are open or closed,
gathered from figures other screens already compute."""
from .goals_watch import watched_rows
from .screen_education import _fraction_of


def _goal(sim):
    if sim.view("fog_of_war")():
        return {"id": None, "name": None, "reached": sim.view("goal")()["year"] is not None,
                "year_reached": sim.view("goal")()["year"], "withheld": "the goal's name is fogged until you learn it"}
    if sim.view("goal")()["node"] not in sim.view("tree_nodes")():
        return {"id": sim.view("goal")()["node"], "name": None, "reached": sim.view("goal")()["year"] is not None,
                "year_reached": sim.view("goal")()["year"], "withheld": "no goal is set"}
    return {"id": sim.view("goal")()["node"], "name": sim.view("tree_nodes")()[sim.view("goal")()["node"]]["name"],
            "reached": sim.view("goal")()["year"] is not None, "year_reached": sim.view("goal")()["year"]}


def _literacy(sim):
    general = float(sim.view("literacy")("literacy_general"))
    elite = float(sim.view("literacy")("literacy_elite"))
    ceiling_general = sim.view("literacy_ceiling")["literacy_general"]
    ceiling_elite = sim.view("literacy_ceiling")["literacy_elite"]
    return {"general": round(general, 4), "general_ceiling": round(ceiling_general, 4),
            "share_of_ceiling_general": _fraction_of(general, ceiling_general),
            "elite": round(elite, 4), "elite_ceiling": round(ceiling_elite, 4),
            "share_of_ceiling_elite": _fraction_of(elite, ceiling_elite)}


def _reserve(sim):
    staff = sim.view("staff")()
    return {"craftsmen": staff["reserve_craftsmen"], "scholars": staff["reserve_scholars"],
            "policy_on": bool(sim.view("founder")()["policy"].get("reserve_staff", False))}


def _institutions(sim):
    rows = []
    for node_id in sorted(sim.view("techniques_held")()):
        node = sim.view("tree_nodes")().get(node_id)
        if not node or node.get("kind") != "INSTITUTION":
            continue
        if sim.view("fog_of_war")() and not sim.view("visibility")(node_id):
            continue
        rows.append({"id": node_id, "name": node["name"],
                     "state": "open" if sim.view("running")[node_id] else "closed",
                     "units": round(sim.view("institution_units")[node_id], 2)})
    return rows


def commitments_report(sim):
    watched = watched_rows(sim)
    note = ("tracked here only; the formal goal stays the one the score uses" if watched else
            "the game has one goal; 'goals watch <goal>' tracks others")
    return {"ok": True, "goal": _goal(sim), "literacy": _literacy(sim),
            "secondary_goals": watched, "secondary_goals_note": note,
            "reserve": _reserve(sim), "institutions": _institutions(sim)}
