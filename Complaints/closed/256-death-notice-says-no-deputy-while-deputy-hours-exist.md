# The death notice says "you trained no deputy" while `state` shows hundreds of deputy hours, and the run-dissolution clock counts those deputies as nobody

**Status:** closed

Run 2 (C): "You trained no deputy... nobody to direct anything" at death, yet the next year showed 244 to 370 deputy hours, and "THE PROGRAMME IS DISSOLVING ... no deputy" repeated yearly while those deputies went on to finish `corpus_dispersed`.

Cause: deputies are a continuous level `household.directors_extra`, worked in hours as `directors_extra * director_hours_per_year` (`director_pool`, `sim/engine/labour_capacity.py`, 1800 hours per deputy). The death notice and the dissolution test (`sim/engine/core_step_phases.py`, `_step_founder_mortality`: `directors_extra >= 0.5`; also `sim/engine/proto/dispatch_labour.py`) treat anything under 0.5 as "no deputy", so 244 to 370 hours (0.14 to 0.2 of a deputy) is real work that is denied in the text and does not stop the twelve-year clock. `state` shows the hours and no deputy count in words.

Why it matters: the player cannot tell whether a succession exists, and the message tells them there is nothing to try. The tester also asks for succession to be a named visible goal (a deputy count in `state`, "train a successor").

What it would take: one rule for "a deputy exists" shared by the notice, the dissolution clock and `state`; say "your deputies carry a fraction of the work, N hours" instead of "nobody"; show the deputy count and a named successor objective. Related: 257, 108, 255.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bug 2 and suggestion 2). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.

Fixed: one rule for whether deputies carry the work (`deputies_carry_the_work` in `sim/engine/mechanics.py`) now feeds the death notice, the dissolution clock, `hire` and `state`; the notice and the yearly dissolution line name the hours the deputies carry instead of saying nobody.

Remains done: `state` now shows a `succession` block with the deputy count, their hours, the threshold, and a named 'train a successor' objective saying how many more are needed and where deputies come from; the rule that a fractional deputy does not carry the work is the stated threshold, now visible.
