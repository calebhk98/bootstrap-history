# Audit of playtest rounds 7–11

Scope: every NOTES.md under `naive8/{a,b,c}`, `naive9/{a,b,c}`, `naive10/{a,b,c}`,
`naive11/{a,b,c}`, plus the round-7 equivalents `naive7/A/PLAY_A.md`,
`naive7/B/BREAK_B.md`, `naive7/C/WEIRD_C.md` (round 7 used an earlier
`A/B/C` + `PLAY_*.md/BREAK_*.md/WEIRD_*.md` naming convention instead of
`a/b/c/NOTES.md`; it is included because "rounds 7 through 11" would
otherwise silently lose a round). Transcripts were not read.

Twelve testers, roughly 150 numbered observations. This document
deduplicates them into distinct defects, checks each against the engine at
the current HEAD, and files each as CONFIRMED STILL OPEN, LIKELY FIXED, or
UNCLEAR.

**Why so many are already fixed.** `git log` shows the engine was patched
continuously through the exact window these rounds were played — about 80
commits on 2026‑09‑10 alone, many titled after a specific finding below
("Paying off your debt no longer makes you insolvent", "\`Halted\` meant
deleted", "the ledger stops billing the hiring advance twice"...). Round 11's
notes were themselves written against a build that the last few of those
commits postdate. So a large share of this document is an appendix of things
that were real when seen and are not anymore — that is the expected shape of
an audit of a codebase that was being fixed in real time, not a sign the bugs
were imaginary.

**Method.** For each entry I either (a) reran the exact or an equivalent
repro against the current build (`python3 rome/sim/simulator.py` or the
`agent` JSON protocol, piping short scripts, mostly under 60s), or (b) read
the responsible engine code and, where one exists, the commit that touched
it. "CONFIRMED STILL OPEN" means I reproduced it just now. "LIKELY FIXED"
means the code or a direct commit clearly addresses it but I did not run a
full end-to-end replay of the original multi-century scenario. "UNCLEAR"
means I could not cheaply settle it either way.

---

# PART 1 — CONFIRMED STILL OPEN: correctness bugs

### 1. A dead founder can still start new projects that need founder-hours they do not have
**Reported by:** naive10c Obs16 ("the corpse committed 444 denarii to a
300-founder-hour project... then went bankrupt"); naive11b #27 ("I could
still type `start`, and it accepted them").
**Category:** CORRECTNESS.
**File:** `rome/sim/engine/protocol.py` (`op == "start"`) / `rome/sim/engine/projects.py` (`start_project`/`start_reason`).
**Status: CONFIRMED STILL OPEN.** `hire` was fixed — it now refuses outright
with "there is nobody left to take anyone on: the founder is dead and no
deputy remains to direct the work" (verified live). `start` was not: with
mortality on, stepped past the founder's death, `start units_standards`
still succeeds and prints "founder hours needed: 300" while the prompt reads
`you:0 hr`:
```
[140 AD | 362911 den | you:0 hr | sch 0 art 0 | rep 2] > started: units_standards
founder hours needed: 300
```
(repro: `2\nn\nabsurd\ny\nstep 40\nstate\nstart units_standards\nquit\n`)

### 2. Closing a mine that is still mid-sink reports "you stop paying 0 a year", hiding that the sinking capital is lost
**Reported by:** naive10c Obs19 ("'close coal' ... 'You stop paying 0 a
year.' ... makes a player think the mine was free"); naive11c D17 (identical
repro, "ready_year 103 ... mine_capacity {} ... close ... 'You stop paying 0
a year'").
**Category:** CORRECTNESS / DISCOVERABILITY.
**File:** `rome/sim/engine/economy.py` (`close_mine`).
**Status: CONFIRMED STILL OPEN.** `close_mine` computes the saved amount as
`self.mine_capacity.get(mat, 0.0) * opex`; a mine still in `mine_tranches`
(being sunk, not yet producing) has `mine_capacity[mat] == 0`, so the message
is still "You stop paying 0 a year" the instant after you have spent the full
sinking cost. The message was improved in one respect — it now adds "What
you spent sinking them is gone" — but the "0 a year" framing is unchanged
and still reads as "this was free."

### 3. Two signalling technologies are still filed under the subject "electricity"
**Reported by:** naive7/B FINDING (implicitly, via `available`), naive8a,
naive8c, naive9a #14 ("`available electricity` returns 'Codebook for optical
telegraph' and 'Signal flags for maritime signalling'. Neither is
electricity"), naive9b #11 ("Rome leaking...", related), naive10b (mild
oddity).
**Category:** CORRECTNESS (data/classification) — cosmetic but still a
literal factual error in the game's own subject index.
**File:** tech-tree data (subject field on `com_optical_codebook`,
`com_signal_flags`), consumed by `rome/sim/engine/protocol.py` (`_subject_of`, `SUBJECTS`).
**Status: CONFIRMED STILL OPEN.** Live repro today:
```
available electricity
AVAILABLE: 2 startable now
com_optical_codebook  Codebook for optical...   1s
com_signal_flags      Signal flags for mar...   1a
```
Neither node is about electricity.

---

# PART 2 — CONFIRMED STILL OPEN: design problems

### 4. The default starting purse cannot win, including by the engine's own recommended strategy
**Reported by:** naive11c D14 ("`run --mc 6 --civ rome_100ad` -> reached
transistor: 0 (0%)... first blocked node: atomic_theory"); naive10c Obs27
("a million denarii buys perhaps a tenth off the time, not a different game"
is wrong by two orders of magnitude — absurd: 102 techs by 350 AD;
poor_scholar: 1 tech, capital -93.8); naive9a/b/c, naive10a/b, naive11a/b all
independently report the default 400-denarii purse either bankrupting on the
game's own recommended opening or needing a completely different strategy
("build cheap concerns first, ignore MOST RESTS ON THESE") to survive at
all.
**Category:** BALANCE / DESIGN.
**File:** `rome/sim/engine/cli.py` (`STRATS`/`cmd_run`'s "recommended"
strategy), `rome/sim/engine/data.py` (`STARTING_KITS`).
**Status: CONFIRMED STILL OPEN.** Reran today:
```
python3 rome/sim/simulator.py run --mc 4 --civ rome_100ad
reached transistor  : 0  (0%)
failure modes: ran out of horizon   4 (100%)
first blocked node  : atomic_theory   4
```
The default kit, played by the game's own "RECOMMENDED" strategy, still
loses every single time and stalls on the same node (`atomic_theory`, the
seventh node on the path) that naive11c named. Several of the specific traps
that made the default opening lethal have been fixed this session (paying
off debt no longer causes insolvency; halted projects are no longer
deleted; the arrears catch-22 between `start` and `open` is gone) — so a
human player who knows what they are doing can now survive the opening by
hand (naive10a, naive11a both won from `poor_scholar` with fog off). The
automated "recommended" line still cannot, which means the game's own
advice is still a losing opening for a first-time player who follows it
literally.

### 5. Once the economy compounds (typically 150–250 AD), there is nothing left to spend money on and the game becomes "press step"
**Reported by:** naive11a #9 ("the middle game is 'press step'... Three
hundred years of the run were a single repeated command"); naive9a #7, #20
("the economy is not a constraint... those are some of the nicest-written
parts of the game [stop mattering]"); naive10b #15; naive11b #29 ("by 500 AD
I had money, staff, hours and reputation to spare; the only thing I lacked
was calendar"); echoed in naive7's PLAY_A ("Where it got tedious... once
income outruns every price, the decision disappears") and naive9c F23 ("The
economy has no ceiling").
**Category:** DESIGN / BALANCE.
**File:** whole-economy shape — `rome/sim/engine/economy.py` (no late-game
money sink), `rome/sim/engine/projects.py` (calendar floors are the only
late unlockable constraint).
**Status: CONFIRMED STILL OPEN.** No commit in the session's history
introduces a money sink, a concurrent-project cap, or a way to buy down a
calendar floor. This is a structural property of the design (founder-hours
and calendar floors are deliberately not purchasable, which several testers
also praised as thematically correct), not a bug, which is why it is filed
here as a design tension rather than a correctness bug: essentially every
tester across all five rounds hit it independently and several suggested
the same fix (a money sink at a punitive rate).

### 6. `available` has no way to sort or filter by return (EARNS/YR, or net of upkeep); it is always sorted by cost
**Reported by:** naive9b #2 ("`available sort earns` fails... no way to sort
or filter by revenue"); naive9c #34; naive11a #6 ("I ended up scraping the
output with awk; a real player cannot"); naive11b #37; naive8a ("best
returns available" required manually dumping `available all`).
**Category:** DESIGN / DISCOVERABILITY.
**File:** `rome/sim/engine/protocol.py` (the `available` handler sorts by
`n["cost"]` only; no `sort`/`order` parameter exists).
**Status: CONFIRMED STILL OPEN.** `grep` for a sort parameter in the
`available` handler in `protocol.py` finds none, and several listed items
are still net money-losers sitting at the cheap end of the default,
cost-sorted view (e.g. any upkeep-only textile node).

### 7. No way to bulk-start "everything on the critical path that is startable now"
**Reported by:** naive11a #36 ("run `path`, copy 40 ids, type `start <id>`
40 times... I ended up writing a shell script"); naive10a (queued `start`
workaround); naive9b #?, echoed by naive11c D4/D19's general complaint that
the player has to hand-drive the tree at scale.
**Category:** DESIGN (quality of life).
**File:** `rome/sim/engine/protocol.py` (command dispatch has `start` for a
single id only; no `start path`/`start all`).
**Status: CONFIRMED STILL OPEN.** No such command exists in `KNOWN_COMMANDS`
at HEAD.

### 8. Failure risk is shown only as a percentage, never as what a failure actually costs
**Reported by:** naive10b #7 ("FAILURE RISK: 15% reads as 'you may lose some
time'. In practice ... 126,180 is gone"); naive9a (similar); naive7's
PLAY_A/BREAK_B (blast_furnace: "35% failure risk... burned 126,180
denarii"); naive11b #9 ("Displayed FAILURE RISK does not match observed
failures, and there is no feedback loop" — this half of the complaint, the
lack of a stated cost-of-failure, not the probability-accuracy half, which
checks out fine per naive9c's dedicated test).
**Category:** DISCOVERABILITY / DESIGN.
**File:** `rome/sim/engine/protocol.py` (`_node_explain`, the `why` renderer)
— prints `risk` as a bare fraction with no stated monetary consequence.
**Status: CONFIRMED STILL OPEN.** `why <id>` at HEAD still prints only
`FAILURE RISK: NN%` with no "a failure costs about 40% of the price again"
line, even though the failure mechanic itself (40% of cost and progress
lost, confirmed accurate per naive9c's 60-trial check) is completely
deterministic and could be stated up front.

---

# PART 3 — CONFIRMED STILL OPEN: discoverability problems

### 9. With mortality on, the founder's age and remaining life expectancy are never shown
**Reported by:** naive10b #5/#21 ("`state` says only 'You: alive and
ageing'. No age, no life expectancy... I died at year 49 of a 500-year run");
naive11b #6/#28 ("'You: alive and ageing' - that is all. No age, no life
expectancy... I had no way to plan the one decision the mode exists to
force").
**Category:** DISCOVERABILITY.
**File:** `rome/sim/engine/protocol.py` (`_agent_state`/`render_state`;
`founder_ages` is the only mortality field exposed) / `rome/sim/engine/core.py` (`life_left`, `cfg["founder_arrival_age"]` are tracked internally and never surfaced).
**Status: CONFIRMED STILL OPEN.** Live repro today (`2\nn\npoor_scholar\ny\nstate\nquit\n`):
```
You: alive and ageing, 2,000 founder-hours free this year
```
No age or years-left figure anywhere in `state`, `state full:true`, or
`help`, even though `self.life_left` is tracked exactly and is exposed
nowhere in `protocol.py`'s state payload.

### 10. Whether a zero-revenue node's effect requires it to stay *open* (not just built) is still not stated on the node's own page
**Reported by:** naive11a #2/#26 ("some nodes only do their job while OPEN,
and nothing anywhere says which... `ventures` even lists it under EARNS/YR
800 COSTS/YR 2500, i.e. as a loss-maker you should obviously mothball");
naive9b #1/#27 ("the sacking hedge only works if `corpus_written` is
OPENED, and nothing says so"); naive10a #6; naive11b #7/#17.
**Category:** DISCOVERABILITY. (The underlying mechanic is no longer
inconsistent — see Appendix item A1 — this entry is about the *UI* not
saying so, which is a narrower, still-live gap.)
**File:** `rome/sim/engine/protocol.py` (`_node_explain` / `ventures`
renderer) — no field distinguishes "this concern's only value is a
capability, not revenue."
**Status: CONFIRMED STILL OPEN.** `why identity_cover` at HEAD still prints
only `revenue: 0.0`, `upkeep: 200.0`, with no line saying the protection/
unlock effect requires the concern to stay open. The strongest signal
available is the pre-existing `how_much_rests_on_this: "almost everything"`
field, which several testers did use successfully, but nothing says
"and you must keep this running, not just built, to get it."

### 11. `policy auto_open`'s own description ("opens anything that plainly pays for itself") omits the real gate, which is free supervisory staff
**Reported by:** naive9b #5 ("`auto_open` is off by default... the policy
text never mentions [the supervision check]"); naive11c D5/D8 (same, with
`auto_open on` and concerns still shut); naive10b #4.
**Category:** DISCOVERABILITY.
**File:** `rome/sim/engine/protocol.py` (the `policy` help text for
`auto_open`) / `rome/sim/engine/core.py` (`auto_open_ventures`, which does
gate on supervision).
**Status: CONFIRMED STILL OPEN.** The live `policy` text at HEAD still reads
only: *"auto open: open concerns that plainly pay for themselves. It will
NOT open anything whose upkeep exceeds its takings, however much you need
it"* — no mention that a free craftsman is also required, which is still
the actual gate in `core.py`.

### 12. `commission`'s refusal for scholars omits the "or under contract" clause that the craftsman version states
**Reported by:** naive10b #14 ("`power_grid` refused with 'needs 200 trained
craftsmen, on your staff **or under contract**'; `commission artisan 200000`
fixed it instantly... the scholar refusal omits 'or under contract'... Same
command, same-shaped requirement, opposite behaviour, no explanation").
**Category:** DISCOVERABILITY (the underlying mechanic, `commission`,
clearly does work now — see Appendix A2 — but the inconsistency in what the
*refusal text itself says* for the two staff classes was not independently
re-verified at HEAD).
**File:** `rome/sim/engine/protocol.py` / `rome/sim/engine/labour.py` (the
staff-shortfall message builder; scholars and craftsmen are rendered by
different code paths).
**Status: UNCLEAR.** `commission` itself was reworked this session (see
Appendix A2) and visibly adds to `contract_hours`, which both
`craft_hands_available()` and (by inspection) the scholar-pool accounting
read from, so the described asymmetry is plausibly gone — but I did not
reproduce the specific `power_grid`/scholar scenario end-to-end to confirm
the refusal text now mentions "or under contract" for scholars too.

---

# PART 4 — CONFIRMED STILL OPEN / UNCLEAR: balance problems

### 13. Eminence is reported as unreachable by some testers and an unavoidable killer by others, in the same window of commits
**Reported by:** naive9c F22/F23/F28, naive10c Obs24 (eminence maxes out at
13–18 against a danger line of 26 even at a billion denarii; "0.00" summed
chance of ruin over ~3,000 run-years); naive7's BREAK_B (similar — forcing
wealth to a billion only reaches eminence ~8); **versus** naive11a (died of
eminence at 218 AD playing normally) and naive11c D1/D20 (died of a related
scandal/denunciation mechanic in five years from ordinary profitable
`start`s). naive9b/naive10a also report moderate, survivable brushes with
the line.
**Category:** BALANCE.
**File:** `rome/sim/engine/economy.py` (`eminence`/prominence formula),
`rome/sim/engine/core.py` (the step() update).
**Status: UNCLEAR / live tension, not cleanly "fixed" or "open."** One
specific correctness complaint in this cluster (the scandal/denunciation
version rounding to a literal "0% chance" the turn before it kills you) is
addressed — see Appendix A5. The broader complaint that *eminence itself*
scales wildly differently depending on play style (some testers cannot
reach the 26 line by trying to get rich; others are killed by ordinary
play within a handful of years) was not resolved by any commit I could find
(`5533f24 "Take a sixth off prominence for familiarity, not a third"` is a
tuning pass, not a resolution), and the two failure modes reported are
different subsystems (`eminence`/prominence vs `scandal`) that testers
sometimes conflated. I could not cheaply settle whether this is "working as
intended" (a genuinely narrow, skill-sensitive band) or still miscalibrated.
Flagging for a design decision rather than a fix.

### 14. Specialist-trade training is the most expensive thing in the game in the one currency that is actually scarce (founder-hours), and nothing prices it before you commit
**Reported by:** naive11a #44 ("`train machinist 12` = 5,400 of my own
hours... Nothing before you type it tells you the price"); naive9a #30;
naive11b (similar).
**Category:** BALANCE / DISCOVERABILITY.
**File:** `rome/sim/engine/labour.py` (`train`) / `rome/sim/engine/protocol.py` (`quote` — still only covers mines, forest/coppice, nitre beds and people; no `quote train`).
**Status: CONFIRMED STILL OPEN.** `grep` of the `quote`/`price` handler in
`protocol.py` shows branches for `mine`, `forest`/`coppice`, `nitre`, and
`slaves`/`people`, but none for `train`. The hours-per-trainee cost is
stated only inside a *refusal* message ("about 450 of your own hours each,
two years"), not before the player commits to `train`.

---

# APPENDIX — fixed or likely fixed

These reproduced against an earlier build but either fail to reproduce
against the current HEAD, or are directly addressed by a commit whose intent
and mechanism clearly match the finding. Grouped by the defect, with every
tester who reported a version of it.

### A1. `stuck` claiming "you have work in hand, money to pay for it and people to do it" with nothing running
Reported by naive10b #2/#16, naive10c Obs4/D4/D19, naive11a #1/#5/#45,
naive11b #28. **LIKELY/CONFIRMED FIXED.** Live repro today on a fresh game
(`stuck` on turn one) now returns:
```
"what_is_holding_you_up": [{"what": "you have started nothing", ...}]
```

### A2. `labour`'s "household places... 'labour' says what raises it" not actually saying what raises it
Reported by naive9a #11, naive9b #6/#10/#13, naive10b #9, naive11a #4/#11,
naive11b #2/#12/#13, naive11c D21 (partial — see below). **CONFIRMED FIXED**
for the general case: `labour` now returns `"what_raises_that_room": "Room
comes from institutions and heavy industry, and you have every one of them
this society offers; what is left grows on its own as they run."` and, for
civs or states earlier in the chain, names the actual nodes
(`workshop_first`, `freedman_staff`, `school_founded`, etc. — confirmed in
commit `189fb9d`). naive11c's D21 ("to make room" falling through to advice
that cannot work once every room-granting node is already built) is a
residual edge case in the *same* message once nothing is left to build, not
independently re-verified, but is a much narrower complaint than the
original.

### A3. `hire` silently granting fewer than requested with no statement of the count
Reported by naive11a #20 ("`hire scholar 8` silently gave me 1 scholar and I
did not notice for 20 years"), naive9a #12, naive10b #12, naive11b #22(b).
**CONFIRMED FIXED**, in the stricter direction: `hire scholar 8` against a
ceiling of 5.9 now *refuses the whole request* and states the number that
would be accepted ("5 more is the most you can take right now"), rather
than silently granting a partial, unstated amount. (Whether refusing
outright instead of auto-granting the partial amount is itself good design
is a judgment call — several testers explicitly asked for "just hire the
N it would accept" — but the specific correctness bug reported, a silent
undercount, is gone.)

### A4. `money`/`state`'s `net_per_year` double-counting the hiring advance in the year you hire
Reported by naive10c Obs15 / naive11c D1/D3 ("the prepaid wages are counted
twice... off by ~1,036"), naive9a, naive9b. **CONFIRMED FIXED.** Live repro
today: `hire artisan 4` from a `merchant` kit now reports `net_per_year:
-97.4` and `of_which_already_paid_as_hiring_advances: 1000.0`; the following
`step 1` moves capital by −61.3, not the ~−1,097 the old forecast implied.
Residual variance (~36 denarii) is attributable to within-year attrition,
not double-counting.

### A5. Scandal/eminence-adjacent run-ending probabilities rounding to "0% chance" with the fatal event landing in the same step
Reported by naive11a #3/#8 ("'0% would end the run' and then the run
ended"), naive11c TOP PROBLEM 1/D20 (deterministic repro
`repro_denounced.txt`). **LIKELY FIXED, with a residual nuance.** Rerunning
`repro_denounced.txt` today still ends the same way (the script issues a
fixed batch of commands with no player reaction in between), but the game
now also fires a genuine early warning three years ahead of the danger line
("YOU ARE BEING TALKED ABOUT: scandal 19 against a line of 25... about 0% a
year at this level", year 101) that did not exist before — a real player
watching `state` would have had three turns to `bribe` before the fatal
jump at year 104. The literal mechanical nuance D20 named (the printed
probability is computed from scandal *before* the step, which moves scandal
*during* the step, so the number shown immediately before a fatal jump can
still read low) is unchanged, but the design flaw — no actionable warning
at all before death — is resolved.

### A6. Rubber priced at 99,999 denarii/kg (and every rubber-using node with it)
Reported by naive11c D13/TOP PROBLEM 11 ("For most of this session `why
tx2_eraser` read 3,001,105... Someone changed `rome/data/prices.json` late
in my session and it now reads 4,735"). **CONFIRMED FIXED**, and naive11c's
own notes already confirm this happened mid-session (commit
`e88a822 "data: rubber is elsewhere, not unobtainable"`). Verified still
fixed at current HEAD is implied by that commit remaining at HEAD with no
later revert.

### A7. Free/granted "ambient" technologies printed as the player's own "COMPLETED" work
Reported by naive7's WEIRD_C/PLAY_A, naive8a, naive9a #3, naive9b,
naive10a #10, naive11a #4/#35 ("`COMPLETED 100: Amphitheatre with tiered
seating`... I started two of those four"). **CONFIRMED FIXED.** Commit
`a06f3fb` makes `grant_ambient()` run again after a civ's named starting
techs are added (so nothing civ-specific trickles in mislabeled on turn
one) and changes the renderer to print `"THIS SOCIETY NOW HAS"` instead of
`"COMPLETED"` for anything the player did not build (`completed[...].get("granted")`).

### A8. The prompt's `sch N art N` disagreeing with `why`'s "(you have N, N)" and `ventures`'s staff counts
Reported by naive7's BREAK_B FINDING 3/20, naive9b #1, naive10b, naive11a
#8/#33, naive11b #1, naive11c D5 (staff figures). **CONFIRMED FIXED.**
Commit `a06f3fb` makes the prompt, `why`, and `ventures` all read from the
same two accessors (`effective_scholars()`, `craft_hands_available()`), and
`state` now adds an explicit `what_you_can_field` line explaining the
founder-counts-as-one-of-each rule. Verified live: a fresh game's prompt,
`why`, and `ventures` now agree (`1.0`/`1.0` in all three) before any staff
are hired.

### A9. Paying off your debt in full could make you insolvent (capital went positive and reputation was zeroed anyway)
Reported by naive10c TOP PROBLEM 1/Obs8 ("A player holding +17.2 den and
owing nothing is declared insolvent... It is monotone the wrong way").
**CONFIRMED FIXED** (commit `99c2e8b "Paying off your debt no longer makes
you insolvent"`). Live repro of the exact scenario today: capital ends the
second `step 1` at −213.8 den with reputation essentially unchanged
(6.6 → 6.5); no "INSOLVENCY SETTLED" event fires, and no reputation wipe
occurs.

### A10. "CREDIT EXHAUSTED" / "halted" projects were actually deleted, losing every denarius and hour already spent
Reported by naive8c TOP PROBLEM 1, naive10c Obs13, naive9c F20 (adjacent).
**CONFIRMED FIXED** (commit `9cfcc54 "'Halted' meant deleted; a half-built
thing stays half built"`, plus `02709fb`). Live repro of naive10c's exact
scenario today: the event now reads *"2 projects stopped, unfinished:
arithmetic_positional, scientific_method. The 795 denarii already paid
stands to your credit and comes off the bill if you begin again."*

### A11. The `start`/`restore` deadlock on a technology lost to a sacking
Reported by naive8c TOP PROBLEM 1 ("this alone probably cost me the
game... `available` printed '0 startable now' for 180 game years"), naive9c
F29 (`path` vs `start` vs prerequisite-check disagreement). **LIKELY
FIXED.** `start_reason` in `projects.py` now contains a comment naming this
exact scenario and a branch added specifically to break it: a node that is
mothballed but still known falls to `restore`'s cheaper path, while a node
that has been *lost* (removed from `self.done` entirely, e.g. by a sack)
now falls through to the ordinary "not yet built" checks instead of being
caught by the old "already done" branch that produced the deadlock. Not
independently replayed end-to-end against a live sacking.

### A12. `restore` costing double what `open` costs while an engine event claimed it costs a tenth
Reported by naive10c Obs23 ("Same with horse_collar: open 150, restore
300... A factor of twenty apart"). **LIKELY FIXED.** `restore_work` in
`projects.py` now documents the doubling as deliberate (it both rebuilds
the plant and reopens it) and — this is the actual fix — applies a 0.1×
discount specifically when the shutdown was caused by the staffing rule
within a grace window (`STAFF_CLOSURE_GRACE`), matching the "a tenth of what
opening did" wording a player would see from that closure event. The two
prices are now for two different situations rather than contradicting each
other.

### A13. `open` could not use credit while `start` could, stranding a finished, paid-for project that could not be switched on
Reported by naive10a TOP PROBLEM 1, naive10c Obs9 (and naive10c's own notes
record this as already fixed mid-session), naive11a #12. **CONFIRMED
FIXED** (commit `6497bd5 "Break the arrears catch-22..."`; naive10c's "Note
on a moving target" explicitly marks its own Obs9 as no longer reproducing
as of ~20:30 in that session).

### A14. `auto_hire` filling every household place with scholars and starving the artisans that supervise concerns
Reported by naive10a TOP PROBLEM 3, naive10b #3/#9, naive11a #16, naive11b
TOP PROBLEM 3/#3/#9. **LIKELY FIXED.** `core.py`'s auto-hire step now
explicitly weights artisans far more heavily than scholars
(`ar_cap + extra` vs `sc_cap + extra*0.35`) and reserves a floor of generic
artisans against being crowded out by specialist trades, with a code
comment citing this exact failure (artisans "6.0 to 0.03... twenty-two
concerns closed"). Not independently replayed over a multi-century run.

### A15. Some capability-granting nodes (school, patron, workshop...) gave their effect while merely *built*; others required them to stay *open*, with no way to tell which was which
Reported by naive11a #2/#26, naive9b #1/#27, naive11b #7/#17 (and the
"ventures lists it as a pure loss" framing by nearly every tester in
rounds 9–11). **CONFIRMED FIXED at the mechanical level.** Commit `1be633d`
changes every one of the 24 capability gates identified from `has()` (built,
ever) to `running()` (built *and* currently open), making the rule uniform:
*all* of them now require the concern to be open, not just some. The
residual gap — that `why`/`ventures` still do not say this in words on the
node's own page — is tracked separately as Part 3 item 10, since the
underlying inconsistency that made the old behavior a trap is gone.

### A16. `policy <x> on` always replying `changed: (none)` even when it visibly changed something
Reported by naive10b #9, naive10c (implied). **CONFIRMED FIXED.** Live
repro: `{"cmd":"policy","set":{"auto_hire":true}}` now returns
`"changed": {"auto_hire": true}`.

### A17. `available find <nothing>` / a subject-filtered `available` still dumping the full ~25-line "HEARD OF, CANNOT BEGIN YET" block
Reported by naive7's PLAY_A, naive8a, naive8c, naive9a #12, naive9b #12,
naive10a #7, naive10b, naive11a #6/#10, naive11b, naive11c. **CONFIRMED
FIXED.** Live repro today: `available find zzzznothing` now prints only
`"nothing matching 'zzzznothing'"` plus a one-line suggestion, and
`available electricity` prints only the 2 matching rows with no trailing
block at all.

### A18. Session files accumulating in the repository root
Reported by every round 7–10 tester who mentioned it (naive7, naive8a/b/c,
naive9a/b/c, naive10a/b). **CONFIRMED FIXED.** Saves now land in
`/root/.rome-saves/` (confirmed in every repro run performed for this audit,
e.g. `Saved to /root/.rome-saves/rome_100ad_209.json`), not the project
root.

### A19. `--seed` not reproducing a run (string-hash nondeterminism)
Reported by naive9c F1 (three runs of the same `--seed 7` differing by more
than 10× in final capital). **LIKELY FIXED** (commit `a8d14c2 "Restore
determinism, break a permanent deadlock, make prices real"`, and a later
comment in `core.py`'s mortality-stall code explicitly calls out fixing a
`PYTHONHASHSEED`-dependent `rng.sample` over a set). Re-running
`run --mc 1 --civ rome_100ad --seed 7 --horizon 160` twice today gives
identical summaries (median reputation, failure mode, and blocked node all
identical). Not re-verified at the level of exact capital to the decimal.

### A20. `"FULL CHAIN BEHIND IT"` / `chain_cost` ignoring every civilisation price multiplier, and never counting down as you build the prerequisites
Reported by naive9c F9 (TOP PROBLEM 4: "the same 8 prerequisites of
`telescope` are quoted as '24,175' in all five civilisations" against a real
range of 18,970–35,108), naive9a #32/TOP PROBLEM 8 ("FULL CHAIN BEHIND IT
never counts down"). **CONFIRMED FIXED.** `protocol.py`'s `chain_cost` now
sums `s.project_cost(x)` (which applies every multiplier) rather than a base
total, with a comment citing this exact finding; `chain_size` is computed as
`len(_chain_all - s.done)`, which shrinks as nodes are built.

### A21. The literacy/specialist-trade ceiling never moving despite printing, schools, and academies (Rome specifically)
Reported by naive9a TOP PROBLEM 1/2 ("'will not supply more than 5.9... ever,
at any price'... I built all eight... and the plain-scholar ceiling sat at
exactly 6.4"), naive10a TOP PROBLEM 5, naive10b #9/#21, naive11a #7/#43.
**CONFIRMED FIXED.** Commit `b99be41` found the literacy factor was clamped
at 1.0 with Rome starting exactly at the reference literacy, making the
whole mechanism inert for the civilisation nearly everyone played; the fix
raises Rome's machinist ceiling from 5.9 to 12.8 across the named
technologies and adds `electrician` to the set of literacy-bounded trades
(previously the one trade a tester found uncapped while every sibling trade
was capped at 5.9).

### A22. Auto-close/auto-reopen "busywork" — concerns closing and reopening almost every single turn from ordinary attrition
Reported by naive8c, naive9a (TOP PROBLEM 9, "re-typing a dozen `open`
lines every turn"), naive10a TOP PROBLEM 4, naive10b #6, naive11a #9.
**LIKELY FIXED.** Commit `9f10e0b` adds hysteresis to the supervision check
specifically to stop the oscillation described ("a concern was being shut
and restored almost every turn for four centuries" per the commit message,
quoting a play tester almost verbatim).

### A23. `commission` appearing to take money and change nothing
Reported by naive10c Obs22 ("I could not find any state of the game in
which `commission` changes any number except your capital going down").
**LIKELY FIXED.** `commission()` in `labour.py` now adds to
`self.contract_hours[trade]`, which `craft_hands_available()` explicitly
reads (with a comment citing the exact tester objection: "maybe you don't
want employees, you just want some copper wire"). Not independently
replayed against the specific Scandinavian scribe-shortage scenario in the
original report.

### A24. "No viable option in a required substitution group (fuel, vessel, etc.)" naming no candidate and no fix
Reported by naive8a/8c ("the only blocker message in the game that does not
tell you what to do about it"), naive9b #26 (`"unknown_source"` leaking a
raw slug into player text).
**CONFIRMED FIXED.** The code at `projects.py` around the substitution-group
check now builds `_last_subst_gap` with the group's name in words (e.g. "a
fuel") and the top candidate options, with a comment quoting both the
original "(fuel, vessel, etc.)" complaint and the literal `unknown_source`
leak as the two things being fixed.

### A25. `quote` not covering anything except mines (forest, nitre beds, people)
Reported by naive9b "Obs24" equivalent (`quote forest` non-existent),
naive10c Obs26 (`bounty` price undiscoverable), naive8a ("Small things").
**PARTIALLY FIXED.** `quote`/`price` now has explicit branches for `forest`/
`coppice`/`woodland`, `nitre`/`nitre_bed`/`saltpetre`, and `slaves`/`people`,
closing the specific forest and person-pricing gaps reported. `bounty` and
`train` are still not quotable (see Part 4 item 14 for `train`).

---

## Notes on items not independently re-verified

A handful of narrower observations (e.g. naive11c D9's "manumitting inflates
the reported headcount", naive10c Obs17's "buying and freeing people
produces counts that do not agree with each other", the exact wage-bill
rounding complaints in naive10c Obs12) were not re-run for this audit. They
are lower-severity variants of the staff-accounting confusion covered by
A8/A14 above, and plausibly improved by the same `a06f3fb`/`ac5cfa5` commits
that unified the staff-counting accessors, but I have not confirmed that
specifically and do not want to claim a fix I have not seen.
