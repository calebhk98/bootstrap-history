"""Numbers of the spatial stage: how much contact the traffic between two tiles makes."""
from sim.constants import declare

DISEASE_TRAVELLERS_PER_TONNE_CARRIED = declare(
    "DISEASE_TRAVELLERS_PER_TONNE_CARRIED", 0.5, kind="temporary_heuristic",
    unit="people making the trip per tonne carried between two tiles",
    source=None, confidence="D", retire="Complaints/674: the people's own journeys and the carriers' crews replace the assumed trips",
    why="The merchants' carried tonnes between tiles (the economy's flow ledger) say how much moves, not how many "
        "people go with it. A cart, a pack train or a boat takes a crew and a trader for a load of some tonnes; "
        "this is that crew per tonne until the carriage hours the economy books are read per edge.")
DISEASE_VISIT_DAYS = declare(
    "DISEASE_VISIT_DAYS", 3.0, kind="temporary_heuristic",
    unit="days a traveller mixes with the people at the far end of a trip",
    source=None, confidence="D", retire="Complaints/674: the people's own journeys and the carriers' crews replace the assumed trips",
    why="A person making a trip spends this long among the people of the place reached (market, inn, quayside), so "
        "the share of a tile's people-days that is shared with another tile is the trips between them times this, "
        "over 365 and the tile's people. Migrants count as one trip each.")
DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR = declare(
    "DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR", 0.5, kind="temporary_heuristic",
    unit="trips per person per year to a bordering tile (market, kin, pilgrimage)",
    source=None, confidence="D", retire="Complaints/674: the people's own journeys and the carriers' crews replace the assumed trips",
    why="Goods carried and migrants do not account for the everyday travel between neighbouring districts, and "
        "without it a tile that trades with no one would be sealed off from an epidemic. Each person makes this many "
        "trips a year to the tiles it borders, shared out by the neighbours' people, so a larger neighbour draws more.")
