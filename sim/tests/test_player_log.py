"""The player's own `log`, the policy screen's switches, and the ledger of what a concern earns."""
from .harness import *  # noqa: F401,F403
from sim.ui.protocol import _agent_log as _AL, parse_typed as _PT


def ask(game, **command):
    return S._agent_dispatch(game, NODES, command)


# --- The log records what the player did, not just what the engine did.
game = sim()
ask(game, cmd="start", id="units_standards")
ask(game, cmd="hire", trade="smith", n=2)
ask(game, cmd="fire", trade="smith", n=1)
_entries = ask(game, cmd="log").get("entries") or []
check("log records what the player did - starting, hiring, letting go - not "
      "just what the engine did on its own",
      any("started" in entry["what"] for entry in _entries)
      and any("smith" in entry["what"] and "taken on" in entry["what"] for entry in _entries)
      and any("smith" in entry["what"] and "go" in entry["what"] for entry in _entries),
      _entries)
check("log defaults to most-recent-first",
      _entries[0]["year"] >= _entries[-1]["year"], [entry["year"] for entry in _entries])

# --- Never dumped in one go, however large a limit is asked for.
game.log = [(100 + index % 500, "hired 1 smith") for index in range(3000)]
check("the log is hard-capped regardless of what limit is asked for",
      len(_AL(game, {"limit": 1000000})["entries"]) <= 100)
check("...and defaults to a short recent window with no limit given at all",
      len(_AL(game, {})["entries"]) <= 25)

# --- Filtering to failures.
game.log = [(100, "started: Foo"), (101, "FAILED at Foo: it did not work."), (102, "hired 1 smith")]
_fails = _AL(game, {"failures": True})
check("'failures' filters the log to only the bad news",
      len(_fails["entries"]) == 1 and "FAILED" in _fails["entries"][0]["what"], _fails["entries"])

# --- Fog: a log line must not name what fog would refuse to answer `why` about.
game.fog = True
game.revealed = set()
game.log = [(100, "completed: Point-contact transistor")]
_scrubbed = _AL(game, {})["entries"][0]["what"]
check("the log redacts a name fog would refuse to answer `why` about",
      "Point-contact transistor" not in _scrubbed and "transistor" not in _scrubbed.lower(), _scrubbed)
_hidden_search = _AL(game, {"find": "transistor"})
check("a search cannot smuggle out what the redaction just hid", _hidden_search["count"] == 0, _hidden_search)
game.fog = False
_unscrubbed = _AL(game, {})["entries"][0]["what"]
check("...but only under fog - with it off the log reads exactly as written",
      "Point-contact transistor" in _unscrubbed, _unscrubbed)

# --- The typed front end reaches every filter, and multi-word names survive.
_cmd, _err = _PT("log failures find plague since 200 oldest limit 5")
check("the typed form reaches every filter the JSON protocol has",
      _cmd == {"cmd": "log", "failures": True, "find": "plague", "since": 200, "order": "oldest", "limit": 5}, _cmd)
_cmd2, _err2 = _PT("why horizontal loom")
check("a multi-word typed name is not truncated to its first word",
      _cmd2 == {"cmd": "why", "id": "horizontal loom"}, _cmd2)

# --- The automatic behaviours are approximations, and every switch says what it does.
_policy = ask(game, cmd="policy")
check("the policy screen says these are approximations, not optimal play",
      bool(_policy.get("these_are_approximations_not_optimal_play")), _policy.keys())
check("...and every switch the game offers says what it does",
      not [name for name in _policy["policy"] if not (_policy.get("what_each_does") or {}).get(name)],
      [name for name in _policy["policy"] if not (_policy.get("what_each_does") or {}).get(name)])

# --- The ledger's parts add up to the total, with an aged loom among the concerns.
ledger = sim(civ="rome_100ad", capital=500000.0)
ledger.done.add("tex_power_loom")
ledger.done_year["tex_power_loom"] = 100
ledger._done_changed()
ledger.artisans = ledger.scholars = 80.0
ledger.employees["carpenter"] = 1.0
ledger.year = 100
ledger.open_venture("tex_power_loom")
ledger.year = 300
_sources = ledger.revenue_sources()
check("the ledger's parts still add up to the revenue it states, with an aged goods concern running",
      abs(sum(_sources.values()) - ledger.revenue()) < 1.0, (sum(_sources.values()), ledger.revenue()))
