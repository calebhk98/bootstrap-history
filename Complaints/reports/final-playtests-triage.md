# Triage: final blind playtests (two Rome 100 AD fog runs and three mortal Mexica 1500 fog runs)

Inputs (verbatim copies in this folder):

- **A** `playtest-rome-fog-fuzzy-demo.md`: Rome 100 AD, fog plus fuzzy estimates, immortal, point-contact transistor in 358 AD, plus a short destitute mortal run. Overall 8 out of 10.
- **B** `playtest-rome-fog-demo-65pct.md`: Rome 100 AD, fog, immortal, point-contact transistor in 301 AD, score 65.1%. Numbered bugs 1 to 12.
- **C** `playtest-mexica-1500-mortal-three-runs.md`: three mortal fog Mexica 1500 runs, goal "epidemics stop deciding who lives", none reached it; scores 22.5% and 12.6%. Numbered bugs 1 to 12.
- The project owner's own observation (extra report): after winning there is no score; several agents had to `step N` to the end of the timeline to see theirs. Filed into complaint 224, which now asks for a victory screen and a finish-and-score command.

Every "reproduces" was checked on branch `final-playtests-triage` (fast-forwarded to the merge "Merge china-fog-playtest-triage (complaints 217-249)") by piping commands into `python3 sim/simulator.py play --civ <id> --seed 1 --session <file>`, by the test harness (`sim/tests/harness.sim`), by reading the data in `data/`, or by reading the code, as each complaint states. "Untested" needs a long played game. Only files under `Complaints/` changed; no code or data was changed.

Filed as new: **250 to 272** (23 complaints). "Also reported" paragraphs appended to 31 existing complaints: 68, 81, 90, 96, 99, 100, 101, 104, 107, 114, 116, 129, 151, 184, 185, 186, 196, 204, 205, 208, 213, 214, 218, 220, 223, 224, 226, 233, 234, 243, 249.

## New complaints

| # | Title | Reproduces now |
|---|---|---|
| 250 | Load browser shows "None AD" and 0 technologies (`list_saves` reads flat keys, the save is nested) | Yes |
| 251 | A failed project charges the full book material bill, 26 to 100 times the `why` forecast (blast furnace, zinc) | Yes (harness; exact match to the tester's figures) |
| 252 | A failed bounty stays flagged, is never worked, and the poster pays a failure loss too | Yes (harness) |
| 253 | Material stock sells at a flat 80% of the buy price with no volume limit (coal about 108 a tonne, 7,000 t at once) | Yes (harness; same 755 thousand) |
| 254 | Default seed is 1 everywhere: every player gets the same lifespan, invasion and early-failure rolls | Yes |
| 255 | Mortal founder's age is never shown; death age is arrival age plus elapsed years; "DEAD ... and ageing" | Yes |
| 256 | Death notice says "no deputy" while deputy hours exist (0.5 threshold versus hours) | Yes (code plus run text); the live 244 to 370 hours not replayed |
| 257 | Run ends "work was forgotten" after the corpus was dispersed; the ending ignores it | Yes (text path) |
| 258 | "lapsed: Germ theory of disease is closed" for knowledge that cannot be closed | Yes (harness; cause is the national-adoption discount) |
| 259 | "achieved: ..." repeated after forgetting removes the measured node | Untested live (code reading) |
| 260 | Mexica data: 96 zero-cost Old World nodes startable at 1500, Roman labels ("the Museum") | Yes (data; `denarii` in hedge costs not reproduced) |
| 261 | Rome data: `mat_copper` blocked on `blast_furnace`; no `mat_pozzolana` at start | Yes (data) |
| 262 | `clock_mechanical_escapement` is free and instant in every civilisation that does not hold it | Yes (data and `available all`) |
| 263 | New-game menu and `play` disagree on the default goal; point-contact not offered; mod civilisation missing | Yes |
| 264 | "The Roman Empire under Trajan" label stays to the end | Yes |
| 265 | `stuck` counts 69 payable starts that `start` refuses ("you could raise 0"); the rule and the number needed are not stated | Yes |
| 266 | Sacks and epidemics leave fractional people on the payroll | Yes (code; harness multiplication) |
| 267 | `why ... compact` `blocked_by` omits supply gates | Yes (code) |
| 268 | `RESTS` counts descendants, not relevance to the goal; critical supplies read as minor | Yes (code) |
| 269 | "sharing this year's 200 directed hours" and "priority #9 of 9" are stale | Untested (code reading) |
| 270 | No divergence readout; dated events never check their causes (request, relates to 184) | Yes (by design) |
| 271 | Request: replay option that remembers routes built in an earlier run | n/a (request) |
| 272 | Request: progress toward several goals, and goals after victory | n/a (request) |

## Severe bugs: what was found

1. **Failure loss far above the forecast (251, with 218 and 151).** `why` quotes `project_cost(node) * 0.4` (`sim/engine/proto/techtree.py`, `failure_costs`), where `project_cost` is the bill frozen at start: labour and capital plus only the materials not already held, at market prices. A failure charges `node["_total_cost"] * 0.4 * cost_money_factor()` (`sim/engine/projects_completion.py`, `_lost`), where `_total_cost` includes the static book material bill (`sim/engine/money_units.py`). So the charge ignores the materials the player bought at the start (complaint 151's up-front purchase, which stay in stock), mined, or held. With the harness in Rome: blast_furnace charge 846,998 (the tester's exact number; quote 365,587 with nothing held, about 32 thousand after a mine); industrial zinc charge 11,804,966 (tester 11.8 million); bulk steel quote and charge agree (6.25 and 6.24 million) while nothing is held. The better the supply chain the player builds, the wider the gap. Not fixed here.
2. **Failed bounty becomes an orphan (252).** `post_bounty` sets `ph_left = 0` and `bountied`; `project_hour_pace` returns 0 for `bountied` ids; a failed roll raises `ph_left` to 40% and charges the poster but keeps the flag, so pace stays 0 forever (harness: bountied True, `ph_left` 80, pace 0.0, cash lost 1,918). Only `stop` then `start` clears it.
3. **Coal arbitrage (253).** `sell_material_stock` pays `sold * sell_per_tonne`, a flat 0.8 of the buy price, capped only by stock; the buy side is capped at the market's yearly tonnage and its price rises, the sell side is not. The harness reproduces 7,000 t for 754,647 (107.81 a tonne) and 20,000 t for 2,156,134 at the same unit price.
4. **Save browser "None AD" (250).** `settings.list_saves` reads `year`, `capital`, `done` from the top level; the save nests them under `scenario`, `household`, `projects`.
5. **Mortal founder, all three runs dies 1538 "about 73" (254, 255).** The shared cause is the fixed default seed: `play --seed` defaults to 1 and the menu hard-codes `args.seed = 1`. Seed 1 gives 38.3 remaining years (35 + 38 = 73, death in 1538); seeds 2 to 6 give deaths between 1519 and 1547. The same fixed stream explains "sacked in all three years", and quite possibly the 1-in-750 `patron_local` failures (the first draw of seed 1 is 0.134, under the 15% risk). The age shown is arrival age plus elapsed years; "alive and ageing" gives no number; after death the status reads "DEAD (aged about 73 at death, in 1538) and ageing".
6. **Death notice contradicts deputy hours; ending ignores dispersal (256, 257).** Deputies are a continuous `directors_extra` worked at 1800 hours each; the notice and the dissolution clock treat anything under 0.5 as nobody, so 244 to 370 hours (0.14 to 0.2 of a deputy) is denied in the text. The dissolution counter calls `_catastrophe` at twelve years without looking at `corpus_dispersed`.
7. **"lapsed: Germ theory of disease is closed" (258).** `hazard_relief(..., beyond_national=True)` multiplies a running counter's strength by `1 - civ_diffusion`; the label "lapsed ... is closed" is chosen whenever strength is under 1, so a fully running knowledge node partly adopted nationally reads as closed. Harness: with `civ_diffusion` set to 0.4, germ_theory (running True, not a venture) gets the lapsed label. Related closed complaints 182 and 202 covered naming the concern, not this label.
8. **Achievements.** Repeated literacy announcement (259): measured goal nodes live in `projects.done` and the forgetting and loss samples (dissolution, sack, plague) do not exclude them, so the yearly check re-awards and re-logs them; code reading, untested live. "Never closed for want of staff" ticked despite closures: duplicate of open 223 (appended).
9. **Free and instant nodes.** `clock_mechanical_escapement` has cost 0, 0 hours, 0 years, prerequisite `cap_tol_1mm` (free), startable in Rome and in Mexica (262). 144 nodes in the tree cost nothing; 96 are startable free in Mexica at 1500, 28 in Han, 37 in Norse, 16 in England, 3 in Rome (260). `cap_power_muscle`, `fin_coined_money`, `mat_brass`, `mat_olive_oil`, `mat_silk` are all listed at cost 0 in a Mexica `available all`; `tr_sleeping_car` has no prerequisites and needs two artisans. Rome: `mat_copper` needs `blast_furnace` and `cap_heat_1100`; `mat_pozzolana` is not a starting tech (261).

## Item tables

Outcome key: **New N** filed; **Dup N (open)** appended as "Also reported"; **Dup N (closed)** a closed complaint covers it; **Not filed** with reason.

### Report A (Rome, fog plus fuzzy, won 358 AD)

| Item | Outcome | Reproduces now |
|---|---|---|
| Bug 1: save browser "None AD", 0 technologies | New 250 | Yes |
| Bug 2: weight-driven mechanical clock free and instant | New 262 | Yes |
| Bug 3: Rome still "under Trajan" at 361 AD | New 264 | Yes |
| Inconsistency 4: menu versus `play` default transistor goal | New 263 (closed 160 fixed only `goals`) | Yes |
| UI 5: literacy 0.75 shown while milestone BLOCKED | Dup 96 (open) | Untested |
| Validator nonfatal material-pricing warning | Dup 186 (open) | Yes (`el2_inductor_ferrite_core`, `ferrite_kg`) |
| Late-game wealth: 451.8 million at 361 AD | Dup 104, 184 (open) | Not replayed (a 361 AD game) |
| Exploit tests: buy 0.5 t iron, resell; sell hours twice | Not filed: no defect found (the spread is 80% of the buy price by design); positive |  n/a |
| Early game and destitute mortal run: sole carpenter lost, wages not financeable | Dup 233, 265 (new), 214 | Untested |
| Four separate pieces of delay information | Dup 234, 90 (open) | Yes (by design) |
| Optional warning before `step N` with unused hours | Not filed: exists (`multi_year_hours_warning`, `sim/engine/proto/dispatch.py`); noted on 100 | Yes (exists) |
| Knowledge/specialists/material/capital/calendar status, bottleneck report | Dup 129, 90 (open); compact half New 267 | Yes |
| Goal-aware importance (`why` "a few things" undervalues narrow prerequisites) | New 268 | Yes |
| Fog kept as serious option; praise | Positive | n/a |
| Dated events do not react to divergence; conditional events, neighbours, adoption | New 270; Dup 184, 107, 116 (open) | Yes (by design) |
| Public adoption dashboard | Dup 116 (open) | n/a |
| Political reactions to becoming indispensable | Dup 114 (open) | n/a |
| Mortality and succession as a system | New 256 (visible successor), 257; Dup 108 | n/a |
| Workforce visibility screen and warning | Dup 233 (open) | n/a |
| Interrupting time advancement on significant events | Dup 81 (open) | Partly exists (step stops early on some warnings) |
| Integrated portfolio dashboard | Dup 90 (open) | n/a |
| Save portability: export, backups, compression, summary | Dup 185, 208 (open); metadata is 250 | Untested |
| Post-victory and multi-goal tracking; score under fog | New 272; Dup 199, 224 | n/a |
| Fuzzy estimates: confidence display once started | Not filed: closed 192 and 195 cover the option; the request is a wording preference | n/a |
| Catalogue count 2,883 versus 2,879 | Not filed: not a defect; the testers' builds or loaded sample mods differ (untested) | Untested |
| Research failures that improve later odds; third-century crisis and dispersal | Positive | n/a |

### Report B (Rome, fog, won 301 AD, 65.1%)

| Item | Outcome | Reproduces now |
|---|---|---|
| Bug 1: failure loss far above forecast | New 251 (with 218, 151) | Yes |
| Bug 2: failed bounty orphan | New 252 | Yes |
| Bug 3: "never closed for want of staff" ticked | Dup 223 (open) | Yes (code) |
| Bug 4: FOREMAN column blank in `available` | Dup closed 149 lineage; not reproduced | No: `available all` shows smith, carpent, glassbl (truncated to seven letters) |
| Bug 5: `stuck` says 159 payable, `start` refuses "raise 0" | New 265 | Yes |
| Bug 6: stale hour pool in RUNNING lines | New 269 | Untested |
| Bug 7: priority rank counts finished work | New 269 | Untested |
| Bug 8: training list incomplete | Not filed: smith, mason and scholar trainees all list in `labour`; engineers and machinists need techs not reached | No for those trades |
| Bug 9: mod civilisation missing from menu | New 263 | Yes |
| Bug 10: default goal mismatch | New 263 (closed 160) | Yes |
| Bug 11: start allowed with no machinist | Not filed: the start warning exists (closed 131); startable-with-trainees is deliberate | n/a |
| Bug 12: `quit` gives no score; score needs a fast-forward | Dup 224 (open) | Yes (by design) |
| Coal arbitrage | New 253 | Yes |
| Runaway income; money irrelevant by about 125 AD | Dup 184, 104, 117 (open) | Not replayed |
| Idle waiting; no nudge | Dup 100, 101 (open) | n/a |
| Two-stroke engine startable about 109 AD | Dup 226 (open) | Yes (data: `pre cap_tol_1mm`) |
| Population may run hot (120.2 million by 302 AD) | Dup 104 (open, observation) | Untested |
| `mat_copper` blocked on `blast_furnace` | New 261 (with 127) | Yes |
| No pozzolana at start | New 261 | Yes |
| Medieval clock free in Rome | New 262 | Yes |
| Theory runs ahead of evidence (band theory in 141 AD before the electron) | Not filed: intended by the node notes (`em_theory`, `quantum_solidstate_theory`: "you carry the conclusions"); recorded for the owner | n/a |
| Industry never spreads (18 engineers, 10 on payroll) | Dup 107, 116 (open) | Untested |
| Dated events fire; "Rome under Trajan" in 600 AD; no divergence signal | New 270, 264; Dup 184 | Yes |
| Hidden funding rule | New 265 | Yes |
| Training cost surprise | Dup 220 (open) | Untested |
| Heavy attrition of specialists | Dup 205, 233 (open) | n/a |
| Supply gates invisible to `blocked_by` | New 267 | Yes (code) |
| Critical supply nodes look minor (RESTS) | New 268 | Yes |
| Long ids; aliases | Dup 196 (open) | Yes |
| No victory moment | Dup 224 (open) | Yes |
| Warnings drown in the year report; ALERTS block | Dup 81 (open) | Yes |
| Wait-time nudges | Dup 100 (open) | n/a |
| Diffusion of industry; divergence tracking; events that change | Dup 107, 116; New 270 | n/a |
| `score --final` | Dup 224 (open) | n/a |
| More civilisations (Abbasid, Song, Ptolemaic); speedrun mode and leaderboard | Not filed: product requests; noted (136 concerns adding civs as data) | n/a |
| AI players: scripts hide warnings; help discoverability of `sittings` | Dup 81, 99 (open) | Yes |

### Report C (three mortal Mexica runs)

| Item | Outcome | Reproduces now |
|---|---|---|
| Bug 1: no age shown | New 255 | Yes |
| Bug 2: death notice versus deputy hours | New 256 | Yes (text); live hours not replayed |
| Bug 3: ending ignores the dispersal | New 257 | Yes (text path) |
| Bug 4: "lapsed: Germ theory ... is closed" | New 258 (closed 182 and 202 are a different half) | Yes (harness) |
| Bug 5: `patron_local` failed three times running | New 254 (shared fixed seed) | Yes (seed stream) |
| Bug 6: "denarii" and "the Museum" in a Mexica game | New 260 | Museum yes; denarii in `risk` or step log no |
| Bug 7: "DEAD ... and ageing" | New 255 | Yes |
| Bug 8: achievement announced repeatedly | New 259 | Untested live |
| Bug 9: fractional people | New 266 | Yes (code) |
| Bug 10: corpus "600 offered, 0 effective" | Dup 68 (open) | Untested |
| Bug 11: `step 12` after death does nothing | Not filed: `step 12` at 1540 advanced to 1550 and ended the run, and after the end `step` answers "the run has ended"; tester's exact state not reproduced | No |
| Bug 12: unnamed move tiles | Dup 243 (open) | Yes |
| Lifespan fixed at 1538 | New 254, 255 | Yes |
| Invasion near-certain; say the design intent | New 270; Dup 204, 184, 249 (open) | Yes (90% a year in `risk`) |
| Knowledge hedge out of reach on a normal clock | Dup 213 (open) | n/a |
| Debt after smallpox is a trap | New 265; Dup 214 (open) | Untested |
| Losses scale with what you built | Dup 213 (open) | n/a |
| Fog resets between runs | New 271 (request) | n/a |
| No explicit successor mechanic | New 256 | Yes |
| Civ data: `cap_power_muscle`, `fin_coined_money`, `mat_brass`, olive oil, silk, clock, `tr_sleeping_car`, vaccination name | New 260 (clock also 262) | Yes |
| Suggestions 1 to 8 | Covered by 255, 256, 257, 258, 204, 265, 260, 271 | n/a |
| Own mistakes (helper script reopened concerns, etc.) | Not filed: the tester marks them as their own | n/a |

## Positives (do not break)

- The Mexica clock: a known 1519 deadline makes the first 19 years a real trade-off (C). Localised texture (cacao beans, ticitl, tecuhtli of the calpulli, plain quantitative Nahuatl). Plague measures visibly stacking (80% to 53% to 29%). The students finishing the dispersal after the founder's death was the most moving moment (C).
- Knowledge versus running it: finishing buys knowledge, running needs the right foreman (B). Materials and supply chains decide things: a coal mine took the blast furnace from about 1.0 million to about 105 thousand (B, the best moment); nitre beds, manganese, platinum by trade, precision straightness, vacuum and purity chains (A, B). Do not remove material requirements; both testers asked for them to be more visible, not softer.
- Fog is honest: `stuck` and `path` do not leak the tree; both Rome testers want fog kept.
- Consequences carry forward: early sanitation cut the Antonine plague to about 4% instead of about 28%; a dispersed corpus saved knowledge through a sacking and the third-century crisis (A, B). Research failures that improve later odds (A).
- Society pushes back (scandal, eminence, annona, proscription, confiscation) and the market saturation mechanic: A asked to expand it rather than replace it with cost multipliers.
- Early economy and destitute start: real financial traps; academy and delegated hours as strategic tools (A).
- Help and prose: `help sittings`, the arrival text; diffusion floors "a generation to train the trades"; "this society simply has its own engineers now" (B).
- No duplication exploit found in the iron buy-and-resell test (A); `--session` one-command-per-process works for agents (B).

## Cross-tester themes (three or more testers, counting earlier triages)

| Theme | Reported by | Complaints |
|---|---|---|
| Late money and money stops mattering; runaway snowball | A, B, Rome, England, Han | 184, 104, 117, 194, 118; new exploit 253 |
| No victory moment, no score after winning, score needs a run to the horizon | A, B, owner, Han | 224 (now asks for a victory screen and finish-and-score), 183 closed; 272 |
| Warnings and alerts drowning in step output; scripts hide sackings | B, A, C, Han, England | 81, 84, 233, 225; ALERTS block requested in 81 |
| Dated events do not react to divergence; no divergence signal | A, B, C (invasion predetermined), Rome, Han | 184, 270, 264; fixed seed 254 |
| Industry does not diffuse beyond the founder; no adoption view | A, B, Han, England | 107, 116, 104 |
| Blocked projects do not say what kind of blocker, or hide supply gates | A, B, Han, Rome | 129, 267, 268, 90, 219, 234 |
| Failure forecast disagrees with the charge | B, Han, England | 218, 251, 151, 241 |
| Staffing attrition and closures: hidden cause, no remedy named | A, B, C, Han | 233, 205, 223, 130 closed |
| Content from one civilisation leaks into another; free or instant nodes | B, C, Han, England | 260, 261, 262, 231, 198, 128, 42 (pinned), 226, 227 |
| Time gates and idle hours need explaining, not removal | A, B, Rome, Han | 100, 101, 234 |
| Debt, credit and the hidden funding rule | A, B, C, England | 265, 214, 220, 95, 154 closed |
| Default goal or entry point mismatch | A, B, Rome | 263, 160 closed |
| Saves: preview, export, size | A, Han, Rome | 250, 208, 185 |

Suggested priority for the owner: (1) 251 and 252, which silently destroy money; (2) 254 and 255, which make every mortal game look fixed and unfair and are cheap; (3) 224 with its owner's request, then 81 (alerts); (4) 253 (exploit) and 260 to 262 (data) before further playtests of Mexica; (5) 250 (save browser), 265 (stuck versus start) and 258 (a wrong message on every epidemic).
