# Repeated epidemic waves compound a civilisation's population toward extinction

**Status:** closed - the disease model is wired into `step_year` (`sim/engine/disease_port.py`); the Mexica epidemic `staff_loss` entry is gone

`data/civilizations/mexica_1500.json` declares "Old World epidemics on contact" with `staff_loss` 0.8 over the years 1520 to 1600. A wave can strike in any year of that window (the wave chance per year is shown in `sim/engine/fog.py`), and each wave removes the declared share of the population. Waves compound: in a game played on the agent economy, Mexica seed 2 falls from about five million people to a few hundred within twenty years of contact.

Why it matters:
- CLAUDE.md 4.1: the size of an epidemic is an outcome the simulation should produce from disease, immunity, crowding and nutrition, not a fraction fixed in data. The historical record is a fall of the order of nine tenths over about a century, not near extinction within two decades (CLAUDE.md 4.2 asks for it to be a plausible draw; this is not).
- The agent economy follows the engine's population, so each wave also strips a market of most of its workers and buyers in one year. That stress is real, but its size here comes from the authored fraction.

Evidence: run a mexica_1500 game with `cfg={"agent_economy": True}` (or `ROME_AGENT_ECONOMY=1`) and seed 2 for 40 years, and print the population each year (`sum(cohort.people for cohort in game.economy.agent.economy().record.cohorts.values())`).

What it would take: express the hazard as a disease mechanism (an infection reaching a population without immunity, with mortality that falls as survivors gain immunity), or at least make the authored loss a total over the window rather than per wave. The docstring above `core.py`'s hazard mortality already names routing hazards through `Population.step` as the principled direction.

Related: 95, 113.

Research updated (2026-10-09): `Complaints/reports/epidemic-model-research.md` section 11 is the build plan (a disease package with a per-pathogen sub-year step, data files per pathogen, a validation range for the Americas, and a first code step with its tests). Several sources were seen only as search summaries and are tagged so.

Closed (stage 2, branch close-386-disease-wiring):
- `sim/engine/disease_port.py` holds `DiseaseWorld` (what the disease step reads from `Sim`) and `DiseasePortMixin.disease_year`, called in `_demographic_recovery` after agriculture sets the food and before `Population.step`. `DiseaseState` (`sim/engine/state.py`) is saved with the game as plain data; a round trip equals a straight run (`sim/tests/test_disease_wiring.py`). Deaths by band go to `Population.step(epidemic_deaths=...)`, so births, ageing and the accounting identity stay in demography.
- The nation is one patch of three age bands (`sim/disease/year.py`). Bands mix as one; immunity ages across band edges with the people who carry it; births arrive susceptible; the dead leave the contact denominator.
- Age and food act on fatality in the simplest derived form, both labelled heuristics (`AGE_FATALITY_FROM_STARVATION_VULNERABILITY` in `disease_port.py`): each band's case fatality is the demography module's relative vulnerability rescaled to a mean of one, times the nutrition shortfall through the curve baseline mortality uses.
- Seeding: `civ["disease_exposure"]["outside_contact"]` lists pathogens and a window; while the window is open and a pathogen is absent from the nation, a labelled yearly chance (`DISEASE_CONTACT_ANNUAL_CHANCE`) introduces a few infected adults, drawn from a hash of the game's weather salt, never `Sim.rng`. Retire it when the spatial stage carries infected people along routes.
- The "Old World epidemics on contact" `staff_loss` entry is removed from `data/civilizations/mexica_1500.json`. Other civilisations keep the generic staff_loss path (their plagues are not modelled yet). The duplicate wave-chance literal in `sim/engine/fog.py` now reads `STAFF_LOSS_HAZARD_ANNUAL_CHANCE`.
- Technology relief: The disease-relevant nodes carry `mechanics.disease_effects` (`acts_on` case_fatality or transmission, `factor`, optional `pathogens`), scaled by how far the country has taken the node up (`civ_diffusion`). Their `hazard_counters` stay for the other civilisations' staff_loss hazards until those plagues move into the model (report section 8, stage 4). `validate` checks the new fields and the civilisation's pathogen names.
- Checks: `sim/tests/test_disease_century.py` steps the model alone on the Mexica start's population for a century with the pathogens the scenario seeds and asserts the deepest 75-year fall lies inside the published span, no near extinction within twenty years, and that later waves kill fewer than the first (not quick tier; the run time is printed by the runner). `sim/tests/test_disease_ensemble.py` is the whole-game ensemble on this complaint's evidence command (slow tier, a whole game each; written, not run when the wiring landed). A one-off smoke run of a real unopened Mexica game for 25 years showed a first-wave fall and a save/load round trip of the records.
- Open measurements are filed as Complaint 471 (care collapse and density scaling of contact), which the model does not yet have.
