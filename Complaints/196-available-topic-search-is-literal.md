# `available <topic>` matches words literally: natural topic words return nothing

**Status:** open

Player words such as `physics`, `science`, `education`, `health`, `furnace`, `literacy`, `sanitation` and `water` return "Nothing you could begin today matches that", even though related items exist (heard-of or blocked) and the game refers to them elsewhere. The tester counted 143 startable items at the start and 231 by 1332, so filtering is the only way through the list, and it depends on guessing the internal vocabulary. Wanted: a thesaurus or related-names search ("physics" surfacing mechanics, waves, energy), or category browsing, without exposing prerequisite chains.

Reproduces on the current branch (all eight words above return nothing at the start):

    printf 'available physics\navailable education\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

Closed complaint 74 (`closed/74-keyword-search-fragile-under-fog.md`) asked for semantic tags and was closed; `matches_find` now matches id, name, doc anchor and aliases, which fixed exact-name misses but not synonyms or categories. Related: 72 (fog gives no direction), 197 (the one search that does match is matching a file name).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.
