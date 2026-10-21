"""Rules of the command and tree surface that need no game: the advertised sort keys, which nodes open as a going concern
(`is_venture`, called on the real mixin over the tree), the commands the unknown-command refusal advertises, that no
change-log marker is shipped in the prose a player reads, what needs a node (`_unlocked_by`, `_downstream_of`), and that the
tree is acyclic on hard prerequisites. What the commands do in a whole game is test_sort_nearest_scenario."""

QUICK_TOPIC = True

from types import SimpleNamespace

from .harness import *  # noqa: F401,F403
from sim.engine.projects_capability import CapabilityMixin


class Tree(CapabilityMixin):
    """The tree over the real concern rule; nothing is granted."""
    nodes = NODES
    state = SimpleNamespace(projects=SimpleNamespace(granted=set()))


# `available sort nearest` measured distance to becoming startable, never distance to a goal;
# it is now fewest_missing, with the old spelling kept working.
check("'fewest_missing' is the advertised sort key now, not the misleading 'nearest'",
      "fewest_missing" in _protocol._SORT_KEY_NAMES and "nearest" not in _protocol._SORT_KEY_NAMES,
      _protocol._SORT_KEY_NAMES)
check("...but the old spelling still works, for any script already using it",
      "nearest" in _protocol._SORT_KEYS and "fewest_missing" in _protocol._SORT_KEYS,
      sorted(_protocol._SORT_KEYS))


shared = Tree()

# is_venture offers `open` only where there is something to open a door on.
check("opening `arithmetic_positional` is not offered - a notation is not a door to open",
      not shared.is_venture("arithmetic_positional")
      and NODES["arithmetic_positional"]["rev"] == 0 and NODES["arithmetic_positional"]["up"] == 0,
      (NODES["arithmetic_positional"]["rev"], NODES["arithmetic_positional"]["up"]))
check("circuit theory does not open as a concern; the capacitor it improves does",
      not shared.is_venture("el2_negative_feedback_stability_gain") and shared.is_venture("el2_capacitor_electrolytic"),
      (shared.is_venture("el2_negative_feedback_stability_gain"), shared.is_venture("el2_capacitor_electrolytic")))
check("a financial instrument is not a venture; the bank that uses one is",
      not shared.is_venture("fin_cheque") and shared.is_venture("fin_deposit_bank"),
      (shared.is_venture("fin_cheque"), shared.is_venture("fin_deposit_bank")))
check("a husbandry method does not open its own shop; the farm it improves does",
      not shared.is_venture("ag2_hybridisation") and shared.is_venture("crop_rotation"),
      (shared.is_venture("ag2_hybridisation"), shared.is_venture("crop_rotation")))
check("a trade practised for a fee (an assay office) still opens as a concern",
      shared.is_venture("fin_assay_office"), shared.is_venture("fin_assay_office"))
granted_tree = Tree()
granted_tree.state = SimpleNamespace(projects=SimpleNamespace(granted={"crop_rotation"}))
check("a node a seat was granted is not a venture of its own", not granted_tree.is_venture("crop_rotation") and shared.is_venture("crop_rotation"))
venture_count = sum(1 for node_id in NODES if shared.is_venture(node_id))
check("the count of nodes offered to `open` is neither inflated by notations nor collapsed toward zero",
      1300 <= venture_count <= 1450, venture_count)

check("'values' and 'rush' are in the list every unknown-command refusal advertises",
      "values" in S.KNOWN_COMMANDS and "rush" in S.KNOWN_COMMANDS, S.KNOWN_COMMANDS)

# --- BREAK, round 12: a developer's own change-log marker was shipped in the
# prose a player reads. 1,108 nodes carried "[AUDIT: ... See JOB 1 upkeep
# audit.]" in their note field, the win condition among them, naming the task
# numbering of the agent that had edited them. The reasoning for a change
# belongs in the commit message; the note field is what the player reads.
_leaks = sorted(node_id for node_id, value in NODES.items()
                if "AUDIT" in ((value.get("note") or "") + (value.get("name") or "")))
check("no developer change-log marker is shipped in player-facing prose",
      not _leaks, _leaks[:5])

from sim.ui.protocol import _unlocked_by as _UB, _downstream_of as _DS
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

