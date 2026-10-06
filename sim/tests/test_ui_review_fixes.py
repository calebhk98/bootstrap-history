"""Review fixes in sim/ui, on stubs (no game is built): filler note, programme caps, note log rows,
replay order, portfolio paging input, goals cache."""

QUICK_TOPIC = True

import inspect
import weakref
from types import SimpleNamespace as _Namespace

from sim.engine import ui_port
from sim.ui import cli_agent, memory, replay
from sim.ui.proto import goals_watch, programme, programme_draw, stuck_advice
from sim.ui.proto.dispatch_programme import _cmd_programme
from sim.ui.proto.notes_store import NoteLine
from sim.ui.proto.parse_portfolio import _parse_portfolio
from sim.ui.proto.portfolio_scale import page_rows
from sim.ui.proto.state_log import _agent_log_filter_rows, _is_failure_line, _log_scrub

from .harness import check


class Stub(_Namespace):
    """A stand-in game that memory can key on weakly."""

    __hash__ = object.__hash__

    def __init__(self, **fields):
        super().__init__(**fields)
        self.state = _Namespace(interface={})

# 1. filler note only for starts off the remaining route, never under fog
graph = {"goal": {"pre": ["on_route"]}, "on_route": {"pre": []}, "side": {"pre": []}}
stuck_advice.saving_plan = lambda game: None
clear = Stub(fog=False, goal="goal", done=set())
check("a start on the route is not called filler", stuck_advice.filler_note(clear, "on_route", graph) is None)
check("a start off the route is filler", "filler" in (stuck_advice.filler_note(clear, "side", graph) or ""))
check("no filler claim under fog",
      stuck_advice.filler_note(Stub(fog=True, goal="goal", done=set()), "side", graph) is None)

# 2. programme caps count standing draw; pause on reserve; set keeps committed
programme_draw._rush_cost_left = lambda game, node_id: 800.0
running = Stub(capital=1000.0, active={"a": {}}, nodes={"a": {"yrs": 4}, "n": {"cat": "farming"}},
                          fog=False, year=100)
state = {"target": {"kind": "category", "value": "farming"},
         "caps": {"max_annual_draw": 300.0, "reserve_cash": 900.0}, "started_ids": ["a", "gone"]}
check("standing draw is cost left over years, finished ids forgotten",
      programme_draw.standing_draw(running, state) == 200.0 and state["started_ids"] == ["a"], state)
check("capital minus standing draw below the reserve pauses",
      "reserve" in (programme.pause_reason(running, state) or ""))
running.capital = 1200.0
check("enough capital after the standing draw does not pause", programme.pause_reason(running, state) is None)
command, why = programme._year_rush(running, state)
check("this year's rush gets the cap minus the standing draw", command["max_annual_draw"] == 100.0, command)
state["caps"]["max_annual_draw"] = 150.0
check("a cap used up by standing draw starts nothing", programme._year_rush(running, state)[0] is None)

owner = Stub(nodes={"n": {"cat": "farming"}}, fog=False, year=100)
_cmd_programme(owner, None, {"action": "set", "target": "farming", "max_total_cost": 500.0}, None)
memory.remembered(owner, "programme").update(committed=120.0, started_ids=["n"])
_cmd_programme(owner, None, {"action": "set", "target": "farming", "max_total_cost": 500.0}, None)
check("setting the same programme keeps what it committed",
      memory.remembered(owner, "programme")["committed"] == 120.0)
_cmd_programme(owner, None, {"action": "set", "target": "farming", "max_total_cost": 600.0}, None)
check("a changed cap resets what it committed", memory.remembered(owner, "programme")["committed"] == 0.0)

# 3. a note is never a failure line and is never fog-scrubbed
note = NoteLine("note: the mill was destroyed")
check("a note saying destroyed is not a failure", not _is_failure_line(note) and _is_failure_line(str(note)))
check("the failure filter keeps real failures only",
      [row[1][1] for row in _agent_log_filter_rows([(1, "mill destroyed"), (1, note)], None, None, True)]
      == ["mill destroyed"])
check("under fog a note is left as the player wrote it",
      _log_scrub(Stub(fog=True, fog_scrub=lambda text: "X"), note) is note)

# 4. known routes are applied after the session is loaded; carried ids accumulate
source = inspect.getsource(cli_agent.cmd_agent)
check("agent applies known routes after loading the session",
      source.index("load_state(sim, session)") < source.index("apply_known_routes"))
fogged = Stub(fog=True, revealed=set())
replay.apply_known_routes(fogged, ["a"], {"a", "b"})
replay.apply_known_routes(fogged, ["b"], {"a", "b"})
check("carried routes accumulate", memory.remembered(fogged, "replay")["carried"] == ["a", "b"])

# 5. portfolio input
rows = [{"id": "p", "blocker_kind": "calendar", "constraint": "calendar", "pool_rank_this_year": 1}]
trades = [{"trade": "Stone Mason", "projects_drawing_on_it": ["p"]}]
check("non-numeric offset is a clean error", "whole numbers" in (page_rows(rows, [], {"offset": "x"})[2] or ""))
check("non-numeric limit is a clean error", "whole numbers" in (page_rows(rows, [], {"limit": "many"})[2] or ""))
check("a JSON group is case-insensitive", page_rows(rows, [], {"group": "CALENDAR"})[1]["total"] == 1)
group = _parse_portfolio("portfolio", ["stone", "mason"], [], [], False)[0]["group"]
check("a multi-word trade name matches", page_rows(rows, trades, {"group": group})[1]["total"] == 1, group)

# 6. goals tree is cached per game
calls = []
ui_port.load = lambda: calls.append(1) or ({"meta": {}},)
ui_port.selectable_goals = lambda tree, nodes: []
first, second = Stub(nodes={}), Stub(nodes={})
goals_watch._catalog(first)
goals_watch._catalog(first)
check("one read per game", len(calls) == 1, calls)
goals_watch._catalog(second)
check("another game reads its own", len(calls) == 2, calls)
check("the cache does not keep a game alive", isinstance(goals_watch._TREES, weakref.WeakKeyDictionary))

from sim.ui.proto.typed import parse_typed as _parse_typed
check("a typed note keeps the words json and compact as written",
      _parse_typed("note keep the json export compact")[0] == {"cmd": "note", "text": "keep the json export compact"})
check("other commands still read json as the output mode", _parse_typed("state json")[0].get("json") is True)
