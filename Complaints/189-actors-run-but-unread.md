# Government and Firm actors run every year but nothing reads their results

**Status:** open

`sim/engine/core_step_phases.py:493` calls `self.advance_actors(...)` each year. The code inventory found no reader of their results outside `society_actors.py`: they do not affect the founder's revenue, prices, or any player screen.

Why it matters: it costs step time (see 185) and gives the impression, in code, of multi-actor economics that play does not have. CLAUDE.md's direction ("every mechanism the founder uses must be usable by any actor") needs these wired or clearly marked as scaffolding.

What it would take: either wire one consumer (e.g. state demand feeding requisitions or goods demand), or skip the phase and label it experimental.

Found by a code inventory made for the new-player playtest (`playtest_notes/code_systems_inventory.md`); each claim below was re-checked by grep.
