# A failed project says only "it did not work", and knowledge nodes fail like machines

**Status:** closed

Request. The tester values the failure mechanics (next-attempt risk falls, part of the elapsed calendar is kept, hours must be redone) but finds the cause generic: a failed statistics curriculum and a failed grid
read alike. They also saw the nitrogen-cycle knowledge node (zero calendar years) fail twice, losing 0.3 million each, and asked what a modern founder who "knows" the cycle is failing to prove or teach. The recap shows a reduced
retry risk, while `portfolio` shows the original risk (27 percent against 35 percent on one grid retry), without saying which is active.

What it would take: one sentence per node type of what failed (teaching and adoption, apparatus, materials, politics), drawn from data fields the node already has; label which risk is live; consider node kinds that cannot "fail" by luck
(a pure concept the founder already holds) and only lose time. Related: 120 (nothing lowers the risk beforehand), closed 81.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 40, 159, 202). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Fixed: the failure line now says what failed, one sentence drawn from the node's kind, materials, trades and the state's attitude to its traits (`sim/engine/failure_cause.py`); it labels the retry risk it quotes as the live one, and `state` and `portfolio` show the live risk beside the first-attempt risk, labelled. Remaining: node kinds that cannot fail by luck (a concept the founder already holds) still roll the dice; the sentence says a knowledge-only failure lost nothing physical, but the roll itself is unchanged.

**Also done:** science nodes with no materials and no hired trades load with no chance of failing (`data.has_luck_component`).
