<!-- Verbatim blind playtest report C: three mortal fog Mexica 1500 runs. Triage: final-playtests-triage.md -->

# Bootstrap History: Three Mexica Runs, Issues and Impressions

Sep 30, 2026

Three mortal, fog-on runs of the Mexica 1500 scenario, all hand-played by me: the best scored 22.5%, none reached the goal, and all three founders died in 1538. The scenario is the most gripping thing in the demo, and a handful of bugs and one near-fixed outcome hold it back.

## The three runs

All three used Mexica 1500, fog on, mortal founder, goal "Epidemics stop deciding who lives" (cut 85% of epidemic and famine losses). Every run was sacked in all three invasion years, 1519-1521.

|  | Run 1 | Run 2 | Run 3 |
| --- | --- | --- | --- |
| Starting kit | Merchant (3,909 beans) | Equestrian (97,711) | Equestrian (97,711) |
| Strategy | Earn first, medicine late | Everything fast | Print and disperse first |
| Town patron | 1506 | 1501 | 1504 (failed 3 times first) |
| Germ theory | 1522 | 1506 | 1512 |
| Vaccination | 1524 | 1507 | 1514 |
| Written corpus | 1518 | 1512 | 1514 |
| Technologies lost 1519-1521 | 6 | 42 | 21 |
| Best epidemic cut | 63% | 59% | 59% (before losses) |
| Codices dispersed | Never | 1549, by students | Never |
| Founder died | 1538, about 73 | 1538, about 73 | 1538, about 73 |
| Final score | not computed | 22.5% | 12.6% |

Run 2 did best because it went fast early and happened to leave a school whose students finished dispersing the codices after the founder died. Run 3's plan depended on a patron in year one; three failed attempts pushed everything three years late, and it ended in a debt trap after smallpox.

## What I thought

The Mexica scenario is the best part of the demo: a known deadline turns every early choice into a real trade-off. It stops being fun after smallpox, when the game becomes a slow, near-unwinnable grind.

**What worked:**

- **The clock.** Knowing Cortés lands in 1519 and smallpox follows in 1520 made the first 19 years tense in a way the Rome run never was.
- **Historical texture.** Cacao beans as money, the *ticitl* collegium, "the patronage of a *tecuhtli* of the *calpulli*", the corpus written "in plain quantitative Nahuatl, in a notation you devise for it". These made it feel like Tenochtitlan, not a reskin.
- **Visible progress against plague.** In run 1, waves fell from 80% to 53% to 29% as measures stacked up. That was the best feedback loop in any run.
- **Believable collapse.** After smallpox the country fell to about 746,000 people and only about 21 artisans existed nationally. Grim, and accurate.
- **The legacy moment.** In run 2 the founder's students printed and scattered the codices in 1549, eleven years after his death. It was the most moving thing the game produced.

**Where it lost me:**

- **The invasion feels predetermined.** The best I got the sack chance to was 66% a year, about a 4% chance of escaping all three years. Walls, powder and rifles barely mattered.
- **The founder always dies in 1538.** Same age, same year, three runs, with no age ever shown. It reads as a fixed timer, not a life.
- **Post-1522 is a grind.** Too few people to hire, debt that blocks hiring, and concerns closing one by one. Realistic, but not much agency left.

## Bugs

The most serious are the contradictory death and succession messages and protections reported as "lapsed" that the player cannot reopen.

| # | Severity | Bug | What happened | Where |
| --- | --- | --- | --- | --- |
| 1 | High | No age shown in mortal mode | Every year says "alive and ageing" with no number. The founder then dies "aged about 73" with no warning. | All runs, 1538 |
| 2 | High | Death notice contradicts deputies | "You trained no deputy... nobody to direct anything", while the next year shows 244-370 deputy hours, and those deputies later finished `corpus_dispersed`. "THE PROGRAMME IS DISSOLVING... no deputy" repeats yearly. | Run 2, 1538-1550 |
| 3 | High | Ending ignores the dispersal | The run ends "the school dispersed and the work was forgotten" one year after the codices were printed and dispersed. `open corpus_dispersed` is refused because the run has ended. | Run 2, 1549-1550 |
| 4 | High | Protections "lapsed" but cannot be opened | Epidemic reports say "lapsed: Germ theory of disease is closed" and "lapsed: Silage and the silo is closed". `open germ_theory` refuses: "that is knowledge, not a going concern". | Runs 1-3, every epidemic year |
| 5 | Medium | Possible retry-odds problem | `patron_local` failed three years running at stated risks of 15%, 11%, 8% (about 1 in 700). | Run 3, 1501-1503 |
| 6 | Medium | Roman labels in a Mexica game | Invasion hedge costs priced in "denarii"; the school is named "the Museum". | Runs 1-3 |
| 7 | Medium | "DEAD... and ageing" | The status line reads "You: DEAD (aged about 73 at death, in 1538) and ageing". | Run 2, after 1538 |
| 8 | Medium | Achievement repeats | "achieved: A literate people, not just a literate few" announced in 1539, 1546 and 1548. | Run 2 |
| 9 | Low | Fractional people | Sacks and epidemics leave "0.55 carpenters", "0.4 scribes" on staff. | Runs 1-3 |
| 10 | Low | Corpus progress display | Portfolio showed "600 offered, 0 effective, of 6,000 hrs total to go" while money still paid in and completion was projected. | Run 1, 1511-1515 |
| 11 | Low | `step 12` after death | Did not advance; stepping one year at a time worked. | Run 3, 1539 |
| 12 | Low | Unnamed move tiles | `move` lists `mexico_06`, `honduras_01` with no city names, so leaving Tenochtitlan before 1519 was not a real decision. | Run 1, 1519 |

## Design complaints

These are not bugs; they are choices that made the scenario feel less winnable or less readable than it could be.

- **Mortal lifespan looks fixed.** Three runs, three deaths in 1538 at "about 73". Show the age, show a life-expectancy range, and let health or medicine you build move it.
- **The invasion is close to certain.** Base 90% a year for three years. Everything military I built only reached 66% (run 2). If the design intent is "you cannot stop the conquest, only save the knowledge", say so in the risk text; if not, walls and firearms should matter more.
- **The knowledge hedge is out of reach on a normal clock.** Dispersal needs the corpus (7.8-10 year floor), a printing press, then about 4.8 more years. That only fits before 1519 with a patron in year one or two. One unlucky early roll decides the whole run.
- **Debt after smallpox is a trap with no exit.** Hiring is refused "past half your line", the population is gone, and concerns close for want of hands. The refusal should say exactly how much to pay down, and there should be some lever (selling assets, a smaller household) to climb out.
- **Losses scale with what you built.** Run 2 built the most and lost 42 technologies; run 1 built little and lost 6. The game ends up rewarding a slow start before 1519, which works against its own clock.
- **Fog resets between runs.** Reasonable, but for a mortal scenario meant to be replayed, a "remembered routes" option for things you actually built in an earlier run would make replays less of a re-discovery grind.
- **No explicit successor mechanic.** Deputies come quietly from schools and patrons. In a mortal game the successor should be a named, visible goal, with a count shown in `state`.

## Civ data problems

The civ description says the Mexica have "no draught animals, no iron, no wheel in practical use", yet several items that contradict it cost 0 or are startable in 1500.

| Item | Why it doesn't fit |
| --- | --- |
| `cap_power_muscle` (draught-animal power), free | No draught animals in the Americas |
| `fin_coined_money`, free | Cacao and cloth, not coins |
| `mat_brass`, free | No brass in Mesoamerica |
| `mat_olive_oil`, `mat_silk`, free | Old World goods |
| `clock_mechanical_escapement`, free | A European invention of about 1300 (also free in Rome) |
| `tr_sleeping_car` startable | A railway car in a society without the wheel |
| `med_vaccination_progression` | Vaccination came from cowpox; there are no cattle. Variolation from smallpox is plausible, so the name may just need adjusting |

The localised names (*ticitl*, *tecuhtli* of the *calpulli*, Nahuatl corpus) are excellent where they exist, which makes the Roman leftovers stand out more.

## Suggestions

Ordered by how much each would improve a mortal Mexica run.

1. **Show the founder's age** in the prompt and `state`, with a warning in the last few years.
2. **Make succession explicit:** a deputy count in `state`, a named "train a successor" goal, and death and dissolution messages that agree with the deputy hours actually shown.
3. **Count dispersed knowledge at the end.** If the codices were printed and scattered, the ending should say so and score it.
4. **Fix "lapsed" reporting** so it only names things the player can reopen, or tells them what to do instead.
5. **State the invasion's intent in the risk text:** "you cannot stop the conquest, only protect what you know" (if that is the design), plus a clearer view of how much each hedge moves the odds.
6. **Give a way out of the post-plague debt trap:** show the pay-down needed to hire again; allow selling holdings or shrinking the household.
7. **Finish the Mexica data pass:** remove Old World freebies, rename Roman leftovers, name map tiles.
8. **A "lessons" carry-over for replays:** after a death, offer a new run that remembers which nodes you built before (fog lifted only for those).

## My own mistakes

Several bad outcomes were mine, not the game's; listing them so they are not mistaken for design problems.

- **Run 1:** never hired the scribe the corpus needed, so it sat idle for years; built iron in 1528 instead of before 1519; never built a school, so no successor.
- **Run 2:** spent 1510-1518 on artillery and gunpowder instead of paper, press and dispersal. The press started in 1519, one year too late, and 42 technologies were lost.
- **Run 3:** borrowed heavily to rebuild after 1521, then could not hire in an emptied country. A helper script I wrote reopened five costly concerns I had just mothballed, pushing income negative again.
- **All runs:** asked to train 2 of a trade when the household cap was below 2, wasting a year once; relied on filtered output, which nearly hid a sacking in the Rome run.
