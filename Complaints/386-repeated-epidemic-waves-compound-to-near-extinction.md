# Repeated epidemic waves compound a civilisation's population toward extinction

**Status:** open - owner decision (2026-10-06): replace the authored fraction per wave with a population-level epidemic model that spreads through trade and geography and responds to technology; research in Complaints/reports/epidemic-model-research.md comes before code

`data/civilizations/mexica_1500.json` declares "Old World epidemics on contact" with `staff_loss` 0.8 over the years 1520 to 1600. A wave can strike in any year of that window (the wave chance per year is shown in `sim/engine/fog.py`), and each wave removes the declared share of the population. Waves compound: in a game played on the agent economy, Mexica seed 2 falls from about five million people to a few hundred within twenty years of contact.

Why it matters:
- CLAUDE.md 4.1: the size of an epidemic is an outcome the simulation should produce from disease, immunity, crowding and nutrition, not a fraction fixed in data. The historical record is a fall of the order of nine tenths over about a century, not near extinction within two decades (CLAUDE.md 4.2 asks for it to be a plausible draw; this is not).
- The agent economy follows the engine's population, so each wave also strips a market of most of its workers and buyers in one year. That stress is real, but its size here comes from the authored fraction.

Evidence: run a mexica_1500 game with `cfg={"agent_economy": True}` (or `ROME_AGENT_ECONOMY=1`) and seed 2 for 40 years, and print the population each year (`sum(cohort.people for cohort in game.economy.agent.economy().record.cohorts.values())`).

What it would take: express the hazard as a disease mechanism (an infection reaching a population without immunity, with mortality that falls as survivors gain immunity), or at least make the authored loss a total over the window rather than per wave. The docstring above `core.py`'s hazard mortality already names routing hazards through `Population.step` as the principled direction.

Related: 95, 113.

Research updated (2026-10-09): `Complaints/reports/epidemic-model-research.md` section 11 is the build plan (a disease package with a per-pathogen sub-year step, data files per pathogen, a validation range for the Americas, and a first code step with its tests). Several sources were seen only as search summaries and are tagged so.
