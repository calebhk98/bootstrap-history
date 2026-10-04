"""Presentation and formatting values: how a report LOOKS, never what it
MEANS. Column widths, how many rows a table shows, how far a string
truncates before an ellipsis. Changing any number in this file changes
where text wraps or how many lines print; it can never change a price, a
population, a wage or a judged grade - see sim/constants.py's own module
docstring for the numbers that CAN and belong there instead, and see this
file's own THE TENSION WITH sim/constants.py section below for why the two
are governed differently on purpose rather than by oversight.

WHAT BELONGS HERE. A number a REPORT or TABLE function uses to decide how
much of its own output to print - "show the worst 20", "truncate this
column to 34 characters", "draw the bar 28 characters wide" - gathered from
the report/table functions in sim/ui/ where the
value is not already defended by, or inseparable from, one specific
sentence of surrounding prose.

WHAT DELIBERATELY DOES NOT BELONG HERE, EVEN THOUGH IT LOOKS LIKE THE SAME
SHAPE OF NUMBER. This project's event log and CLI narration are full of
small slice bounds inside otherwise hand-written sentences - `"; ".join(
why[:3])` inside one specific denunciation message in sim/engine/
society_hazards.py, `reopen[:2]` inside one specific "you can reopen these"
sentence in sim/labour/labour_capacity.py, and dozens more like them across
sim/engine/core_step_phases.py, economy_credit.py, projects_staffing.py and
others. Those were surveyed for this file and deliberately left where they
are: each one is load-bearing for the GRAMMAR of the one sentence it sits
inside (moving "3" out to a shared PLAYER_LOG_REASONS_SHOWN constant used by
a dozen unrelated sentences would not make any of them more editable - a
future editor changing that shared constant to 5 would silently reshape
sentences they never read, in messages this file's own author has no way to
check the wording of, which is a worse outcome than the number staying a
literal "3" one line above the string it counts words for). This is the
same judgement sim/constants.py's own docstring already makes about a
formula-adjacent number generally - the defending context (here, the
sentence, not a paragraph) is what makes the number safe to have at all,
and moving it away loses that. Only numbers belonging to a genuinely
freestanding report FUNCTION - one whose whole job is formatting a table or
a bar chart, not narrating a single event - are gathered here.

THE TENSION WITH sim/constants.py, RESOLVED. sim/constants.py's own
docstring states, under WHAT DOES NOT BELONG HERE: "Numbers that do not
change a simulated outcome. Column widths, 'show the top 5 slowest', retry
counts, buffer sizes. Moving those away from the code that uses them makes
that code worse, not better." Taken alone, that reads as an argument
against ANY file like this one - and it is not wrong about sim/constants.py
itself. The registry is a PROVENANCE tool: `kind`, `source`, `confidence`
and `why` exist to answer "is this a fact, a guess, or an outcome" for a
number that affects what the simulation computes, and none of those
questions has a sensible answer for "how many characters wide is the audit
bar chart" - it does not have a `kind` in CLAUDE.md SS3.1's sense at all,
because SS3.1 is about claims on the SIMULATED WORLD, and a column width
makes no such claim. This file is a genuinely different thing serving a
genuinely different purpose (the stakeholder's own stated reason: these
values should be gathered somewhere editable, because a person tuning a
report's shape should not have to go spelunking through three tools to
find every width and row limit at once) and does not use `declare()` at
all - see NOT PART OF THE REGISTRY below. sim/constants.py's own docstring
points here rather than arguing a position this file exists to make moot.

NOT PART OF THE REGISTRY, DELIBERATELY. Nothing in this file calls
`declare()`. That is not an oversight: sim/constants.py's `--burndown` is
the project's progress bar for how much of the simulated MODEL is still
provenance-tracked or still a promise to keep, and a presentation value
counted alongside a calorie requirement or a wage elasticity would make
that bar measure something it was never meant to. A plain module-level
float with a one-line comment is the right amount of ceremony for a number
nobody needs to defend, only to be able to find.

HOW A CONSUMER USES ONE OF THESE. Imported fully qualified, `from
sim.ui.presentation import AUDIT_BAR_WIDTH_CHARS`, the same convention this
task's sim/unit_conversions.py uses and for the same reason (this file is
reached from sim/, the repository root, and sim/engine/ alike, and a single
spelling avoids loading it twice under two sys.modules keys - see that
module's own HOW A CONSUMER USES ONE OF THESE section for the full
argument, which applies here unchanged).
"""

# ============================================================================
# sim/ui/cli_analysis.py - the `explain` command's "unknown node" reply
# ============================================================================

EXPLAIN_NEAR_MATCH_SUGGESTIONS_SHOWN = 8
# How many "did you mean" node-id suggestions `explain <unknown>` offers.
