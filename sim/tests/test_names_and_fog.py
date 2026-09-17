"""names_and_fog: split verbatim from the old test_regressions.py (original lines 6722-6867).

Moving contiguous blocks verbatim: no check below was reformatted, reworded or otherwise touched in the split.
"""
from .harness import *  # noqa: F401,F403

# =============================================================================
# NAMES, NOT JUST IDS: testers found it jarring that `state` and `available`
# print a human NAME ("Reaper-binder") while every command that acts on a
# technology took only the machine id ("ag2_reaper_binder"). `why`, `start`,
# `stop`, `bounty`, `mothball`, `restore` and `open` now all resolve a typed
# name to its id first - case and punctuation folded, a unique prefix or
# distinctive substring both work - and refuse with the real ids to choose
# between when the name is not unique. Ids keep working unchanged, because
# scripts and the `agent` protocol depend on them.
# =============================================================================
r, _, _ = proto([{"cmd": "why", "id": "Reaper-Binder"}])
check("a typed name resolves to the id, case and punctuation folded",
      r[0].get("ok") and r[0].get("id") == "ag2_reaper_binder",
      r[0].get("error") or r[0].get("id"))

r, _, _ = proto([{"cmd": "why", "id": "ag2_balanced_ration"}])
_printed_name = r[0].get("name")
r2, _, _ = proto([{"cmd": "why", "id": _printed_name}])
check("a name copied verbatim off another screen resolves the same way",
      r2[0].get("ok") and r2[0].get("id") == "ag2_balanced_ration",
      (_printed_name, r2[0].get("error")))

r, _, _ = proto([{"cmd": "why", "id": "loom"}])
check("an ambiguous name is refused with the real ids to choose between",
      not r[0].get("ok") and r[0].get("error", "").count("(") >= 2
      and "tex_horizontal_loom" in r[0]["error"],
      r[0].get("error"))

# --- fog: the ambiguous-name list must never offer more than full visibility
# would, and on a fresh game it must offer strictly less (or the filter is a
# no-op that only looks like it is doing something).
import re as _re_names
_full, _, _ = proto([{"cmd": "why", "id": "loom"}])
_fog, _, _ = proto([{"cmd": "why", "id": "loom"}], fog=True, kit="poor_scholar")
_full_ids = set(_re_names.findall(r"(\w+) \(", _full[0].get("error", "")))
_fog_ids = set(_re_names.findall(r"(\w+) \(", _fog[0].get("error", "")))
check("under fog, an ambiguous name never offers more candidates than full "
      "visibility would",
      _fog_ids and _fog_ids < _full_ids,
      (sorted(_fog_ids), sorted(_full_ids)))

# --- the goal's NAME gets the same one exception its id already has on
# `why` alone - see protocol.py's _goal_why comment - and nothing widens it.
r, _, _ = proto([{"cmd": "why", "id": NODES[GOAL]["name"]},
                 {"cmd": "start", "id": NODES[GOAL]["name"]},
                 {"cmd": "why", "id": "transistor"}], fog=True, kit="poor_scholar")
check("why on the goal's exact printed name is the one thing fog answers",
      r[0].get("ok") and r[0].get("id") == GOAL,
      r[0].get("error"))
check("...but the exception does not widen to other commands on the same name",
      not r[1].get("ok") and "never heard of" in r[1].get("error", ""),
      r[1].get("error"))
check("...and a vague guess does not silently resolve to the goal",
      not r[2].get("ok") and GOAL not in r[2].get("error", "")
      and "aiming at" not in r[2].get("error", ""),
      r[2].get("error"))


# =============================================================================
# FOG LEAK #1, AS THE PLAYER FOUND IT: with fog on, `why aqueduct_survey` -
# a name for nothing in the tree - suggested six ids as "did you mean", and
# nobody had checked whether all six were things the player had actually
# heard of. Verified the honest way: re-ask `why` about every id the
# suggestion offered, and none of them may come back "never heard of".
# =============================================================================
r, _, _ = proto([{"cmd": "why", "id": "aqueduct_survey"}], fog=True, kit="poor_scholar")
_sugg = [suggestion.strip() for suggestion in
         r[0].get("error", "").split("Did you mean:")[-1].split(",") if suggestion.strip()] \
        if "Did you mean" in r[0].get("error", "") else []
_checks = [{"cmd": "why", "id": sid} for sid in _sugg]
_verify, _, _ = (proto(_checks) if _checks else ([], "", 0))
check("the did-you-mean list under fog only ever suggests things the player "
      "has heard of",
      all("never heard of" not in x.get("error", "") for x in _verify),
      [(sid, x.get("error")) for sid, x in zip(_sugg, _verify)
       if "never heard of" in x.get("error", "")])


# =============================================================================
# FOG LEAK #2: `available`'s "HEARD OF, CANNOT BEGIN YET" block used to
# ignore `find`/`subject` and print its usual nearest-first twenty-five
# regardless of the search, so a search that matched nothing startable still
# dumped seven things nobody asked about. Reproduced exactly as found: reveal
# something (units_standards unlocks several), then search for nonsense.
# =============================================================================
s_hd = sim(civ="rome_100ad", manual=False)
s_hd.fog = True
s_hd.revealed = set()
S._agent_dispatch(s_hd, NODES, {"cmd": "start", "id": "units_standards"})
for _ in range(2):
    s_hd.step()
_hd_nonsense = S._agent_available(s_hd, NODES, {"find": "zzzznonexistentxyz"})
_hd_plain = S._agent_available(s_hd, NODES, {"limit": 50})
check("a search matching nothing startable does not also dump the generic "
      "heard-of list",
      not _hd_nonsense.get("heard_of_but_cannot_begin"),
      _hd_nonsense.get("heard_of_but_cannot_begin"))
check("...but the same heard-of list still shows up unfiltered when no "
      "search was asked for",
      _hd_plain.get("heard_of_but_cannot_begin"),
      "empty heard-of list with no search active")
_hd_match = S._agent_available(s_hd, NODES, {"find": "corpus"})
check("...and a search that DOES match a heard-of item still shows it",
      any(entry["id"] == "corpus_written"
          for entry in _hd_match.get("heard_of_but_cannot_begin") or []),
      _hd_match.get("heard_of_but_cannot_begin"))


# =============================================================================
# SORT AND PAGE, ALL THE WAY TO THE END. Several screens truncated to 25 rows
# and said "N more, nearest first" with no way to ask for a different order.
# `available` now takes `sort` (price/hours/years/earns/upkeep/risk/alpha/
# nearest) and `reverse`, on both the startable list and the heard-of one.
# =============================================================================
r, _, _ = proto([{"cmd": "available", "limit": 10, "sort": "risk", "reverse": True}])
_risks = [entry["risk"] for entry in r[0]["available"]]
check("available can be sorted by risk, reversed, all the way through the page",
      _risks == sorted(_risks, reverse=True), _risks)

_pretty_sorted = _RP("available", r[0])
_json_first_id = r[0]["available"][0]["id"]
_json_last_id = r[0]["available"][-1]["id"]
check("the printed table keeps the JSON's sort order rather than re-sorting "
      "back to cost",
      -1 < _pretty_sorted.find(_json_first_id) < _pretty_sorted.find(_json_last_id),
      (_json_first_id, _json_last_id, _pretty_sorted))

r2, _, _ = proto([{"cmd": "available", "limit": 3}])
check("a plain page still defaults to cheapest first",
      [entry["cost"] for entry in r2[0]["available"]]
      == sorted(entry["cost"] for entry in r2[0]["available"]),
      [entry["cost"] for entry in r2[0]["available"]])

# --- the tester's other question: does `available` show staff requirements,
# and is the legend for them nearby rather than a screen away.
_staff_pretty = _RP("available", r2[0])
_lines = _staff_pretty.splitlines()
_staff_hdr = next(i for i, line in enumerate(_lines) if "STAFF" in line)
_staff_legend = next((i for i, line in enumerate(_lines)
                      if "STAFF is the standing people" in line), None)
check("the STAFF column has its legend within a few lines of the table, "
      "not a screen away",
      _staff_legend is not None and _staff_legend - _staff_hdr < 15,
      (_staff_hdr, _staff_legend))


