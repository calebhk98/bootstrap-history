# Rome starts with iron, bronze and glass but not the furnace rung they imply

**Status:** open

**Source:** `reports/COMBINED_TECH_TREE_REALISM_REVIEW_part_01.md` (strict audit, executive findings) and `reports/COMBINED_TECH_TREE_REALISM_REVIEW_part_03.md` (highest-confidence fixes).

## What is wrong

Rome's starting techs include bloomery iron, bronze casting and glassmaking but
only the lowest heat capability. The tree's own text for `cap_heat_1100` says
that temperature is reached wherever those crafts are practised, and the
playtest log shows Rome paying for the rung as research. The resolution audits
closed the inheritance findings but never mention this one.

## Evidence

- `grep -o '"cap_heat[0-9_]*"' data/civilizations/rome_100ad.json` lists only
  the lowest rung.
- `python3 sim/simulator.py why cap_heat_1100` (its note against the Roman
  start).
- Related but different: `Complaints/42` pins prerequisite violations; this is
  a capability-versus-industry disagreement, not a missing prerequisite.

## Why it matters

The heat rung gates a large part of the chemistry and metallurgy tree, and the
price solver's technique choice reads it (`Complaints/closed/44`). Making Rome
buy what its own smiths already have distorts the opening.

## What it would take

Either grant the rung to Rome (and check the other civilisations' industries
against their rungs) or change what the industries require. Decide with the
validator in `Complaints/128`, then add a test on the Roman start.
