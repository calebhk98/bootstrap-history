"""Which running concerns a shortfall of people forces shut."""
HAND_RESOURCES = ("scholars", "craftsmen")
FOREMAN_TRADE_MARGIN = 0.01


def staffing_allowances(resources, scholars, craftsmen, employees, slack, strict=False):
    """How much of each resource a household carries before a concern must close. Scholars and craftsmen get the
    closure `slack` (none when `strict`, the test `open` applies); a foreman trade gets the headcount held plus a
    sliver (none when strict)."""
    allowances = {"scholars": scholars + (0.0 if strict else slack),
                  "craftsmen": craftsmen + (0.0 if strict else slack)}
    for resource in resources:
        if resource not in HAND_RESOURCES:
            allowances[resource] = employees.get(resource, 0.0) + (0.0 if strict else FOREMAN_TRADE_MARGIN)
    return allowances


def shortfalls_beyond(totals, allowances):
    """Resource -> amount held beyond the allowance (the short ones only), in resource order."""
    return {resource: totals[resource] - allowances[resource]
            for resource in sorted(totals) if totals[resource] > allowances[resource]}


def closures_for_shortfall(draws, net_value, protected, shortfalls_of):
    """The fewest running concerns, lowest net value first, whose closure covers every shortfall.

    `draws` maps a concern to what it holds of each resource, `net_value` to what it earns after upkeep,
    `protected` is the set flagged to stay staffed (they close only after every unflagged one), and
    `shortfalls_of(totals)` names the resources still short. A shortfall of one resource only closes concerns
    holding it. A concern chosen early that fits again once later closures freed enough is kept open."""
    totals = {}
    for held in draws.values():
        for resource, amount in held.items():
            totals[resource] = totals.get(resource, 0.0) + amount
    order = sorted(draws, key=lambda node_id: (node_id in protected, net_value[node_id], node_id))
    chosen = []
    unfixable = set()
    while True:
        short = [resource for resource in shortfalls_of(totals) if resource not in unfixable]
        if not short:
            break
        holders = [node_id for node_id in order if node_id not in chosen and short[0] in draws[node_id]]
        if not holders:
            unfixable.add(short[0])
            continue
        chosen.append(holders[0])
        for resource, amount in draws[holders[0]].items():
            totals[resource] -= amount
    kept_open = []
    for node_id in sorted(chosen, key=lambda node_id: (-net_value[node_id], node_id)):
        for resource, amount in draws[node_id].items():
            totals[resource] += amount
        if shortfalls_of(totals):
            for resource, amount in draws[node_id].items():
                totals[resource] -= amount
        else:
            kept_open.append(node_id)
    return [node_id for node_id in chosen if node_id not in kept_open]
