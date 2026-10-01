# Upkeep is quoted at 0.75 of the amount the ledger charges (`why`, `open`, `ventures` against `money`)

**Status:** closed

Replay: build and open buttons, then compare. `open hom_button` says it "costs 1,876 a year to run" and `ventures` shows 1,876, while `money` prints "upkeep of what you built 2,502" for the same single concern (ratio 0.75). Toys: `why` says UPKEEP 3,753, the `open`
reply's upkeep line and the ledger say 5,004. The tester saw the same in the year they opened (closed science 187,634 in `ventures` against 250,178 in `why`). The "x0.75 prices" factor is applied to the displayed figure and not to the charge.

    printf 'start hom_button\nstep\nopen hom_button\nmoney\nventures\nquit\n' | python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session /tmp/repro.json

Closed complaint 153 fixed earnings quoted at base while `ventures` showed the real figure; this is the upkeep side, in the opposite direction (displayed is lower than charged), and the tester's budgets came out short by the difference.

What it would take: one upkeep figure used by `why`, `open`, `ventures`, `available` and the ledger (labelled with the price factor if it is shown at all), and a test that the ledger's upkeep equals the sum of the quoted upkeeps for the running concerns.

Found in a Han China 100 AD blind playtest (fog on, poor_scholar kit, immortal founder, goal reached in 399 AD, tester item(s) 25, 94). Reports: `Complaints/reports/playtest-han-china-100ad-fog-tester-notes.md`, `Complaints/reports/playtest-han-china-100ad-fog-yearly-journal.md`; triage: `Complaints/reports/playtest-han-china-100ad-fog-triage.md`.

Also reported (Han China 100 AD fog playtest, tester item(s) 102; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the same factor shows in mines: the coal mine quote said 50.2 million a year and the effective figure later was 37.7 million, the iron 267.9 million against 201.2 million (ratio 0.75); the screens do not say which is the real charge.

**Fixed:** `venture_real_upkeep` (`sim/engine/projects_venture_quotes.py`) is now the only upkeep figure: the ledger's `upkeep()` sums it and every screen quotes it, at the civilisation's price level and with enrolment scaling. `sim/tests/test_upkeep_quote_matches_ledger.py` checks ledger equals the sum of quotes in a civilisation whose price level is not one.

**Remains:** the mine quote (`mine_quote`) against the charged `mine_operating_cost` was not re-measured; both apply the price level, so the gap reported may come from the per-working cost scale. Check with the coal and iron replay before closing.

**Fixed:** re-measured: with no other workings, `mine_quote` and the charged `mine_operating_cost` agree apart from wage drift over the lead years, in a civilisation whose price level is not one. A real gap remained when older workings were depleted: the quote used the material's average depletion while a new working starts fresh. `mine_quote` now prices running cost through `mine_operating_cost_new`, the function that charges every working.
