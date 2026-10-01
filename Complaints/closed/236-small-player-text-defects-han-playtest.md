# Small player-text defects: goal wording, algebra example, a six-row list with five rows, kit and mortality prose, a spelling variant

**Status:** closed

Each item is tiny and reproduces; grouped so they are fixed in one pass.

1. The epidemic goal is worded "Cut four-fifths of what plague and famine take" and then "have cut 85%" (`python3 sim/simulator.py goals`). Four-fifths is 80%.
2. `why algebra_symbolic`: "when you add 5 and triple it you get 24" followed by 3x + 5 = 24 and x = 19/3. The equation is right; the sentence describes 3(x + 5) = 24. (`data/tech_tree.json`, `algebra_symbolic` note.)
3. The opening `available` screen titles a list "CHEAPEST SIX RIGHT NOW" and prints five rows (replayed: the five zero-cost rows).
4. The poor_scholar kit says "A few months' subsistence"; 4 labourer-years of wages is more than a year and a half of the household's own living cost (440 thousand a year against 750 thousand), and the tester read it as
   wrong by an order of magnitude. `sim/engine/data.py`, `STARTING_KITS`.
5. The `absurd` kit description says "It used to make things worse and no longer does" (patch history in a player field; see 126). The mortality question says "one is the honest number", which the tester read as
   judging the default (`sim/engine/cli_interactive.py`, `_new_game_ask_mortality`).
6. `labour laborer` is refused; only `labour labourer` is accepted. The refusal lists the right names, but common US and UK spellings could both work.
7. `help commands` lists every command except `options` (interactive only), although the intro and the submenu text send the player to it. The alias that once pointed at `available` is gone (closed 161).
8. The "people kept on your own staff" sentence ends several `why` pages with no trade or number and no staff ever arrived (tester, not replayed).
9. `funding_capacity()` and `your_real_ceiling` appear in the combined-commitment warning (`sim/engine/proto/dispatch_ventures.py`, `what_this_means`) in player text; see 126.

10. The `train` reply says nobody can do the work until the trainees graduate, but industrial hygiene started with no ready chemists completed in the same annual resolution in which two chemists graduated (tester, not replayed).
11. `ventures closed` silently ignores the word and prints the whole table; there is no closed-only, capability-hidden or trade filter (paging, closed 174, works).

Replay of 1, 3, 6, 7: `python3 sim/simulator.py goals`, and

    printf 'available\nlabour laborer\nhelp commands\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 9, 11, 27, 32, 34, 36, 37, 63, 64, 6, 3). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

**Remains:** All items fixed. Items 1-7 and 9, 11 were fixed previously. Items 8 and 10 fixed: staff text no longer appears without context, and train reply no longer incorrectly says "nobody can do that work yet".
