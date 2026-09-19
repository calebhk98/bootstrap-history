"""sort_nearest: regression checks, run individually with `--only sort_nearest`."""
from .harness import *  # noqa: F401,F403

# =============================================================================
# `available sort nearest` MEASURED DISTANCE TO BECOMING STARTABLE, NEVER
# DISTANCE TO A GOAL - and nothing said so. An external blind playthrough,
# goal set to the junction transistor, read "available sort nearest" as a
# goal-aware planner because nothing told it otherwise, and got agriculture.
# Renamed to fewest_missing (old spellings kept working); `stuck` now says
# outright, under fog, that its goal-aware branch is switched off rather
# than silently falling back to generic advice that looks like the real
# answer.
# =============================================================================
check("'fewest_missing' is the advertised sort key now, not the misleading "
      "'nearest'",
      "fewest_missing" in _protocol._SORT_KEY_NAMES and "nearest" not in _protocol._SORT_KEY_NAMES,
      _protocol._SORT_KEY_NAMES)
check("...but the old spelling still works, for any script already using it",
      "nearest" in _protocol._SORT_KEYS and "fewest_missing" in _protocol._SORT_KEYS,
      sorted(_protocol._SORT_KEYS))
_stuck_goal = sim(capital=1_000_000.0)
_stuck_goal.fog = True
_stuck_goal.revealed = set()
_stuck_out = S._agent_dispatch(_stuck_goal, NODES, {"cmd": "stuck"})
check("`stuck`, under fog with a goal set, says outright that it cannot "
      "check the goal's route - the same candour `rush` already has about "
      "its own limits - rather than silently giving generic advice with no "
      "explanation of what it could not do",
      "this_does_not_know_your_goal" in _stuck_out,
      _stuck_out.get("this_does_not_know_your_goal"))
_stuck_nofog = sim(capital=1_000_000.0)
_stuck_nofog.fog = False
check("...and says nothing of the kind with fog off, where the goal-aware "
      "branch actually runs",
      "this_does_not_know_your_goal" not in S._agent_dispatch(
          _stuck_nofog, NODES, {"cmd": "stuck"}),
      "fog off: no such field")


# --- JOB 3e: the founder's death is legible, not one line among many. A
# normal-play tester in mortal mode found it reported as one more EVENT in a
# long `step`, with the age nowhere but that one sentence. `sim()` has no
# mortal switch of its own - nothing in this file needed one before - so
# this builds the Sim directly, the same way `sim()` itself does.
s_fd = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
             civ=S.load_civ("rome_100ad"), cfg={"immortal": False, "start_capital": 1e9})
s_fd.goal, s_fd.done_year = GOAL, {}
s_fd.end_year = s_fd.cfg["start_year"] + 200
_step_fd = S._agent_dispatch(s_fd, NODES, {"cmd": "step", "years": 150})
check("the founder's death gets a field of its own in the step that carries "
      "it, not only a line in events",
      isinstance(_step_fd.get("the_founder_died_this_step"), dict),
      _step_fd.get("the_founder_died_this_step"))
check("...and the age is a number you can read, not prose you have to parse",
      isinstance((_step_fd.get("the_founder_died_this_step") or {})
                 .get("aged_about"), int),
      _step_fd.get("the_founder_died_this_step"))
check("...and `state` carries the age from then on, not only that one "
      "step's reply",
      _step_fd.get("founder_died_aged")
      == _step_fd["the_founder_died_this_step"]["aged_about"],
      (_step_fd.get("founder_died_aged"), _step_fd.get("the_founder_died_this_step")))
check("...and the step stopped there instead of running the rest of the "
      "150 years requested straight past it",
      _step_fd["year"] < s_fd.cfg["start_year"] + 150, _step_fd["year"])

# THE AGE SURVIVES A --session RESUME. `log` is not itself a saved field -
# see SAVE_FIELDS - so a naive read of it for the founder's age would go
# empty in a freshly constructed process, silently un-reporting an age
# `state` had already shown once. _founder_death_aged/_founder_death_year
# are saved fields precisely so this does not happen.
_sess_fd = os.path.join(ROOT, _rel("founder_death.json"))
S.save_state(s_fd, _sess_fd)
s_fd2 = S.Sim(NODES, ORDER, random.Random(1), events=False, manual=True,
             civ=S.load_civ("rome_100ad"))
s_fd2.goal, s_fd2.done_year = GOAL, {}
S.load_state(s_fd2, _sess_fd)
_st_fd2 = S._agent_dispatch(s_fd2, NODES, {"cmd": "state"})
check("the founder's age at death survives a save and a fresh process "
      "loading it back, not only the process that saw it happen",
      _st_fd2.get("founder_died_aged") == _step_fd.get("founder_died_aged")
      and _st_fd2.get("founder_died_aged") is not None,
      (_st_fd2.get("founder_died_aged"), _step_fd.get("founder_died_aged")))


# --- JOB 3f: a bulk start for the late game, so it is not pure typing.
s_ru = sim()
_ru = S._agent_dispatch(s_ru, NODES, {"cmd": "rush", "force": True})
# --- BREAK, round 12: two testers independently made this their worst finding.
# One wrote that a dead founder's run was "permanently unwinnable from that
# point" with the game never saying so; the other watched a corpse be offered
# 69 startable projects and accept one. The engine was not actually silent
# about the consequence - deputies carry the work, and with none the programme
# dissolves over twelve years - but nothing ever told the player either half.
_s_die = sim(capital=1000000.0, events=True)
_s_die.cfg["immortal"] = False
_s_die.life_left = 1.0
for _ in range(6):
    _s_die.step()
check("the founder's death says what it means for the run, not only that it happened",
      any("THE FOUNDER DIES" in message and "nobody to direct" in message
          for _, message in _s_die.log),
      [message for _, message in _s_die.log if "FOUNDER DIES" in message][:1])
check("...and the programme dissolving is counted down where a player sees it",
      any("DISSOLVING" in message and "ends at twelve" in message for _, message in _s_die.log),
      [message for _, message in _s_die.log if "DISSOLVING" in message][:1])

# --- BREAK, round 12: a developer's own change-log marker was shipped in the
# prose a player reads. 1,108 nodes carried "[AUDIT: ... See JOB 1 upkeep
# audit.]" in their note field, the win condition among them, naming the task
# numbering of the agent that had edited them. The reasoning for a change
# belongs in the commit message; the note field is what the player reads.
_leaks = sorted(node_id for node_id, value in NODES.items()
                if "AUDIT" in ((value.get("note") or "") + (value.get("name") or "")))
check("no developer change-log marker is shipped in player-facing prose",
      not _leaks, _leaks[:5])

# --- BREAK: three civilisations were told their own signature technology led
# nowhere. `why` decided what a node unlocks by scanning hard prerequisites
# only, so anything reached solely as one option of a req_any substitution
# group ("any of a steam engine, a water wheel or a horse will drive this")
# read as a dead end. Ten nodes were affected, among them the Norse clinker
# hull - which really has 466 nodes behind it - the Norse bog-iron bloomery,
# and the Mexica's chinampa. A play tester filed this against the Norse
# starting kit as "flagship technologies are dead ends in the graph".
from engine.protocol import _unlocked_by as _UB, _downstream_of as _DS
_ra_cases = ("sea_clinker_hull", "met_bloomery_bog_iron", "fud_chinampa")
for _k_ra in _ra_cases:
    _un = _UB(_k_ra, NODES)
    check("%s is not a dead end: something really does need it" % _k_ra,
          bool(_un), _un)
check("...and what rests on it is counted, not reported as nothing",
      all(len(_DS(node_id, NODES)) >= 1 for node_id in _ra_cases),
      {node_id: len(_DS(node_id, NODES)) for node_id in _ra_cases})
# THE REASON THE CACHED INDEX CANNOT DO THIS. The tree is a directed acyclic
# graph on `pre` and is NOT acyclic once req_any options are edges too: one
# example is hydrochloric_acid, whose sulfuric_acid_supply group offers
# chm_contact_sulfuric as an alternative to lead_chamber, and
# chm_contact_sulfuric needs cap_pure_4N, which needs analytical_chemistry,
# which needs hydrochloric_acid back again - a real cycle if that branch of
# the substitution is the one walked, even though a player who takes the
# other branch (lead_chamber) never sees it. A bitmask descendant index that
# assumes a DAG runs out of memory on cycles like this, which is exactly what
# happened when this fix was first attempted in data.py, so the walk that
# answers a player carries a visited set instead.
#
# naive14's point_contact_transistor/single_crystal fix (TOP_PROBLEMS #1)
# removed a DIFFERENT cycle that used to live here - junction_transistor ->
# point_contact_transistor -> (req_any option) silicon_path ->
# junction_transistor - because that edge was itself the bug: the node's own
# note said it did not need single_crystal or its silicon_path alternative at
# all. Losing that cycle is the fix working, not a regression, which is why
# the check below no longer hardcodes a path through junction_transistor.
def _cycle_on(edges_of):
    """Any node reachable from itself, following whatever edges are given."""
    seen_all = set()
    for root in sorted(NODES):
        if root in seen_all:
            continue
        stack, seen = [root], set()
        while stack:
            cur = stack.pop()
            for nxt in edges_of(cur):
                if nxt == root:
                    return root
                if nxt not in seen:
                    seen.add(nxt); stack.append(nxt)
        seen_all |= seen
    return None

check("the tree is acyclic on hard prerequisites, which is what closure() "
      "walks and why it must not follow substitutions",
      _cycle_on(lambda k: [prereq_id for prereq_id in NODES[k]["pre"] if prereq_id in NODES]) is None,
      _cycle_on(lambda k: [prereq_id for prereq_id in NODES[k]["pre"] if prereq_id in NODES]))

def _pre_and_single_option_any(node_id):
    node = NODES[node_id]
    out = [prereq_id for prereq_id in node["pre"] if prereq_id in NODES]
    for req_group in (node.get("req_any") or []):
        opts = req_group.get("options") or {}
        if len(opts) == 1:
            (opt,) = opts.keys()
            if opt in NODES:
                out.append(opt)
    return out
check("pre plus every single-option req_any edge is still acyclic over the "
      "whole tree - the safety margin the single-option walk rests on, since "
      "a multi-option group (two or more real alternatives) walked the same "
      "way genuinely can cycle (hydrochloric_acid -> chm_contact_sulfuric -> "
      "cap_pure_4N -> analytical_chemistry -> hydrochloric_acid is real) and "
      "must never be",
      _cycle_on(_pre_and_single_option_any) is None,
      _cycle_on(_pre_and_single_option_any))

def _pre_and_any(node_id):
    # req_any OPTIONS ARE NOT ALL NODES. A group can offer a MATERIAL as an
    # alternative to a technology ("any of lead_kg, mat_lead_sheet ..."), so a
    # walk over these edges has to skip anything that is not a node or it dies
    # on KeyError: 'lead_kg'. _unlocked_by is safe from this by construction,
    # because it only ever asks whether a node's options mention a given
    # node id, never walking through one.
    out = [prereq_id for prereq_id in NODES[node_id]["pre"] if prereq_id in NODES]
    for req_group in (NODES[node_id].get("req_any") or []):
        out.extend(option for option in sorted(req_group.get("options") or {}) if option in NODES)
    return out

# _cycle_on (above) is a root-reachability check that skips any node once it
# has been SEEN from an earlier root, so it can miss a cycle that does not
# happen to include whichever root sorted(NODES) tries first - it is safe
# for the two checks above because pre and pre-plus-single-option are both
# genuinely acyclic there (nothing to miss), but not a safe way to CONFIRM a
# cycle exists, so this checks direct reachability from the one node the
# cycle above was traced through instead.
def _reaches(start, target, edges_of):
    seen, stack = set(), [start]
    while stack:
        cur = stack.pop()
        for nxt in edges_of(cur):
            if nxt == target:
                return True
            if nxt not in seen:
                seen.add(nxt); stack.append(nxt)
    return False

check("...and NOT acyclic once every substitution option counts as an edge, "
      "which is why the cached bitmask index cannot answer this and a "
      "visited set must",
      _reaches("hydrochloric_acid", "hydrochloric_acid", _pre_and_any),
      "no cycle found through hydrochloric_acid")

# --- BREAK, round 12: `rush limit:1000` on turn one started 209 things at
# once, owing 90,944 founder-hours against a lifetime the game itself puts at
# about 72,000. The next step gave hours to exactly one of them, so "RUNNING
# (209)" was a fiction about 208 of them. Committing a couple of years of
# everyone's attention is a decision; committing four centuries of it is not.
_s_rush = sim(capital=5000000.0)
_r_rush = S._agent_dispatch(_s_rush, NODES, {"cmd": "rush", "limit": 1000})
_owed_rush = sum(NODES[entry["id"]]["ph"] for entry in (_r_rush.get("started") or []))
check("`rush` does not commit more hours than a couple of years can hold",
      _owed_rush <= _s_rush.director_pool() * 2.0 + max(
          NODES[entry["id"]]["ph"] for entry in (_r_rush.get("started") or [{"id": GOAL}])),
      (_owed_rush, _s_rush.director_pool()))
check("...and says why it stopped rather than silently starting fewer",
      any("would not make them go faster" in str(entry.get("why"))
          for entry in (_r_rush.get("not_started") or [])),
      [entry.get("why") for entry in (_r_rush.get("not_started") or [])][:1])

# --- BREAK, round 12: five scholars hired, five years stepped, the payroll
# read 5, 4, 3, 3, 2 and NOTHING said why. The rate was right all along
# (measured 0.825 survival over five years against 0.837 expected across forty
# seeds); it was the reporting that was missing, and from the chair it looked
# exactly like staff vanishing.
_s_att = sim(capital=10000000.0, events=False)
run_it(_s_att, "workshop_first", "school_founded", "freedman_staff")
_s_att.hire("scholar", 8)
for _ in range(12):
    _s_att.step()
check("losing people to death and better offers is announced, not silent",
      any("lose" in message and "scholar" in message for _, message in _s_att.log),
      [message for _, message in _s_att.log if "lose" in message][:2])

check("`rush` starts more than one thing in a single call",
      _ru.get("count_started", 0) >= 2, _ru.get("count_started"))
check("...and every id it reports started is actually active now",
      all(entry["id"] in s_ru.active or entry["id"] in s_ru.done for entry in _ru["started"]),
      [entry["id"] for entry in _ru["started"]])
check("...and a limit caps how many it actually begins",
      S._agent_dispatch(sim(), NODES, {"cmd": "rush", "limit": 1})["count_started"] == 1,
      None)

# FOG-SAFE: `can_start` already guarantees visibility (see is_visible's own
# docstring - "anything you could start right now is visible by
# definition"), so this is belt-and-braces: every id `rush` touches under
# fog really was one the fogged `available` list would also have shown.
s_ruf = sim()
s_ruf.fog = True
s_ruf.revealed = set()
_avf = {entry["id"] for entry in S._agent_available(s_ruf, NODES, {"all": True})["available"]}
_ruf = S._agent_dispatch(s_ruf, NODES, {"cmd": "rush", "force": True})
check("under fog, everything `rush` starts was already on the visible "
      "`available` list",
      all(entry["id"] in _avf for entry in _ruf["started"]),
      [entry["id"] for entry in _ruf["started"] if entry["id"] not in _avf])

# EVERY NEW COMMAND MUST BE ADVERTISED. Same check the suite already runs
# for the rest of KNOWN_COMMANDS, pinned here for the two just added so a
# future edit that forgets to wire one up fails immediately rather than
# waiting for the general sweep to notice.
check("'values' and 'rush' are in the list every unknown-command refusal "
      "advertises",
      "values" in S.KNOWN_COMMANDS and "rush" in S.KNOWN_COMMANDS,
      S.KNOWN_COMMANDS)


# --- BREAK: a player asked what opening `arithmetic_positional` (decimal
# positional notation) means, and how writing down zero creates money or has
# a cost. It doesn't: the node carried rev=300 and up=100 purely because
# is_venture() offers `open` to anything with either field set, with no
# distinction between a notation and a business. A prior pass that day had
# zeroed upkeep on 1,096 nodes it judged the same way but left their revenue
# alone, and revenue alone still satisfies is_venture()'s `or`, so the break
# survived half fixed. The rule applied here: a node earns as a concern only
# if there is something to open a door on - premises, staff, stock, or a
# trade a person actually practises for a fee - and not merely because
# knowing it happens to carry a rev figure. Notation, theorems, financial
# instruments, circuit theory, and farming/food-processing METHODS applied
# to a venture that already exists elsewhere in the tree all got their rev
# (and any leftover up) zeroed; genuinely practised trades and manufactured
# products did not.
check("opening `arithmetic_positional` is no longer offered - a notation is "
      "not a door to open",
      not sim().is_venture("arithmetic_positional")
      and NODES["arithmetic_positional"]["rev"] == 0
      and NODES["arithmetic_positional"]["up"] == 0,
      (NODES["arithmetic_positional"]["rev"], NODES["arithmetic_positional"]["up"]))

check("circuit theory (Black's 1927 feedback theorem) does not open as a "
      "concern the way the capacitor it improves still does",
      not sim().is_venture("el2_negative_feedback_stability_gain")
      and sim().is_venture("el2_capacitor_electrolytic"),
      (sim().is_venture("el2_negative_feedback_stability_gain"),
       sim().is_venture("el2_capacitor_electrolytic")))

check("a financial instrument (a cheque) is not itself a venture; the bank "
      "that uses one still is",
      not sim().is_venture("fin_cheque") and sim().is_venture("fin_deposit_bank"),
      (sim().is_venture("fin_cheque"), sim().is_venture("fin_deposit_bank")))

check("a husbandry method (hybridisation) does not open its own shop; the "
      "farm it improves still does",
      not sim().is_venture("ag2_hybridisation") and sim().is_venture("crop_rotation"),
      (sim().is_venture("ag2_hybridisation"), sim().is_venture("crop_rotation")))

# THE HARD MIDDLE, NOT ZEROED: an assay office is a trade a person practises
# for a fee - premises, hallmarking equipment, paying customers - same as the
# physician's practice and surveying business the fix was warned not to
# destroy by treating every revenue figure as if it were a notation.
check("a trade practised for a fee (an assay office) still opens as a "
      "concern, unlike a notation",
      sim().is_venture("fin_assay_office"), sim().is_venture("fin_assay_office"))

# AGGREGATE, SO A FUTURE EDIT CANNOT DRIFT BACK TOWARD EITHER MISTAKE. Before
# this fix, is_venture() offered 1,492 of the tree's 2,833 nodes to `open` as
# going concerns (Rome's own granted set aside); a check tester found the
# true figure for a Rome start was 1,493. This pins it well below that and
# well above zero, so a change that either re-inflates the notation-as-shop
# bug or blindly zeros revenue across the tree (destroying the real income
# the game depends on) fails here rather than shipping.
# ONE Sim, not one per node: is_venture() only reads self.nodes/self.granted,
# neither of which changes across k, so building a fresh Sim (~8ms) for each
# of 2,849 nodes was paying that cost 2,849 times over for a value that never
# moved - 22.6s of the suite's own time on a check that asserts nothing about
# any INDIVIDUAL Sim, only a count. Measured via ROME_TEST_PROFILE.
_venture_s = sim()
_venture_ct = sum(1 for node_id in NODES if _venture_s.is_venture(node_id))
check("the count of nodes offered to `open` as a concern is down from the "
      "break's 1,493, and not collapsed toward zero",
      1300 <= _venture_ct <= 1450, _venture_ct)
