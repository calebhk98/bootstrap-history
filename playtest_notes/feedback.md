# Playtest feedback and requests

General impressions and wishes from a new-player run (Rome 100 AD, poor_scholar kit).

## Onboarding
- The intro and `help` are thorough and honest about the traps (open vs finished, practice income, calendar floors). They are also very long; almost every screen repeats multi-paragraph explanations (e.g. the "venture_hands is a share of a year" paragraph appears in full on every `why`). A `verbose off` switch, or showing each explanation once and then a one-line pointer, would make screens scannable.
- Request: a NET/YR column (earns minus upkeep) in `available`, and `sort net`. The single most useful early question is "what pays back fastest", and today you have to do the arithmetic by eye across pages.
- Request: a payback-years column, or `available sort payback`.

## Money
- The `start` reply's credit forecast is good, but three starts in a row print three near-identical multi-paragraph "total committed" blocks. One summary after a batch would do.

## Staff
- When a foreman (the one carpenter who supervises the loom) dies or leaves, every concern they watched closes that year, with no warning beforehand. Request: warn in `state` when a concern depends on exactly one person ("single point of failure"), and/or an `auto_replace` policy that re-hires the same trade when a foreman is lost. `auto_hire` only replaces taught trades.
- It is unclear which trade supervises which concern until `open` refuses. See bugs.md #4. A FOREMAN column in `available`/`why` would fix it.

## How much each command tells you (measured at 119 AD, seed-1 save)
Screen lengths (non-blank lines): `why lens_grinding` 41, `state` 42, `money` 54, `ventures` 60, `start fin_trademark` 20.
- About 14 of the 41 lines on every `why` are the same "staff to keep it open is a share of a year, not a headcount" explanation, word for word, on every item.
- The "YOUR PRACTICE ... pays about a third ..." paragraph repeats on `money`, `ventures` and `help money` every time.
- Every `start` that dips into credit prints a ~20-line forecast plus a "total committed" block. Three starts in a row = three near-identical blocks.
- Each completion appears twice per step (`COMPLETED 108: X` then `DURING 108: completed: X. STATUS: CLOSED / NOT OPERATING ...`).
- "population still N% below trend ..." prints every single year.
- "<concern> has N spare craftsmen before it closes" prints once per concern with the same N, because it is a household-wide figure.
In practice I grep-filtered most output to find the one line that mattered.

## Where one command was not enough
- **Picking an earner** took five commands and a refusal: `available` (paged; `sort earns` broken, bugs.md #1) -> `why` (gives the wrong staff, bugs.md #4) -> `start`/`step` -> `open` (refused: needs a carpenter) -> `labour carpenter` -> `hire`. The foreman trade only shows up in `ventures` after the concern is open.
- **Pricing a raw material:** I still do not know what a tonne of charcoal costs at market. `quote` takes only mine/forest/people, `economy full` lists only materials "above book price" (none), `materials` is empty until you hold stock, and `buy material` has no dry-run. Request: `quote material <name> <tonnes>`.
- **Unit ambiguity:** `quote mine galena 100000` prints "tonnes per year: 100,000" for a material whose key is `galena_kg`. Only by re-quoting at 280 and 1 could I tell that the input is tonnes.

## Command count
There are about 45 commands. The ones I actually needed: state, path, available, why, start, step, open, ventures, money, labour, hire, quote, economy (13). The hints after each screen point to the right next command well, so remembering them was not the problem.
The friction is inconsistent nouns between sibling commands: `buy` takes farm/housing/school/material/nitre, `quote` refuses all of those, and `help commands` lists `options` as an alias for `available`.

## Route blockers
- For about 9 years (160-169 AD) the route had nothing startable. `path` said only "nothing on the route is startable today - see 'stuck'". `stuck` gave the real reason: "the state is wary of this (state interest -0.6); ... 'open patron_local'". That is a patron I had built decades earlier and never opened, because it earns 0 and costs upkeep.
  Request: have `path` print the blocker line itself when nothing is startable, since `path` is the screen a goal-focused player reads every turn. It would also help if `why patron_local` said up front "some route nodes need this OPEN, not just built".
- The game does warn every year that founder-hours are going to waste ("2,000 founder-hours this year are going into nothing at all"). That warning is good; it just cannot say what to do when the route is politically blocked.

## Hazards and history
- Hazards are dated historical events with names: Antonine plague (from 169), Third century crisis (a 44-year window from 235), currency debasement (205, 220, 235), Plague of Cyprian (249-262), Diocletian's reforms (284-305). `risk` lists them decades ahead. That makes them plannable, which is good for a player. It also means every Rome run meets the same crises at the same dates, which reads as scripted history rather than a society producing its own crises.
- The knowledge-loss mechanic (80% chance a sack destroys knowledge, 40% of it each time) is the harshest rule in the game, and a new player has no strong signal until it happens. Request: when a hazard window with knowledge loss is under 30 years away, show a prominent line in `state` and `path` naming the cheapest hedge and how many steps it is. A one-line "AHEAD: ... hedged by nothing yet" that repeats unchanged for 135 years turns into wallpaper.
- Request: some way to protect cash (a bank, deposits spread across towns, buying land elsewhere). As it stands the correct play before 235 is to spend everything, which is a strange lesson.

## Automation and what a player (or agent) needs
- I ended up writing ~40 lines of shell to play the mid-game: every year open the concerns that pay, hire when `stuck` says craftsmen are short, follow `stuck`'s advice (train a trade, open a patron, hire scholars), start every route node I can pay for in cash, step. That a script this small could play decades at a time says the mid-game has few real decisions. The early game (first ~20 years) and hedging against dated disasters were where the choices mattered, and my script handled neither well.
- The game has pieces of this (`rush`, `auto_hire`, `auto_open`, `auto_train`) but no goal-directed version. Request: `pursue <goal>` or `rush path:<goal>`, which starts what `path <goal>` lists, within a budget, plus a policy to follow `stuck`'s route-blocker advice. `rush` is not a substitute: at 507 AD it chooses from 630 startable things "with no idea what you are building toward".
- Running many years unattended was a mistake on my part. It hid a 30-year stall (an ID my script could not parse), two credit exhaustions and repeated mass closures. The game's per-year output does report these, but a player skimming 30 years at once will not see them. A `step N` summary that ends with "things that went wrong in these N years" would help anyone who steps in batches.

## Output format
- Tables (`available`, `path`, `ventures`, `money`) are well aligned and easy to read. NAME is cut to 20 characters ("Establish a respecta"), so the long names are unreadable in the tables.
- Prose repeats (see "How much each command tells you" above). For an agent every line costs reading time, so I filtered most output with grep. For a human the cost is scrolling past the same paragraphs every year.
- One `step` prints each completion twice and each staffing warning once per concern.

## Paying for materials is not the same as having them (late game)
- At 549 AD `start mat_bulk_steel` took the whole 14.8M bill, most of it "materials" (coal 38,400 t, iron ore 30,000 t). The project then sat at 16% pace: "waiting on materials: this project consumes coal, whose shortage has it running at 16% of the pace ...". `capacity` showed coal supply 3,331 t/yr against demand 20,774, and iron 4,240 against 15,343.
- So the materials charge buys nothing physical. The flow still has to exist, from the market (`buy material coal 5000` delivered only 3,331 t, at ~408/t against a 134.8 book price) or from your own mines (3 years to sink). The price screen and the supply screen are two separate systems, and `why`/`start` do not warn that supply will throttle the project. Request: have `why` show "at today's supply this takes about N years" next to CALENDAR FLOOR, and list the shortfall in each material.
- This decides whether the goal is reachable at all. `why zinc_industry_scale` needs 54,000 t of charcoal; `capacity` in 552 showed charcoal supply ~425 t/yr, which probably already includes the ~375 t/yr from the 500 ha of forest I bought in 540 (I did not check the figure before the purchase). At that rate 54,000 t is over a century of output. Within its 6.6-year floor it would need ~11,000 ha of coppice (~18.5M). The run's outcome was decided by a physical constraint that no screen surfaced until the money was already spent.

## Endgame
- After the horizon, `score` still says "no score: the goal was not reached", even though every component was computed (technology 0.857, literacy 0.970, workforce 0.849, ...). A run that misses the headline goal but transforms the society gets no number at all. Request: always show a total, flagged as "goal not reached".
- Research ran out before time did: `rush` found 4, 8, 0 and 8 things to start in 596-599, with 33,792 founder-hours a year and ~40M a year idle. Late on, the pace is set entirely by prerequisite chains and "diffusion" calendar floors. Money and hours stop mattering. That is probably by design, but the game never says so; the screens keep offering money-shaped advice.
- Two late-game threats needed log-reading to find: the treasury's confiscation chance (shown only in the year it rises, never on `state` or `risk`), and the rule that holdings "too dispersed to be seized" protect you. Buying land lowered it. `risk` should list the confiscation chance with the other hazards.
- `auto_open` did better than my own reopen loop: with it on, the yearly closure waves were reopened within the same year, and a year took ~45s instead of 140-300s.
