"""What the home state's take and levers are to people deciding whether to flee, handed to the economy as plain tiles
(Complaint 657). The rules are the actors' (`sim/agents/flight_inputs.py`, `liability.py`); the economy never imports them."""
from sim.economy import api as economy_api

from .agents_port_flight import government_flight_values


def flight_values(sim, economy):
    """{field of YearInputs: value} for the state's take by tile, its reach, amnesty and immunity; empty without a government."""
    return government_flight_values(sim, economy_api.fugitive_share_by_tile(economy))
