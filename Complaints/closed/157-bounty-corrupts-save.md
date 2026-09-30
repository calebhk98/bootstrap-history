# `bounty` corrupts the save file, and the bounty uses the founder's own hours anyway

**Status:** closed - a posted bounty round-trips through the save and draws no poster hours

Severe. At 572 AD, on copies of the save:
1. `bounty fin_toll_bridge` -> "posted: fin_toll_bridge / price: 437,332" (about 2.5x the node's build cost).
2. The next invocation on the same `--session` file: "could not read the save file '...': this save is corrupt: active['fin_toll_bridge'] is missing 'lab_left'". Reproduced twice on fresh copies.

Anyone playing the README's recommended way (`--session`) loses the game on posting a bounty.

In a single process with no reload (`bounty fin_toll_bridge`, `step 1`, `why fin_toll_bridge`), the bountied node is an ACTIVE project "waiting on your hours: priority #260 of 261". So a bounty does not "pay someone else to solve it" (`help bounty`); it is a start at 2.5x price that still consumes founder hours.

What it would take: save the bounty entry with the fields load expects (and a save/load round-trip test for a posted bounty); decide what a bounty is (a separate actor working on it, without founder hours) and make the screens say so.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.
