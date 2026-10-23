# Disease is one national patch with a dice-roll importation

**Status:** closed - one patch per tile, contact from traffic and density, endemic start, regional cost readers, model forecast on the risk screens; the outside world as actors moved to 677

What was done (rules in `sim/disease/metapopulation.py` and `sim/disease/endemic_state.py`, wiring in `sim/engine/disease_port.py`):

- One SIR-style patch of three age bands per tile held. Infection passes along edges in proportion to the people moving
  (the crews of the merchants' carried tonnes, last year's migrants, everyday trips to bordering tiles); a tile's own
  contact scales with its crowding (density over the people-weighted mean, times the nation's index) to the pathogen's
  `density_exponent`. Tests: `sim/tests/test_disease_metapopulation.py` (no contact, no spread; more traffic, sooner; a dense
  town takes it faster).
- A pathogen enters at the held tile the outside source's routes reach first.
- Initial immunity: `disease_exposure.endemic` lists pathogens already in the people; each tile opens at the equilibrium the
  pathogen's own reproduction number implies (susceptible share is its reciprocal, age-structured by the force of infection).
- Campaign (`sim/agents/budget_works.py`) and settlement (`sim/engine/colonies.py`) costs read the regional disease loss
  (endemic rate of the land plus the model's forecast of the epidemics on the tile).
- Risk screens (`knowledge_risk`, `demography`, the `epidemic` figure) show the model's forecast from current infections and
  contact, not dated hazards. Deaths are kept by tile (`epidemic_deaths_by_tile`).

Remainder is filed as 677.

- `test_plagues_from_contact_validation` (six seeds of Rome over five centuries on the stand-in, about 1100 s) left the test suite. The
  checks it held (some seed has a major epidemic; epidemic years and the first arrival differ between seeds; no year is an epidemic in
  every seed; 1 to 8 pandemics per five centuries with the empire surviving) are reproduced by
  `StandInSim(civilisation("rome_100ad"), seed).run(500)` from `sim/tests/disease_stand_in.py` over seeds 1 to 6; no simulator
  command measures it yet. The seed-independence of the arrival draw stays in `test_disease_arrival_draw`.
