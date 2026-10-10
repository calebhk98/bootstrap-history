# Repeated epidemic waves compound a civilisation's population toward extinction

**Status:** open - stage 1 done (branch disease-patch-model): `sim/disease/` (api, network, step, loader, numerics) steps one patch of people against one pathogen at sub-year resolution with its own seeded generator; four pathogen files in `data/disease/` with source and confidence tags; `validate` checks them; `sim/tests/test_disease_patch.py` holds the seven property tests. Not wired into `Sim`; the authored `staff_loss` epidemics are still in force, so this complaint's collapse is unchanged until stage 2 (below)

`data/civilizations/mexica_1500.json` declares "Old World epidemics on contact" with `staff_loss` 0.8 over the years 1520 to 1600. A wave can strike in any year of that window (the wave chance per year is shown in `sim/engine/fog.py`), and each wave removes the declared share of the population. Waves compound: in a game played on the agent economy, Mexica seed 2 falls from about five million people to a few hundred within twenty years of contact.

Why it matters:
- CLAUDE.md 4.1: the size of an epidemic is an outcome the simulation should produce from disease, immunity, crowding and nutrition, not a fraction fixed in data. The historical record is a fall of the order of nine tenths over about a century, not near extinction within two decades (CLAUDE.md 4.2 asks for it to be a plausible draw; this is not).
- The agent economy follows the engine's population, so each wave also strips a market of most of its workers and buyers in one year. That stress is real, but its size here comes from the authored fraction.

Evidence: run a mexica_1500 game with `cfg={"agent_economy": True}` (or `ROME_AGENT_ECONOMY=1`) and seed 2 for 40 years, and print the population each year (`sum(cohort.people for cohort in game.economy.agent.economy().record.cohorts.values())`).

What it would take: express the hazard as a disease mechanism (an infection reaching a population without immunity, with mortality that falls as survivors gain immunity), or at least make the authored loss a total over the window rather than per wave. The docstring above `core.py`'s hazard mortality already names routing hazards through `Population.step` as the principled direction.

Related: 95, 113.

Research updated (2026-10-09): `Complaints/reports/epidemic-model-research.md` section 11 is the build plan (a disease package with a per-pathogen sub-year step, data files per pathogen, a validation range for the Americas, and a first code step with its tests). Several sources were seen only as search summaries and are tagged so.

Stage 2 (not started), what it needs:
- A `DiseaseWorld` adapter in `sim/engine/disease_port.py` and a `DiseaseState` on `SimulationState` (patch counts per pathogen, saved with the game; no migration shim). It runs inside `step_year` after agriculture sets the nutrition ratio and before `Population.step`, and hands deaths by band back to `Population` (report section 11.4). Treat the nation as one patch first.
- Age bands and severity: a patch is one undivided group today, `case_fatality` is a single number, and the transmission is fully mixed. Per-band counts, nutrition and care effects on fatality, and density scaling are open (report sections 2 and 11.3).
- Seeding: how a pathogen first reaches a population must come from contact (trade, geography, the founder's own travel), not from a dated event. Until the spatial stage exists, a labelled temporary heuristic may seed the Mexica scenario (report section 8).
- Retire the `staff_loss` "Old World epidemics on contact" entry in `data/civilizations/mexica_1500.json` and the hazard path in `sim/engine/society_hazards.py` for it, and move the technology relief (`hazard_counters`) to `disease_effects`.
- A slow-tier ensemble check on the evidence command above (builds a whole game; not run in this stage) against the validation envelope in report section 11.5.
- Deaths shrink the contact denominator in the step (people who die stop contacting); the closed final-size relation holds only with no case fatality, which the tests use for that property.
