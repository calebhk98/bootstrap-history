"""state_help_disclosure: `state` is short by default, `state full` and `state <section>` widen it; `help commands` is an index, a group, or a paged full listing."""

QUICK_TOPIC = True

from .harness import *  # noqa: F401,F403
from sim.ui.proto import command_registry
from sim.ui.proto.help import _agent_help
from sim.ui.proto.render_screen_state import render_state
from sim.ui.proto.render_screen_state_views import SECTIONS
from sim.ui.proto.typed import parse_typed


class _Stub:
    fog = False


_reply = {"year": 100, "capital": 5000.0, "net_per_year": -10.0, "founder_alive": True,
          "founder_hours_available": 2000, "goal": "some_goal", "employees": {"smith": 2},
          "employees_total": 2, "annual_wage_bill": 100.0, "reputation": 1, "protection": 0.0,
          "scandal": 0, "eminence": 0, "done_earned": 0, "done_granted": 1, "done_count": 1,
          "active": {"a_project": {"founder_hours_total": 10, "founder_hours_left": 5,
                                   "still_to_pay": 3, "waiting_on": "money"}}}

_short = render_state(dict(_reply, state_view="short"))
_full = render_state(_reply)
check("short state keeps situation, what to do, goal and risks and drops the detail",
      all(word in _short for word in ("Money:", "You:", "WHAT YOU CAN DO NOW", "Goal:", "AHEAD:"))
      and not any(word in _short for word in ("EMPLOY:", "STANDING:", "RUNNING")), _short)
check("short state ends with one footer naming every section and `state full`",
      _short.splitlines()[-1].startswith("more:") and "state full" in _short.splitlines()[-1]
      and all(name in _short.splitlines()[-1] for name in SECTIONS), _short.splitlines()[-1])
check("without a view the screen prints every section, as before",
      all(word in _full for word in ("EMPLOY:", "STANDING:", "RUNNING (1)")), _full)
check("a reply that says full is the same screen",
      render_state(dict(_reply, state_view="full")) == _full)
for _name in SECTIONS:
    _one = render_state(dict(_reply, state_view=_name))
    check("state %s prints just that section" % _name, bool(_one.strip()) and "more:" not in _one, _one)
check("the staff section is the employ block only",
      render_state(dict(_reply, state_view="staff")).strip().startswith("EMPLOY:"))

check("`state <section>` parses to a view; plain and full parse as before",
      parse_typed("state standing")[0].get("view") == "standing"
      and "view" not in parse_typed("state")[0] and "view" not in parse_typed("state full")[0])
_bad, _error = parse_typed("state nonsense")
check("an unknown state section names the sections", _bad is None and "standing" in _error, _error)
_bad, _error = parse_typed("stat")
check("an unknown command suggests close command names", _bad is None and "state" in _error, _error)

_index = _agent_help(_Stub(), "commands index")
check("`help commands` is a short index with one line per group and its count",
      set(_index["groups"]) == set(command_registry.grouped())
      and all(str(len(names)) in _index["groups"][group]
              for group, names in command_registry.grouped().items())
      and "commands" not in _index, _index)
_group = next(iter(command_registry.grouped()))
_page = _agent_help(_Stub(), "commands " + _group)
check("`help commands <group>` lists exactly that group",
      list(_page["commands"]) == command_registry.grouped()[_group], list(_page["commands"]))
check("an unknown group suggests the real ones", "groups" in _agent_help(_Stub(), "commands nonesuch"))
_all = _agent_help(_Stub(), "commands all")
check("`help commands all` and the bare JSON topic list every command",
      set(command_registry.COMMANDS) <= set(_all["commands"]) and _agent_help(_Stub(), "commands")["commands"] == _all["commands"])
_first = _agent_help(_Stub(), "commands all limit 5")
_second = _agent_help(_Stub(), "commands all limit 5 offset 5")
check("the full listing pages with limit and offset",
      len(_first["usage"]) == 5 and _first["paging"]["next"].endswith("offset 5")
      and not set(_first["usage"]) & set(_second["usage"]), (_first["paging"], _second["paging"]))
