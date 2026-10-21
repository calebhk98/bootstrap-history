# Herd products are separate recipes, not joint products of a herd, and there is no meat

**Status:** partly done. Sheep, goat and cattle herds now make wool, milk, meat, hides, tallow and horn jointly (data/production/95_herds.json, one batch of 100 head-years each), from the species rows in data/world/living_stock.json (sheep_kg, goat_kg, cattle_kg), gated on holding the herd (nodes fud_sheep_flock, fud_goat_herd, fud_cattle_herd; Rome, Han, England and Norse hold them, Mexica does not and the expedition exp_import_draught_animals grants them). meat_kg is a food good (0.4 of wheat a kilogram). Open: pigs; draught_animal_kg still not drawn from the herd; the herd is gated and bred but not charged as capital (365 and 366 are closed, so nothing blocks it); cost is split among outputs by mass, which prices wool and meat per kilogram alike and lets the milk-dominated goat recipe set the meat price (retire with 507); most figures are recalled, confidence D (each row's `source` says which were read); regression test sim/tests/test_herd_joint_products.py.

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
no sheep or cattle can still make wool, hides and tallow from the same recipes (see 531 for tallow and light).

## What it would take

- One joint recipe per herd kind (sheep and goats, cattle, pigs) with outputs wool or hair, milk,
  meat, hide, fat and horn, inputs of pasture and salt (535), and the animal stock as capital,
  so `fat_kg` and `hide_kg` follow herds.
- A meat good that satisfies `food` in `data/world/needs.json`.
- Herds limited by the living stock a civilisation keeps (365, 366), not by research.

## Second note from the same source

- `draught_animal_kg` (`data/production/94_agri_organics_gaps.json`) is labourer hours with no
  inputs: no breeding stock, no winter fodder, no drover. It should come from the same herd model.
