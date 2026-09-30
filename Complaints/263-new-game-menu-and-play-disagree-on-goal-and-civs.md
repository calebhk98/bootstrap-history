# The new-game menu offers the junction transistor as "the original goal" and omits the point-contact transistor and the mod civilisation; `play` and `civs` disagree

**Status:** partly - see the paragraph at the end

Closed 160 marked the default goal in the `goals` command. The menu still disagrees (reproduced: `printf '1\n2\n\n\n\n\n\n\n\n\n\n\n' | python3 sim/simulator.py menu`):

- The goal screen says "The transistor (1951) is the original target and still the default" and lists "1) Grown and alloy junction transistors ... The original goal"; "point-contact" appears nowhere in the list (zero matches), whereas `play` without `--goal` aims at the point-contact transistor ("Aiming at: Point-contact transistor" in `state`).
- `civs` lists six civilisations including `sample_egypt_100bc_e7k2:egypt`; the New game screen offers five.

Also reported: the menu sets the seed itself (see 254).

Why it matters: two testers independently found that different entry points start different games without saying so; the score and the path differ by goal.

What it would take: one source for "the default goal" used by `play`, `goals`, the menu and the README; list the goal actually played, and either show mod civilisations in the menu or say `civs` lists mods that the menu hides. Related: closed 160.


Found in the final blind playtests of this branch (Rome 100 AD and Mexica 1500 fog runs; A inconsistency 4; B bugs 9, 10). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`, `Complaints/reports/playtest-rome-fog-demo-65pct.md`; triage: `Complaints/reports/final-playtests-triage.md`.

**Remaining:** the menu goal list now leads with the goal `play` aims at by default and offers every civilisation `civs` lists, including mod ones. The blurb of the junction-transistor goal in the tech tree data still says "The original goal"; that text lives in the data files and needs a data edit. `cmd_goals` in cli.py keeps its own copy of the default-first ordering rather than calling `selectable_goals` in `sim/engine/data.py`.
