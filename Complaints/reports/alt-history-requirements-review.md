# Alt-history requirements review

An alt-history group wants to play several countries at once in one world, and fakes it today with the
founder standing in for a state. Three of their researchers wrote what the simulator would need to do.
This review checked each item against the code on `main`. Five read-only audits by area, then spot
checks of the key claims. Findings are filed as Complaints 481 to 493; the mod hooks that would let a
mod add systems like these are Complaints 494 to 496.

Verdicts: **yes** = simulated and usable by any actor; **home** = simulated for the home country or
founder seat only; **partial** = some of it exists; **no** = missing.

| Requirement | Verdict | Where it stands | Complaint |
|---|---|---|---|
| Play as a country, several players, hand a seat to a new player | no | Seats are households; states take no commands | 481 |
| Other countries run the same rules | no | Static population, one-formula state | 482 |
| Region owner, one owner per region, control levels | no | Static `home_tiles`, no transfer, no control state | 483 |
| Terrain, adjacency | yes | Tile layers and `borders` | |
| Travel by land, river (up and downstream), sea; cost falls with transport technology; freight in prices | yes | `sim/geography/routes_*`, built ways, carriers | |
| Seasonal access | no | Routes are year-round | 487 |
| Authority falling with distance, garrison against unrest, corruption | no | No army location, no leakage | 484 |
| Tolls by volume and competing routes, new canals | partial | Flat dues; land canals only; sea links are map data | 487 |
| Population per region, growth, carrying capacity from crops and tools | home | National cohorts; farming model is real | 489, 482 |
| Strata, bonded labour, overhead classes | partial | Strata per country; no producer, soldier or clergy strata; no revolt | 486, 489 |
| Surplus constraint on soldiers and scholars | no | Army is a budget line, not checked against food or people | 489 |
| Training pipeline, skilled people take time | partial | Labour-market cohorts with training and attrition | |
| Plague with recovery; contagion along trade edges | home | Pathogen model for the home patch; arrival by dice; Rome still has a dated plague | 490 |
| Revenue streams, private vs state wealth, spending lines | home | Home `Government` has revenue forms and budget lines | 482 |
| Monopoly and mine revenue | no | Monopolies only block exports | 492 |
| Mines with grade, depth, depletion, recovery technology | home | Founder workings; cyanidation is a flat multiplier | 492 |
| Capacity separate from money (shipyards, timber, skilled hands) | partial | True for private producers; the state cannot commission ships | 492 |
| Maintenance and attrition of state assets | partial | Masonry works only | 492 |
| Input-output chains with hard chemical inputs | yes | `data/production/`, material gating | |
| Alternative recipes that are weaker or riskier | partial | Alternatives exist for seats; no quality or failure on recipes | 491, 492 |
| Tech prerequisites, effort, materials | yes (seats) | Actor research skips the gates | 491 |
| Stages from investigated to widely adopted; "a few aircraft" | no | Known, built, operating | 491 |
| Research from scholars, literacy, printing; uncertain discovery | partial | Failure is a roll; literacy does not drive output | 491, 489 |
| Diffusion by trade, espionage, observation, battle | partial | Distance-scaled visibility of seat inventions only | 491 |
| Adoption when it pays, or forced by the state | partial | Firms adopt on profit; no subsidy or mandate | 491 |
| Military units, quality, supply range, terrain and disease | no | Army is a headcount; logistics module unwired | 485 |
| Waging war, conquest, overstretch, natural borders | no | No conflict phase | 485 |
| Stability, factions, ruler competence, succession | no | Accession dice roll; loss-driven interest groups | 486 |
| Diplomacy, treaties, trust, notes on other powers | no | Smuggling closure only | 487 |
| Beliefs, news speed, secrets, deception | no | Tech-name fog only | 488 |
| Base-rate shocks, world event log, per-turn validation | partial | Dated hazards; per-seat log; debug-only invariants | 493 |

## Can mods do this?

Partly. Mods add data (technologies, recipes, civilisations, map overlays, hazards, actor kinds) and,
with the player's consent, Python that registers commands, actor kinds, policies and spawners
(`mods/README.md`, `sim/engine/mod_code.py`). A handler gets the whole `sim`, so nothing stops a mod
in principle. In practice the state a war or country-play mod would drive is missing or frozen in the
base game (tile owners, foreign demography, army objects, a phase hook in the year), so the mod would be
rebuilding core systems. The group's reviewer was right that this needs base-game work first; 481 says
which. Three hooks would let later groups (a fantasy world with magic and other creatures, for example)
add their own systems without engine edits: a phase registry for the year (494), declared per-tile,
per-actor and per-pair stores (495), and stable effect operations (496). Building 481 to 493 on those
hooks keeps the base game's own systems as moddable as a mod's.
