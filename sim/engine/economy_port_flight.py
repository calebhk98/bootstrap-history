"""What the home state's take and levers are to people deciding whether to flee, handed to the economy as plain tiles
(Complaint 657). The rules are the actors' (`sim/agents/flight_inputs.py`, `liability.py`); the economy never imports them."""
from sim.agents.api import flight_inputs, government_levers, government_levers_tax
from sim.economy import api as economy_api


def flight_values(sim, economy):
    """{field of YearInputs: value} for the state's take by tile, its reach, amnesty and immunity; empty without a government."""
    government = sim.actors.government_of(None)
    if government is None:
        return {}
    from .agents_port import SimWorld
    world = SimWorld(sim)
    record = government.record
    away = economy_api.fugitive_share_by_tile(economy)
    people = {tile: count * (1.0 - away.get(tile, 0.0)) for tile, count in world.collection_people_by_tile().items() if count > 0.0}
    reach = world.collection_shares()
    taxed = flight_inputs.taxed_share_by_tile(government_levers.revenue_forms(record), reach,
                                              government_levers_tax.liability_rule(record), record.registered_people, people)
    return {"taxed_share_by_tile": taxed, "state_reach_by_tile": dict(reach),
            "amnesty_share": government_levers_tax.amnesty_share(record),
            "immunity_years": government_levers_tax.immunity_years(record)}
