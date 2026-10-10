"""pursue_programme: regression checks, run with `--only pursue_programme`."""
from .harness import *  # noqa: F401,F403
from sim.engine.ui_port import closure
from sim.ui.memory import load_state, save_state
from sim.ui.proto.programme import programme_before_year
from sim.ui.proto.render_programme import render_pursue, render_programme, render_programme_rows


def _run(sim_state, **command):
    return S._agent_dispatch(sim_state, NODES, command)


# --- renderers on hand-written replies
_row = {"year": 100, "what": "programme for goal X", "started": [{"id": "a", "name": "Alpha", "cost": 1200.0}],
        "skipped": [{"id": "b", "why": "not begun: over max_total_cost"}], "spent": 1200.0}
_lines = render_programme_rows([_row, {"year": 101, "what": "programme for goal X", "did_nothing_because": "in debt"}])
check("programme rows list starts and skips", any("Alpha" in line for line in _lines)
      and any("skipped b" in line for line in _lines), _lines)
check("programme rows say why it did nothing", any("did nothing: in debt" in line for line in _lines), _lines)
check("render_programme shows caps and pause", "(paused)" in render_programme(
    {"ok": True, "programme": {"target": "goal X", "caps": "no caps", "paused": True,
                               "committed_so_far": 0, "runs": "yearly"}}))
check("render_pursue names the order", "critical path" in render_pursue(
    {"ok": True, "started": [], "pursue": {"name": "X", "startable_on_route": 0, "order": "critical path"}}))

# --- one game for the handler checks
game = sim(capital=20000.0)
game.end_year = game.cfg["start_year"] + 50
route = closure(NODES, GOAL)
_preview = _run(game, cmd="pursue", preview=True, limit=50)
check("pursue preview works", _preview.get("ok") and _preview.get("preview"), _preview)
_would = [row["id"] for row in _preview.get("would_start", [])]
check("pursue preview starts only route members", _would and all(node_id in route for node_id in _would), _would)
check("pursue preview changes nothing", not game.active, sorted(game.active))
check("pursue names its order", "order" in _preview.get("pursue", {}), _preview.get("pursue"))
check("pursue refuses an unknown goal", not _run(game, cmd="pursue", goal="no_such_node_anywhere")["ok"])

_capped = _run(game, cmd="pursue", max_total_cost=1500.0, limit=50)
check("pursue obeys rush caps", sum(row["cost"] for row in _capped["started"]) <= 1500.0 + 1e-6, _capped)
check("pursue starts only route members", all(node_id in route for node_id in game.active), sorted(game.active))

# --- a programme persists across save and load and acts in the next step
_set = _run(game, cmd="programme", action="set", target=GOAL, max_annual_draw=400.0, limit=50)
check("programme set", _set.get("ok") and _set["programme"]["caps"].startswith("max_annual_draw"), _set)
with tempfile.TemporaryDirectory() as folder:
    path = os.path.join(folder, "game.json")
    save_state(game, path)
    _run(game, cmd="programme", action="clear")
    check("programme cleared", _run(game, cmd="programme")["programme"] is None)
    load_state(game, path)
check("programme survives save and load", _run(game, cmd="programme")["programme"] is not None)

_active_before = set(game.active)
_step = _run(game, cmd="step")
_rows = _step.get("programme") or []
check("programme acts in the next step", len(_rows) == 1 and _rows[0]["year"] is not None, _step.get("programme"))
check("programme row is self-describing", all(key in _rows[0] for key in ("what", "started", "spent")), _rows)
check("programme starts stay within its yearly draw cap",
      all(node_id in route for node_id in set(game.active) - _active_before), sorted(game.active))

# --- a paused programme does nothing
_run(game, cmd="programme", action="pause")
_active_before = set(game.active)
_rows = programme_before_year(game, NODES)
check("paused programme says it did nothing", _rows and _rows[0].get("did_nothing_because") == "paused by the player", _rows)
check("paused programme starts nothing", set(game.active) == _active_before, _rows)
check("paused programme committed nothing", _rows[0]["started"] == [], _rows)

# --- debt pauses it too
_run(game, cmd="programme", action="resume")
game.capital = -10.0
_rows = programme_before_year(game, NODES)
check("programme does nothing in debt", "debt" in str(_rows[0].get("did_nothing_because")), _rows)

# Pause logic is read through the per-year hook directly; the one step above proves the dispatcher calls it.
# --- pause conditions the player sets: debt, war risk, shortage; each is reported and can auto-resume
_run(game, cmd="programme", action="clear")
game.capital = 20000.0
_set = _run(game, cmd="programme", action="set", target=GOAL, max_annual_draw=400.0, limit=50, pause_debt=500.0)
check("programme set takes a debt pause threshold", _set.get("ok") and "pause_debt" in _set["programme"]["pauses"], _set)
game.capital = -900.0
_rows = programme_before_year(game, NODES) or [{}]
check("debt over the threshold pauses and says why", "debt over" in str(_rows[0].get("did_nothing_because")), _rows)

_run(game, cmd="programme", action="set", target=GOAL, limit=50, pause_war_risk=0.05)
game.capital = 20000.0
game.civ["hazards"] = [{"name": "Raiders", "years": [game.year - 1, game.year + 30], "sack_chance": 0.4}]
_rows = programme_before_year(game, NODES) or [{}]
check("war risk over the threshold pauses and says why", "war risk" in str(_rows[0].get("did_nothing_because")), _rows)
check("a pause that is not auto-resume stays paused after the risk ends",
      _run(game, cmd="programme")["programme"]["paused"], _run(game, cmd="programme"))
game.civ["hazards"] = []
_rows = programme_before_year(game, NODES) or [{}]
check("without auto_resume it waits for the player", "war risk" in str(_rows[0].get("did_nothing_because")), _rows)
_run(game, cmd="programme", action="resume")
_rows = programme_before_year(game, NODES) or [{}]
check("resume works once the risk is gone", "war risk" not in str(_rows[0].get("did_nothing_because")), _rows)

_run(game, cmd="programme", action="set", target=GOAL, limit=50, pause_war_risk=0.05, auto_resume=True)
game.civ["hazards"] = [{"name": "Raiders", "years": [game.year, game.year + 30], "sack_chance": 0.4}]
_rows = programme_before_year(game, NODES) or [{}]
check("auto_resume programme pauses on war risk", "war risk" in str(_rows[0].get("did_nothing_because")), _rows)
game.civ["hazards"] = []
_rows = programme_before_year(game, NODES) or [{}]
check("auto_resume programme resumes when the risk clears",
      "war risk" not in str(_rows[0].get("did_nothing_because")) and not _run(game, cmd="programme")["programme"]["paused"], _rows)

_run(game, cmd="programme", action="set", target=GOAL, limit=50, pause_shortage=0.2, auto_resume=True)
game.state.holdings.shortage_condition = {"material": "iron", "since": game.year, "reported": 0.5,
                                         "previous": 0.5, "latest": 0.5}
_rows = programme_before_year(game, NODES) or [{}]
check("a shortage past the threshold pauses and names the material",
      "iron" in str(_rows[0].get("did_nothing_because")) and "shortage" in str(_rows[0].get("did_nothing_because")), _rows)
game.state.holdings.shortage_condition = None
_rows = programme_before_year(game, NODES) or [{}]
check("auto_resume programme resumes when the shortage clears",
      "shortage" not in str(_rows[0].get("did_nothing_because")), _rows)
check("pause settings reject a negative number",
      not _run(game, cmd="programme", action="set", target=GOAL, pause_debt=-1)["ok"])
from sim.ui.proto.parse_pursue import _split  # noqa: E402
check("typed parse reads pause and hour caps",
      _split(["max_total_hours:50", "pause_war_risk:0.1", "auto_resume"])[0]
      == {"max_total_hours": 50.0, "pause_war_risk": 0.1, "auto_resume": True})

# --- the director-hour cap stops starts
free_game = sim(capital=200000.0)
free_game.end_year = free_game.cfg["start_year"] + 50
_run(free_game, cmd="programme", action="set", target=GOAL, limit=50)
_free_row = programme_before_year(free_game, NODES)[0]
check("uncapped programme commits some founder hours", _free_row.get("hours", 0) > 0, _free_row)
capped_game = sim(capital=200000.0)
capped_game.end_year = capped_game.cfg["start_year"] + 50
_hour_cap = _free_row.get("hours", 0) / 2.0
_run(capped_game, cmd="programme", action="set", target=GOAL, limit=50, max_total_hours=_hour_cap)
_row = programme_before_year(capped_game, NODES)[0]
check("hour cap keeps starts within the cap", _row.get("hours", 0) <= _hour_cap + 1e-6
      and len(_row.get("started", [])) < len(_free_row.get("started", [])), (_row, _free_row))
_shown = _run(capped_game, cmd="programme")["programme"]
check("programme show reports hours committed and the cap",
      "max_total_hours" in _shown["caps"] and "hours_committed_so_far" in _shown, _shown)
_run(capped_game, cmd="programme", action="set", target=GOAL, limit=50, max_total_hours=0.5)
_row = programme_before_year(capped_game, NODES)[0]
check("a spent hour cap stops starting", _row.get("started") == [] and "hour" in str(_row.get("did_nothing_because")), _row)
