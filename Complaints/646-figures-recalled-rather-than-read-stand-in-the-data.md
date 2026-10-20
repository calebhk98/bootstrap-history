# Figures recalled rather than read stand in the data and the constants

**Status:** open

Owner direction (2026-10-20): a figure needs a source someone read; "recalled" is not a source. The data and the
declared constants carry many figures marked as recalled (confidence D), from the herd rows (532) to the savings
constants (606). List them:

    grep -rn "recalled" data sim --include=*.json --include=*.py | wc -l

What it would take: for each, find and read a source and record it (author, work, page or URL, and the passage), or
mark the figure as having none and keep it a labelled heuristic with a `retire`. The rule for new work is in
CLAUDE.md section 6. Research agents follow the same rule: every claim cites a source opened in that session.
