# Stuck says nothing is started while training and queued work run

**Status:** closed - stuck lists training in hand from the same rows state shows

Found by an agent playtest (`Complaints/reports/playtest-rome-seed7-agent-100-years-log.md`). Around 130 AD, `stuck`
replied that the player had started nothing, while `train machinist` was running and a project was queued.

Why it matters: `stuck` is the command the game points a lost player to; when it misreads the state, an agent acts
on a false premise. The screens and the engine should read one function (`STATE_OF_THE_PROJECT.md`).

What it would take: `stuck` reads the same record of work in hand (projects, training, queued starts) that `state`
shows; test that with only training running `stuck` names it.

## Resolution

`stuck` adds a "training in hand" entry built by the function `state` uses for `training_pending` (`training_in_hand`), and no longer says nothing is started while people are in training. Test: `sim/tests/test_stuck_sees_training.py`.
