# The run ends "the school dispersed and the work was forgotten" one year after the students printed and dispersed the codices, and the ending does not count the dispersal

**Status:** closed

Run 2 (C): codices dispersed in 1549 by the founder's students (the tester's most moving moment), then the run ended in 1550 with "the school dispersed and the work was forgotten"; `open corpus_dispersed` was then refused because the run had ended.

Cause: the dissolution counter in `_step_founder_mortality` (`sim/engine/core_step_phases.py`) reaches `DISSOLUTION_YEARS_UNTIL_END` and calls `_catastrophe(...)` unconditionally; it never looks at `corpus_dispersed` or at what was done since the founder died. Reproduced for the text path (Mexica, mortal, no deputy, bare `step`s): "RUN ENDS: the founder died without training successors; the school dispersed and the work was forgotten" in 1549 and "THE RUN IS OVER" in 1550, with nothing about knowledge that survived.

Why it matters: the dispersed corpus is the game's own answer to death and sacking (`corpus_intact`, "knowledge survival"); the ending says the opposite and the score does not credit it.

What it would take: before ending, check whether a dispersed corpus (or any successor institution) holds; end-text should name what survived and the score should count it; decide whether a dispersed corpus is an alternative to a deputy for not dissolving. Related: 252, 209, 220.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bug 3 and suggestion 3). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
