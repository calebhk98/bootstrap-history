# Resolution audit: combined tech-tree realism review, part 04

**Scope:** only `COMBINED_TECH_TREE_REALISM_REVIEW_part_04.md`: the remainder
of the Norse inherited-state table, the complete Norse opening-project table,
the complete England opening state, and English opening-project rows 1–107.

**Result:** every definite inheritance, contamination, bundle, scope, and hard
gate finding in this file is dispositioned. Triage labels that merely say a
project is plausible remain projects; they are not defects requiring removal.

## Norse opening state

The four explicit Norse seeds remain intact. The Roman and Mediterranean
inheritance identified in this part—Roman medicine and surveying instruments,
mosaics, papyrus manufacture, theatre, monsoon navigation, Mediterranean hull
construction, spritsails, and murex dyeing—is excluded.

The 67 `CHECK: LIKELY ALREADY KNOWN/AVAILABLE` rows were reviewed rather than
blindly granted. Fifty-five ordinary northern crafts, agricultural practices,
construction methods, transport services, food preservation methods, metalwork,
and textile operations are now explicit Norse knowledge. Twelve entries remain
projects or trade acquisitions because their node scope specifically assumes a
formal literate contract, an urban hotel or pawnshop, a tropical/Mediterranean
import, Roman medical literature, gold-mercury practice, textbooks, lead hull
sheathing, lodestone knowledge, or indigo. This preserves the review's warning
that “available” trade goods must not be treated as generic local stock.

The seven `BASELINE CONTAMINATED` rows no longer receive their bad prerequisite
from the opening state. The 34 `GENERIC MISSING GATE` rows are the same causal
graph repairs protected by the part 02 and part 03 regression suites.

## England in 1300

The opening state retains the horse collar, substantial water power, imported
paper access, and sternpost rudder. It does not inherit the bundled
crank/flywheel/cam/trip-hammer node, domestic rag-paper production, or a
pendulum clock.

Clockwork is now split correctly. England receives a weight-driven verge-and-
foliot mechanical clock, while the later pendulum-regulated clock depends on
that medieval mechanism and remains a research project. The inherited
watermill node now covers overshot wheels, millponds, and leats without claiming
general-purpose industrial line shafts.

All 34 rows explicitly judged `LIKELY ALREADY KNOWN BY 1300` in the portion of
the English project table contained here are now explicit English grants. The
two contaminated clock descendants are no longer exposed by an anachronistic
pendulum grant, and all ten generic hard gates were already repaired in the
earlier graph work.

## Boundary

Part 04 ends at English project row 107. The remaining English rows and the
Mexica review belong to part 05 and are deliberately not claimed here.

## Regression protection

`sim/tests/test_realism_part04.py` locks the Norse exclusions and reviewed local
practice grants, the English exclusions and inherited practices, the clock
split, and the corrected watermill scope.
