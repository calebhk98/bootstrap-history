"""The credit institutions the home society holds, handed to the economy as plain names.

A node declaring a mechanic (data/branches/MECHANICS.md) that the home state knows, in its own knowledge or in what
its society already knows, gives the economy the institution it names; without one its households found no bank.
"""
from sim.economy import api as economy_api

# node mechanic -> the institution the economy names
MECHANIC_INSTITUTIONS = {"deposit_banking": economy_api.DEPOSIT_BANKING, "share_trading": economy_api.SHARE_TRADING,
                         "bond_market": economy_api.BOND_MARKET, "insurance_underwriting": economy_api.INSURANCE_UNDERWRITING,
                         "risk_pooling": economy_api.RISK_POOLING, "pooled_funds": economy_api.POOLED_FUNDS}


def institutions_of(mechanics_known):
    """The institutions named by the mechanics a society has a node for (a collection of mechanic names)."""
    return tuple(institution for mechanic, institution in sorted(MECHANIC_INSTITUTIONS.items())
                 if mechanic in mechanics_known)


def held(sim):
    """The institutions the home state's society holds; none without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return ()
    world = sim.actor_world()
    return institutions_of({mechanic for mechanic in MECHANIC_INSTITUTIONS
                            if any(government.knows(node_id, world) for node_id in sim.nodes_with_mechanic(mechanic))})
