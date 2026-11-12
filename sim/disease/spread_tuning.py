"""Numbers of the spatial stage: how much contact the traffic between two tiles makes."""
from sim.constants import declare

DISEASE_TRAVELLERS_PER_TONNE_CARRIED = declare(
    "DISEASE_TRAVELLERS_PER_TONNE_CARRIED", 0.25, kind="temporary_heuristic",
    unit="people making the trip per tonne carried between two tiles",
    source="Wikipedia, Cog (ship) (en.wikipedia.org/wiki/Cog_(ship), opened): 'one sailor, exclusive of any dedicated fighting men, was required for every 10 tons burthen' (0.1 a tonne, said to be on the low side) and 'crews of up to 45 for civilian cogs are recorded' (about 0.2 a tonne for the 200-ton Saint Mary Cog); plus a trader or passengers. Carts and pack trains are not covered.", confidence="C", retire="Complaints/677: the people's own journeys and the carriers' crews replace the assumed trips",
    why="The merchants' carried tonnes between tiles (the economy's flow ledger) say how much moves, not how many "
        "people go with it. A cart, a pack train or a boat takes a crew and a trader for a load of some tonnes; "
        "this is that crew per tonne until the carriage hours the economy books are read per edge.")
DISEASE_VISIT_DAYS = declare(
    "DISEASE_VISIT_DAYS", 3.0, kind="temporary_heuristic",
    unit="days a traveller mixes with the people at the far end of a trip",
    source="Agecroft Hall, Going to Market (agecrofthall.org/single-post/going-to-market-setting-out-from-agecroft-hall, opened): 'Most villages were within 6 miles of a local market', 'between three and four hours' by cart, a market trip 'generally consumed a full day' (one day). A ship's stay in port was not found in any opened source (Ostia-antica.org gives none); 3 days is a ballpark between a market day and a port stay of days.", confidence="C", retire="Complaints/677: the people's own journeys and the carriers' crews replace the assumed trips",
    why="A person making a trip spends this long among the people of the place reached (market, inn, quayside), so "
        "the share of a tile's people-days that is shared with another tile is the trips between them times this, "
        "over 365 and the tile's people. Migrants count as one trip each.")
DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR = declare(
    "DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR", 0.5, kind="temporary_heuristic",
    unit="trips per person per year to a bordering tile (market, kin, pilgrimage)",
    source="Agecroft Hall, Going to Market (agecrofthall.org/single-post/going-to-market-setting-out-from-agecroft-hall, opened): most villages were within 6 miles of a market, an average trip 'a little over four miles', and a 'weekly shopping trip' is described for one household. Weekly is about 52 a year for the household member who goes; 52 x one member in five x one trip in twenty crossing a tile border is about 0.5 (the one-in-five and one-in-twenty are my assumptions, no source found), so the figure is a ballpark, not a measurement.", confidence="C", retire="Complaints/677: the people's own journeys and the carriers' crews replace the assumed trips",
    why="Goods carried and migrants do not account for the everyday travel between neighbouring districts, and "
        "without it a tile that trades with no one would be sealed off from an epidemic. Each person makes this many "
        "trips a year to the tiles it borders, shared out by the neighbours' people, so a larger neighbour draws more.")
