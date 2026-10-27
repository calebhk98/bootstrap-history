# The nearest-blockers lists of `stuck` and `path` change with the hash seed

**Status:** open

`sim/ui/proto/route_blockers.py` sorts `road`, a set of node ids, by how many nodes are still missing from each one's
closure. Nodes that tie keep the set's iteration order, which for strings depends on `PYTHONHASHSEED`, so the same
game answers `stuck` (`the_nearest_few`) and `path` with a different list in two processes. Seen by replaying one
scripted agent session in two processes with different hash seeds: the fifth to third names of
`what_is_holding_you_up[].the_nearest_few` differ, everything else is identical. With `PYTHONHASHSEED=0` in both,
two builds of the UI gave the same 168 replies byte for byte.

It breaks the rule that order must not depend on history, and a protocol golden that reached this reply would flake.
The fix is a second sort key (the node id) so ties are broken the same way everywhere; it changes which nodes a
player sees in a tie, so it is a behaviour change and was not made in the move of the screens to views.
