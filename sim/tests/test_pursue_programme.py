"""pursue and programme: the route order, the caps, the pause conditions and the handlers run on a stub game the test builds
(a small tree, a capital, a year, hazards); the same commands on a running game, with a save and load, are
test_pursue_programme_scenario."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto import programme, programme_pause
from sim.ui.proto.dispatch_ventures import _rush_cap_refusal, _rush_caps
from sim.ui.proto.dispatch_programme import _cmd_programme
from sim.ui.proto.dispatch_pursue import _cmd_pursue
from sim.ui.proto.parse_pursue import _split
from sim.ui.proto.programme import programme_before_year
from sim.ui.proto.pursue import route_order, rush_command
from sim.ui.proto.render_programme import render_pursue, render_programme, render_programme_rows

NODES = {
    "goal": {"name": "Goal", "pre": ["mid"], "req_any": [], "yrs": 3, "cat": "tech"},
    "mid": {"name": "Mid", "pre": ["root"], "req_any": [], "yrs": 2, "cat": "tech"},
    "root": {"name": "Root", "pre": [], "req_any": [], "yrs": 1, "cat": "tech"},
    "long_root": {"name": "Long root", "pre": [], "req_any": [], "yrs": 5, "cat": "tech"},
    "side": {"name": "Side", "pre": [], "req_any": [], "yrs": 1, "cat": "craft"},
}
NODES["mid"]["pre"] = ["root", "long_root"]
STARTABLE = {"root", "long_root", "side"}


def a_game(capital=1000.0, startable=STARTABLE, fog=False, hazards=(), done=()):
    game = SimpleNamespace(
        nodes=NODES, done=set(done), active={}, can_start=lambda node_id, _memo=None: node_id in startable,
        project_cost=lambda node_id: {"root": 10.0, "long_root": 30.0, "side": 5.0}.get(node_id, 100.0),
        capital=capital, year=1000, civ={"hazards": list(hazards)}, fog=fog, goal="goal",
        state=SimpleNamespace(interface={}, scenario=SimpleNamespace(year=1000)), shortage_rows=[],
        hazard_figure=lambda name, hazard: hazard.get(name, 0.0), material_shortfall_t=lambda material: 0.0)
    game.view = lambda name: (lambda: game.shortage_rows)      # the standing material shortage, as rows
    return game


def ask(game, **command):
    return _cmd_programme(game, NODES, dict(cmd="programme", **command), None)


# --- the route: only members of the goal's closure, longest remaining chain first, cheaper first on ties
game = a_game()
check("the route lists the startable members of the goal's route, longest chain first",
      route_order(game, "goal") == ["long_root", "root"], route_order(game, "goal"))
check("a startable node off the route is not in it", "side" not in route_order(game, "goal"))
check("a node already done or active is not offered",
      route_order(a_game(done={"root"}), "goal") == ["long_root"]
      and "long_root" not in route_order(SimpleNamespace(**dict(vars(game), active={"long_root": {}})), "goal"))

# --- pursue: refusals before any rush
check("pursue refuses under fog", not _cmd_pursue(a_game(fog=True), NODES, {"cmd": "pursue"}, None)["ok"])
check("pursue refuses an unknown goal", not _cmd_pursue(game, NODES, {"cmd": "pursue", "goal": "no_such_node_anywhere"}, None)["ok"])
check("pursue refuses a goal that is done", not _cmd_pursue(a_game(done={"goal"}), NODES, {"cmd": "pursue", "goal": "goal"}, None)["ok"])
nothing = _cmd_pursue(a_game(startable=()), NODES, {"cmd": "pursue", "goal": "goal"}, None)
check("with nothing startable on the route pursue starts nothing and names its order",
      nothing["ok"] and nothing["started"] == [] and "order" in nothing["pursue"] and nothing["pursue"]["startable_on_route"] == 0, nothing)

# --- the rush a pursuit makes
command = rush_command(["a", "b"], caps={"max_total_cost": 5.0, "reserve_cash": None}, limit=3, preview=True)
check("a pursuit's rush names only the given ids in the given order, with the caps that were set",
      command["ids"] == ["a", "b"] and command["in_given_order"] and command["max_total_cost"] == 5.0
      and "reserve_cash" not in command and command["limit"] == 3 and command["preview"], command)

# --- caps: each stops the next project that would break it
caps = {"max_total_cost": 100.0, "max_annual_draw": 40.0, "reserve_cash": 20.0, "max_total_hours": 50.0}
spent = dict(budget=500.0, cost=10.0, draw=5.0, cost_so_far=0.0, draw_so_far=0.0)
check("a project within every cap is not refused", _rush_cap_refusal(None, caps, hours=10.0, hours_so_far=0.0, **spent) is None)
check("the hour cap refuses a project that would take the rush past it",
      _rush_cap_refusal(None, caps, hours=30.0, hours_so_far=30.0, **spent) is not None
      and _rush_cap_refusal(None, caps, hours=20.0, hours_so_far=30.0, **spent) is None)
check("a rush with no hour cap is not stopped by hours",
      _rush_cap_refusal(None, dict(caps, max_total_hours=None), hours=1e9, hours_so_far=1e9, **spent) is None)
hours_each = [40.0, 40.0, 40.0, 40.0]
committed, taken = 0.0, 0
for hours in hours_each:
    if _rush_cap_refusal(None, caps, hours=hours, hours_so_far=committed, **spent) is None:
        committed += hours
        taken += 1
check("hours committed in turn stay within the cap and fewer start than with no cap",
      taken == 1 and committed <= caps["max_total_hours"], (taken, committed))
parsed, error = _rush_caps({"max_total_hours": 12, "max_total_cost": None}, a_game())
check("an hour cap is read as hours, not money, and a cap not given is None",
      error is None and parsed["max_total_hours"] == 12.0 and parsed["max_total_cost"] is None, (parsed, error))
check("a negative hour cap is refused", _rush_caps({"max_total_hours": -1}, a_game())[1] is not None)

# --- the standing programme: set, show, pause, resume, clear
game = a_game()
check("with none set the programme is None", ask(game)["programme"] is None)
check("a programme cannot be paused before it is set", not ask(game, action="pause")["ok"])
reply = ask(game, action="set", target="goal", max_annual_draw=400.0, limit=50)
check("programme set", reply["ok"] and reply["programme"]["caps"].startswith("max_annual_draw"), reply)
ask(game, action="set", target="craft")
check("a category of work can be the target", game.state.interface["programme"]["target"] == {"kind": "category", "value": "craft"},
      game.state.interface["programme"]["target"])
check("an unknown target is refused", not ask(game, action="set", target="no_such_node_anywhere")["ok"])
check("a goal programme is refused under fog", not ask(a_game(fog=True), action="set", target="goal")["ok"])
check("a negative cap is refused", not ask(game, action="set", target="goal", max_total_cost=-1)["ok"])
check("pause settings reject a negative number", not ask(game, action="set", target="goal", pause_debt=-1)["ok"])
check("a limit below one is refused", not ask(game, action="set", target="goal", limit=0)["ok"])
ask(game, action="set", target="goal", pause_debt=500.0)
check("programme set takes a debt pause threshold", "pause_debt" in ask(game)["programme"]["pauses"])
check("pausing is shown", ask(game, action="pause")["programme"]["paused"] is True
      and ask(game, action="resume")["programme"]["paused"] is False)
ask(game, action="clear")
check("programme cleared", ask(game)["programme"] is None)
ask(game, action="set", target="goal", max_total_cost=50.0)
game.state.interface["programme"]["committed"] = 30.0
ask(game, action="set", target="goal", max_total_cost=50.0)
check("setting the same caps again keeps what was committed", game.state.interface["programme"]["committed"] == 30.0)
ask(game, action="set", target="goal", max_total_cost=80.0)
check("setting different caps starts the count again", game.state.interface["programme"]["committed"] == 0.0)

# --- what the programme does in a year, before any rush
def row_of(game):
    return programme_before_year(game, NODES)[0]


def pause_kind(game):
    """The kind of pause the programme holds now (None when it may act): the check the year makes before it rushes."""
    held = programme.pause(game, programme.state(game))
    return held[0] if held else None


game = a_game()
check("with no programme there is no row", programme_before_year(game, NODES) == [])
ask(game, action="set", target="goal", max_annual_draw=400.0, limit=50)
ask(game, action="pause")
row = row_of(game)
check("a paused programme says it did nothing and started nothing",
      row.get("did_nothing_kind") == "paused_by_player" and row["started"] == [] and row["spent"] == 0.0, row)
ask(game, action="resume")
game.capital = -10.0
check("a programme does nothing in debt", row_of(game).get("did_nothing_kind") == "in_debt")
ask(game, action="set", target="goal", reserve_cash=500.0)
game.capital = 100.0
check("a programme does nothing below its reserve floor", row_of(game).get("did_nothing_kind") == "below_reserve_floor")
ask(game, action="set", target="goal", max_total_cost=50.0)
game.state.interface["programme"]["committed"] = 50.0
check("a spent total cap stops starting", row_of(game).get("did_nothing_kind") == "total_cap_reached")
ask(game, action="set", target="goal", max_total_hours=10.0)
game.state.interface["programme"]["hours"] = 10.0
check("a spent hour cap stops starting", row_of(game).get("did_nothing_kind") == "hour_cap_total")
ask(game, action="set", target="goal", max_annual_hours=10.0)
game.state.interface["programme"]["hours_year"] = [game.year, 10.0]
check("a spent hour cap for the year stops starting",
      row_of(game).get("did_nothing_kind") == "hour_cap_this_year")
game.state.interface["programme"]["hours_year"] = [game.year - 1, 10.0]
check("last year's hours do not count against this year's cap",
      programme.hours_started_this_year(game, game.state.interface["programme"]) == 0.0)
reached = a_game(done={"goal"})
ask(reached, action="set", target="goal")
check("a goal already reached is said", row_of(reached).get("did_nothing_kind") == "goal_reached")
blocked = a_game(startable=())
ask(blocked, action="set", target="goal")
check("a route with nothing startable is said", row_of(blocked).get("did_nothing_kind") == "nothing_startable")

# --- the pause conditions the player sets: debt, war risk, shortage; each is reported and can auto-resume
game = a_game(capital=-900.0)
ask(game, action="set", target="goal", pause_debt=500.0)
row = row_of(game)
check("debt over the threshold pauses and says why",
      row.get("did_nothing_kind") == "debt_over_limit" and row.get("did_nothing_because"), row)
game.capital = -100.0
check("debt under the threshold does not pause on the debt condition",
      programme_pause.tripped(game, {"pause_debt": 500.0}) is None)

raiders = [{"name": "Raiders", "years": [999, 1030], "sack_chance": 0.4}]
game = a_game(hazards=raiders)
ask(game, action="set", target="goal", pause_war_risk=0.05)
row = row_of(game)
check("war risk over the threshold pauses and says why",
      row.get("did_nothing_kind") == "war_risk_over_limit" and row.get("did_nothing_because"), row)
check("a pause that is not auto-resume stays paused", ask(game)["programme"]["paused"])
game.civ["hazards"] = []
check("without auto_resume it waits for the player once the risk ends", pause_kind(game) == "war_risk_over_limit")
ask(game, action="resume")
check("resume works once the risk is gone", pause_kind(game) is None)
check("a hazard that has not begun is no risk now",
      programme_pause.war_risk(a_game(hazards=[{"name": "Later", "years": [1005, 1030], "sack_chance": 0.4}])) == 0.0)

game = a_game(hazards=raiders)
ask(game, action="set", target="goal", pause_war_risk=0.05, auto_resume=True)
check("an auto_resume programme pauses on war risk", row_of(game).get("did_nothing_kind") == "war_risk_over_limit")
game.civ["hazards"] = []
check("an auto_resume programme resumes when the risk clears",
      pause_kind(game) is None and not ask(game)["programme"]["paused"], pause_kind(game))

game = a_game()
ask(game, action="set", target="goal", pause_shortage=0.2, auto_resume=True)
game.shortage_rows = [{"material": "iron", "throughput": 0.5, "years": 1, "trend": "steady"}]
row = row_of(game)
check("a shortage past the threshold pauses and names the material",
      row.get("did_nothing_kind") == "shortage_over_limit" and row.get("did_nothing_material") == "iron", row)
game.shortage_rows = []
check("an auto_resume programme resumes when the shortage clears", pause_kind(game) is None)
game.shortage_rows = [{"material": "iron", "throughput": 0.9, "years": 1, "trend": "steady"}]
check("a shortage under the threshold does not pause", programme_pause.tripped(game, {"pause_shortage": 0.2}) is None)

# --- the typed line
check("typed parse reads pause and hour caps",
      _split(["max_total_hours:50", "pause_war_risk:0.1", "auto_resume"])[0]
      == {"max_total_hours": 50.0, "pause_war_risk": 0.1, "auto_resume": True})
check("typed parse reads the goal in the rest", _split(["goal_x", "limit=3", "preview"])[:2] == ({"limit": 3, "preview": True}, ["goal_x"]))
check("typed parse refuses a cap that is not a number", _split(["max_total_cost:lots"])[2] is not None)

# --- renderers on hand-written replies (presentation: how the programme and the pursuit read)
_row = {"year": 100, "what": "programme for goal X", "started": [{"id": "a", "name": "Alpha", "cost": 1200.0}],
        "skipped": [{"id": "b", "why": "not begun: over max_total_cost"}], "spent": 1200.0}
_lines = render_programme_rows([_row, {"year": 101, "what": "programme for goal X", "did_nothing_because": "in debt"}])
check("programme rows list starts and skips", any("Alpha" in line for line in _lines)  # presentation: row wording
      and any("skipped b" in line for line in _lines), _lines)
check("programme rows say why it did nothing", any("did nothing: in debt" in line for line in _lines), _lines)  # presentation: row wording
check("render_programme shows caps and pause", "(paused)" in render_programme(  # presentation: the paused marker
    {"ok": True, "programme": {"target": "goal X", "caps": "no caps", "paused": True,
                               "committed_so_far": 0, "runs": "yearly"}}))
check("render_pursue names the order", "critical path" in render_pursue(  # presentation: the order is named
    {"ok": True, "started": [], "pursue": {"name": "X", "startable_on_route": 0, "order": "critical path"}}))
