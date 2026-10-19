# Salt is not eaten and preserves nothing

**Status:** closed - salt is a need, herds lick it, cheese and salted meat preserve with it; salted fish moved to 530

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

## Resolution

- Salt is a need with a sourced floor (`data/world/needs.json`); herd recipes in `data/production/95_herds.json` take `salt_kg` from each species row's `salt_kg_per_head_year` in `data/world/living_stock.json`.
- `cheese_kg` and `salted_meat_kg` (`data/production/40_organics.json`) consume salt and have spoilage rows far below the fresh goods (`data/world/spoilage.json`); `salted_meat_kg` is food in `data/world/needs.json`.
- Cheese labour stays conf D: a search found no published time study of hand-made hard cheese, and the yield basis says so.
- Salted fish: no fish good exists, so the sub-item is now in Complaints/530 (add a salted-fish recipe and spoilage row once the fish good exists).
- Test: `sim/tests/test_salt_is_eaten_and_preserves.py`.
