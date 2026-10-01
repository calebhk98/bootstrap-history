# Systems I noticed in play vs systems the code has

In play I counted about 26 systems. A separate agent reading only the code (`code_systems_inventory.md`) found 62: 53 wired into the yearly step, 7 partly wired, and a few unused or offline-only.

## Seen in play and confirmed in code
Technology tree and project risk/progress; calendar floors; credit, interest and insolvency; concerns (ventures) with ramp and upkeep; market saturation; labour market per trade and wages; hiring, attrition and training; household room, deputies, founder hours; wage work and standing hour orders; materials, stock and supply throttle; mines, forests and nitre; society values; literacy and schooling; trade naturalisation ("this society simply has its own chemists now"); reputation, scandal, eminence, protection, patronage; state pressure (levies, requisitions, office, confiscation); dated hazards; random fires and banditry; knowledge loss; automation policies; bounties; founder practice income; save/load.

## In the code but invisible to me in play (effects only, or not at all)
Demography by age cohort; agriculture, harvest and granary; correlated farm weather; farming technique from technologies; disease burden from technologies; farmland clearing; farm-vs-trade labour split; money units and the coin standard (I saw only debasement); freight and a material price factor; electricity; geography and reach; settlement and moving base (a `move` command exists; I never used it); military leverage; founder mortality, succession and dissolution (off by default); founder debt bondage; fog of war (I played without it); technology effects on the civilisation; diffusion across civilisations; trade registry; mods; settings.

## Present but only partly wired (per the code agent)
Price solver (by default project and goods costs still come from `data/prices.json`; I checked that `data.load` defaults `use_solved_prices=False`, not every caller); military logistics; transport physics; the stock ledger; Government and Firm actors (run every year, but nothing outside their module reads the result); household demand; invariant checks.

## What this changes in my conclusions
- It models more than I thought: about 2.4x the systems I counted. The farm, weather, demography and disease layers drive the numbers I did see (wages, "population below trend", plague losses) without ever appearing by name.
- The partly wired price solver may explain complaint 147: project material costs from the old price book disagree with the market prices the materials screen shows.
- The code agent also reports patterns that conflict with CLAUDE.md: content ids special-cased in the engine (4.7), a save version constant (4.6), and project prices still read from `data/prices.json` (4.5). I verified one instance of each by grep; they are not filed as complaints.
