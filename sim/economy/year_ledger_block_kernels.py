"""Block writes into the year ledger's tables: many figures or many agents' rows in one kernel call.

Each equals the per-item write the ledger's views make (`view[key] = value`, `inner[sub] = amount`, `inner[sub] += amount`) done for
every item left to right, so the figures and the order the entries first appeared in are the loop's."""
from sim.economy.year_ledger_kernels import add_pair, clear_agent_rows, set_figure, set_pair, touch
from sim.jit import njit


@njit
def set_in_order(values, orders, counters, figure, slots, amounts):
    """`set_figure` for each (slot, amount), left to right."""
    for position in range(len(slots)):
        set_figure(values, orders, counters, figure, slots[position], amounts[position])


@njit
def replace_agents_rows(target, agents, starts, subkeys, extras, amounts):
    """For each agent in order: it becomes a member of the pair table's figure, its rows are removed, and the rows
    `starts[i]:starts[i + 1]` of the entry arrays are made in order (`NestedView[agent] = {sub: amount, ...}`). Agents must differ.
    The caller reserved room for every entry."""
    for position in range(len(agents)):
        agent = agents[position]
        touch(target.orders, target.counters, target.figure, agent)
        clear_agent_rows(target, agent)
        for entry in range(starts[position], starts[position + 1]):
            set_pair(target, agent, subkeys[entry], extras[entry], amounts[entry], 0.0)


@njit
def add_agents_rows(target, agents, starts, subkeys, extras, amounts):
    """For each agent in order: it becomes a member of the pair table's figure (keeping its place if it was one) and each of its entries
    `starts[i]:starts[i + 1]` is added to its row (`inner[sub] = inner.get(sub, 0.0) + amount`). The caller reserved room for every entry."""
    for position in range(len(agents)):
        agent = agents[position]
        touch(target.orders, target.counters, target.figure, agent)
        for entry in range(starts[position], starts[position + 1]):
            add_pair(target, agent, subkeys[entry], extras[entry], amounts[entry], 0.0)
