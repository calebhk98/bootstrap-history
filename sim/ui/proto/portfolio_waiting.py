"""Work that could be started but is blocked, grouped by the gate's own blocker kind (Complaints/293).

Reads `start_blockers`, the list the `start` refusal reads, so this cannot
disagree with the gate. Work missing prerequisites is not listed: that is
the tree's business (`available`, `path`), not a bottleneck on what is open.
"""

import sim.engine.ui_port as ui_port
from sim.engine.ui_port import BLOCKER_MEANING

WAITING_KIND_ORDER = ("specialists", "supply", "money", "power", "politics", "closed", "calendar")
_NOT_WAITING = ("knowledge", "goal", "done", "active", "unavailable")
_MEANING = {"power": "a power capability is missing: build or reach it first",
            "politics": "the state or a patron stands in the way",
            "closed": "built once but shut: 'open' it"}
SHOWN_PER_GROUP = 6


def waiting_to_start(sim, nodes):
    """One group per blocker kind among visible, unbuilt, idle nodes whose prerequisites are met."""
    by_kind = {}
    for node_id in nodes:
        if node_id in sim.done or node_id in sim.active or any(pre not in sim.done for pre in nodes[node_id]["pre"]):
            continue
        if not ui_port.visible_to_player(sim, node_id):
            continue
        blockers = sim.start_blockers(node_id)
        if not blockers or any(blocker["kind"] in _NOT_WAITING for blocker in blockers):
            continue
        by_kind.setdefault(blockers[0]["kind"], []).append(node_id)
    groups = []
    for kind in WAITING_KIND_ORDER + tuple(sorted(set(by_kind) - set(WAITING_KIND_ORDER))):
        members = sorted(by_kind.get(kind, ()), key=sim.project_cost)
        if members:
            groups.append({"kind": kind, "count": len(members), "projects": members[:SHOWN_PER_GROUP],
                           "what_it_means": _MEANING.get(kind) or BLOCKER_MEANING.get(kind, "")})
    return groups
