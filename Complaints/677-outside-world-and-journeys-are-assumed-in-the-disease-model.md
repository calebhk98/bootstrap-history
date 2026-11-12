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

## Update 2026-10-23

`step_regions` (`sim/world/regional_population.py`) now takes `epidemic_deaths_by_tile`, and the demography module (`sim/demography/regions.py`) passes the disease module's `epidemic_deaths_by_tile` view. A region takes the deaths that happened on its
tile; deaths no tile accounts for (other providers' deaths, an untracked tile) are shared by band share, which is also
the whole of it when no deaths by tile exist (`None`). The third open point above is done; the status stays open for the rest.
Check: `python3 -m sim.tests --only regional_epidemic_deaths_follow_the_tile`.

## Update (sourcing pass)

Each sourcing point now carries an opened citation in its declaration (`sim/disease/nation_tuning.py`, `sim/disease/spread_tuning.py`), confidence C:
- `DISEASE_TRAVELLER_ANNUAL_CHANCE` 0.6: Wikipedia Second plague pandemic: Italy had an outbreak in 68 percent of years 1348-1600; Constantinople ten recurrences before 1400; Russia once every five or six years; England every 5-12 years (Black Death in England).
- `DISEASE_EMERGENCE_ANNUAL_CHANCE` 0.0015: three plague pandemics (541, 1347, 1855; Wikipedia pages on each) in 1,485 years is 0.002 a year.
- `DISEASE_TRAVEL_DECAY_DAYS` 150: Black Death took about 500 days to cross England (Wikipedia Black Death in England); the e-folding distance itself is not in a source.
- `DISEASE_CONTACT_INFECTED_PEOPLE` 10: a cog's crew of 20 to 45 (Wikipedia Cog (ship)).
- `DISEASE_TRAVELLERS_PER_TONNE_CARRIED` 0.5 changed to 0.25: one sailor per 10 tons, recorded crews of up to 45 (Wikipedia Cog (ship)), plus a trader.
- `DISEASE_VISIT_DAYS` 3: a market trip is a full day (Agecroft Hall); no opened source gives a ship's port stay.
- `DISEASE_LOCAL_TRIPS_PER_PERSON_YEAR` 0.5: weekly market within 6 miles (Agecroft Hall), then two assumed shares (one household member in five, one trip in twenty crossing a tile); the assumptions are named in the declaration.
- England's endemic smallpox and measles: derived in 669 (critical community size and dates).

The mechanism part remains: the outside world has no actors, and households' own journeys and the carriers' crews should replace the assumed trips and the yearly chance. The status stays open for that.
