"""The mechanics rules as plain functions of plain values: the index over the tree, effect terms and their sizes.

A node carries `"mechanics": {name: parameters}`; the engine asks "which nodes declare this mechanic" instead of naming
node ids, so a mod that adds, renames or replaces a node gets the same behaviour by declaring the same mechanic.
The vocabulary is documented in data/branches/VOCABULARY.md."""


def nodes_declaring(nodes, name):
    """[(node id, spec)] for nodes declaring mechanic `name`, in (order, id) sequence."""
    found = [(node_id, node["mechanics"][name]) for node_id, node in nodes.items()
             if name in (node.get("mechanics") or {})]
    return sorted(found, key=lambda item: (item[1].get("order", 0), item[0]))


def staff_capacity_sources(nodes):
    """[(node, scholars, artisans, directors, scales_with_units, must_be_running)] from `staff_capacity`."""
    return tuple((node_id, spec.get("scholars", 0.0), spec.get("artisans", 0.0), spec.get("directors", 0.0),
                  spec["scales_with_units"], spec["must_be_running"])
                 for node_id, spec in nodes_declaring(nodes, "staff_capacity"))


def mechanics_index(nodes):
    """{mechanic name: {node id: parameters}}, nodes in id order."""
    index = {}
    for node_id in sorted(nodes):
        for name, parameters in (nodes[node_id].get("mechanics") or {}).items():
            index.setdefault(name, {})[node_id] = parameters
    return index


def ordered_terms(specs):
    """[(node id, spec)] in (order, id) sequence."""
    return sorted(specs.items(), key=lambda item: (item[1].get("order", 0), item[0]))


def capability_sets(capability_specs):
    """(capability ids, scalable ids, {id: lost benefit}) from the `capability` mechanic's specs."""
    return (frozenset(capability_specs),
            frozenset(node_id for node_id, spec in capability_specs.items() if spec.get("scalable")),
            {node_id: spec["lost_benefit"] for node_id, spec in capability_specs.items() if spec.get("lost_benefit")})


def room_sources(terms):
    return tuple((node_id, spec["flat"]) for node_id, spec in terms)


def labour_productivity_sources(terms):
    return tuple((node_id, spec["trade"], spec["bonus"]) for node_id, spec in terms)


def hazard_counter_rows(counters_by_node):
    """{kind: [(order, node, share, label)]} from each node's `hazard_counters` list, unsorted."""
    rows = {}
    for node_id, counters in counters_by_node.items():
        for counter in counters:
            rows.setdefault(counter["kind"], []).append((counter["order"], node_id, counter["share"], counter["label"]))
    return rows


def hazard_counters(rows, own_sources):
    """{kind: [(node or pseudo-source, share, label)]}: the node rows with `own_sources` ({kind: [(order, source,
    share, label)]}, the counters that are not nodes) merged in, each kind ordered by its whole row."""
    merged = {kind: list(own) for kind, own in own_sources.items()}
    for kind, found in rows.items():
        merged.setdefault(kind, []).extend(found)
    return {kind: [(node, share, label) for _order, node, share, label in sorted(entries)]
            for kind, entries in merged.items()}


def switched_on(spec, is_held, is_running):
    """Whether a declared effect is on: operating, or merely built if the spec says gate `has`."""
    return is_held if spec.get("gate") == "has" else is_running


def effect_size(spec, units_of_institution, money_per_labour_hour):
    """The size of one node's effect: flat, or scaled by how much of the institution runs.

    The two functions of no arguments are asked only when the spec needs them."""
    scale = money_per_labour_hour() if spec.get("labour_hours") else 1.0
    if "per_sqrt_unit" in spec:
        return spec["per_sqrt_unit"] * scale * units_of_institution() ** 0.5
    if "per_unit" in spec:
        return spec["per_unit"] * scale * units_of_institution()
    return spec["flat"] * scale


def grouped_values(terms, is_on, size_of):
    """[(node id, size)] for every term that is on, in order; a spec with `group` counts once, for its first holder."""
    out, seen_groups = [], set()
    for node_id, spec in terms:
        if not is_on(node_id, spec):
            continue
        group = spec.get("group")
        if group is not None:
            if group in seen_groups:
                continue
            seen_groups.add(group)
        out.append((node_id, size_of(node_id, spec)))
    return out


def sum_in_order(values, start):
    """`start` plus each value added one at a time."""
    total = start
    for _node_id, value in values:
        total += value
    return total


def factor_product(terms, is_on, units_of, start, exponent):
    """`start` times every `factor` (or `1 + factor_per_unit_power * units ** exponent`) of the terms that are on."""
    product = start
    for node_id, spec in terms:
        if not is_on(node_id, spec):
            continue
        if "factor_per_unit_power" in spec:
            product *= 1.0 + spec["factor_per_unit_power"] * units_of(node_id) ** exponent
        else:
            product *= spec["factor"]
    return product


def best_by_tier(terms, is_on):
    """(node id, spec) of the term that is on with the highest `tier` (the first of equals), or None."""
    best = None
    for node_id, spec in terms:
        if is_on(node_id, spec) and (best is None or spec["tier"] > best[1]["tier"]):
            best = (node_id, spec)
    return best


def corpus_best_first(corpus_specs):
    """Ids of the corpus nodes, highest `rank` first."""
    return sorted(corpus_specs, key=lambda node_id: (-corpus_specs[node_id]["rank"], node_id))


def corpus_hedge_tiers(corpus_specs):
    """[(hedge node, loss chance, fraction lost)], strongest first."""
    return [(node_id, corpus_specs[node_id]["loss_chance"], corpus_specs[node_id]["fraction_lost"])
            for node_id in corpus_best_first(corpus_specs)]


def approval_patron(approval_specs, gate):
    """The first node (in id order) whose `state_approval` lifts `gate` ("wary" or "opposed"), or None."""
    for node_id, spec in approval_specs.items():
        if spec["gate"] == gate:
            return node_id
    return None


def school_node(schooling_terms):
    """The first schooling node whose operation is required for any schooling, or None."""
    for node_id, spec in schooling_terms:
        if spec.get("required"):
            return node_id
    return None


def patrons_lost_to_eminence(lost_nodes, patron_specs):
    """The patron nodes an eminent household can lose to a quarrel, highest tier first."""
    return sorted(lost_nodes, key=lambda node_id: -patron_specs[node_id]["tier"])
