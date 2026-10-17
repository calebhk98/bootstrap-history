# Herd products are separate recipes, not joint products of a herd, and there is no meat

**Status:** open

Reference (an outside table of ancient supply chains, not code-aware): a herder on pasture, with
salt, shears and dogs, yields wool, hair, hides, meat, milk, cheese, tallow and horn together, and
sells them to spinners, tanners, cooks and temples.

## What the data does

`data/production/40_organics.json` makes each of these on its own, with no animal behind it:

- `wool_kg` and `milk_kg`: labourer hours and arable `land_hectare_years`, no flock, no pasture.
- `hide_kg` and `fat_kg`: no inputs and a fraction of a labourer hour each, so hides and tallow cost
  almost nothing whatever the society slaughters.
- No meat good exists (`grep -rln '"meat' data/production` finds only the schema).

The schema already allows joint production (`outputs` with several keys, `data/production/_SCHEMA.md`),
and pasture exists as a food mechanism (`sim/geography/food_pasture.py`). Living stock is still
modelled as research (Complaint 365) with no breeding or purchase (366).

## Why it matters

A good made jointly is mispriced when made alone (the schema's own example is lead and silver from
galena). Here wool can be expanded without more hides or meat, tallow and parchment
(`parchment_sheet` takes `hide_kg`) are cheap in societies with few animals, and a Mexica start with
no sheep or cattle has wool, hides and tallow at the same cost as Rome (see 531 for tallow and light).

## What it would take

- One joint recipe per herd kind (sheep and goats, cattle, pigs) with outputs wool or hair, milk,
  meat, hide, fat and horn, inputs of pasture and salt (535), and the animal stock as capital,
  so `fat_kg` and `hide_kg` follow herds.
- A meat good that satisfies `food` in `data/world/needs.json`.
- Herds limited by the living stock a civilisation keeps (365, 366), not by research.
