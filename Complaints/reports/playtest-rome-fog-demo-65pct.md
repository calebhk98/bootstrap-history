<!-- Verbatim blind playtest report B: Rome 100 AD, fog, won 301 AD, score 65.1%. Triage: final-playtests-triage.md -->

# Bootstrap History Demo: Playtest Feedback

Sep 30, 2026

One blind playthrough by me, reached the point-contact transistor in 301 AD and scored 65.1%; the game is excellent, and the bugs below are fixable.

## The run

Rome 100 AD, poor\_scholar kit, fog on, immortal founder, default transistor goal. Only the root README was read before play; no source code was read and the plan, search and run optimizers were not used.

| Milestone | Year |
| --- | --- |
| Horse collar, first real income | 101 AD |
| Scientific method, place-value notation | 102-105 AD |
| Blast furnace (second attempt) | 135 AD |
| Quantum solid-state theory | 141 AD |
| Voltaic pile | 142 AD |
| Newcomen engine | 166 AD |
| Self-exciting dynamo | 211 AD |
| Discovery of the electron | 218 AD |
| Power grid | 258 AD |
| Point-contact transistor (third attempt) | 301 AD |

Final score at the 600 AD horizon: 65.1% (652 / 1000). Technology coverage was 493 of 2,879 nodes (17%), which cost the most points. Literacy, workforce and standing were maxed. Achievements: 4 of 5; the miss (never paid interest) was a deliberate early-borrowing choice.

Wall-clock time was about 45 minutes, with the second half driven by small helper scripts.

## What works

The core idea, the historical care and the help system are the game's strengths; please keep all of these.

- **Finish is not open.** Building buys knowledge; running it needs the right foreman. It forces real economic thinking from turn one.
- **Supply chains beat money.** The blast furnace quoted at 1,003,716 denarii, 92% of it coal at Roman scarcity prices. Sinking a coal mine dropped it to 105,072. This was the best moment of the run.
- **Faithful dependency chains.** Zinc gates the voltaic pile; germanium comes from zinc-smelter flue dust, is purified as GeCl4 and reduced in graphite boats; Watt needs Wilkinson's boring mill. Each one clicked.
- **Society pushes back.** Scandal, eminence, the annona, the fabricae requisitions and proscription made wealth a liability in a believable, Roman way.
- **Consequences carry forward.** Early sanitation cut the Antonine plague to about 4% empire-wide instead of about 28%. A dispersed written corpus meant a 283 AD sacking took 326M denarii and 3,641 people but no knowledge.
- **Fog is honest.** `stuck` and `path` refuse to leak the tree; completions report "on the road to your goal" after the fact. Reasoning the route by hand was the fun part.
- **Help and prose.** `help sittings` openly supports one-command-per-process play. The arrival text ("Nobody can measure a temperature, hold a tolerance, sustain a vacuum, or purify anything") is excellent.
- **Diffusion floors.** "The economy needs roughly a generation to train the trades" is a good, defensible reason money cannot buy speed.
- **Trades becoming native.** "This society simply has its own engineers now, the way it always had smiths" is a satisfying milestone.

## Bugs

The two worst bugs are failure losses far above their forecast and a failed bounty that can never progress; the rest are display errors.

| # | Severity | Bug | What happened | Where |
| --- | --- | --- | --- | --- |
| 1 | High | Failure loss far exceeds forecast | `why blast_furnace` said "IF IT FAILS: 31,947 gone". The failure took 846,998, and cash really dropped by about that. Same pattern: bulk steel lost 6.2M, industrial zinc lost 11.8M against a forecast of 119k. Likely stockpiled materials (coal) charged at market value. | Blast furnace 133 AD; bulk steel 188-190 AD; zinc 270 AD |
| 2 | High | Failed bounty becomes an orphan | `master_screw` was bountied in 127 AD, failed in 128, then sat 13 years at "0 offered, 0 effective" with priority #1-2 and 7,000+ free hours. `allocate master_screw 700` reported "its own pace this year - at most 0 hours". `stop` then `start` fixed it. Nothing warned that a bounty had become the player's job. | 128-144 AD |
| 3 | Medium | Wrong achievement | "No concern ever closed for want of staff" is ticked, but the log shows "nobody left to keep an eye on 2 concerns, so lens\_grinding, opt\_manometer closed". | 117 AD log |
| 4 | Medium | Foreman column blank | The `available` table's FOREMAN column shows "-" while `why` lists a specialist foreman needed to open. | tex\_horizontal\_loom (carpenter), horse\_collar (smith), opt\_manometer (glassblower) |
| 5 | Medium | `stuck` contradicts funding | `stuck` said "159 of them you could pay for" and suggested the cheapest, while every start was refused with "you could raise 0". | 109 AD, deep debt |
| 6 | Low | Stale hour pool in report | After a new year began with 2,000 hours free, RUNNING lines still said "sharing this year's 200 directed hours". | 107 AD |
| 7 | Low | Priority rank counts finished work | The step report showed "priority #9 of 9" when `priority` listed only 5 active projects. | 129 AD |
| 8 | Low | Training list incomplete | After training 2 engineers and 2 machinists, `labour` IN TRAINING listed only the engineers. | 108 AD |
| 9 | Low | Mod civ missing from menu | `civs` lists `sample_egypt_100bc_e7k2:egypt`; the New game screen offers only 5 civs. | `menu` |
| 10 | Low | Default goal mismatch | The CLI default goal is the point-contact transistor; the menu's goal list opens with the junction transistor as "the original goal" and does not list point-contact. | `goals` vs `menu` |
| 11 | Low | Start allowed with no one to do it | `precision_three_plate` was startable while no machinist existed (trainees not finished); it then warned it would be abandoned in 3 years. | 119 AD |
| 12 | Low | `quit` gives no final score | Under fog the total is "not computable until the run ends"; quitting does not end the run, so the score needs a fast-forward to the horizon. | `score` |

## Balance and exploits

Money is hard for about 15 years, then irrelevant; the coal market is the clearest exploit.

- **Coal arbitrage.** A 4,000 t/yr mine costs about 10 denarii a tonne (40k/yr standing). On a copy of the 126 AD save, `sell coal 7000` returned about 755k, roughly 108 a tonne, while `materials` listed demand at 254.5 t/yr. Selling 28 years of demand at once barely moved the price. Geology caps it (8-17k t/yr per region), so it is bounded, but it could multiply mid-game income several times. Suggest: sell price falls with volume against demand.
- **Runaway income.** Income went from +16k/yr (111 AD) to +1M/yr (137 AD) to +5M/yr (170 AD). By 216 AD the household held about 400M denarii, likely more than the Roman treasury's yearly revenue. Proscription answers it, which is realistic, but the income itself feels too easy.
- **Money stops mattering by about 125 AD.** After that the limits are calendar floors and staff. Fine as design, but the mid and late game lose their economic tension.
- **Idle waiting.** Several stretches (the 24-year power grid, 11.8-year floor) had nothing forced to do. Diversifying helps score, not the goal date, and nothing in the UI nudges the player toward that.
- **Two-stroke engine.** `en_two_stroke_cycle` needs only `cap_tol_1mm` and was startable around 109 AD, earning 2,900-10,500/yr for 2,005. Not used in this run.
- **Population may run hot.** 120.2M by 302 AD from a start of about 65M, after plague mitigation. Another AI run reported 66.9M at 361 AD. Worth checking the demography.

## Tree and history

The tree (2,879 nodes, valid DAG) is strong on physical chains and weak where theory and diffusion are concerned.

- **Rome needs a blast furnace for copper.** `mat_copper` is blocked on `blast_furnace`, though Rome smelted copper for centuries. The early copper-iron brine cell even used copper.
- **No pozzolana at start.** Rome begins without `mat_pozzolana`, the basis of Roman concrete.
- **Medieval clock free in Rome.** `clock_mechanical_escapement` costs 0 and is startable in 100 AD; its own text calls it an "inherited medieval mechanism" from about 1300.
- **Theory runs ahead of evidence.** Band theory and the p-n junction finished in 141 AD, 77 years before the electron (218 AD), needing only scholars. Electromagnetic theory came before any battery. The premise (knowing is free) partly covers this, but some experimental prerequisite would help.
- **Industry never spreads.** At 302 AD the whole empire had about 18 engineers, chemists, machinists and electricians each, 10 of them on the player's payroll, while running a power grid. The revolution stays inside one household.
- **Rails.** Dated events (the 235 crisis, Decian edict, Diocletian's 284 reforms) fire on schedule in an empire with telegraphs and 120M people. Effects are softened by what you built, but whether they happen at all never changes. The civ is still "Rome under Trajan" in 600 AD.
- **No divergence signal.** Nothing tells the player when history has clearly left its track.

## Annoyances

Most friction comes from hidden rules and from warnings that are easy to miss.

- **Hidden funding rule.** Starts were refused with "you could raise 0" at 26k debt against a 42k credit limit. The real rule (about cash + half the credit line + a few years of spare income) is only explained inside a long credit note. Say it plainly on refusal, with the number needed.
- **Training cost surprise.** `train` also charges about 3,056 per pair for upkeep, and trainees join the payroll automatically at scarcity wages (2,609/yr per engineer). This flipped income negative and froze all spending. A warning on `train` about the wage bill to come would help.
- **Heavy attrition of specialists.** Glassblowers, engineers and machinists left almost every year "to death and better offers", closing concerns. Realistic, but punishing before `auto_hire` and schools are discovered.
- **Supply gates are invisible to `blocked_by`.** `why ... compact` returns `blocked_by: []` for items gated on a supply ("needs a manganese supply ... any of mat\_manganese"). Tools and players following `blocked_by` miss them.
- **Critical supply nodes look minor.** `mat_manganese` and `nitre_beds` gated the whole endgame but were not flagged as ALL or much in `available`.
- **Long IDs.** Typing `el2_electropolishing_etching_surface_finish` by hand is rough for humans.
- **No victory moment.** Reaching the goal prints one plain "COMPLETED" line; the game only says more at the 600 AD horizon.
- **Warnings drown in the year report.** Sackings, confiscations and eminence alarms sit among dozens of routine lines.

## Feature requests

Ordered by how much each would improve play.

1. **A pinned ALERTS block at the top of every step report** for run-ending or costly events: sackings, proscription, eminence or scandal near the line, a concern closing, a project abandoned, a bounty turned into the player's own job.
2. **A victory screen** when the goal completes, with the date, the score so far and the achievements.
3. **Wait-time nudges.** When every goal-path project is calendar-bound, say so and suggest side goals or coverage work. Another player called the time gates "obviously so you could catch up on the rest of your research"; make that explicit.
4. **Diffusion of industry** beyond the household: copycat firms, native trade counts that grow with what you run, a society that industrialises around you.
5. **Divergence tracking.** A history screen comparing the run with the real record (population, literacy, key inventions) and flagging when a dated event no longer fits the world.
6. **Scheduled events that can change or fail** once the world has moved far enough from history.
7. **Supply gates in `blocked_by`** and in the RESTS rating, so critical supplies are visible.
8. **Short aliases or tab completion** for long ids in the menu game.
9. **A `score --final` or end-run command** that resolves the fog score without stepping to the horizon.
10. **More civs with different problems:** Abbasid Baghdad (\~800), Song China (\~1050), Ptolemaic Alexandria (\~250 BC) as a real civ rather than Rome relabelled.
11. **A speedrun or daily-seed mode** with a leaderboard for fastest goal date by civ and kit.

## AI players and scripting

The game suits large language models well; scripted play is faster but less fun and riskier.

- **One command per process works.** `--session` plus piped commands ran cleanly for the whole game; a turn took about 0.5 to 6 seconds.
- **Scripts hide warnings.** Output filters in this run hid the 283 AD sacking until the log was checked, and the eminence danger was only caught by reading `state`. Other players reportedly lost runs this way. The ALERTS block above would fix it.
- **Hand play was more fun.** The first 50 hand-played years were the best part; the script-stepped late game felt like supervision.
- **Model size.** Winning needs long context (a single `why` screen can exceed 1,000 tokens), reliable instruction-following over 1,000+ commands, cash-flow arithmetic and real history-of-technology knowledge under fog. `stuck`, `why` and the RESTS column lower the bar noticeably.
- **Help discoverability.** The README's Saving section already shows piping one command per run. In-game, the fuller explanation sits under `help sittings`, which the game notes most agents miss; a pointer from `help` or the first screen would help.
