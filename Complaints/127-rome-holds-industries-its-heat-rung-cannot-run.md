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

Also reported (Han China 100 AD fog playtest, tester item(s) 67; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the same problem in reverse for Han: `data/civilizations/han_china_100ad.json` grants `cap_heat_1300` (and `cap_heat_0700`) but not `cap_heat_1100`, the rung `cap_heat_1300` itself requires (`data/tech_tree.json`), so anything gated on 1100 (for example `mt2_zinc_by_retort`) makes a Han player research a rung the node's own note says bronze, glass and bloomery societies already have. Reproduces: yes (data). Likely one of the pinned violations in 42.

**Also:** `iron_bar_kg` has only the puddling (finery) recipe, so every pre-modern civilisation's iron is unmakeable from its own starting techniques; this is most of the "unmakeable material" column `python3 sim/simulator.py validate` reports per civilisation. A bloomery bar recipe, with yield from ore grade and slag loss, is the fix. It will move iron prices; that is the intended effect (CLAUDE.md 4.5: yields are physical facts), not a reason to leave it.
