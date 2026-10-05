# Goods data states no unit mass, no unit dimension and no spoilage for livestock

**Status:** partly - a production entry may state `unit_mass_kg` (regression test unit_mass_is_production_data); a few goods carry it; the droving mode, the unit dimension field and the livestock and organic spoilage rows remain

The agent economy needs a mass per unit to price carriage and draw market areas. For goods whose id carries no mass unit it now infers one (`sim/economy/good_mass.py`): live weight from the animal table in `sim/world/transport.py`, a tonne for `_tons`, a labelled bulk density for `_m3`, the mass of consumed inputs for one-item recipes, and infinite mass (uncarriable) for land and energy units read from the id. Several of these are bounds or guesses because the data states nothing structured:

- No `unit_mass_kg` in `data/production/`: masses appear only in prose (a dressed stone block "about 140 kg", "1000 bricks = 2500 kg"). The mass-balance rule overstates them (stone block 200 kg, bricks 3700 kg, a parchment sheet about seventeen times a real one), and seasoned timber is about 600 kg per cubic metre, not the 1000 assumed.
- No unit dimension field: land and energy are marked immobile by the `hectare_` and `_mj` tokens in their ids.
- `spoilage.json` has no entries for livestock or for perishable organics such as parchment, animal gut and sugar, so they never spoil.
- Livestock are carried at freight rates by weight; driving animals on the hoof was cheaper. That needs a carriage mode, not data alone.

Evidence: `unit_mass_and_source(good, production)` in `sim/economy/good_mass.py` returns each good's mass and where it came from; a good falling back to the declared `UNKNOWN_UNIT_MASS_KG` is still a guess. No command lists them yet.

What it would take: a stated unit mass and a unit dimension per good in `data/production/`, spoilage entries for living and organic goods, and a droving mode for live animals.

Related: 395, 398.

Done: `unit_mass_kg` (documented in `data/production/_SCHEMA.md`, checked by `validate_production.check_unit_mass`, read first by `unit_mass_and_source` after a mass unit in the id) is stated for the dressed stone block, the thousand bricks and the parchment sheet. Remaining goods still infer their mass; list them with `unit_mass_and_source`. No spoilage rows were added: live animals do not rot like cargo (their loss is feed and death, a droving mode), and parchment, gut and sugar keep for long enough that a rate would be a guess with no source.
