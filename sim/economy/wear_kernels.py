"""The year's spoilage and wear as goods-move rows, read from the book's stock table.

`loss_moves` is `inventory.spoilage_moves` and `inventory.wear_moves` for every agent at once: each stock slot of an agent that is in
the pass, holding more than zero of a good that loses a share, gives that share (`quantity * share`, when above zero) away. Rows come
out in the order the Python sorted its moves: by the agent's place in `agent_order`, then good name, then tile name.
"""
import numpy

from sim.book_tables import FREE
from sim.jit import njit


@njit
def loss_moves(agent_order, agent_first_slot, stocks, share_lost, takes_part, good_rank, tile_rank):
    """(agent number, stock slot, quantity lost) for each loss, in the order described above.

    agent_order    the agent numbers to visit, already in name order
    agent_first_slot, stocks   the book's tables
    share_lost     per good number: the share of a holding that goes in the pass (0.0: none; already held within 0..1)
    takes_part     per agent number: 1 when the agent is in the pass (wear counts only agents that use their durables)
    good_rank, tile_rank   per good and tile number: the place of its name among all names
    """
    visits = 0
    longest = 0
    for position in range(len(agent_order)):
        agent = agent_order[position]
        if takes_part[agent] != 0:
            length = 0
            slot = agent_first_slot[agent]
            while slot != FREE:
                length += 1
                slot = stocks.next_in_agent[slot]
            visits += length
            longest = max(longest, length)
    agents = numpy.empty(visits, dtype=numpy.int64)
    slots = numpy.empty(visits, dtype=numpy.int64)
    lost = numpy.empty(visits)
    keys = numpy.empty(longest, dtype=numpy.int64)
    chain_slots = numpy.empty(longest, dtype=numpy.int64)
    chain_lost = numpy.empty(longest)
    tiles = len(tile_rank) + 1
    used = 0
    for position in range(len(agent_order)):
        agent = agent_order[position]
        if takes_part[agent] == 0:
            continue
        entries = 0
        slot = agent_first_slot[agent]
        while slot != FREE:
            quantity = stocks.quantity[slot]
            if quantity > 0.0:
                loss = quantity * share_lost[stocks.good[slot]]
                if loss > 0.0:
                    keys[entries] = good_rank[stocks.good[slot]] * tiles + tile_rank[stocks.tile[slot]]
                    chain_slots[entries] = slot
                    chain_lost[entries] = loss
                    entries += 1
            slot = stocks.next_in_agent[slot]
        order = numpy.argsort(keys[:entries])
        for place in range(entries):
            agents[used] = agent
            slots[used] = chain_slots[order[place]]
            lost[used] = chain_lost[order[place]]
            used += 1
    return agents[:used].copy(), slots[:used].copy(), lost[:used].copy()
