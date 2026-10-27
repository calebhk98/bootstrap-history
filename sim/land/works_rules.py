"""The works register's rules as plain functions: what more capacity at a tile costs, why a start is refused, which works finish, and what a loss leaves."""


def cost_curve(units, convexity):
    """The cost of `units` of capacity at one tile, in the node's ordinary sizes: each further unit costs more."""
    return units + convexity * 0.5 * max(0.0, units - 1.0) ** 2


def work_money(project_cost, have, capacity, convexity):
    """What adding `capacity` to the `have` already at a tile costs, from the node's ordinary cost."""
    units = cost_curve(have + capacity, convexity) - cost_curve(have, convexity)
    return project_cost * units


def start_refusal(capacity, held_here, node_id, buildable, known, being_built, tile):
    """The sentence when a work cannot be started, else None (the checks in the order they are made, the money last)."""
    if capacity <= 0:
        return "the capacity to build must be above nothing."
    if not held_here:
        return "you can build only on a tile your nation holds."
    if not buildable:
        return "%s is not something that can be built and kept up." % node_id
    if node_id not in known:
        return "your people do not know how to build %s yet." % node_id
    if being_built:
        return "%s is already being built on %s." % (node_id, tile)
    return None


def finish_works(pending, built_works, year):
    """Count, in place, the works whose build time has passed on their tiles, in tile then node order."""
    for tile in sorted(pending):
        for node_id in sorted(pending[tile]):
            due_year, capacity = pending[tile][node_id]
            if due_year <= year:
                built = built_works.setdefault(tile, {})
                built[node_id] = built.get(node_id, 0.0) + capacity
                del pending[tile][node_id]
        if not pending[tile]:
            del pending[tile]


def lose_work(built_works, tile, node_id, capacity):
    """Take up to `capacity` of a work from a tile, in place; a tile left with nothing is dropped."""
    built = built_works.get(tile, {})
    left = built.get(node_id, 0.0) - capacity
    if left > 1e-9:
        built[node_id] = left
        return
    built.pop(node_id, None)
    if not built:
        built_works.pop(tile, None)
