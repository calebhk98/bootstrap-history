# Request: knowledge hedges between "nothing" and a full corpus or school

**Status:** open

For decades the household showed every built technology "hedged by nothing yet" (28 by 1335, 45 by 1350) because the first hedge on offer, the written corpus, is a very large project. The tester wants cheaper partial hedges: duplicate notebooks, deposit copies with monasteries or universities, named apprentices trained in one field, scribes paid to copy one field, distributed copies, guild teaching, cathedral schools, university chairs, patron-funded translations. The warning itself was praised but "wallpaper" for decades (compare closed complaint 166, which escalated the warning).

Not a defect. Corpus hedges are data-driven (`mechanics.corpus` with `rank`, `loss_chance`, `fraction_lost`, `dispersed`; see `corpus_hedge_tiers` in `sim/engine/mechanics.py`), so the change is new nodes with lower ranks, with no engine special case. Related: 166 (closed), 196, 208.

Found in an England 1300 blind playtest (fog on, poor_scholar kit, 1300 to 1375). Reports: `Complaints/reports/playtest-england-1300-fog-tester-notes.md`, `Complaints/reports/playtest-england-1300-fog-yearly-log.md`; triage: `Complaints/reports/playtest-england-1300-fog-triage.md`.

Also reported (final playtests, C; `Complaints/reports/final-playtests-triage.md`): the Mexica knowledge hedge is out of reach on a normal clock: the written corpus has a 7.8 to 10 year floor, then a printing press, then about 4.8 more years, so dispersal only fits before 1519 with a patron in year one or two and one unlucky early roll decides the run (partly the fixed default seed, 250). Also: losses scale with what was built (the fastest run lost 42 technologies, the slowest 6), which rewards a slow start against the game's own clock. The corpus, when dispersed by students after death, still does not count at the ending (253).
