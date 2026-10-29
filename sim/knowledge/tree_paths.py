"""What the tree says a goal needs: the mandatory prerequisites, a build order and the longest chain, as functions of the nodes."""
from collections import deque
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

Nodes = Mapping[str, Any]


def hard_pre(nodes: Nodes, node_id: str) -> List[str]:
    """Every edge that is genuinely mandatory: `pre`, plus the `req_any` groups
    that offer exactly one real node and are therefore not a choice at all.

    ONE DEFINITION, used by closure(), topo_order() and critical_path()
    alike. They disagreed for a while: the closure learned to follow
    single-option groups and the other two did not, so `mat_manganese` was
    correctly listed as required and then topologically sorted AFTER the
    `mat_bulk_steel` that requires it, and the critical path was measured
    along a graph missing the edge. A requirement the ordering does not know
    about is a requirement the plan will schedule too late.

    Multi-option groups stay out. Those are real substitutions - silicon or
    germanium will do - and following all of them both overstates the work and
    cycles: junction_transistor -> silicon_path -> point_contact_transistor ->
    junction_transistor is a genuine loop once every option counts. `pre` plus
    the single-option edges alone is acyclic across all 2,833 nodes, checked
    directly, which is what makes this safe where the full walk is not.
    """
    # DEDUPED, in first-seen order. A node may name the same id in `pre` and
    # again in a single-option group - el2_valve_voltmeter_high_impedance
    # names vacuum_tube twice - and topo_order counts in-degree by walking
    # this list, so a duplicate raises the count by two against a decrement
    # that can only ever subtract one. The first version of this reported a
    # "cycle" among ten nodes that have no cycle between them at all: they
    # were simply the nodes Kahn's algorithm could never finish emitting.
    node = nodes[node_id]
    out, seen = [], set()
    for prereq_id in node["pre"]:
        if prereq_id not in seen:
            seen.add(prereq_id)
            out.append(prereq_id)
    for grp in (node.get("req_any") or []):
        opts = grp.get("options") or {}
        if len(opts) == 1:
            (opt,) = opts.keys()
            if opt in nodes and opt not in seen:
                seen.add(opt)
                out.append(opt)
    return out


def topo_order(nodes: Nodes, subset: Optional[Iterable[str]] = None) -> List[str]:
    """Kahn topological sort. `subset` restricts to a set of ids.

    Was O(V^2 log V + V^2 E): every one of the (up to) 2,849 iterations of
    the main loop re-sorted every key in the tree and linear-scanned every
    node's prerequisite list looking for the id just emitted. 2.6s for the
    real tree, for what should be an O(V+E) pass.

    Rebuilds to the textbook version - a reverse-adjacency index built once
    (prereq -> the nodes that name it as a hard prerequisite), so emitting
    `node_id` only touches node_id's actual dependents - while reproducing the exact
    output order the old quadratic version produced, which the optimiser's
    `order` depends on byte-for-byte:
      (a) the initial ready list is sorted, same as before;
      (b) FIFO via collections.deque (O(1) popleft instead of list.pop(0)) -
          same emission order, just not O(n) per pop;
      (c) nodes newly at in-degree 0 are appended in sorted(keys) order
          WITHIN one outer iteration - reproduced here by sorting each
          node's own dependents list once, up front, so appending them in
          that fixed order during the walk matches what re-sorting all of
          `keys` and filtering would have produced each time.
    """
    keys = set(subset) if subset else set(nodes)
    hard_pre_by_node = {node_id: hard_pre(nodes, node_id) for node_id in keys}
    indeg = {node_id: 0 for node_id in keys}
    for node_id in keys:
        for prereq_id in hard_pre_by_node[node_id]:
            if prereq_id in keys:
                indeg[node_id] += 1
    # Reverse index: for each key, the OTHER keys that name it as a hard
    # prerequisite, in sorted order - the same relative order `sorted(keys)`
    # would have visited them in, since it is a subsequence of that sort.
    dependents: Dict[str, List[str]] = {node_id: [] for node_id in keys}
    for dependent_id in sorted(keys):
        for prereq_id in hard_pre_by_node[dependent_id]:
            if prereq_id in keys:
                dependents[prereq_id].append(dependent_id)
    ready = deque(sorted(node_id for node_id in keys if indeg[node_id] == 0))
    out = []
    while ready:
        node_id = ready.popleft()
        out.append(node_id)
        for dependent_id in dependents[node_id]:
            indeg[dependent_id] -= 1
            if indeg[dependent_id] == 0:
                ready.append(dependent_id)
    if len(out) != len(keys):
        raise RuntimeError("cycle detected among: %s" % sorted(keys - set(out)))
    return out


def closure(nodes: Nodes, goal: str) -> Set[str]:
    """Everything the goal needs, following `pre` AND the `req_any` groups
    that are not really alternatives at all.

    A `req_any` group is a substitution: any one option satisfies it, so
    counting all of them as required would both overstate the work and cycle
    outright - `junction_transistor -> silicon_path -> point_contact_transistor
    -> junction_transistor` is a real loop once every option counts, and
    indexing the tree that way runs out of memory against it.

    But 125 of the tree's groups have exactly ONE option naming a real node.
    That is not a choice between routes; it is a prerequisite that happened to
    be authored as a substitution group. `mat_bulk_steel`'s manganese_supply
    group is `{"mat_manganese": 1.0}` and nothing else, so following `pre`
    alone would leave manganese out of the goal's closure - and with it,
    `mat_bulk_steel` and the 51 nodes behind it: the whole road to the goal
    through steel, power and semiconductor purification, never ranked ahead
    of the tree's other, genuinely optional nodes.

    Following the single-option groups takes the goal's closure from 158 nodes
    to 185 and cannot introduce a cycle: `pre` plus every single-option
    `req_any` edge in the whole 2,833-node tree is acyclic, checked directly.

    ONE RULEBOOK, deliberately: a mandatory prerequisite is mandatory for
    `validate`'s count, for `why`'s "full chain behind it" and for what the
    fog reveals, not only for the planner, so this is the one closure()
    every one of them calls rather than each keeping its own copy. A
    second copy of "what does the goal need" is how this project got a
    household capped at six scholars while its own optimizer held 146.
    """
    need, stack = set(), [goal]
    while stack:
        node_id = stack.pop()
        if node_id in need or node_id not in nodes:
            continue
        need.add(node_id)
        stack.extend(hard_pre(nodes, node_id))
    return need


def critical_path(nodes: Nodes, goal: str) -> Tuple[float, List[str]]:
    """Longest chain by minimum calendar years plus director-hours at one director.

    Iterative, over a topological order. The recursive version blew the stack once
    the tree passed a thousand nodes, which is a fair warning that this is no
    longer a toy graph.
    """
    need = closure(nodes, goal)
    order = topo_order(nodes, need)
    best: Dict[str, float] = {}
    chain: Dict[str, List[str]] = {}
    for node_id in order:
        node = nodes[node_id]
        own = max(node["yrs"], node["ph"] / 2000.0)
        prereq_best, prereq_chain = 0.0, []
        for prereq_id in hard_pre(nodes, node_id):
            if prereq_id in best and best[prereq_id] > prereq_best:
                prereq_best, prereq_chain = best[prereq_id], chain[prereq_id]
        best[node_id] = prereq_best + own
        chain[node_id] = prereq_chain + [node_id]
    return best[goal], chain[goal]
