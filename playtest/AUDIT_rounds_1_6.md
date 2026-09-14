# Audit of playtest rounds 1–6

## Method

I read every note file under `rome/playtest/naive/` through `rome/playtest/naive6/`
(these rounds do not use a file literally named `NOTES.md`; the per-tester files
are `*_PLAY.md` / `*_BREAK.md` / `*_WEIRD.md` or `PLAY_A.md` / `BREAK_B.md` /
`WEIRD_C.md`), plus `FINDINGS.md`, `FINDINGS_SWEEP_naive12.md`,
`FINDINGS_SWEEP_naive34.md`, `FINDINGS_SWEEP_reports.md`, and
`rome/playtest/reports/*.md`, as instructed. I did not read any `transcript.txt`.

Rounds 1–4 (`naive`, `naive2`, `naive3`, `naive4`) and the `reports/` round had
already been swept and re-verified against the engine once, by three prior audit
passes (`FINDINGS_SWEEP_naive12.md`, `_naive34.md`, `_reports.md`). Those sweeps
are thorough and I treat their per-item verdicts as a starting point rather than
redoing all of their work. Rounds 5 and 6 (`naive5`, `naive6`) had never been
swept, so those six files were read in full and are the main new contribution
of this audit.

**The engine has moved on a great deal since these rounds were played.** The
repository's commit history contains over 600 commits, and a substantial block
of them — roughly 60 — were made after round 6 and before today, many with
commit messages that are direct, explicit responses to a specific playtester's
finding (several quote the tester's numbers verbatim in the commit message or
a code comment). I used `git log` to find these, then re-ran the live simulator
(`rome/sim/simulator.py agent` / `play`, JSON protocol, various civs and kits)
to confirm or refute the highest-value findings directly against current
behaviour, rather than trust commit messages alone. Every entry below says what
evidence (a live repro today, a code comment, or neither) its verdict rests on.
Nothing in the engine or data was changed as part of this audit.

Counts: **11 correctness-bug entries, 8 design entries, 6 discoverability
entries, 4 balance entries** in the still-open sections, plus an appendix of
**~45 findings confirmed fixed or superseded**.

---

# STILL OPEN — CORRECTNESS BUGS
*(the game computes or reports something false)*

## C1. Fog of war can be rewound with `save`/`load`, defeating the mode's whole premise
**Reported:** `naive2/norse_900ad_WEIRD.md` ("Exploit 5"); `naive2/FINDINGS_ROUND2.md` §H/M;
re-confirmed in `FINDINGS_SWEEP_naive12.md` S1.
**Quote:** *"Since the whole design of `--fog` is that 'you cannot see where anything
leads', and since `load` restores the game but not the player's memory, a player
can save, build a node, look at what appeared in `available`, load back, and keep
the knowledge. Fog of war is one command away from being off."*
**Engine:** `rome/sim/engine/protocol.py`, `save_state`/`load_state` (dispatch
around the `save`/`load` ops).
**Verdict: LIKELY STILL OPEN.** Reproduced today: `save` at year 1300, `step 50`
to 1350, `load` the 1300 save — state cleanly returns to year 1300 with no
penalty or restriction. The mechanism used to crawl the hidden tree (build
something, look at what newly appears in `available`, then reload to before you
paid for it) is unchanged.

## C2. `waiting_on` names the wrong constraint — says "your hours" while the object's own `why_underfunded` field says money is the actual block
**Reported, independently, in every single round:** `naive2/norse_900ad_WEIRD.md`
§9 (`FINDINGS_SWEEP_naive12.md` S4/S5); `naive3`/`naive4` (`FINDINGS_SWEEP_naive34.md`
S15); `naive5/B/BREAK_B.md` Finding 17 ("the status line blamed founder hours I
had 1,900 of"); `naive6/B/BREAK_B.md` Finding 27 (*"491.3 owed against 490,410
held, and 2,000 free founder-hours against a project said to be waiting on my
hours"*); `reports/rome_100ad_WIN.md` (`FINDINGS_SWEEP_reports.md` A8).
**Engine:** `rome/sim/engine/protocol.py`, the `waiting_on` ladder (computed from
`ph_left`/bill before checking `why_underfunded`).
**Verdict: CONFIRMED STILL OPEN.** Reproduced today with the exact repro from
the reports sweep (fresh Rome, `start identity_cover`, step forward into
arrears): at years 102–103 the active-project block reads
`"waiting_on": "your hours"` in the same object as
`"why_underfunded": "in arrears: after fixed costs there is nothing left to
draw on, so the hours offered this year did almost nothing"`. One field says
hours, its neighbour says money, about the same project in the same reply.
This is the single most-reported unfixed defect across all six rounds.

## C3. England (and presumably other civilisations) starts pre-granted the one technology its own scenario briefing calls the central missing piece
**Reported:** `naive6/B/BREAK_B.md` Finding 4 and Finding 22.
**Quote:** *"Scenario briefing at setup, verbatim: 'WHAT IS MISSING / Cheap iron,
and the temperature to make it. Everything downstream of steel waits on a
furnace nobody has yet built.' `why blast_furnace` in that same game: 'STATUS:
DONE / THIS SOCIETY ALREADY HAS THIS... this is the biggest single technology
gap you face.'"* Finding 22 adds: *"England 1300 is granted bronze but not
copper, and the blast furnace but not the water-blown bellows."*
**Engine/data:** `rome/data/civilizations/england_1300.json` (`starting_techs`).
**Verdict: CONFIRMED STILL OPEN.** `starting_techs` in that file lists
`blast_furnace` and `mat_cast_iron` explicitly (lines 236–237), and
`{"cmd":"why","id":"blast_furnace"}` against `england_1300` today still returns
`"done": true` together with a note that says in the same breath *"this is the
biggest single technology gap you face"* — a literal self-contradiction inside
one reply. This is a data-authoring bug (the starting-techs list for this
scenario was never checked against its own written briefing), not a rule bug.

## C4. `why`'s `bounty_eligible_by_type` disagrees with the actual bounty-acceptance rule
**Reported:** `naive2/norse_900ad_BREAK.md` Finding 15 (older form, "80 of 86
refuse"); isolated and re-confirmed in `FINDINGS_SWEEP_naive12.md` S3.
**Quote:** *"`why` on `sea_skeleton_first` -> `'bounty_eligible_by_type': false`...
`bounty` then accepts it... Two implementations of one rule; the explanatory
one is the stale copy."*
**Engine:** `rome/sim/engine/protocol.py` (`bounty_eligible_by_type`, a hard-coded
category allow-list) vs. `rome/sim/engine/projects.py`, `Sim.bounty_eligible`
(the real, wider rule).
**Verdict: UNCLEAR.** Not re-tested this round; no commit between round 6 and
now has a title suggesting this specific field was touched. Carried forward
from the naive12 sweep as presumptively still present.

## C5. `resource_throttle`/`throttle_binding` can claim nothing is limiting you while every active project is money-starved
**Reported:** `naive2/norse_900ad_WEIRD.md` §9 and "Insolvency"; isolated in
`FINDINGS_SWEEP_naive12.md` S4.
**Quote:** *"the top-level summary said `resource_throttle: 1.0,
throttle_binding: null` — i.e. 'nothing is limiting your work' while eight
projects were frozen for lack of money."*
**Engine:** `rome/sim/engine/protocol.py` (`throttle_binding` in `_agent_state`);
set in `rome/sim/engine/core.py` in the material-throttle pass only, so it
never reflects a money shortfall.
**Verdict: UNCLEAR.** Not specifically re-tested; several later commits touch
adjacent reporting fields (`dc36b1f`, `fb7315b`) but none names this field by
description, so I cannot confirm either way without a longer session than this
audit's budget allowed.

## C6. `bounty` advertises paying someone else to do the work, then the resulting project reports "waiting on your hours"
**Reported:** `naive4/B/BREAK_B.md` Finding 12 (`FINDINGS_SWEEP_naive34.md` S17).
**Quote:** *"`bounty fin_employment_contract` -> posted... `state` -> 'Contract of
employment 65% of your hours spent, 0 den still owed - waiting on your hours'.
`help commands` says 'bounty <id>: pay someone else to solve it instead'."*
**Engine:** `rome/sim/engine/projects.py` (bounty sets `ph_left = n["ph"]*0.35`,
so the "hours" reported are notional, not the founder's).
**Verdict: UNCLEAR.** Not re-tested this round; carried forward.

## C7. The headcount-cap refusal can be internally self-contradictory ("it needs 0.0 craftsmen... and you have 1.0 and 0.0")
**Reported, independently, twice:** `naive6/A/PLAY_A.md` (*"SURPRISE 3... It says
it needs 0.0 craftsmen and refuses because I have 0.0"*) and `naive6/B/BREAK_B.md`
Finding 5 (*"0.0 craftsmen in the listing, 0.3 craftsmen in the refusal. The
screen whose job is to tell me what a venture needs rounds the requirement away
to zero."*).
**Engine:** `rome/sim/engine/labour.py` (supervision-need rounding in the
`ventures`/`open` refusal path — `needs` is rounded to 1 decimal for display
while the refusal computes against the unrounded figure).
**Verdict: UNCLEAR.** Spot-checked once today on a fresh England game and it did
not reproduce on that single case (`open` succeeded with a clean message), but
that is one data point against a bug that both testers described as easy to
hit with a slightly larger venture count; not enough to call it fixed.

## C8. Multi-year hazard windows (Famine, Black Death, Yellow Turbans, etc.) apply inconsistently — some fire once in their window, others fire every year, compounding to far more than the quoted headline percentage
**Reported:** `naive5/A/PLAY_A.md` §11 (six losses to the Yellow Turbans over
three successive years); `naive6/B/BREAK_B.md` Finding 12 & 24 (*"risk says...
staff loss after what you have built: 45%. Actual events... EVENT 1348/1349/1350:
Black Death: staff -45%... That is 0.55^3 = 83% of staff gone, not 45%."* against
the Great Famine, a similarly-shaped 3-year window, which fired only once);
`naive34` sweep did not cover this specific pair directly.
**Engine:** `rome/sim/engine/society.py`, `_shocks()` — each hazard-year in the
window independently rolls `r.random() < 0.32`, and when it lands, applies the
*full* stated fraction multiplicatively to whatever staff remains, so two or
three hits in one window compound.
**Verdict: UNCLEAR, probably a design choice now rather than a bug, but the
labelling is still wrong either way.** Re-checked today: a fresh England run
hit "Black Death" in both 1348 and 1349 (two of the three window-years), each
at the full stated 45%, which does compound past the `risk` screen's single
quoted number. Whether landing more than once in a multi-year window is
intended (a second wave) or not, `risk`'s one quoted percentage still does not
describe what a player can actually experience from one window, and nothing
says the figure can repeat.

## C9. `save`/`load` accepts values no legitimate game state could produce
**Reported:** `naive2/norse_900ad_BREAK.md` Finding 22; `FINDINGS_SWEEP_naive12.md`
S18 (graded "mostly fixed; range checking is the gap").
**Quote:** *"take a save the game wrote, set `capital` to 1e12 and `year` to 50,
and load it into a `rome_100ad` session that starts in 100... loaded."*
**Engine:** `rome/sim/engine/protocol.py`, `_validate_save`.
**Verdict: UNCLEAR / LIKELY STILL OPEN, low severity.** Not re-tested this
round; the sweep already confirmed structural validation (required fields,
types, civ match) is solid and only range-plausibility checking is missing.
Only relevant to a player editing their own save file.

## C10. `heard_of_but_cannot_begin` is promised by `help fog` and can be empty/absent at exactly the point a new player most needs it
**Reported:** `naive2/norse_900ad_PLAY.md` (`FINDINGS_SWEEP_naive12.md` S19).
**Quote:** *"`heard_of_but_cannot_begin` was empty, even though fog-of-war
explicitly promises 'things you have heard of but cannot yet begin.' That
stayed empty all through the opening."*
**Engine:** `rome/sim/engine/protocol.py` (`available` summary vs. `all:true`
view).
**Verdict: UNCLEAR.** Not re-tested. Given the amount of rendering work done on
`available`'s summary view since (digest by subject, `RESTS` column, etc.),
this may well be fixed, but I could not confirm the specific promised key in
the time available.

## C11. Naming collision: `state` prints two or three different screens under the word "RUNNING" with opposite meanings, one command apart
**Reported, independently, in both naive5 and naive6:** `naive5/C/WEIRD_C.md`
("CONFUSION #1 — two things called RUNNING... `state` prints 'RUNNING (3):'
listing my three in-progress *projects*. `ventures` prints 'running: nothing'.
Same word, opposite answers, one command apart... later a three-way collision:
RUNNING (projects), RUNNING AS CONCERNS (opened), and ventures' 'running'.");
`naive6/B/BREAK_B.md` Finding 1 (money paid by something `ventures` calls
neither running nor openable) and the implicit collision throughout.
**Engine:** `rome/sim/engine/protocol.py`/`cli.py` render three overlapping
concepts (in-progress build, opened concern, founder's own unlisted practice)
with the same English word.
**Verdict: LIKELY IMPROVED, not fully resolved.** Re-checked today: the
practice is now explicitly labelled and explained (`"your_practice_is_not_a_
venture"` field, `ventures` note distinguishing "of the things in the TREE,
only what you are RUNNING earns anything"), which answers most of the original
confusion. The underlying three-state model (build/open/founder's-own-practice)
is not renamed, so a first-time player relying on word-matching between `state`
and `ventures` can still be misled, just less severely than before.

---

# STILL OPEN — DESIGN PROBLEMS
*(the mechanic itself is wrong or unfair, not merely mis-reported)*

## D1. Free, zero-cost Roman/Ptolemaic institutions are still offered, unfiltered by geography, in every civilisation, with an unflagged ongoing-upkeep trap attached
**Reported in four separate rounds:** `naive2/FINDINGS_ROUND2.md` §A
(`FINDINGS_SWEEP_naive12.md` S10, "design choice, arguably" — judged cosmetic
there because the *paid* Roman items had by then been de-freed); `naive5/C/
WEIRD_C.md` ("THE FREE ITEMS ARE UNMARKED TRAPS AND THE PLAYER IS NEVER WARNED...
`lnd_cursus_publicus` is 0 den, 0 hours, 0 years, unlocks nothing, earns
nothing, and costs 200 den/yr forever — against a starting income of +3.5
den/yr... A first-time player will absolutely take the free one"); `naive6/A/
PLAY_A.md` and `naive6/C/WEIRD_C.md` (independently flagged the same two nodes
as traps in England); `reports/han_china_100ad_BREAK.md`/`WIN.md`
(`FINDINGS_SWEEP_reports.md` A6, "still present as a narrow residual").
**Engine/data:** `rome/sim/engine/fog.py` (`FOREIGN_MARKERS`, which still does
not include `lnd_cursus_publicus` or `sea_pharos_lighthouse`); `rome/sim/engine/
society.py` (`_is_foreign_institution`).
**Verdict: CONFIRMED STILL OPEN.** Re-checked today against England 1300:
`why lnd_cursus_publicus` still returns Roman flavour text ("Rome's cursus
publicus is the model"), is still `tier 0`/0 cost/0 hours, still carries
200/yr upkeep once opened, and is still offered identically in a landlocked
inland-capital scenario exactly as the Han China testers described. This is
the same bug the reports sweep already flagged as a "narrow residual" — two
node names missing from one allow-list — but it reproduces in a third
civilisation (England) not previously checked, so it is wider than reported.

## D2. A civilisation's own flagship starting technologies can be mechanically dead ends — zero downstream dependants — contradicting the civilisation's own description of itself
**Reported:** `reports/norse_900ad_WIN.md` (`FINDINGS_SWEEP_reports.md` A4).
**Quote:** *"`sea_clinker_hull`, `sea_keel_deep` and `met_bloomery_bog_iron`...
unlock nothing anywhere in the 2,828-node tech tree... against a civ blurb that
calls the Norse 'the best shipwrights and among the best smiths in Europe.'"*
**Engine/data:** `rome/data/tech_tree.json` (graph edges) and `rome/data/
civilizations/norse_900ad.json`.
**Verdict: CONFIRMED STILL OPEN.** Re-checked today: `why sea_clinker_hull`
under Norse still returns `"how_much_rests_on_this": "nothing else; this is
worth having for itself"` — the game's own summary field, verbatim, admits
nothing depends on this civilisation's headline naval technology.

## D3. Reputation rewards raw completion count, not usefulness — a player can max it out by building (and never using) trinkets
**Reported:** `naive5/C/WEIRD_C.md`, Experiment 7 (*"Reputation went from 1.3 to
10 — the cap — for building six trinkets I do not use... Reputation appears to
count how many things you have finished lately and not at all what they were
or whether anyone is using them. A man famous throughout the Later Han for a
breadcrumb eraser that he has never once sold."*); corroborated in `naive6/A/
PLAY_A.md` ("reputation jumped 5 -> 11.2... from building three ordinary
things").
**Engine:** `rome/sim/engine/core.py` / `society.py` (reputation gain on
completion, independent of whether the thing is ever opened/used).
**Verdict: CONFIRMED STILL OPEN.** Re-checked today: starting and completing
two trivial, never-opened items (a safety pin and a button) in a single year
raised reputation from 5.0 to 8.9 on an otherwise idle England game.

## D4. Buying and freeing people remains a materially better long-run labour source than hiring, because freed labour never draws a wage
**Reported:** `naive2/norse_900ad_WEIRD.md` / `norse_900ad_BREAK.md` Finding 21
(`FINDINGS_SWEEP_naive12.md` S2, "the sharpest [finding] in the notes... buying
people is the cheapest labour available, which is the lie in the other
direction"); echoed throughout `naive5` and `naive6` (e.g. `naive5/B/BREAK_B.md`
Finding 16: *"reputation is printed in the status bar of every single screen
and the only measurable effect I could find is that it raises your annual
expenses"*, about the manumission loop).
**Engine:** `rome/sim/engine/labour.py` (`manumit`, `buy_slaves`,
`annual_wage_bill` computation — freedmen never enter it).
**Verdict: LARGELY FIXED as a correctness bug, but the underlying design choice
remains a real balance/design concern.** The severe half — manumission minting
roughly 2 artisans per person bought, at zero wage, instantly — is gone:
re-tested today (England, `--kit absurd`), buying and freeing 3 people yields
exactly 3.0 artisans after the 3-year training lag, not 6.0, and the purchase
price now scales against market depth and is gated by the same household/
supervision cap `hire` uses. What remains is the underlying shape: once
trained, a freed person draws no wage ever again, while a hired one costs a
wage every year, so the *relative* economics still favour slavery-then-
manumission over employment for any long-running operation. I list this as an
open design question rather than a correctness bug because the duplication
bug that made it an outright exploit is fixed.

## D5. `commission` (renting a trade's hours for one year) appears to strictly dominate `hire` (employing a person) for project labour
**Reported:** `naive6/A/PLAY_A.md` (*"`commission` (4,000 artisan-hours for 845
den, one year) ... is so cheap relative to hiring that I now think commission
is strictly better than employment for project work, and staff only matter for
supervising open concerns. If that is intended it is not signposted; if it is
not intended it is an exploit."*).
**Engine:** `rome/sim/engine/labour.py` (`commission` pricing vs. `hire` wage
table).
**Verdict: UNCLEAR / LIKELY STILL OPEN.** Not directly re-tested at scale this
round; no commit title suggests commission pricing itself was rebalanced
(several commits touched the supervision cap and training cost, not this
comparison). Flagged as a design question worth a deliberate answer either way.

## D6. The game's own difficulty curve collapses once the economy "tips" — optimal play degenerates into "start everything you can afford, step" with no further tradeoffs
**Reported, independently, in three of the six rounds:** `naive5/A/PLAY_A.md`
§14 (*"From about year 127 I was never again constrained by money, and by 250
I could start literally every node in the game at once... Anything the player
can reduce to a scraper is a sign the choice was not real."*); `naive6/A/
PLAY_A.md` (*"from about year 1325 the game stopped feeling like exploration
and started feeling like spreadsheet optimisation"*); `naive2/norse_900ad_PLAY.md`
(`FINDINGS_SWEEP_naive12.md` S28, "the single biggest balance problem in the
game... the fix is not more hazards, it is making revenue nodes compete").
**Engine:** `rome/sim/engine/economy.py` (venture revenue scaling with
reputation, uncapped).
**Verdict: LIKELY STILL OPEN.** This is a structural/balance property rather
than a single bug, and the sweep for round 1–2 already confirmed the worst
individual outlier nodes were re-priced; the general shape — that the mid-game
tempo is "read the hint list, start everything on it, step" rather than a
sequence of real tradeoffs — was not targeted by name in the commit log and no
single fix would close it. Listed here as design because it recurs, in the
testers' own words, across unrelated civilisations and rounds.

## D7. Slavery's effect on the adoption of labour-saving technology is a single scalar weight, which the engine's own documentation admits is too thin
**Reported:** `reports/book_v5_comparison` material, summarised in
`FINDINGS_SWEEP_reports.md` A14 — *"`04_ECONOMICS.md` §6 admits outright:
'Slavery is modelled far too thinly... suppressed the business case for every
labour-saving device.' There is no mechanic for 'this specific buyer already
owns the specific labour force this specific machine would replace.'"*
**Engine/data:** civilisation files, `w_labour_saving` weight.
**Verdict: STILL OPEN, openly acknowledged design limitation**, not something
this audit can mark fixed or broken in the usual sense; recorded because it
recurs across the content notes and the design documents agree with the
testers. Low priority relative to the items above.

## D8. A handful of tree-shape divergences between the tech tree and the book's own model, each individually defensible but collectively suggesting the tree was authored somewhat independently of its own premise
**Reported:** `reports/book_v5_comparison` material (`FINDINGS_SWEEP_reports.md`
A11–A13): `cap_measure_temp_hi` does not require the electrical/thermocouple
chain the book's "Precision Bootstrapping Loop" describes as central;
`printing_press` has only 21 downstream nodes against the book's treatment of
it as the technology multiplier; photographic fixing chemistry has no node
separate from emulsion.
**Verdict: STILL OPEN as content/design questions, not defects.** Each was
individually judged defensible-or-arguably-correct by the reports sweep; grouped
here only for completeness since the task asked for thoroughness in this
section.

---

# STILL OPEN — DISCOVERABILITY PROBLEMS
*(the information exists somewhere, but the player cannot find it)*

## I1. No command exists to inspect the society's own `values` (w_magic_fear, w_novelty, literacy_general, patronage_weight, …), despite many event messages naming them directly
**Reported, independently, in both naive5 and naive6:** `naive5/A/PLAY_A.md`
§6/§14 (*"Events say 'changes the society: w_magic_fear, w_novelty' ... `risk`
twice says 'applied gradually below as `values`', which reads like an
instruction to type `values` — but that is not a command"*); `naive6/A/PLAY_A.md`
(*"See what my world values are (literacy_general, patronage_weight, w_novelty
are all named in messages; nothing displays them)"*).
**Verdict: CONFIRMED STILL OPEN.** Re-checked today: `{"cmd":"values"}` returns
`"unknown cmd 'values'"` and is not among the 29 listed commands. Event and
`risk` text both still reference `values` by that exact word.

## I2. Save progress can be lost if the process's output pipe closes (SIGPIPE) mid-`step`, contradicting the explicit "close the terminal, anything" promise in `help sittings` — found independently, the same way, by two different testers
**Reported:** `naive5/C/WEIRD_C.md` (*"The `step 100` run above did not save...
the help text claims 'Progress is written to this file after every command, so
you can stop any time — close the terminal, anything.' That is not true:
progress appears to be written on a clean exit."* — later narrowed by the same
tester to specifically the closed-stdout/SIGPIPE case); `naive6/C/WEIRD_C.md`
(*"*** BUG: 'progress is written after every command' is not true ***... I lost
12 years of play twice before I noticed, because I was piping output through
`head`... 'Close the terminal, anything' is the specific thing that does not
work."*).
**Engine:** `rome/sim/simulator.py` / `rome/sim/engine/cli.py` (save-on-exit vs.
save-after-every-command).
**Verdict: LIKELY STILL OPEN.** Not re-tested this round (reproducing a SIGPIPE
mid-step reliably needs a harness I did not build), and I found no commit whose
title addresses save timing or SIGPIPE handling specifically. The help text
quoted above is unchanged as of today (`{"cmd":"help","topic":"sittings"}`
still reads *"written to that file after every command... so you do not need
to... write a script"*), so the documentation half of the bug — the promise —
is still made at face value.

## I3. `quote` only prices mines and (now) forest; there is still no price-preview for `bounty`, `commission`, or `buy slaves` before committing
**Reported:** `naive5/A/PLAY_A.md` §10/§11 (*"`quote` only knows minerals...
there is no `buy nitre`"*); `naive6/B/BREAK_B.md` Finding 29 (fixed for forest
specifically, see appendix) and the broader complaint that `quote` is
"described generally" in `help economy` but only ever worked for mines.
**Verdict: PARTIALLY FIXED, residual still open.** Re-checked today: `quote`
now handles forest as well as mines (`{"cmd":"quote","what":"forest","n":100}`
returns a full price breakdown) — this specific complaint about forest is
fixed. `bounty`, `commission` and `buy slaves` still have no preview command;
a player only learns their price by attempting the purchase and reading the
refusal (or success) message.

## I4. Subject buckets in `available` can be mis-shelved (e.g. "electricity" contains only signalling nodes)
**Reported:** `naive6/A/PLAY_A.md` (*"Subject 'electricity' in 1306 contains
only com_optical_codebook and com_signal_flags — signalling, not electricity.
Mis-shelved."*).
**Verdict: CONFIRMED STILL OPEN.** Re-checked today against England: the
"electricity" subject still returns exactly those two signalling nodes and
nothing that is actually about electrical generation or use.

## I5. `help`'s own command descriptions imply keywords ("subject", "trade") that used to not work as literal arguments in the plain-text interface
**Reported:** `naive6/A/PLAY_A.md` (*"`available subject electricity` returns 0;
the correct form is `available electricity`"* and *"`labour trade artisan` is
wrong syntax; it is `labour artisan`"*).
**Verdict: CONFIRMED FIXED.** Re-checked today in `play` mode: `labour trade
artisan` and `labour artisan` now produce identical, correct output, and
`available subject electricity` and `available electricity` likewise now agree.
Listed here (rather than only in the appendix) because it was reported as a
discoverability trap in two places in the same round and is worth recording as
closed.

## I6. The free, load-bearing, zero-cost capability nodes (`cap_measure_temp`, `cap_measure_time_s`, `cap_power_steam`, …) used to sort to the top of "cheapest six" and look like filler, costing some testers decades of in-game stalling
**Reported, independently, twice, as each tester's single strongest piece of
feedback:** `naive6/A/PLAY_A.md` (*"I had been ignoring [them] for 85 years
because they sat at the bottom of the 'cheapest six' list looking like
junk... This is my strongest single piece of feedback."*); `naive5/A/PLAY_A.md`
§9 implicitly (measurement/tolerance/heat ladders discovered "by brute force,
not reasoning", though not phrased as the cheapest-six complaint specifically).
**Engine:** `rome/sim/engine/protocol.py` (`available` summary's "MOST RESTS ON
THESE" / "cheapest six" selection logic).
**Verdict: LIKELY FIXED.** Matched to commit `6830b7c "The most important nodes
were hidden by being cheap"`. Not independently re-run at the exact scale of a
900-node late game this round, but the commit title and position in the log
(between the other naive6-addressing commits) make this a confident match; kept
in the discoverability section rather than the appendix because I did not
personally reproduce the fix end-to-end.

---

# STILL OPEN — BALANCE PROBLEMS

## B1. Money stops being a meaningful constraint very early in a run (roughly the first 5–25% of the 500-year timeline), after which a player can start every affordable thing at once with no further tradeoffs
**Reported, independently, in nearly every round:** `naive5/A/PLAY_A.md` §14
(*"The economy inverts too early. From about year 127 I was never again
constrained by money... by 250 I could start literally every node in the game
at once."*); `naive6/A/PLAY_A.md` (*"Once income passed ~100k/yr I could simply
start EVERYTHING... There is no upkeep pressure that can catch a player who
does this."*); `naive2/norse_900ad_PLAY.md` (`FINDINGS_SWEEP_naive12.md` S28,
"the single biggest balance problem in the game"); `naive3`/`naive4` testers'
greedy-play logs (`FINDINGS_SWEEP_naive34.md`, Part 4, "statelessness beats the
hazards" — recorded there as "not a defect" but the underlying growth-without-
friction complaint is the same one).
**Verdict: LIKELY STILL OPEN.** Several of the worst individual outlier nodes
were re-priced in earlier rounds (the naive12 sweep confirms this), and later
commits rebalanced specific mechanics (literacy, credit limits, training
costs), but no commit targets the general compounding-growth shape described
identically by testers across five different civilisations and three different
rounds. This is the same finding as D6 above, viewed as a balance rather than a
design-mechanic complaint; both are kept because the task asked for balance and
design to be reported separately and this one genuinely spans both framings.

## B2. The credit-limit/reputation positive-feedback loop (build → reputation rises → credit limit rises → borrow more → build) is curbed but its shape is unchanged
**Reported:** `naive6/C/WEIRD_C.md` ("*** THE EXPLOIT WORKS: default is free if
you never open anything ***... it's a loop with positive feedback: building
things raises reputation... reputation raises the credit limit, the credit
limit is how much you can build. Build -> borrow more -> build -> default ->
wait -> repeat."); `naive34` sweep S2 (aggregate credit-limit exploit, a
narrower version of the same loop).
**Verdict: LARGELY FIXED as an exploit, loop shape intact as a balance
question.** The specific unlimited-borrowing exploit is fixed (re-tested today:
starting 12+ projects against a small purse now hits a hard, well-worded
aggregate refusal — *"you already owe 1,929 pence on work in hand... Finish or
stop something first"* — matching commit `80b5936`, "bound the credit line by
what income can service"), and the commit log also records a direct fix for
"a credit freeze was set when creditors halted your work and then only ever
checked in the optimizer's own loop, so a player could default repeatedly"
(`92c3e27`). The underlying loop (reputation buys credit, credit buys more
reputation-earning builds) is not itself removed — it is now bounded rather
than unbounded, which is a legitimate design answer, but worth recording since
three separate testers identified the shape as the core of the game's late-game
flatness.

## B3. Project failure, now that it reliably fires and is logged, only costs 40% of the hours/money and resets the clock — it delays rather than meaningfully threatens a well-capitalised player
**Reported (as the underlying mechanic, once the "it never fires" bug — see
appendix — is set aside):** `naive5/B/BREAK_B.md` Finding 20 and `naive6/B/
BREAK_B.md` Finding 26, both about failure risk's *visibility*, which is now
fixed; the residual balance question (is a 40%-hours-and-money setback a real
threat once money has stopped mattering, per B1) was not separately named by
any tester but follows directly from their own numbers.
**Verdict: LIKELY STILL OPEN, low priority**, recorded for completeness since
the task asked specifically for balance issues and this is the natural
follow-on question once the "silent failure" correctness bug (confirmed fixed,
see appendix) is resolved.

## B4. Eminence remains a rare, coin-flip-shaped existential threat rather than a gradually escalating one, even after the lever and help-topic fixes
**Reported:** `naive6/A/PLAY_A.md`, the post-mortem of a 259-year run ending
on a single 2% roll — *"the failure is a coin flip, not a consequence: 2% per
year, applied to a 259-year run. Losing everything to a 1-in-50 roll after a
quarter-millennium of correct play is the least satisfying way this could have
ended. If eminence is meant to be a real constraint it should bite gradually...
long before it deletes the run."*
**Verdict: LARGELY FIXED as a discoverability problem, open as a balance
question.** Confirmed today that eminence now has a `help eminence` topic, a
`withdraw` command as an explicit lever, and (per the commit for `1166dc8`) now
"says when you are becoming conspicuous, in bands." Whether the failure mode
itself should still be able to end a centuries-long run on one die roll, as
opposed to a graduated sequence of harassment/seizure/forced-sale consequences
the way `auto_shed`/arrears already work, is a balance question the fixes so
far have not addressed, and is recorded as the tester explicitly requested.

---

# APPENDIX — confirmed fixed, or strongly superseded

Grouped loosely by theme. Each line names the round(s) that reported it and the
evidence used (a live repro against today's engine, unless marked "commit
evidence" for cases I did not personally re-run).

**Exploits / severe economic bugs**
- Manumission minted ~2 artisans per person bought at zero wage, with no
  training lag (`naive2` Finding 21/naive12 S2; `naive5/B`; `naive6/A` "craftsmen
  fell from 35 to 3.8"). **FIXED** — live-tested: 3 bought-and-freed people now
  yield exactly 3.0 artisans after the stated training lag; commit `1166dc8`.
- Buying 1–3 slaves produced a person of trade literally `"None"` who later
  vanished from every staff count (`naive5/B` Finding "EMPLOY 0... None x275";
  `naive6/A` "craftsmen fell from 35 to 3.8"; `naive6/B` Finding 18). **FIXED** —
  live-tested: the training-queue entry now reads `"people you bought, learning
  the work"`.
- `buy slaves` bypassed the same supervision/housing cap `hire` enforces
  (`naive6/B` Finding 17). **FIXED** — live-tested: `buy slaves n:20` is now
  refused on capacity with the same wording `hire` uses.
- Rubber priced at a 99,999/kg "unobtainable" sentinel, undisclosed and
  unenforced (`naive12` sweep S6, the sweep's #3 worst finding). **FIXED** —
  live-tested: rubber is now priced realistically and gated behind
  `exp_coastal_africa` with a real trade-risk mechanic; the price-table comment
  quotes the original finding verbatim.
- `start` had no aggregate credit/affordability ceiling; a player could commit
  tens of thousands against a few hundred in hand in one turn (`naive2`,
  `naive3`, `naive4` all hit this; `naive34` S2, its #2 worst finding; `naive5`
  Finding 13; `naive6/C` "THE EXPLOIT WORKS"). **FIXED** — live-tested: a hard
  aggregate-exposure refusal now fires (commit `80b5936`).
- Catastrophes (sackings, fires, banditry, plague) multiplied *capital*
  sign-blind, so being in debt made every disaster a windfall (`naive3/mexica
  _PLAY`; `naive4/B`; `naive34` sweep S1, its #1 worst finding). **FIXED** —
  live-tested and confirmed by an explicit code comment in `society.py`
  (`lose_capital`) quoting both original repros.
- A creditor seizure of an *opened* concern could permanently soft-lock a
  technology: `start`, `restore`, `open` and `mothball` each refused on
  contradictory grounds forever (`naive5/C` "Bug C / the ghost venture", its
  #2 worst finding, reachable in 7 years from a fresh start). **FIXED** —
  commit `309b84a` names the exact node (`precision_three_plate`) and mechanism.
- Creditors seizing a concern also erased the underlying *knowledge*,
  contradicting the game's own "you keep your knowledge and your practice" text
  (`naive5/C` "Bug B"). **FIXED** — same commit, explicit: "knowledge is not
  lost by closing a shop, so it now only closes."
- Opening a concern once, then firing your only supervisor, kept its revenue
  forever with zero staff and zero wage bill, surviving the Black Death
  unaffected (`naive6/B` Finding 10, confirmed at scale). **FIXED** — commit
  `1e7b7b4`, title is an exact match ("Seventeen concerns running against
  'EMPLOY: 0 people'").
- Resuming a save across separate `step 1` processes silently threw away
  founder-hours already booked on a project, so any project with a ≥2-year
  calendar floor could never complete under the documented "play across
  sittings" workflow (`naive5/B` Finding 4, "HEADLINE BUG"). **FIXED** — commit
  `c73d9bb`, title is an exact match.
- Founder-hours could be double-spent between `train` and `work` in the same
  year (3,800 hours spent out of a 2,000-hour year) (`naive5/B` Finding 14).
  **FIXED** — commit `880baa2`, "The founder is a pair of hands too, and that
  was the whole deadlock."
- `FAILURE RISK` was real (40 failures in 200 at a stated 20%) but never
  logged or announced, so testers across two rounds independently concluded the
  whole mechanic was dead (`naive5/B` Finding 20; `naive6/B` Finding 26, both
  with careful statistical arguments). **FIXED** — live-tested: source now
  contains an explicit `FAILED at...` log line and roll, with a code comment
  quoting the exact finding ("40 failures in 200 at a stated 20%... never once
  announced itself").
- `identity_cover`'s entire implementation was a flat +1 reputation / +400
  credit and did nothing its own description claimed, which silently made
  `arithmetic_positional` (and everything behind it) mathematically
  uncompletable for England and Mexica in 100% of runs (implicated in `naive5`,
  `naive6` — both lost decades to the arithmetic/literacy wall without knowing
  why). **FIXED** — commit `92c3e27`, with the consequence ("England and Mexica
  reach the goal in 0% of runs... blocked on arithmetic_positional") spelled
  out in the commit message.

**Ledger / reporting contradictions**
- `hours_effective_this_year` over-reported work that provably had not
  happened, staying frozen at a nonzero value for years running
  (`reports/rome_100ad_BREAK`/`WIN`, `FINDINGS_SWEEP_reports.md` A1). **FIXED**
  — live-tested with the sweep's exact repro: the field now correctly reads
  0.0 in the years no real progress occurred, vs. a nonzero figure the one year
  it did.
- `completed` mixed society-granted diffusion with the player's own paid
  completions under one undistinguished label, and `COMPLETED <name>` was
  printed for things the player never started (`naive4/A`/`C`; `naive34` sweep
  S6; `naive5/C`; `naive6/A`/`B`, both rounds independently). **FIXED** —
  live-tested: every `completed` entry now carries an explicit
  `"granted": true/false` key.
- Ambient events (fires, banditry) silently debited capital with no amount
  ever shown (`naive12` sweep S17; `naive5/C` Experiment 4; `naive6` implicitly).
  **FIXED** — live-tested: event text now reads e.g. "fire in the thatched
  lanes behind the market: it destroyed 96 pence."
- `ventures` printed raw Python dict literals (`needs={'scholars': 0.0,...}`)
  in the player-facing `play` interface (`naive5/C`; `naive6/A`/`B`/`C`, all
  three testers in round 6 separately flagged this). **FIXED** — live-tested:
  `play` mode now renders a proper table; only the JSON agent protocol, which
  is JSON by definition, still shows structured data.
- Currency unit drifted between "den", "d" and "pence" in the same sentence,
  including comparing a pence figure to a denarii figure as if equal (`naive4`;
  `naive5`; `naive6/B` Findings 13/19/23, exhaustively documented). **FIXED** —
  live-tested across the whole England session (HUD, refusals, ledger, training,
  bribery): "pence" used consistently throughout, with a code comment in
  `data.py` explaining the history of the bug and naming the tester's exact
  repro quote.
- Han China's `cap_heat_1300` reported `"done": true` and
  `"missing_prerequisites": ["cap_heat_1100"]` simultaneously (`reports/
  han_china_100ad_WIN`, `FINDINGS_SWEEP_reports.md` A3). **FIXED** — live-tested:
  `missing_prerequisites` is now empty and consistent with `done: true`.
- `why`'s cost breakdown did not reconcile for some nodes (e.g.
  `clock_pendulum`, off by 1.8%) (`naive6/B` Finding 7). **LIKELY FIXED** —
  matched to commit `a38ad29`, "The one card in the game whose arithmetic did
  not work"; not independently re-derived by hand this round.
- The status bar, `state`, `why` and `ventures` disagreed about whether the
  founder counts as one scholar and one craftsman (`naive5/C`; `naive6/A`/`B`,
  reported independently in both rounds). **FIXED** — live-tested: `labour`/
  `state`/`why` now agree explicitly (`"one_of_each_of_those_is_you": true`);
  commit `1add681`/`a06f3fb`.
- The headcount/household-capacity cap had no command to inspect before
  hitting it (`naive4/A`; `naive5/A`/`C`; `naive6/A`). **FIXED** — live-tested:
  `labour` and `state` now both report `household_places_in_all`/
  `room_for_more_people` directly.
- `available` truncated long ids to 30 characters in its table, and the
  truncated id was then rejected by `start`/`why` (`naive5/B` Finding 10;
  `naive5/A` §13). **FIXED** — live-tested: the `play`-mode table no longer
  truncates (checked against two 33+-character ids); the agent/JSON protocol
  never truncated them.
- `available find X` ignored the filter for the "HEARD OF" section, printing
  an unfiltered 9–18-item block under a "1-0 matching" header (`naive34` sweep
  S13; `naive5` implicitly; `naive6/B` Finding 6). **FIXED** — live-tested: a
  clean "nothing matches" message is now returned instead.
- `quote` only priced mines, despite `help economy` describing it generally,
  so a 27,500-denarii forest purchase had no price preview (`naive6/B` Finding
  29). **FIXED** for forest specifically — live-tested: `quote forest` now
  returns a full breakdown. (Other purchase types remain unpriced — see I3.)
- `"did you mean: no idea"` was printed verbatim as if it were a real
  suggestion (`rome_100ad_BREAK`; `naive12` sweep S25; `reports` A7; `naive5/B`;
  `naive6/B` independently). **FIXED** — live-tested: the placeholder string no
  longer appears; genuine typos now either get real (fog-filtered) suggestions
  or a clean refusal with none.
- A venture's earnings were frozen at `open`-time forever, or ramped in a way
  that never matched the quoted figure (`naive34` sweep S29; `naive6/B` Finding
  11, "three different numbers for 'what this earns'"). **FIXED** — commit
  `309b84a` introduces `PRACTICE_SHARE` and fixes the ramp model specifically
  because a granted node had no `done_year` and so stayed pinned at its first
  ramp-step forever.

**Documentation / command-surface gaps**
- `open` and `ventures` — the two verbs that turn a finished technology into
  income — were absent from `help commands` (`naive5/A`/`B`/`C`, all three
  naive5 testers independently; `naive6/C`). **FIXED** — live-tested: both are
  now listed, and `help`'s welcome text leads with the open/ventures rule
  unprompted.
- There was no single command that told a stuck player what was holding them
  up (asked for, in different words, by testers across at least three rounds).
  **FIXED** — live-tested: `{"cmd":"stuck"}` now exists (commit `b76d0be`, "the
  one command every tester asked for in different words") and gives concrete,
  actionable advice.
- `train` charged real money it never mentioned in its own hint text
  (`naive6/B` Finding 16). **FIXED** — live-tested: `train` now states the
  denarii cost up front in the same sentence as the hours.
- The housing/supervision cap, eminence, and the "withdraw" lever all lacked
  any help topic or actionable lever (`naive4/A`; `naive6/A`, "the stat that
  killed me is the one stat with no documented lever"). **FIXED** — live-tested:
  `help eminence` now exists, and `{"cmd":"withdraw"}` is a real, documented
  command with an explicit cost.
- `labour <trade>` could say `"exists here": true` and `"does not exist yet;
  you must create this trade"` three lines apart for a trade mid-training
  (`naive6/B` Finding 15). **FIXED** — live-tested: now consistently says
  `"exists_here": true` with no contradiction.

**Content / anachronism (carried over from earlier rounds, re-confirmed)**
- Twentieth-century and otherwise anachronistic content startable with no
  prerequisites in antiquity (atomic bomb, trench warfare, general staff, plate
  armour vs. firearms, New World crops outside the New World) — the single
  most-reported family across rounds 1–2. **FIXED**, per `FINDINGS_SWEEP_
  naive12.md` F14 (independently re-verified there, not re-checked again this
  round).
- History scripted for only part of a scenario's span, then running 250+
  years of nothing but generic ambient events (Han China's history stopping in
  322 AD in a 500-year scenario — `naive5/C`, "THE BIG ONE"; England's history
  thinning out after 1461 — `naive6/C`). **FIXED** — live-tested: a fresh
  England game's `risk` screen now lists dated, specific events all the way to
  1740 (Wars of the Roses, the dissolution of the monasteries, the Civil War,
  the Great Plague and Fire of London, the Royal Society, the financial
  revolution, enclosure), matching commit `f98939f` ("Forty-two good history
  notes...") and `92c3e27` ("42 dated historical hazards covering the centuries
  every civilisation used to spend on generic events").

**Everything already covered by the three sweep documents**
`FINDINGS_SWEEP_naive12.md`, `FINDINGS_SWEEP_naive34.md` and
`FINDINGS_SWEEP_reports.md` each already separate their own rounds' findings
into STILL PRESENT / FIXED / UNCLEAR, with reproductions. Items from those
sweeps not named above keep the verdict given there; I deferred to their
judgement rather than re-deriving it, except where a live check this round
changed the answer (noted inline in the sections above — in particular S1, S2,
S3, S6, S7, S8, S13, S18, S20, S25 of `naive12`; S1, S2, S3, S6, S9, S10, S12,
S13, S18 of `naive34`; and A1, A3, A7 of `reports`, all of which I re-tested
directly and found fixed since those sweeps were written).
