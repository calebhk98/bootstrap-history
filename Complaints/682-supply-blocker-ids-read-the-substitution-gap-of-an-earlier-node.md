# A living-stock supply blocker names options from the substitution gap of whichever node was checked before

**Status:** open

`start_blockers` classifies a refused `supply` check by the ids it names. For every supply check except
`unheld_stock` and `materials_have_a_seller` those ids are the options of the last `req_any` group that had no option
(`sim/projects/blocker_views.py` `_classify`, `last_substitution_gap`). That gap is kept per seat by
`_substitution_quality` (`sim/projects/start_checks.py`), which sets it when a group fails, clears it when every group
passes, and leaves it as it was when the node has no `req_any` group at all.

The `needs_held_herd` check (kind `supply`, "the same gate, when what is missing is living stock") runs before the
`substitution` check in the gate's order, so when it refuses it classifies with the gap left by the previous call: an
unrelated node's group, or nothing. The ids of a living-stock blocker can therefore be another node's substitution
options (shown only if the player may see them). The answer depends on which node was asked about last, which breaks
CLAUDE.md section 5 ("order must not depend on history").

Kept as it was in the move of project starting into the projects module (the old `household._last_subst_gap` had the
same behaviour); not fixed there. Fix: classify `needs_held_herd` with its own ids (the held-herd gate's materials, like
`unheld_stock`), or compute the gap for the node being classified instead of reading the last one. A regression test:
call `start_blockers` on a node with a failing substitution group, then on one whose `needs_held_herd` refuses, and
assert the second names none of the first's options.
