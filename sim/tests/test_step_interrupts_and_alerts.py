"""A multi-year step commits each year as it goes; step replies carry a short ALERTS block."""
from .harness import *  # noqa: F401,F403
from sim.ui.protocol import _agent_dispatch, save_state, load_state
from sim.ui.proto import step_progress
from sim.ui.proto.step_alerts import step_alerts, alert_lines
from sim.ui.proto import render_screens_big as _render_big

def playable():
    live_sim = sim()
    live_sim.end_year = live_sim.cfg["start_year"] + 50
    return live_sim


scratch = tempfile.mkdtemp()
save_path = os.path.join(scratch, "game.json")
interrupted_sim = playable()
start_year = interrupted_sim.year
seen_years = []


def commit_year(live_sim, summary):
    seen_years.append(summary["year"])
    save_state(live_sim, save_path)
    if len(seen_years) == 2:
        raise KeyboardInterrupt


step_progress.set_after_year(commit_year)
try:
    _agent_dispatch(interrupted_sim, NODES, {"cmd": "step", "years": 4})
    interrupted = False
except KeyboardInterrupt:
    interrupted = True
finally:
    step_progress.set_after_year(None)
check("the hook runs once per simulated year and an interrupt escapes", interrupted
      and seen_years == [start_year + 1, start_year + 2], seen_years)
reloaded = sim()
load_state(reloaded, save_path)
check("an interrupted multi-year step keeps the completed years on disk",
      reloaded.year == start_year + 2, (reloaded.year, start_year))

quiet = _agent_dispatch(playable(), NODES, {"cmd": "step", "years": 2})
check("a quiet step has an empty alerts list", quiet.get("alerts") == [], quiet.get("alerts"))

events = [{"year": 101, "message": "CREDIT EXHAUSTED: 3 projects stopped"},
          {"year": 102, "message": "a site is sacked: the library scrolls burn"},
          {"year": 102, "message": "something harmless happened"}]
alerts = step_alerts(events=events, lost=[{"name": "Aqueduct", "year": 102}],
                     closed_concerns=["Sand filter"], founder_died=None,
                     goal_year=None, stopped_early=None, population_change=-0.4)
joined = " | ".join(alerts)
check("alerts name credit, sacking, loss, closure and population collapse, not harmless events",
      "CREDIT EXHAUSTED" in joined and "sacked" in joined and "Aqueduct" in joined
      and "Sand filter" in joined and "population" in joined.lower() and "harmless" not in joined, alerts)
check("alerts are capped and short",
      len(step_alerts(events=[{"year": year, "message": "CREDIT EXHAUSTED %d" % year} for year in range(40)],
                      lost=[], closed_concerns=[], founder_died=None, goal_year=None,
                      stopped_early=None, population_change=0.0)) <= 8)
shown = _render_big.render_step(dict(ok=True, completed=[], events=[], lost=[], year=103, alerts=alerts))
check("the step screen puts ALERTS first, within the first lines",
      shown.splitlines()[0] == alert_lines(alerts)[0] and "ALERTS" in shown.splitlines()[0], shown[:200])

collapse = playable()
collapse.state.population.population_change_last_year = -0.5
state_reply = _agent_dispatch(collapse, NODES, {"cmd": "state"})
check("a population collapse is a field on the state reply",
      state_reply.get("demographic_emergency", {}).get("population_change") == -0.5, sorted(state_reply)[:5])
check("the state screen leads with DEMOGRAPHIC EMERGENCY",
      _render_big.render_state(state_reply).splitlines()[0].startswith("DEMOGRAPHIC EMERGENCY"),
      _render_big.render_state(state_reply)[:200])
calm = _agent_dispatch(playable(), NODES, {"cmd": "state"})
check("no emergency without a collapse", "demographic_emergency" not in calm)
shutil.rmtree(scratch, ignore_errors=True)

import io
progress_stream = io.StringIO()
step_progress.set_after_year(step_progress.commit_and_report(None, progress_stream))
_agent_dispatch(playable(), NODES, {"cmd": "step", "years": 3})
single_stream = io.StringIO()
step_progress.set_after_year(step_progress.commit_and_report(None, single_stream))
_agent_dispatch(playable(), NODES, {"cmd": "step", "years": 1})
step_progress.set_after_year(None)
check("a multi-year step prints one progress line per year; a single year prints none",
      len(progress_stream.getvalue().splitlines()) == 3 and single_stream.getvalue() == "",
      (progress_stream.getvalue(), single_stream.getvalue()))

# ---- the per-year hook belongs to one command: a played command clears it afterwards,
# so a later step in the same process does not also save into that command's session file
from sim.ui import cli_interactive as _interactive
_hook_sim = sim()
_hook_session = os.path.join(tempfile.mkdtemp(), "hooked.json")
_interactive._play_run_one_command(_hook_sim, _hook_sim.nodes, {"cmd": "step", "years": 1}, _hook_session)
check("the per-year save hook is cleared once the played command is done",
      step_progress._after_year[0] is None, step_progress._after_year[0])
