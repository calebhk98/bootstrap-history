# Rome starts with iron, bronze and glass but not the furnace rung they imply

**Status:** closed - Rome, England, Norse and Han hold cap_heat_1100

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
- Related but different: `Complaints/41` pins prerequisite violations; this is
  a capability-versus-industry disagreement, not a missing prerequisite.

## Why it matters

The heat rung gates a large part of the chemistry and metallurgy tree, and the
price solver's technique choice reads it (`Complaints/closed/43`). Making Rome
buy what its own smiths already have distorts the opening.

## What it would take

Either grant the rung to Rome (and check the other civilisations' industries
against their rungs) or change what the industries require. Decide with the
validator in `Complaints/124`, then add a test on the Roman start.

Also reported (Han China 100 AD fog playtest, tester item(s) 67; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the same problem in reverse for Han: `data/civilizations/han_china_100ad.json` grants `cap_heat_1300` (and `cap_heat_0700`) but not `cap_heat_1100`, the rung `cap_heat_1300` itself requires (`data/tech_tree.json`), so anything gated on 1100 (for example `mt2_zinc_by_retort`) makes a Han player research a rung the node's own note says bronze, glass and bloomery societies already have. Reproduces: yes (data). Likely one of the pinned violations in 41.

**Also:** `iron_bar_kg` has only the puddling (finery) recipe, so every pre-modern civilisation's iron is unmakeable from its own starting techniques; this is most of the "unmakeable material" column `python3 sim/simulator.py validate` reports per civilisation. A bloomery bar recipe, with yield from ore grade and slag loss, is the fix. It will move iron prices; that is the intended effect (CLAUDE.md 4.5: yields are physical facts), not a reason to leave it.

## Fixed so far: the bloomery bar recipe

`data/production/10_ferrous.json` now has `iron_bar_bloomery_kg`, a second
way to make `iron_bar_kg`: draw consolidated bloom (`iron_bloom_kg`) out into
bar. Its yield is a mass balance (a bloom is mostly metal, a few percent of
that scales away in the reheats, a little slag stays as grain), the ore grade
and slag loss live in the bloom's own entry, and its charcoal is the smith's
reheating fuel. It is gated on `mat_wrought_iron`, which the iron-working
civilisations already hold. Measured with
`python3 sim/simulator.py validate` (unmakeable-material column) and
`python3 sim/solve_prices.py --civ <civ> --why iron_bar_kg`:

    civ              unmakeable before -> after   iron_bar_kg before -> after (labour-hours/kg)
    rome_100ad       17 -> 5                      no path -> 3.81
    england_1300     19 -> 5                      no path -> 2.81
    norse_900ad      14 -> 3                      no path -> 2.70
    han_china_100ad   3 -> 0                      no path -> 3.71
    mexica_1500       0 -> 0                      no path -> no path (holds no iron working)

The undated solve still picks the finery route (2.57). What is left in the
unmakeable column is cordage, borax and paper, not iron.

## Remains

The headline of this complaint: Rome's industries imply `cap_heat_1100` and
it does not hold it, and Han holds `cap_heat_1300` without the 1100 rung
below it (`python3 sim/simulator.py validate` still prints rung gaps for
rome, england and han). Deciding between granting the rung and changing what
the industries require is untouched.

## Resolution

Granted rather than loosened: `cap_heat_1100` and `refractory_fireclay` are now in the starting techs of Rome, England, Norse and Han (Han's `cap_heat_1300`, `blast_furnace`, `mat_cast_iron` and `bellows_water_blown` no longer lack them). `python3 sim/simulator.py validate` shows rung-gap 0 everywhere. The fireclay node needs the founder's first-workshop node, which no start holds; that pin is recorded in `sim/tests/test_civilisation_prerequisites.py` and described in Complaints/297.
