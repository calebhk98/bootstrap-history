# data/production/ - what makes each material, and how much comes out

WHAT MAKES EACH MATERIAL, AND HOW MUCH COMES OUT. The tech tree records what every process CONSUMES and almost never what anything PRODUCES: of the 162 materials its recipes consume, not one has a node declaring a yield. iron_bar_kg is consumed by 590 nodes and nothing makes it. That is why every cost in this engine bottoms out in a book price - there is no production side to compute one from, so a book was the only place a number could come from. This file is the production side.

## Why this is a separate directory from the tech tree

The tech tree answers 'what must exist before I can build this'. That is a different question from 'what does a kilogram of this cost to make', and mixing them into the same node made the merge fight itself: mat_* ids are duplicated across seventeen branch files and treetool keeps the first, so a recipe added to one of them silently loses. Keeping production separate also makes the material-to-producer link EXPLICIT. sim/audit_costs.py currently has to guess it by stripping a unit suffix off the material key and hoping a node id matches, which works for 47 of 162.

One file per material family, merged by material key, exactly like
`data/branches/`. Several people can author at once without colliding.
A key defined twice is an error rather than a silent overwrite -
`sim/validate_production.py` says which files disagree.

## THE RULE THAT GOVERNS EVERY NUMBER HERE

A yield is a physical fact about a process - ore grade times recovery, reduction stoichiometry, kerf and drying loss, extraction rate. It is NEVER derived from what the material sells for, and never tuned so that a computed price matches data/prices.json. Those prices are 91.8% the author's own estimates and this file exists to replace them, so calibrating against them would be arguing in a circle. If you cannot say where a number comes from in physical terms, write what you can defend and mark conf C - an honest C is worth more than a fitted A.

## How the price falls out

Once every material has inputs and a yield, the price of each is the cost of what it consumes plus the labour it takes plus rent on anything nature supplied rather than a process, and every one of those is defined the same way. That is a system of equations, solved for the fixed point where all prices agree. See docs/architecture/ENDOGENOUS_COSTS_AND_DOMAINS.md Part 2.

## Fields

| field | meaning |
|---|---|
| `outputs` | {material_key: quantity}. Usually one key. More than one means genuine joint production - smelting galena yields lead AND silver, and pretending otherwise misprices both. |
| `inputs` | {material_key: quantity} consumed to produce that output. Keys must be material keys the tree already uses, or new ones you also define an entry for. A material with no inputs is EXTRACTED rather than made: say so in extracted_from. |
| `labour_hours` | {trade: hours} to produce one basis unit. Trades must exist in data/prices.json wage_rates_denarii_per_hour. |
| `energy_mj` | Process heat and mechanical work that is not already accounted for by a fuel listed in inputs. Usually 0 for pre-industrial processes, where the fuel IS the energy. |
| `extracted_from` | For materials nature supplies: 'ore deposit', 'forest', 'quarry', 'arable land', 'seawater'. These earn a rent set by the worst source still worth working, rather than a cost of production. Omit for manufactured materials. |
| `basis` | The quantity the whole entry is quoted per. Say it in words. |
| `yield_basis` | WHY these numbers, in physical terms. This is the most important field in the entry. An entry whose yield_basis does not survive a metallurgist reading it is a guess wearing a lab coat. |
| `conf` | A well attested, B probable, C the author's estimate. Be honest; C is fine and common. |

## Confidence

- **A** - well attested
- **B** - probable, scholarly consensus, contested in detail
- **C** - author's estimate or inference

## Worked examples

`00_examples.json` holds one entry of each shape - extracted,
smelted, harvested. Copy the shape, not the numbers.

Run `python3 sim/validate_production.py` after every edit, and
`--todo` to see what is still missing, worst first.
