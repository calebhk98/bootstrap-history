"""A seat founds a bank in the agent economy (Complaint 106): its capital, in coin, comes out of its money and into the bank.

Part of the port (it imports `sim.economy.api`)."""
from sim.economy import api as economy_api


def found(economy, founder_id, capital_coin, year):
    """The bank the seat's `capital_coin` founds, or None; the capital is counted in the economy's unit."""
    units = capital_coin / economy.setup.coin_per_unit
    return economy_api.found_bank_from_outside(economy, founder_id, units, year, economy_api.EDGE_EXCHANGE)
