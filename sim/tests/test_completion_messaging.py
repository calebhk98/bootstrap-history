"""completion_messaging: failure severity, goal deltas, built-not-open status and summary-first waves."""
from .harness import *  # noqa: F401,F403
from sim.engine.proto import render_screens_big as _render_big
from sim.engine.proto.wave_summary import wave_summary


def _finish(test_sim, node_id, failing=False):
    """Run one attempt at `node_id` to its end and return the log lines it added."""
    test_sim.effective_risk = lambda _node_id: 1.0 if failing else 0.0
    test_sim.initialize_project(node_id, ph_left=0.0)
    before = len(test_sim.log)
    test_sim._complete(node_id)
    return [message for _year, message in test_sim.log[before:]]


# --- Complaint 83: failure narrative scales with consequence.
minor_sim = sim()
minor_sim.funding_capacity = lambda: 1e12
minor_lines = _finish(minor_sim, "school_founded", failing=True)
major_sim = sim()
major_sim.funding_capacity = lambda: 1.0
major_lines = _finish(major_sim, "school_founded", failing=True)
check("a failure that is small next to your means is one compact line",
      len(minor_lines) == 1 and minor_lines[0].startswith("FAILED at")
      and "minor" in minor_lines[0] and len(minor_lines[0]) < 160, minor_lines)
check("a failure that is large next to your means keeps the full consequences",
      len(major_lines) == 1 and "minor" not in major_lines[0]
      and "hours are to do again" in major_lines[0], major_lines)

severity_sim = sim()
means = 1000.0
small_loss = severity_sim.MINOR_FAILURE_SHARE * means * 0.75
off_path = next(node_id for node_id in NODES if node_id not in severity_sim.goal_closure_ids())
on_path = next(node_id for node_id in severity_sim.goal_closure_ids())
check("the same loss reads minor off the goal path",
      severity_sim.failure_severity(off_path, small_loss, means) == "minor")
check("...and major when the failed project is on the goal path",
      severity_sim.failure_severity(on_path, small_loss, means) == "major")

# --- Complaint 86: built is not open.
closed_sim = sim()
closed_lines = _finish(closed_sim, "school_founded")
check("a finished concern says it is closed and how to open it",
      any("STATUS: CLOSED" in line and "open school_founded" in line
          for line in closed_lines), closed_lines)
check("...and names what switches on when it opens",
      any("Scholar and artisan training" in line for line in closed_lines), closed_lines)
check("a piece of knowledge does not claim to be closed",
      not any("STATUS: CLOSED" in line
              for line in _finish(sim(), "ag2_balanced_ration")))

# --- Complaint 131 (completion half): say when today's staff could not open it.
short_sim = sim()
short_sim.venture_staff_free = lambda: (0.0, 0.0)
short_sim.venture_hands = lambda node_id: (5.0, 5.0)
short_lines = _finish(short_sim, "school_founded")
check("a finished concern you lack the staff to open says so",
      any("could not open it" in line for line in short_lines), short_lines)
staffed_sim = sim()
staffed_sim.venture_staff_free = lambda: (50.0, 50.0)
check("...and stays quiet when the staff are free",
      not any("could not open it" in line
              for line in _finish(staffed_sim, "school_founded")))

# --- Complaint 85: goal deltas on completion.
goal_sim = sim()
goal_sim.goal = "goal_literacy_common"
goal_sim.civ["literacy_general"] = 0.10
goal_sim.apply_tech_effects = lambda node_id: goal_sim.civ.__setitem__("literacy_general", 0.15)
goal_lines = _finish(goal_sim, "ag2_balanced_ration")
check("a completion that moves the goal metric shows before and after",
      any("goal effect" in line and "10.0%" in line and "15.0%" in line
          for line in goal_lines), goal_lines)
unmoved_sim = sim()
unmoved_sim.goal = "goal_literacy_common"
unmoved_sim.goal_closure_ids = lambda: set()
unmoved_sim.apply_tech_effects = lambda node_id: None
unmoved_sim.literacy_ceiling_general = lambda: 0.35
check("a completion that moves nothing on the goal adds no goal line",
      not any("goal effect" in line for line in _finish(unmoved_sim, "ag2_balanced_ration")))

path_sim = sim()
path_node = sorted(path_sim.goal_closure_ids())[0]
path_lines = _finish(path_sim, path_node)
check("a completion on the road to the goal says so",
      any("goal effect" in line and "road" in line for line in path_lines), path_lines)
fog_sim = sim()
fog_sim.fog = True
fog_lines = _finish(fog_sim, sorted(fog_sim.goal_closure_ids())[0])
check("under fog the road line never reveals the total",
      any("goal effect" in line for line in fog_lines)
      and not any(" of " in line for line in fog_lines if "goal effect" in line), fog_lines)

# --- Complaint 82: summary first.
wave = [{"id": "a%d" % index, "name": "Thing %d" % index, "year": 200,
         "granted": False, "kind": "technology"} for index in range(12)]
wave.append({"id": "c1", "name": "Shop", "year": 200, "granted": False, "kind": "concern"})
events = [{"year": 200, "message": "FAILED at X (minor): lost 3."},
          {"year": 200, "message": "FAILED at Y: it did not work."}]
summary = wave_summary(wave, events, goal_before=None, goal_after=None)
check("summary counts completions by kind and failures by severity",
      summary["completed"] == 13 and summary["by_kind"] == {"technology": 12, "concern": 1}
      and summary["failed"] == 2 and summary["minor_failures"] == 1, summary)
check("no summary for a quiet step", wave_summary([], [], None, None) is None)

rendered = _render_big.render_step(dict(ok=True, completed=wave, events=events,
                                        lost=[], summary=summary, year=200))
lines = rendered.splitlines()
summary_at = next(i for i, line in enumerate(lines) if "13 completed" in line)
detail_at = next(i for i, line in enumerate(lines) if "Thing 0" in line)
check("a large wave prints its one-line summary before the detail",
      summary_at < detail_at and "2 failed" in lines[summary_at], lines[:4])
small = dict(ok=True, completed=wave[:2], events=[], lost=[],
             summary=wave_summary(wave[:2], [], None, None), year=200)
check("a small wave stays a plain list with no summary line",
      "completed (" not in _render_big.render_step(small))
