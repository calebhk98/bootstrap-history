# test_labour_productivity cannot import: restore_work reports "you have not shut that down"

**Status:** closed - pinned by sim/tests/test_start_data_leftovers.py (the hand needle is priced in bone, Mexica holds it)

`sim/tests/test_labour_productivity.py` (the `cementation_steel` restore-work fixture near the staffing-closure checks) fails at import with an `IndexError` on `_msg_rg2.split("for ")`: after `close_unstaffed_ventures`, `restore_work` answers `(False, 'you have not shut that down')`, so the venture was not recorded as closed for staffing. It fails the same way on the integration branch before the start-data edits, so it is not caused by them. Found while running topics for Complaints/297. Reproduce: `python3 sim/test_regressions.py --jobs 1 --only labour_productivity`.

Also noted, not fixed: Mexica holds no hand needle because its recipe uses `iron_bar_kg`; a bone or obsidian-worked needle variant (different material) would let it hold one.

Resolved part: derived revenue left cementation_steel with no revenue (its output nets below its inputs at solved prices), so its supervision draw fell under the founder and closure slack and nothing shut. The fixture now picks a concern by that property instead of a fixed id.


Resolved: `tx2_needle_hand` is priced in `bone_kg` (the node's own note names bone first) instead of iron bar, and `mexica_1500` holds it; `sim/tests/test_realism_part02.py` exempts it from the Rome-only list as it does the obsidian blade.
