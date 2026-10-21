# The outside world and the people's journeys are assumed in the disease model

**Status:** open

Split from 490 (closed). Open points:

- Arrival from outside is a yearly chance by distance (`DISEASE_TRAVELLER_ANNUAL_CHANCE`, `DISEASE_EMERGENCE_ANNUAL_CHANCE`,
  `DISEASE_TRAVEL_DECAY_DAYS`, `DISEASE_CONTACT_INFECTED_PEOPLE` in `sim/disease/nation_tuning.py`): the outside has no actors.
- Contact between tiles uses assumed people per tonne, days per visit and local trips (`sim/disease/spread_tuning.py`), none
  sourced; households' own journeys and the carriers' crews should replace them.
- `sim/world/regional_population.py` `step_regions` spreads the nation's epidemic deaths by people; it should take
  `sim.epidemic_deaths_by_tile()` so a tile's deaths follow its own infection.
- England's endemic smallpox and measles (`data/civilizations/england_1300.json`) have no source read (see 669).
