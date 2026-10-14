# Temporary heuristics grow faster than they are retired

**Status:** open

`python3 sim/constants.py --burndown` reports most declared numbers as temporary heuristics, and the count
rises from week to week (compare `git grep -c temporary_heuristic <commit> -- 'sim/*.py' ':!sim/tests'`
across old and new commits). Many recent fixes clamp a symptom with a new labelled constant (a thin-market
blend share, a rate ceiling at a multiple of the starting rate, several "negligible share" cutoffs) instead
of fixing the mechanism, often because the mechanism's owner is on the other side of a seam the fixing agent
cannot see (507, 508). CLAUDE.md 4.4 allows labelled shortcuts; it does not make them free.

What it would take: a rule that a change adding a `temporary_heuristic` names, in the declaration's `why`,
the mechanism or complaint that will retire it; each pull request states the burndown count before and
after; and a test that fails when a heuristic's `why` names no retirement path.
