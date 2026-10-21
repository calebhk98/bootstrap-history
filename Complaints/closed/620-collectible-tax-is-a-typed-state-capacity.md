# A state's collectible share is a typed `state_capacity`, not derived from officials, literacy and distance

**Status:** closed

Part of Complaint 542 (State capacity and tax rates are typed, there is no corvée, and the fiscal crisis is a fixed cascade).

Related: 604 (literacy state).

**What is wrong.** Nothing derives capacity from officials, scribes, literacy or distance from the capital.

**Evidence.** `state_capacity` is a typed number (`sim/agents/cast.py`, `records.py`); `ADMINISTRATIVE_SPAN` (`sim/agents/tuning.py`) sizes the officials kept, not what they can collect; assessment is in `sim/agents/revenue.py`.

**Why it matters.** The tax a state can collect should follow from its administrators and reach (CLAUDE.md 4.1).

**What it would take.** Collectible share derived from the officials and literate staff a state employs and the travel time from its seat to each tile (freight and routes exist), replacing typed `state_capacity` for collection.

**Test.** A test: doubling the officials raises collection; a far tile yields less than a near one; no typed capacity is read for collection.

## Outcome

- `sim/agents/collection.py` derives the share collected on each tile from the officials employed (the administration
  line, less the share of their pay left unpaid), their working days, the literacy of the propertied stratum, the
  people on the tile and the days of travel from the seat (the tile with most people) found by `reach` through the
  geography api. `sim/agents/collection_world.py` gathers those from the home world and from a country.
- `revenue.assess` scales each form by `world.collectible_share(tiles)`; `Assessment.collectible` records it.
  `budget.officials_kept` is people over `ADMINISTRATIVE_SPAN` and no longer reads capacity.
- Labelled heuristics (each with `retire`): `ASSESSMENT_DAYS_PER_PERSON`, `WRITING_SAVES_SHARE_OF_ASSESSMENT`,
  `ROUNDS_OF_COLLECTION_PER_YEAR`; `ADMINISTRATIVE_SPAN` stays one.
- At the opening Rome's share is saturated (all of it collected), so revenue is unchanged until officials go unpaid
  or the road is long. Measure: `SimWorld(sim(civ="rome_100ad")).collectible_share()` in `sim/tests/harness.py`.
- Tests: `sim/tests/test_state_collection_follows_officials.py`.
- Typed `state_capacity` was still read outside collection; Complaint 658 moved those readers onto the same share
  and removed the typed field. Labour dues (`labour_days`) are not scaled by the collectible share.
- Sources: no source found for officials' time per taxpayer or rounds per year. Only a publisher description of
  Stasavage, States of Credit (2011), was seen in a search (smaller polities sustained assemblies more easily); the
  book was not opened and nothing here depends on it.
