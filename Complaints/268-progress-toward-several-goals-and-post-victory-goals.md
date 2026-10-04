# Request: show progress toward several goals at once and support a further goal after the first is reached

**Status:** partly - `goals` shows the formal goal's progress and every watched goal's (counts only under fog), `goals watch|unwatch <goal>`, and `commitments` lists watched goals (`sim/ui/proto/goals_watch.py`, test `sim/tests/test_ui_goals_watch.py`); remains: making a watched goal the formal one after a win needs per-goal reach years in the engine (422)

A (section 11): multiple victory objectives are good; asks for a way to display progress toward multiple goals during an endless or post-victory campaign even if only one is the formal goal, and suggests self-imposed goals (societal transformation, one-lifetime challenge, knowledge survival, industrial independence, completionist). Score components easier to inspect under fog without revealing names (see 195).

What it would take: a `goals` view with the closure progress of every listed goal (fog-safe counts only) and a command to change or add the goal after completion. Related: 220 (victory is not an ending), 176, 195.


Found in the final blind playtests of this branch (Rome 100 AD fog plus fuzzy, immortal, won 358 AD; A section 11). Reports: `Complaints/reports/playtest-rome-fog-fuzzy-demo.md`; triage: `Complaints/reports/final-playtests-triage.md`.
