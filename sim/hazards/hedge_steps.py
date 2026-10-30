"""Which hedges against a hazard are worth naming to a player: the counters themselves and their direct
prerequisites, startable ones first. Plain functions on the numbers and sets handed in."""


def hedge_wants(counter_rows, nodes, done):
    """The (distance, node id) pairs to consider, the counters at distance 0 and their unfinished direct
    prerequisites at 1, with what each leads to. `counter_rows` are (node id, share, label) rows.
    Returns (wants, leads_to, counters)."""
    wants = []
    leads_to = {}
    counters = set()
    for node, _share, label in counter_rows:
        if node not in nodes or node in done:
            continue
        wants.append((0, node))
        counters.add(node)
        leads_to.setdefault(node, label)
        for prerequisite in nodes[node]["pre"]:
            if prerequisite in nodes and prerequisite not in done:
                wants.append((1, prerequisite))
                # a prerequisite can look unrelated to the hazard, so it says what it leads to
                leads_to.setdefault(prerequisite, "a step toward %s" % label)
    return wants, leads_to, counters


def startable_first(entries):
    """What can begin now comes first; the order within each group is kept."""
    return sorted(entries, key=lambda entry: not entry["can_begin_now"])
