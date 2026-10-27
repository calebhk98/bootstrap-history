"""player_command_fixes: sort words, a quote handler for every buy target, the rush preview's wording, the school spellings.
The parser, the sort and the dispatch tables run on inputs and stubs the test builds; the commands on a running game (a quote
for every target, the rush preview, founding a school) are test_player_commands_smoke."""
QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import check

from sim.ui.proto import buy_targets
from sim.ui.proto.dispatch_money import _BUY_HANDLERS
from sim.ui.proto.render_typed import render_pretty
from sim.ui.proto.techtree import _SORT_KEYS, _SORT_KEY_NAMES, _agent_available, _available_params, _sort_startable_list
from sim.ui.proto.typed import parse_typed

# --- 146: `available sort earns` sorts, and an unknown sort key is refused
spaced = parse_typed("available sort earns limit 200")
coloned = parse_typed("available sort:earns limit 200")
check("sort with a space parses like the colon form", spaced == coloned and spaced[0].get("sort") == "earns", (spaced, coloned))
reversed_form = parse_typed("available sort earns reverse limit 5")[0]
check("reverse parses as a flag next to the sort key", reversed_form.get("sort") == "earns" and reversed_form.get("reverse"), reversed_form)

earnings = {"low": 1.0, "mid": 5.0, "high": 9.0}
sorting_game = SimpleNamespace(venture_real_earnings=lambda node_id: earnings[node_id], project_cost=lambda node_id: 1.0)
earns_fn = _available_params({"sort": "earns"})[7]
check("sort earns orders the smallest earner first",
      _sort_startable_list(sorting_game, {}, ["mid", "high", "low"], earns_fn, False) == ["low", "mid", "high"])
check("sort earns reverse puts the biggest earner first",
      _sort_startable_list(sorting_game, {}, ["mid", "high", "low"], earns_fn, True) == ["high", "mid", "low"])
check("every advertised sort key is a sort", all(name in _SORT_KEYS for name in _SORT_KEY_NAMES))

empty_game = SimpleNamespace(nodes={}, fog=False, order=[], can_start=lambda node_id, _memo=None: False)
refused = _agent_available(empty_game, {}, {"sort": "bogus", "limit": 5})
check("an unknown sort key is refused, naming the valid ones",
      not refused["ok"] and refused["error"].cause == "unknown_sort_key" and "earns" in refused["error"].choices, refused)

# --- 147: every buy target has a handler (a quote for each, taken on a running game, is in the scenario)
check("a buy handler exists for every buy target", set(buy_targets.target_names()) == set(_BUY_HANDLERS),
      set(buy_targets.target_names()) ^ set(_BUY_HANDLERS))
check("every spelling of a target reaches a handler",
      all(buy_targets.canonical_target(spelling) in _BUY_HANDLERS
          for target, (spellings, _usage) in buy_targets.BUY_TARGETS.items() for spelling in (target,) + tuple(spellings)))

# --- 155: the rush preview is rendered as a preview
preview = {"ok": True, "preview": True, "nothing_changed": True, "count_would_start": 2, "would_start": [], "total_cost": 10.0,
           "total_annual_draw": 3.0, "total_founder_hours": 4.0, "filters": {}, "trade_bottlenecks": [], "risk_exposure": None,
           "count_not_started": 0, "not_started": [], "excluded": []}
check("a rush preview renders as a preview, not as '0 started'",
      "RUSH PREVIEW" in render_pretty("rush", preview), render_pretty("rush", preview)[:80])  # presentation: the preview heading
check("a rush that started things renders as a rush",
      "RUSH PREVIEW" not in render_pretty("rush", {"ok": True, "started": [], "count_started": 0, "count_not_started": 0}))  # presentation: the heading

# --- 156: buy school <trade> <n> reads as a school purchase whichever way it is spelled
def founded_by(text):
    """(target the words name, trade the school is founded for) when the typed line is run through the school handler."""
    founded = []
    school_game = SimpleNamespace(
        labour=SimpleNamespace(found_trade_school=lambda trade, seats: (founded.append((trade, seats)) or True, ""),
                               market_supply=lambda trade: 0.0),
        view=lambda name: (lambda: {"chemist": 1, "smith": 2}), capital=0.0)
    reply = parse_typed(text)[0]
    _BUY_HANDLERS[buy_targets.canonical_target(reply["what"])](school_game, reply, reply["n"])
    return buy_targets.canonical_target(reply["what"]), founded


for words in ("buy school chemist 1", "buy trade school chemist 1", "buy trade_school chemist 1"):
    check("%r founds a school for the trade named" % words, founded_by(words) == ("school", [("chemist", 1.0)]), founded_by(words))
check("the help example for schools is the form that founds one", founded_by("buy school smith 2") == ("school", [("smith", 2.0)]),
      founded_by("buy school smith 2"))
