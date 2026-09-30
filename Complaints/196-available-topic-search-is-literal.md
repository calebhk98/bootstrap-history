# `available <topic>` matches words literally: natural topic words return nothing

**Status:** open

Player words such as `physics`, `science`, `education`, `health`, `furnace`, `literacy`, `sanitation` and `water` return "Nothing you could begin today matches that", even though related items exist (heard-of or blocked) and the game refers to them elsewhere. The tester counted 143 startable items at the start and 231 by 1332, so filtering is the only way through the list, and it depends on guessing the internal vocabulary. Wanted: a thesaurus or related-names search ("physics" surfacing mechanics, waves, energy), or category browsing, without exposing prerequisite chains.

Reproduces on the current branch (all eight words above return nothing at the start):

    printf 'available physics\navailable education\nquit\n' | python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

Closed complaint 74 (`closed/74-keyword-search-fragile-under-fog.md`) asked for semantic tags and was closed; `matches_find` now matches id, name, doc anchor and aliases, which fixed exact-name misses but not synonyms or categories. Related: 72 (fog gives no direction), 197 (the one search that does match is matching a file name).

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 153, 174, 192; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): bare `available autoclave` and `available cadaver` returned zero although `why` on the same ids said CAN START NOW (they are startable later in the game; at 100 AD `available autoclave` is correctly empty). `available find <word>` returns the literal match; the bare word goes to the subject matcher, and the empty-result text says "this looks at both ids and names" without teaching `find`. Also `available find rail` returns aviation and naval-mine rows (synonym expansion is not stated). Reproduces: yes for the message; the exact zero-result case needs the node startable.

Also reported (final playtests, B; `Complaints/reports/final-playtests-triage.md`): long ids such as `el2_electropolishing_etching_surface_finish` are hard to type; asks for short aliases or tab completion in the menu game. Reproduces: yes (ids are the only handle `start` and `why` accept; see also 217).
