"""The home government's side of the tax-flight inputs: what its record says about the take, reach, amnesty and immunity.
Kept apart from the engine's flight module so the module that talks to the economy never reads a government's record."""
from sim.agents.api import flight_inputs, government_levers, government_levers_tax


def government_flight_values(world, away_by_tile):
    """{field of YearInputs: value} for the state's take by tile, its reach, amnesty and immunity, given the share of
    each tile's people already away; empty without a government. `world` is the actors' world."""
    government = world.registry.government_of(None)
    if government is None:
        return {}
    record = government.record
    people = {tile: count * (1.0 - away_by_tile.get(tile, 0.0)) for tile, count in world.collection_people_by_tile().items() if count > 0.0}
    reach = world.collection_shares()
    taxed = flight_inputs.taxed_share_by_tile(government_levers.revenue_forms(record), reach,
                                              government_levers_tax.liability_rule(record), record.registered_people, people)
    return {"taxed_share_by_tile": taxed, "state_reach_by_tile": dict(reach),
            "amnesty_share": government_levers_tax.amnesty_share(record),
            "immunity_years": government_levers_tax.immunity_years(record)}
