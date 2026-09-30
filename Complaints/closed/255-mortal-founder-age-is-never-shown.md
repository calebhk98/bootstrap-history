# A mortal founder's age is never shown, the death age is arrival age plus years elapsed, and the status line reads "DEAD ... and ageing"

**Status:** closed

In mortal mode every `state` says "You: alive and ageing" with no number; then the founder dies "aged about 73" with no warning. After death `state` says "You: DEAD (aged about 73 at death, in 1538) and ageing, 0 founder-hours free this year". Reproduced (Mexica 1500, `--mortal --fog`, seed 1): text as quoted, every year 1500 to 1538.

Code: `_step_founder_mortality` (`sim/engine/core_step_phases.py`) draws `life_left` once (Gaussian around `founder_life_mean`, standard deviation `founder_life_sd`, from `sim/engine/core.py`) and prints `founder_arrival_age + year - start_year` as the age, so the printed age is arrival age plus elapsed years, not a modelled biography (medicine and sanitation add years to `life_left` only through the `founder_life_extension` mechanic, which never appears on the age shown). The status string in `sim/engine/proto/render_screens_big.py` appends "and ageing" whenever `founder_ages` is true, including after death.

Why it matters: the tester asks for the obvious thing for a mortal scenario: show the age, show a life-expectancy range, warn in the last few years, and let measures they build visibly move it. Without it death looks arbitrary (see 254: the same age and year in every run).

What it would take: put the age and an expected remaining range in `state` and the prompt for mortal games, warn when the founder is past the mean, and drop "and ageing" after death. Related: 254, 256, closed 38.


Found in the final blind playtests of this branch (three mortal fog Mexica 1500 runs; C bugs 1 and 7, design complaint on fixed lifespan). Reports: `Complaints/reports/playtest-mexica-1500-mortal-three-runs.md`; triage: `Complaints/reports/final-playtests-triage.md`.
