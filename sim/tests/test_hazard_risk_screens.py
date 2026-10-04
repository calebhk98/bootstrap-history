"""Hazard, risk and score screens agree with what the engine applies: Complaints/194, 195, 196, 197, 198, 199, 200, 219."""
from .harness import *  # noqa: F401,F403
from sim.engine.data import money_word
from sim.ui.proto.render_screen_why import render_why
from sim.ui.proto.render_screens_status import render_risk, render_score
from sim.ui.proto.score import _score_achievements, score_report


class FixedDraws:
    """A random source that returns the listed draws, then a high value."""

    def __init__(self, *draws):
        self.draws = list(draws)

    def random(self):
        return self.draws.pop(0) if self.draws else 0.99


def england():
    return sim(civ="england_1300", capital=1e6)


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
scandal_sim = sim()
alarming = next(node_id for node_id in sorted(NODES) if scandal_sim.alarm_of(NODES[node_id]) > 0.01)
alarming_why = S._agent_dispatch(scandal_sim, NODES, {"cmd": "why", "id": alarming})
check("why reports the scandal finishing the work would add",
      abs((alarming_why.get("standing_effect") or {}).get("scandal", -1.0)
          - scandal_sim.alarm_of(NODES[alarming])) < 0.06, alarming_why.get("standing_effect"))
check("the why page prints the scandal line", "scandal" in render_why(alarming_why).lower())
scandal_before = scandal_sim.scandal
scandal_sim.initialize_project(alarming, ph_left=0.0)
scandal_sim.effective_risk = lambda _node_id: 0.0
scandal_sim._complete(alarming)
check("the scandal that why quoted is the scandal completion added",
      abs((scandal_sim.scandal - scandal_before) - (alarming_why.get("standing_effect") or {}).get("scandal", -1.0)) < 0.06,
      (scandal_sim.scandal - scandal_before, alarming_why.get("standing_effect")))

# --- 199: score names what each component counts, and which institutions are finished but closed
score_sim = sim()
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
check("resilience says it does not read the hazard screen",
      "risk" in components["resilience"].get("counts", ""), components["resilience"].get("counts"))
score_text = render_score({"components": components, "goal_reached": False, "end_reason": None})
check("the score screen prints the institution waiting to be opened",
      closed_institution in score_text and "resilience" in score_text and "counts" in score_text.lower(), score_text)

# --- 200: completing the corpus says what is already in force and what waits for opening
corpus_sim = sim()
corpus_sim.effective_risk = lambda _node_id: 0.0
corpus_sim.initialize_project("corpus_written", ph_left=0.0)
corpus_before = len(corpus_sim.log)
corpus_sim._complete("corpus_written")
corpus_text = " ".join(message for _year, message in corpus_sim.log[corpus_before:])
check("the corpus completion message names the hedge as already in force",
      "in force" in corpus_text.lower() and "hedge" in corpus_text.lower(), corpus_text)
check("...and still says what waits for opening", "Not in effect until open" in corpus_text, corpus_text)
check("risk agrees with the completion message about the hedge",
      corpus_sim.corpus_hedge()[2] == "corpus_written")

# --- 201: the cash line names the money and says what it is
cash_sim = sim()
cash_sim.state.household.capital = 50_000.0
cash_sim.state.household.employees = {"clerk": 10.0}
cash_sim.labour._resync_pools()
cash_sim.rng = FixedDraws(0.0, *([0.0] * 60))
log_before = len(cash_sim.log)
cash_sim._shock_staff_loss({"name": "Test plague", "staff_loss": 0.3, "years": [100, 110]}, cash_sim.year)
cash_text = " ".join(message for _year, message in cash_sim.log[log_before:])
check("the plague cash line names the currency", money_word(cash_sim.civ) in cash_text, cash_text)
check("the plague cash line says it is takings lost while trade stood idle",
      "takings" in cash_text and "idle" in cash_text, cash_text)

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
closed_text = render_risk(risk_reply(attribution_sim))
check("the lapsed line tells the player which concern to open",
      "open %s" % staff_counter in closed_text, closed_text)
check("a lapsed mitigation's smaller share is marked residual",
      bool(in_force) and closed_entry.get("points", 9.0) < in_force[0]["points"] and "residual" in closed_text,
      closed_text)

national_sim = sim()
built_medical = sorted(node_id for node_id in NODES if node_id in national_sim._diffusible_ids("medical"))[0]
national_sim.done.add(built_medical)
national_sim.done_year[built_medical] = national_sim.year - 400
national_sim._done_changed()
national_sim.rng = FixedDraws(0.0, *([0.99] * 60))
national_sim.state.household.employees = {"clerk": 10.0}
national_sim.labour._resync_pools()
log_before = len(national_sim.log)
national_sim._shock_staff_loss({"name": "Test plague", "staff_loss": 0.3, "years": [100, 110]}, national_sim.year)
national_text = " ".join(message for _year, message in national_sim.log[log_before:])
check("the event names the discovery of yours that spread nationally",
      NODES[built_medical]["name"] in national_text, national_text)

# --- 203: why gives the before and after for a mitigation, equal to what risk shows once it is built
preview_sim = england()
preview_node = counter_nodes(preview_sim, "staff_loss")[0]
preview_why = S._agent_dispatch(preview_sim, NODES, {"cmd": "why", "id": preview_node})
effects = [entry for entry in preview_why.get("hazard_effect") or [] if entry["name"] == "Great Famine"]
check("why on a mitigation gives the hazard before and after",
      len(effects) == 1 and effects[0]["with_it"] < effects[0]["now"], preview_why.get("hazard_effect"))
check("the why page prints the hazard estimate", "Great Famine" in render_why(preview_why))
run_it(preview_sim, preview_node)
after_built = hazard_named(risk_reply(preview_sim), "Great Famine")["staff_loss_after_what_you_have_built"]
check("the preview equals what risk shows once the node is running",
      bool(effects) and abs(effects[0]["with_it"] - after_built) < 1e-9, (effects, after_built))

# --- 204: risk says what the number means
wording_text = render_risk(risk_reply(england()))
check("risk does not say 'you take N% of it'", "you take" not in wording_text, wording_text)
check("risk gives staff loss as a share of your staff", "of your staff" in wording_text, wording_text)
check("risk gives the output factor as output against normal", "of normal" in wording_text, wording_text)

# --- 223: closing a concern for want of staff costs the achievement for good, even after it reopens
staff_sim = sim()
staff_sim.goal_year = staff_sim.year
check("with no staffing closure the achievement is held",
      _score_achievements(staff_sim, NODES)["never_understaffed"]["won"])
staff_sim.close_work("school_founded", staff_sim.CLOSED_FOR_STAFF)
staff_sim.clear_closure("school_founded")
check("a concern that closed for staff and reopened still costs the achievement",
      not _score_achievements(staff_sim, NODES)["never_understaffed"]["won"])
manual_sim = sim()
manual_sim.goal_year = manual_sim.year
manual_sim.close_work("school_founded", manual_sim.CLOSED_BY_CHOICE)
check("a closure by choice does not cost it",
      _score_achievements(manual_sim, NODES)["never_understaffed"]["won"])
