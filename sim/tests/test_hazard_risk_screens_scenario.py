"""SCENARIO: in an England and a Rome game the hazard, risk, why and score screens agree with what the engine applies
(Complaints/194 to 204, 219, 223). Each check reads a screen and the function that applies the same figure from one game,
so there is no rule to call on its own."""
from .harness import *  # noqa: F401,F403
from sim.ui.proto.score import _score_achievements, score_report


def england():
    return unopened_sim(civ="england_1300", capital=1e6)


def risk_reply(test_sim):
    return S._agent_dispatch(test_sim, NODES, {"cmd": "risk"})


def hazard_named(reply, name):
    for hazard in reply["knowledge_risk"]["known_hazards_ahead"]:
        if hazard["name"] == name:
            return hazard
    return None


def counter_nodes(test_sim, kind):
    return [node_id for node_id, _share, label in test_sim.HAZARD_COUNTERS[kind]
            if node_id in NODES and not node_id.startswith("_")
            and not test_sim._counter_requirements(node_id, kind, label)]


# --- 198: why says what finishing a thing does to scandal, from the function that applies it
scandal_sim = unopened_sim()
alarming = next(node_id for node_id in sorted(NODES) if scandal_sim.alarm_of(NODES[node_id]) > 0.01)
alarming_why = S._agent_dispatch(scandal_sim, NODES, {"cmd": "why", "id": alarming})
check("why reports the scandal finishing the work would add",
      abs((alarming_why.get("standing_effect") or {}).get("scandal", -1.0)
          - scandal_sim.alarm_of(NODES[alarming])) < 0.06, alarming_why.get("standing_effect"))
scandal_before = scandal_sim.scandal
scandal_sim.initialize_project(alarming, ph_left=0.0)
scandal_sim.effective_risk = lambda _node_id: 0.0
scandal_sim._complete(alarming)
check("the scandal that why quoted is the scandal completion added",
      abs((scandal_sim.scandal - scandal_before) - (alarming_why.get("standing_effect") or {}).get("scandal", -1.0)) < 0.06,
      (scandal_sim.scandal - scandal_before, alarming_why.get("standing_effect")))

# --- 199: score names what each component counts, and which institutions are finished but closed
score_sim = unopened_sim()
closed_institution = next(node_id for node_id in sorted(score_sim.CAPABILITY_INSTITUTIONS)
                          if node_id not in score_sim.SCALABLE_INSTITUTIONS and node_id in NODES)
score_sim.done.add(closed_institution)
score_sim._done_changed()
components = score_report(score_sim, NODES)["components"]
check("every score component says what it counts",
      all(isinstance(component.get("counts"), str) and component["counts"] for component in components.values()),
      [name for name, component in components.items() if not component.get("counts")])
check("institutions list what is finished but closed",
      closed_institution in components["institutions"].get("finished_but_closed", []),
      components["institutions"])
# --- 200: completing the corpus says what is already in force and what waits for opening
corpus_sim = unopened_sim()
corpus_sim.effective_risk = lambda _node_id: 0.0
corpus_sim.initialize_project("corpus_written", ph_left=0.0)
corpus_sim._complete("corpus_written")
check("risk agrees with the completion about the hedge",
      corpus_sim.corpus_hedge()[2] == "corpus_written")

# --- 202: each mitigation's share, why one lapsed, and where national relief comes from
attribution_sim = england()
staff_counter = counter_nodes(attribution_sim, "staff_loss")[0]
run_it(attribution_sim, staff_counter)
famine = hazard_named(risk_reply(attribution_sim), "Great Famine")
mitigations = (famine or {}).get("what_you_can_do", {}).get("staff_loss", {}).get("mitigations") or []
in_force = [entry for entry in mitigations if entry.get("node") == staff_counter]
check("risk lists each mitigation in force with the points it takes off",
      len(in_force) == 1 and in_force[0]["status"] == "in force" and in_force[0]["points"] > 0.0,
      mitigations)
attribution_sim.close_work(staff_counter, attribution_sim.CLOSED_FOR_STAFF)
famine_closed = hazard_named(risk_reply(attribution_sim), "Great Famine")
closed_entries = [entry for entry in famine_closed["what_you_can_do"]["staff_loss"].get("mitigations", [])
                  if entry.get("node") == staff_counter]
closed_entry = closed_entries[0] if closed_entries else {}
check("a closed mitigation says it lapsed and why it closed",
      closed_entry.get("status") == "lapsed" and "staff" in closed_entry.get("closed_because", ""), closed_entry)
check("a lapsed mitigation's share is smaller than in force",
      bool(in_force) and closed_entry.get("points", 9.0) < in_force[0]["points"], (closed_entry, in_force))

# --- 203: why gives the before and after for a mitigation, equal to what risk shows once it is built
preview_sim = england()
preview_node = counter_nodes(preview_sim, "staff_loss")[0]
preview_why = S._agent_dispatch(preview_sim, NODES, {"cmd": "why", "id": preview_node})
effects = [entry for entry in preview_why.get("hazard_effect") or [] if entry["name"] == "Great Famine"]
check("why on a mitigation gives the hazard before and after",
      len(effects) == 1 and effects[0]["with_it"] < effects[0]["now"], preview_why.get("hazard_effect"))
run_it(preview_sim, preview_node)
after_built = hazard_named(risk_reply(preview_sim), "Great Famine")["staff_loss_after_what_you_have_built"]
check("the preview equals what risk shows once the node is running",
      bool(effects) and abs(effects[0]["with_it"] - after_built) < 1e-9, (effects, after_built))

# --- 223: closing a concern for want of staff costs the achievement for good, even after it reopens
staff_sim = unopened_sim()
staff_sim.goal_year = staff_sim.year
check("with no staffing closure the achievement is held",
      _score_achievements(staff_sim, NODES)["never_understaffed"]["won"])
staff_sim.close_work("school_founded", staff_sim.CLOSED_FOR_STAFF)
staff_sim.clear_closure("school_founded")
check("a concern that closed for staff and reopened still costs the achievement",
      not _score_achievements(staff_sim, NODES)["never_understaffed"]["won"])
manual_sim = unopened_sim()
manual_sim.goal_year = manual_sim.year
manual_sim.close_work("school_founded", manual_sim.CLOSED_BY_CHOICE)
check("a closure by choice does not cost it",
      _score_achievements(manual_sim, NODES)["never_understaffed"]["won"])
