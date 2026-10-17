# Salt is not eaten and preserves nothing

**Status:** partly done. Salt is a need (`data/world/needs.json`, floor and satiation sourced) served by `salt_kg`; `cheese_kg` (milk plus salt, `data/production/40_organics.json`, spoilage in `data/world/spoilage.json`) is the first preserving recipe. Still open: herds' salt need (532), salted fish (530, no fish good) and salted meat (no meat good), and the cheese labour figure (conf D). Test: `sim/tests/test_salt_is_eaten_and_preserves.py`.

Reference (an outside table of ancient supply chains, not code-aware): herders bought salt for their
flocks, fishers for salting the catch, and states taxed or monopolised it (Han, 530).

## What the data does

- `salt_kg` has three recipes (rock, solar pans, brine) but is not a good in `data/world/needs.json`;
  `seasoning` is met only by pepper and cassia. Its only consumers are the chemical recipes
  (hydrochloric acid, soda).
- No recipe preserves food with salt: there is no fish good (530), no salted meat (no meat, 532),
  no cheese.

## Why it matters

People and livestock need salt, it was among the most widely traded goods of antiquity, and it was a
state revenue base. Without demand, salt works have no market and a salt monopoly has nothing to tax.

## What it would take

- Salt as a physiological need (a per-person floor, a physical fact under 4.1) and as an input to
  herds (532).
- Preserving recipes (salt fish, salt meat, cheese) whose output spoils more slowly than the fresh
  good (`data/world/spoilage.json`).
