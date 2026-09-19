"""player_log: regression checks, run individually with `--only player_log`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# THE PLAYER'S OWN LOG. The commonest complaint across eleven rounds of
# testing was some version of "failures are silent" - the engine has always
# kept self.log, and there was no command to read it back. `log` (alias
# `history`) shows it, paged, filterable, and searchable, and it is hard-
# capped so a script asking for everything at once cannot get it.
# =============================================================================
from engine.protocol import _agent_log as _AL

r, _, _ = proto([{"cmd": "start", "id": "units_standards"},
                 {"cmd": "hire", "trade": "smith", "n": 2},
                 {"cmd": "step", "years": 1},
                 {"cmd": "fire", "trade": "smith", "n": 1},
                 {"cmd": "log"}])
_entries = r[-1].get("entries") or []
check("log records what the player did - starting, hiring, letting go - not "
      "just what the engine did on its own",
      any("started" in entry["what"] for entry in _entries)
      and any("smith" in entry["what"] and "taken on" in entry["what"]
              for entry in _entries)
      and any("smith" in entry["what"] and "go" in entry["what"]
              for entry in _entries),
      _entries)
check("log defaults to most-recent-first",
      _entries[0]["year"] >= _entries[-1]["year"],
      [entry["year"] for entry in _entries])

# --- never dumped in one go, however large a limit is asked for or however
# long the history actually is.
s_lg = sim(civ="rome_100ad", manual=False)
for _y in range(3000):
    s_lg.log.append((100 + _y % 500, "hired 1 smith"))
_huge = _AL(s_lg, {"limit": 1000000})
check("the log is hard-capped regardless of what limit is asked for",
      len(_huge["entries"]) <= 100, len(_huge["entries"]))
_default = _AL(s_lg, {})
check("...and defaults to a short recent window with no limit given at all",
      len(_default["entries"]) <= 25, len(_default["entries"]))

# --- filtering to failures specifically, which is what every round of
# testing actually asked for.
s_lf = sim()
s_lf.log = [(100, "started: Foo"), (101, "FAILED at Foo: it did not work."),
            (102, "hired 1 smith")]
_fails = _AL(s_lf, {"failures": True})
check("'failures' filters the log to only the bad news",
      len(_fails["entries"]) == 1 and "FAILED" in _fails["entries"][0]["what"],
      _fails["entries"])

# --- fog: a log line minted while something was visible must not go on
# naming it once fog would refuse to answer `why` about it - whether it was
# forgotten later, or never visible to begin with.
s_lz = sim()
s_lz.fog = True
s_lz.revealed = set()
s_lz.log = [(100, "completed: Point-contact transistor")]
_scrubbed = _AL(s_lz, {})["entries"][0]["what"]
check("the log redacts a name fog would refuse to answer `why` about",
      "Point-contact transistor" not in _scrubbed and "transistor" not in _scrubbed.lower(),
      _scrubbed)
s_lz.fog = False
_unscrubbed = _AL(s_lz, {})["entries"][0]["what"]
check("...but only under fog - with it off the log reads exactly as written",
      "Point-contact transistor" in _unscrubbed, _unscrubbed)

# --- a search cannot be used to confirm the existence of something a
# redacted line would otherwise hide.
s_lz.fog = True
_hidden_search = _AL(s_lz, {"find": "transistor"})
check("a search cannot smuggle out what the redaction just hid",
      _hidden_search["count"] == 0, _hidden_search)

# --- discoverable, per the task's own standard: `help` names it, and the
# screen itself explains its filters without anyone reading the source.
r, _, _ = proto([{"cmd": "help", "topic": "commands"}])
check("log is advertised in help, not just implemented",
      "log" in (r[0].get("help") or {}).get("commands", {}),
      list((r[0].get("help") or {}).get("commands", {}).keys()))
r, _, _ = proto([{"cmd": "log"}])
check("the log screen itself explains how to filter and page it",
      "to_filter_or_sort" in r[0] and "failures" in r[0]["to_filter_or_sort"],
      r[0].get("to_filter_or_sort"))

# --- typed front end: a player at a keyboard, not a script, has to be able
# to reach all of this too.
from engine.protocol import parse_typed as _PT
_cmd, _err = _PT("log failures find plague since 200 oldest limit 5")
check("the typed form reaches every filter the JSON protocol has",
      _cmd == {"cmd": "log", "failures": True, "find": "plague",
               "since": 200, "order": "oldest", "limit": 5},
      _cmd)
# --- BREAK: the automatic behaviours read as the engine offering to play
# well on your behalf, and they are nothing of the kind. Testers turned them
# on and reported the result as a defect: "policy auto_hire true destroyed my
# run in eight years", "auto_train quietly bankrupted me", "policy auto_hire
# on quietly destroyed my economy". They were right about what happened and
# wrong about what these are, and this screen never told them.
_pl, _, _ = proto([{"cmd": "policy"}])
check("the policy screen says these are approximations, not optimal play",
      "approximation" in str(_pl[0].get(
          "these_are_approximations_not_optimal_play")).lower()
      or "rule of thumb" in str(_pl[0].get(
          "these_are_approximations_not_optimal_play")).lower(),
      _pl[0].get("these_are_approximations_not_optimal_play"))
_pl_txt = _RP("policy", _pl[0])
check("...and a player reads that before the list of switches, not after it",
      _pl_txt.index("rule of thumb") < _pl_txt.index("auto_bribe"),
      _pl_txt[:200])
check("...and every switch the game offers says what it does",
      not [switch_name for switch_name in _pl[0]["policy"]
           if not (_pl[0].get("what_each_does") or {}).get(switch_name)],
      [switch_name for switch_name in _pl[0]["policy"]
       if not (_pl[0].get("what_each_does") or {}).get(switch_name)])
check("...and no line of that screen runs past the width everything else wraps to",
      max(len(line) for line in _pl_txt.splitlines()) <= 78,
      max(_pl_txt.splitlines(), key=len))

_cmd2, _err2 = _PT("why horizontal loom")
check("a multi-word typed name is not truncated to its first word",
      _cmd2 == {"cmd": "why", "id": "horizontal loom"}, _cmd2)
# --- NEW: a goods-producing concern sells into a MARKET, not a fixed number.
# A playtester's own example: "an automated loom should be making a lot of
# money early on, but the profit should decrease over time once supply
# starts going up... up to some point." See economy.py's GOODS_CATEGORIES
# and goods_market_factor() for the model this exercises.
s_lm = sim(civ="rome_100ad", capital=500000.0)
s_lm.done.add("tex_power_loom")
s_lm.done_year["tex_power_loom"] = 100
s_lm._done_changed()
s_lm.artisans = s_lm.scholars = 80.0
s_lm.employees["carpenter"] = 1.0
s_lm.year = 100
_ok_lm, _msg_lm = s_lm.open_venture("tex_power_loom")
check("a power loom can be opened, to exercise what it then earns",
      _ok_lm, _msg_lm)
check("a freshly opened power loom earns what the tree quotes, not less - "
      "the first turn is not where this is supposed to show up",
      abs(s_lm.goods_market_factor("tex_power_loom") - 1.0) < 1e-9,
      s_lm.goods_market_factor("tex_power_loom"))

s_lm.year = 130        # thirty years of custom later
_factor_30 = s_lm.goods_market_factor("tex_power_loom")
check("thirty years on, the same loom earns less, because supply of cloth - "
      "yours and everyone else's - has caught up with demand",
      _factor_30 < 0.95, _factor_30)
check("...but not next to nothing: this kind of good keeps a floor price",
      _factor_30 > 0.5, _factor_30)

s_lm.year = 400        # long after the market has fully adjusted
_factor_400 = s_lm.goods_market_factor("tex_power_loom")
check("...and once the market is saturated it flattens, rather than "
      "decaying away for ever",
      abs(_factor_400 - _factor_30) < 0.02, (_factor_30, _factor_400))

# --- The brief's own worked example, almost to the denarius: a concern that
# earned 400 a year now earning about 280, and a player told why rather
# than left to notice the number moved.
s_nt = sim(civ="rome_100ad", capital=500000.0)
s_nt.done.add("tex_horizontal_loom")
s_nt.done_year["tex_horizontal_loom"] = 100
s_nt._done_changed()
s_nt.artisans = s_nt.scholars = 20.0
s_nt.employees["carpenter"] = 1.0
s_nt.year = 100
s_nt.open_venture("tex_horizontal_loom")
s_nt.year = 400
_note = s_nt.goods_market_note("tex_horizontal_loom")
check("a player reading `ventures` or `money` is told WHY a concern earns "
      "less than the tree quotes, in plain language",
      bool(_note) and "tree quotes" in _note and "actually earns" in _note,
      _note)
_vrow_nt = S._agent_dispatch(s_nt, NODES, {"cmd": "ventures"})
_row_nt = next(row for row in _vrow_nt["running"]
               if row["id"] == "tex_horizontal_loom")
check("...and `ventures` itself carries the same explanation on the row",
      "market" in _row_nt and bool(_row_nt["market"]), _row_nt)
_money_nt = S._agent_dispatch(s_nt, NODES, {"cmd": "money"})
check("...and `money` says the same thing in aggregate",
      bool(_money_nt.get("the_market_you_sell_into")), _money_nt.get("the_market_you_sell_into"))

# --- Services, institutions and patronage are untouched: the brief asked
# for exactly that distinction, and this is the honest way to check it -
# a node outside GOODS_CATEGORIES gets a factor of exactly 1.0 no matter
# how old the concern is.
s_sv = sim(civ="rome_100ad", capital=500000.0)
_nongood = next(node_id for node_id in sorted(NODES)
               if NODES[node_id].get("cat") not in s_sv.GOODS_CATEGORIES
               and s_sv.is_venture(node_id) and not NODES[node_id]["pre"])
s_sv.done.add(_nongood)
s_sv.done_year[_nongood] = 100
s_sv._done_changed()
s_sv.artisans = s_sv.scholars = 50.0
s_sv.year = 100
s_sv.open_venture(_nongood)
s_sv.year = 500
check("a service, institution or anything outside the goods categories "
      "still pays the tree's flat figure centuries later, exactly as before",
      s_sv.goods_market_factor(_nongood) == 1.0, _nongood)

# --- The ledger's own "parts add up to the total" invariant has to survive
# this too, with an aged loom actually pulling the total below the flat
# figure - not just in the already-passing young-economy case above.
s_ld = sim(civ="rome_100ad", capital=500000.0)
s_ld.done.add("tex_power_loom")
s_ld.done_year["tex_power_loom"] = 100
s_ld._done_changed()
s_ld.artisans = s_ld.scholars = 80.0
s_ld.employees["carpenter"] = 1.0
s_ld.year = 100
s_ld.open_venture("tex_power_loom")
s_ld.year = 300
_src_ld = s_ld.revenue_sources()
check("the ledger's parts still add up to the revenue it states, with an "
      "aged goods concern pulling the total down",
      abs(sum(_src_ld.values()) - s_ld.revenue()) < 1.0,
      (sum(_src_ld.values()), s_ld.revenue()))

# --- Population and reach are supposed to matter - the brief says market
# size "should depend on the population, on what that society can pay, and
# on how far your goods can travel." A smaller, poorer, less-connected
# civilization should see the SAME concern's margin erode faster.
s_small = sim(civ="norse_900ad", capital=500000.0)
s_small.done.add("tex_power_loom")
s_small.done_year["tex_power_loom"] = 100
s_small._done_changed()
s_small.artisans = s_small.scholars = 80.0
s_small.employees["carpenter"] = 1.0
s_small.year = 100
s_small.open_venture("tex_power_loom")
s_small.year = 110      # ten years in - before EITHER market is fully saturated
_small_factor = s_small.goods_market_factor("tex_power_loom")
s_lm.year = 110
_rome_10 = s_lm.goods_market_factor("tex_power_loom")
check("a smaller, poorer civilization's market for the same good saturates "
      "faster than Rome's did at the same age",
      _small_factor < _rome_10, (_small_factor, _rome_10))

