# Findings sweep: everything reported or revealed by `playtest/reports/` and `playtest/book_v5_comparison/`

Source notes swept (all .md, in full):

- `playtest/reports/rome_100ad_BREAK.md`, `rome_100ad_WEIRD.md`, `rome_100ad_WIN.md`
- `playtest/reports/han_china_100ad_BREAK.md`, `han_china_100ad_WEIRD.md`, `han_china_100ad_WIN.md`
- `playtest/reports/norse_900ad_BREAK.md`, `norse_900ad_WEIRD.md`, `norse_900ad_WIN.md`
- `playtest/book_v5_comparison/technology_and_prerequisites.md`, `society_and_economy.md`,
  `narrative_and_pacing.md`

Every entry below was re-checked against the **current** code in `rome/sim/engine/` and the
current data in `rome/data/` (tech_tree.json, civilizations/, prices.json), and where possible by
actually running `rome/sim/simulator.py agent|play`. Nothing in the repository was modified.

The engine has been split out of the single `simulator.py` into `rome/sim/engine/{data,geography,
economy,labour,society,fog,projects,core,protocol,cli}.py`, and most line numbers quoted in the
notes no longer resolve. Verdicts are against behaviour, not line numbers.

**Score: 14 STILL PRESENT, 4 UNCLEAR/JUDGEMENT, 38 FIXED** (plus 2 entries in Part C that were
never defects and are recorded only so they are not re-filed).

---

# PART A — STILL PRESENT (most severe first)

## A1. `hours_effective_this_year` / `hours_this_year.effective_on_projects` reports work that demonstrably did not happen

- **Claim at issue (notes):** rome_100ad_BREAK F5 — *"`founder_hours_left` **increases** from 0.0
  to 160.0 — a 'hours remaining' counter that goes back up after reaching zero is not a progress
  counter, it's broken"*; rome_100ad_WIN F3 — *"`spent` kept climbing every step throughout …
  even while `founder_hours_left` was already negative"*; han_china_100ad_WIN — *"every project
  report hours 'offered' and none 'effective', with nothing anywhere explaining the gap"*.
- **Where:** `reports/rome_100ad_BREAK.md` §FINDINGS F5; `reports/rome_100ad_WIN.md` §FINDINGS F3.
- **Status: STILL PRESENT** (a residual of an otherwise-fixed family — the negative/non-monotonic
  hours bug itself is gone, see F-A in Part C).
- **Exact reproduction (verified today):**
  ```
  printf '{"cmd":"start","id":"identity_cover"}\n{"cmd":"step","years":1}\n{"cmd":"state","full":true}\n{"cmd":"step","years":1}\n{"cmd":"state","full":true}\n{"cmd":"step","years":1}\n{"cmd":"state","full":true}\n' \
    | python3 rome/sim/simulator.py agent --civ rome_100ad --seed 1
  ```
  Years 101, 102, 103, 104 all report, identically:
  ```
  "hours_this_year": {"available":2400.0,"offered_to_projects":500.0,
                      "effective_on_projects":387.2,"unused":1900.0}
  active.identity_cover: {"founder_hours_left":112.8, "hours_offered_this_year":500.0,
                          "hours_effective_this_year":387.2, "underfunded_this_year":true}
  ```
  `founder_hours_left` never moves off 112.8 across four consecutive years, while the game tells
  the player 387.2 of his hours were *effective* each of those years.
- **My judgement: real defect.** In `engine/core.py` the year's offer is
  `per = min(remaining, max(st["ph_left"], n["ph"]/max(n["yrs"],1.0)))`, deliberately allowed to
  exceed `ph_left`; the *actual* work taken off is `spent_hours = min(per, st["ph_left"])`. The
  refund path correctly caps `give_back` at `spent_hours - refunded`, but the reporting line is
  `st["hours_effective_this_year"] = round(max(0.0, per - refunded), 1)` — computed from `per`,
  not from `spent_hours`. So in any year where a project has fewer hours left than a full year's
  offer *and* is underfunded, effective hours are over-reported (here by 3.4x, and the true net
  effect is zero). The comment two lines up says exactly why this is supposed to be capped ("you
  cannot be refunded work you never did"); the cap was applied to the refund and not to the
  report.
- **Severity: misleads a player, badly.** Founder-hours are the resource the whole game is built
  around, and this is the field the code added specifically so a player could audit them. A player
  budgeting from it will believe 387 hours/yr are being converted into progress while zero are.

## A2. A run can enter a permanent negative-net equilibrium in which "INSOLVENCY SETTLED" fires once a decade forever, and nothing says the run is effectively over

- **Claim at issue (notes):** norse_900ad_WEIRD F3 — *"A player who makes one bad purchase early …
  can be locked out of the goal for the rest of the game, with the game continuing to accept
  commands and give the impression of an ongoing playthrough for 470+ more years, and the only
  feedback being the same static 'in arrears' message every time."* Also han_china_100ad_WEIRD F6
  (*"no insolvency/bankruptcy mechanic"*) — the opposite end of the same axis.
- **Where:** `reports/norse_900ad_WEIRD.md` §FINDINGS F3 (self-described "the most important
  finding of the session").
- **Status: STILL PRESENT in a milder, recoverable form.** The hard softlock is fixed (see C-K);
  the permanent-stall shape is not.
- **Exact reproduction (verified today):** `--civ norse_900ad --kit absurd --seed 1`,
  `start identity_cover`, `step 2`, `buy slaves 150`, `buy manumit 150`, then `step 10` x 12.
  From roughly year 942 onward:
  ```
  EV 949  INSOLVENCY SETTLED: most of the debt is written off and you still owe about 839 denarii...
  EV 959  INSOLVENCY SETTLED: ... you still owe about 328 denarii ...
  EV 969  INSOLVENCY SETTLED: ... about 328 denarii ...
  EV 979 / 989 / 999 / 1009 / 1019  (identical, forever)
  y 972 cap -924.5   y 982 cap -924.5   y 992 cap -924.5   (unchanged to the decimal)
  {"cmd":"money"} -> revenue 202.3, upkeep 200.0, living 222.1, net_per_year -219.9
  ```
  `done_count` never moves again. `{"cmd":"start","id":"units_standards"}` succeeds but the
  project is permanently underfunded and never completes (100 years, `done_count` unchanged).
- **My judgement: real defect, in the *signalling*, not the arithmetic.** `engine/economy.py`
  throttles the settlement to "once a decade at most", and its own comment says *"A write-off is a
  once-in-a-life humiliation, not an annual accounting entry"* — but in a 500-year horizon that
  still fires ~50 times, each time deducting 12 reputation from a value already floored at 0. The
  state is escapable — I got out of it with 40 consecutive `{"cmd":"work","trade":"scholar",
  "hours":1500}` + `step` pairs, reaching +5,933 by year 1032 — but nothing in `state`, `money`,
  `risk` or the repeated event says "your standing costs exceed your practice; sell hours or shed
  works". `mothball` alone was not enough (net stayed -19.9/yr).
- **Severity: loses a game, silently.** A player who does not think of `work` will step to the
  horizon believing the run is alive.

## A3. Han China: `cap_heat_1300` reports `done: true` **and** `missing_prerequisites: ["cap_heat_1100"]` in the same reply

- **Claim at issue (notes):** han_china_100ad_WIN, F-note — *"`why` on `cap_heat_1300` … shows
  `"done": true` **and** `"missing_prerequisites": ["cap_heat_1100"]` simultaneously — the
  simulator considers a node completed whose own direct prerequisite is not completed."*
- **Where:** `reports/han_china_100ad_WIN.md`, "F-note: a real capability-graph inconsistency
  found via `why`".
- **Status: STILL PRESENT.**
- **Exact reproduction (verified today):**
  ```
  printf '{"cmd":"why","id":"cap_heat_1300"}\n' | python3 rome/sim/simulator.py agent --civ han_china_100ad --seed 1
  -> {"id":"cap_heat_1300","done":true,
      "direct_prerequisites":["bellows_water_blown","cap_heat_1100"],
      "missing_prerequisites":["cap_heat_1100"],
      "can_start_now":false}
  ```
- **My judgement: real defect (data + logic).** `han_china_100ad.json` grants `cap_heat_1300`
  directly without back-filling `cap_heat_1100`, and nothing closes a civ's `starting_techs` over
  its own prerequisites at load time. The tester was right that it cost them nothing here, but a
  node that is simultaneously done and blocked is an internally contradictory graph state, and
  `can_start_now: false` on a node already `done: true` is a third contradiction in the same
  object. The obvious fix is to take the prerequisite closure of `starting_techs` when granting
  them, the same way ambient tier-0 grants already walk the order.
- **Severity: mildly corrupts state / misleads a player.** No run has been lost to it, but it
  makes `path`/`why` output untrustworthy for the affected civ.

## A4. Norse's three headline starting technologies are mechanically inert: zero downstream, zero revenue, zero upkeep

- **Claim at issue (notes):** norse_900ad_WIN F2 — *"`sea_clinker_hull`, `sea_keel_deep` and
  `met_bloomery_bog_iron` … (b) unlock nothing anywhere in the 2,828-node tech tree … and (c)
  contribute zero revenue and zero upkeep"*, against a civ blurb that calls the Norse *"the best
  shipwrights and among the best smiths in Europe."*
- **Where:** `reports/norse_900ad_WIN.md` §FINDINGS F2, and its answer to assignment Q4.
- **Status: STILL PRESENT.**
- **Verification (today, over the current 2,831-node tree):**
  ```
  sea_clinker_hull        downstream 0   rev 700.0  up 180.0  cat ships
  sea_keel_deep           downstream 0   rev 300.0  up  60.0  cat ships
  met_bloomery_bog_iron   downstream 0   rev 420.0  up  90.0  cat metallurgy
  exp_openocean_navigation downstream 3  rev   0.0  up 300.0  cat expedition
  ```
  and a fresh Norse `{"cmd":"money"}` at year 900: `revenue 232.7`, of which *all* comes from
  `med_cataract_couching` (166.7) and `med_trepanation` (66.7). None of the 1,420 den/yr of `rev`
  on those three nodes reaches the player, because `revenue()` pays out on granted nodes only for
  `PRACTISABLE_CATS` (surgery/obstetrics/pharmacology/medicine/diagnosis/dentistry).
- **My judgement: real gap, though the revenue half is a defensible design choice.** Excluding
  granted non-practisable nodes from revenue is well argued in the code (owning a bloomery as a
  starting condition is not personal income). The genuinely unjustifiable half is the **zero
  downstream edges**: three named starting advantages that no node in the tree depends on are not
  advantages at all. `exp_openocean_navigation`, the fourth, is real, which shows the difference
  is not intentional.
- **Severity: makes the simulation unrealistic** and hollows out one civilization's stated
  identity; not a state-corruption or loss risk.

## A5. Roman flavour text is still shown verbatim to non-Roman civilizations, including in the `name` field

- **Claim at issue (notes):** han_china_100ad_WEIRD F5; han_china_100ad_WIN F3 (*"the names and
  prose are unmodified Rome, down to the plain `name` field"*); norse_900ad_WIN F10.
- **Where:** `reports/han_china_100ad_WIN.md` §FINDINGS F3; `reports/norse_900ad_WIN.md` F10;
  `reports/han_china_100ad_WEIRD.md` F5.
- **Status: STILL PRESENT (partially fixed).** The single loudest case named in all three reports
  — `citizenship` — **is** fixed: under Han and Norse it now reads
  `"name": "Legal standing: a status the courts will hear"` with a note that begins *"In Rome this
  is citizenship by grant …  Every society has its own version"*. The pattern behind it was not
  swept.
- **Verified today, under `--civ han_china_100ad` and `--civ norse_900ad`:**
  - `corpus_written` → `"name": "Write the corpus: everything you know, in plain quantitative
    Greek and Latin."` (Han's scholarly language is Classical Chinese; Norse is 900 AD
    Scandinavia.) This is the *name*, not background prose, and it is the prerequisite of the
    crisis hedge both WIN reports had to reason about.
  - `patron_imperial` → note: *"Approach through the a rationibus or the Praetorian Prefect …
    a message to the Rhine takes weeks."*
  - `scientific_method` → *"displacing Aristotelian authority … Contradicting Aristotle and Galen
    in public …"*
  - `arithmetic_positional` → *"Sell it to bankers and the fiscus first"*, told to a Han state
    that had used decimal counting rods for centuries.
  - `school_founded` → `"Found the school (the Museum)"` (Alexandria's).
  - `{"cmd":"risk"}` under Norse suggests, by name, *"civ_road_paved — Roman paved road with
    surveying"* as a mitigation.
- **My judgement: real (content) defect, and the notes are right that it is not merely cosmetic**
  — `civ_cost_factor`, `handicap_remedies` and the hazard tables are all now civ-aware (see Part
  C), so the prose is the only layer still asserting one society's institutions for all five.
- **Severity: makes the simulation unrealistic / misleads a player in character.** Cosmetic
  mechanically; it directly contradicts information the same reply gives numerically.

## A6. `lnd_cursus_publicus` and `sea_pharos_lighthouse` are still granted free to every civilization

- **Claim at issue (notes):** han_china_100ad_BREAK F3 — *"Han China is credited with building
  Roman aqueducts, Roman sewers, and Roman partnership law"*; han_china_100ad_WIN F1 — *"a Han
  playthrough is credited with the Cloaca Maxima, the cursus publicus, and Roman cosmetics."*
- **Where:** `reports/han_china_100ad_BREAK.md` F3; `reports/han_china_100ad_WIN.md` F1.
- **Status: STILL PRESENT as a narrow residual; the bulk is FIXED.** `engine/society.py`'s
  `_is_foreign_institution` + `fog.py`'s `FOREIGN_MARKERS = ("_roman","_rome","annona","insula",
  "societas","collegium","argentarii","latifundi")` now keeps the Roman bundle out of other civs.
  Measured today over the actual grant sets:
  ```
  rome_100ad       137 granted, 13 Roman-branded
  han_china_100ad  135 granted,  2 Roman-branded: lnd_cursus_publicus, sea_pharos_lighthouse
  norse_900ad      127 granted,  2 Roman-branded: lnd_cursus_publicus, sea_pharos_lighthouse
  ```
  and `{"cmd":"why","id":"civ_aqueduct_roman"}` under Han now returns `"done": false`.
- **My judgement: real, small residual.** The *cursus publicus* is the Roman imperial dispatch
  relay and the Pharos is a specific Ptolemaic/Roman-Egyptian building; neither has a marker in
  the list. Two more entries would close it.
- **Severity: cosmetic/realism.**

## A7. `"did you mean: no idea"` — the suggestion is a substring match, so a one-character typo gets no help

- **Claim at issue (notes):** rome_100ad_BREAK F14 — *"`units_stadards` is a transposition of two
  letters away from the real, very common id `units_standards` … Instead the literal string
  `"no idea"` is printed as if it were the suggestion, for every bad id I tried."* Also surfaced
  incidentally in han_china_100ad_BREAK F1.
- **Where:** `reports/rome_100ad_BREAK.md` §FINDINGS F14.
- **Status: STILL PRESENT.**
- **Exact reproduction (verified today):**
  ```
  {"cmd":"why","id":"units_stadards"}
  -> {"ok": false, "error": "unknown node 'units_stadards'. did you mean: no idea"}
  ```
  `engine/protocol.py` (`op == "why"`): `near = [x for x in nodes if str(k).lower() in x.lower()]`
  — a pure substring containment test, so nothing near-but-not-containing ever matches. The same
  line exists in `engine/cli.py`'s `cmd_why`.
- **My judgement: real defect, and the tester's diagnosis was exactly right.** A `difflib.
  get_close_matches(k, nodes, n=8, cutoff=0.6)` fallback would fix it in one line.
- **Severity: cosmetic / mildly misleading.** No state effect; "no idea" reads as a placeholder in
  a tool that is otherwise unusually careful about its own error text.

## A8. `waiting_on` says `"your hours"` while the same object says the project is money-starved

- **Claim at issue (notes):** implied rather than named — rome_100ad_WIN F3 (*"the visible numbers
  … read as inconsistent with 'still needs more of this same resource'"*) and
  han_china_100ad_WIN F4.
- **Where:** revealed by, not stated in, `reports/rome_100ad_WIN.md` F3.
- **Status: STILL PRESENT.**
- **Verified today** (fresh Rome, `start identity_cover`, `step 1`):
  ```
  "waiting_on": "your hours",
  "underfunded_this_year": true,
  "why_underfunded": "this year's instalment is more than the purse will bear",
  founder_hours_available: 2400.0
  ```
- **My judgement: a real but arguable labelling defect.** `engine/protocol.py`'s ladder is
  `short_of_trade → "money" if ph_left <= 0 → "the calendar" if ph_left <= 0 → "your hours"`, so
  "money" is only ever reported once the hours are *fully* done. Strictly the project does still
  need hours; practically, the player has 1,900 idle hours and the binding constraint is cash, and
  the same object already knows that. A fourth branch (`"money" if underfunded_this_year`) would
  make the field agree with its neighbours.
- **Severity: misleads a player (minor).**

## A9. `start` is still not capital-gated, and `why`'s `start_blocked_reason` still never names money

- **Claim at issue (notes):** rome_100ad_BREAK F7 — *"`start` has no capital gate at all … `why`'s
  `can_start_now`/`start_blocked_reason` fields never mention money as a blocker"*;
  han_china_100ad_WIN F6 confirms it as a thing learned the hard way.
- **Where:** `reports/rome_100ad_BREAK.md` F7; `reports/han_china_100ad_WIN.md` F6.
- **Status: STILL PRESENT — but it now reads as a deliberate, disclosed design choice.**
- **Verified today:** on a fresh Rome (capital 400.0),
  `{"cmd":"start","id":"identity_cover"}` (quoted total 1,580.0) returns
  `{"ok": true, ..., "the_bill_you_have_taken_on": 1580.0, "note": "This is the price as of
  today, and it is now fixed for this project."}`. `state` carries `credit_limit` and
  `debt_interest_rate`; `available` carries a per-subject `you_could_pay_for` count; and running
  past the credit line now produces `CREDIT EXHAUSTED: N projects halted, unfinished`.
- **My judgement: design choice, and a much better-signposted one than the notes saw.** Deficit
  spending is the stated economic model (`04_ECONOMICS.md`, rome_100ad_WIN F2), and the
  consequences are now real and legible. The residual complaint is narrow and still valid:
  `start_blocked_reason` enumerates trades, staff, and prerequisites but never money, so the one
  blocker that *will* actually stop the work is the one `why` won't name.
- **Severity: confusing, not harmful.**

## A10. The founder is immortal by default in the mode a player actually uses

- **Claim at issue (notes):** narrative_and_pacing finding 1 — *"the actual playable `agent` JSON
  protocol defaults to `founder_ages: false` — an **immortal founder** — and `--mortal` is a flag
  nobody exercised in any playtest report I found … The interactive tool, as shipped, lets you
  skip the exact bottleneck the design doc and the book agree is the whole point."* Independently
  observed by rome_100ad_BREAK (honesty note: *"a founder who is provably immortal against two
  plagues and three and a half centuries of crisis"*), rome_100ad_WIN and han_china_100ad_WIN.
- **Where:** `book_v5_comparison/narrative_and_pacing.md` §Ranked findings #1.
- **Status: STILL PRESENT as a default; the *bug* half is FIXED.** `--mortal` now exists on
  `agent` (it did not; see `engine/cli.py`'s comment "*`run`/`compare`/`play` all take --mortal;
  `agent` silently did not, so the founder was immortal in every scripted or JSON-driven game*"),
  and mortality demonstrably works:
  ```
  printf '{"cmd":"step","years":300}\n' | python3 rome/sim/simulator.py agent --civ rome_100ad --mortal --seed 3
  -> founder_alive false, year 140, ended true,
     events: "the founder dies, aged about 63",
             "RUN ENDS: the founder died without training successors; the school dispersed..."
  ```
  Without `--mortal`: `founder_alive true` at year 400. `state` now discloses `"founder_ages":
  false` and `play` prints "You: alive (you do not age)".
- **My judgement: design choice, now honestly labelled.** The narrative researcher's point stands
  as a *design* criticism — the default configuration does not exercise the constraint the
  briefing calls central — but it is no longer a hidden or unavailable mechanic.
- **Severity: makes the simulation unrealistic in its default configuration.**

## A11. `cap_measure_temp_hi` does not require the electrical/thermocouple chain

- **Claim at issue (notes):** technology_and_prerequisites §9.3 — *"`cap_measure_temp_hi` (needed
  for `crucible_steel`, `cap_heat_1600`, and everything downstream) does **not** require the
  electrical/thermocouple chain at all — it only needs `cap_heat_1300` + `cap_measure_temp` …
  This *contradicts* the book's central 'Precision Bootstrapping Loop'."*
- **Where:** `book_v5_comparison/technology_and_prerequisites.md` §9.3 (rated MEDIUM by its author).
- **Status: STILL PRESENT.** Verified today: `cap_measure_temp_hi pre = ['cap_heat_1300',
  'cap_measure_temp']`.
- **My judgement: design choice, and probably the right one.** The researcher says so themself
  ("the tree is arguably more correct here") — Wedgwood clay-contraction pyrometry predates the
  thermocouple by about a century and needs no electricity. What is genuinely open is whether the
  thermocouple route (`opt_pyrometer_thermoelectric` / `in2_thermocouple`) should then buy
  *anything*, since nothing currently requires it.
- **Severity: realism / balance question, not a defect.**

## A12. `printing_press` still has almost no downstream reach in the DAG

- **Claim at issue (notes):** technology_and_prerequisites §9.4 — *"`printing_press` has only 21
  downstream dependent nodes in the whole 2,828-node tree (versus 1,626 for
  `precision_three_plate` and 1,219 for `arithmetic_positional`)"*, against the book's framing of
  the press as *the* technology multiplier.
- **Where:** `book_v5_comparison/technology_and_prerequisites.md` §9.4.
- **Status: half FIXED, half STILL PRESENT.** The *mechanic* half is fixed (see C-S): `_TECH_
  EFFECTS.json` is now applied by `Sim.apply_tech_effects()` from `_complete()`, and
  `printing_press` carries `{literacy_general +0.1, literacy_elite +0.2, w_information +0.15,
  w_novelty +0.1}`, which feed the hiring pool. The DAG half is unchanged — measured today:
  ```
  printing_press        direct 12  transitive   21
  precision_three_plate direct 12  transitive 1629
  arithmetic_positional direct 13  transitive 1222
  ```
- **My judgement: design choice.** A diffusion multiplier is the right shape for this and now
  exists; encoding printing as a hard prerequisite of 1,600 nodes would be wrong. Recorded because
  the researcher's underlying observation (the book's #1 priority technology is the tree's
  low-leverage one) is still true.
- **Severity: realism / design divergence.**

## A13. Photographic fixer chemistry has no separately-gated node

- **Claim at issue (notes):** technology_and_prerequisites §11 — the book writes fixing as *"the
  one wall Daniel cannot cross … the image arrives and then eats itself"*; the researcher flagged
  MEDIUM confidence that the tree has no equivalent.
- **Where:** `book_v5_comparison/technology_and_prerequisites.md` §11.
- **Status: STILL PRESENT (now confirmed, not just suspected).** Name-searched the full tree
  today: photography nodes exist (`in2_photographic_emulsion`, `if_silver_halide_sensitivity`,
  `in2_cooke_triplet_photography`, `air_aerial_photography`, …) but there is no node containing
  "fixer" or "silver_nitrate", and no node gating fixing chemistry separately from emulsion.
- **My judgement: content gap, not a defect.** The book's claim (fixing is a distinct, harder
  problem than exposure) is technically sound and the tree currently folds it into emulsion.
- **Severity: realism, minor.**

## A14. Slavery's chilling effect on labour-saving technology is a single scalar, and the model says so itself

- **Claim at issue (notes):** society_and_economy PART 3 §1 (ranked most important) — *"The
  simulator's civ file assigns a single scalar penalty (`w_labour_saving: -0.6`) … and
  `04_ECONOMICS.md` §6 admits outright: 'Slavery is modelled far too thinly … suppressed the
  business case for every labour-saving device in this document.' There is no mechanic in the sim
  for 'this specific buyer already owns the specific labour force this specific machine would
  replace, so the sale fails even though the machine works'."*
- **Where:** `book_v5_comparison/society_and_economy.md` PART 3 §1.
- **Status: STILL PRESENT** (`w_labour_saving` is still a scalar weight in the civ files).
- **My judgement: design choice, openly acknowledged by the model's own documentation.** The
  researcher is right that a demand-side "the buyer already owns the labour" mechanic would be
  sharper and more falsifiable; that is a feature request, not a bug report.
- **Severity: realism.**

---

# PART B — UNCLEAR / matters of judgement, not defects

## B1. Calendar floors under-predict actual completion time

rome_100ad_WIN F3 (*"`screw_lathe` stated 3 years, took 11; `citizenship` stated 3, took 9;
`gecl4_purification` stated 5, took 19"*), han_china_100ad_WIN F5 (`power_grid` 25 → 40 years,
but `railway` and `zinc_industry_scale` on floor), norse_900ad_WIN (`railway` 20 → 11 years,
`power_grid` 25 → 19 — i.e. *faster* than floor). **UNCLEAR / largely FIXED in cause.** The two
mechanisms that produced the old overruns are gone (the hour-refund/cycling bug, C-A; the
never-landing-last-payment bug, whose fix is documented in `core.py`: *"a playtester watched one
project sit at '71% done' for twenty-five years with cash in hand"*). The floor is also
explicitly *reduced* by reputation for diffusion-limited nodes (`floor = n["yrs"] / (1 +
reputation/90)` when `yrs >= 5`), which explains Norse finishing early. `identity_cover` (floor
0.5) completed in year 1 in a well-funded run today. What remains true is that `calendar_floor_
years` is a floor, not a prediction, and the notes are right that it reads like one.
**Severity: confusing.**

## B2. `resource_throttle` reads non-1.0 with `active: {}`

han_china_100ad_WIN F4 (*"`resource_throttle` stayed stuck at a stale-looking 0.368-0.246 for
years with `active: {}` (nothing running that the throttle could even be gating)"*).
**UNCLEAR — probably correct behaviour.** `resource_throttle()` is recomputed at the top of every
`step()` from `annual_material_demand()`, which is `O(active + done)`: finished works consume
materials every year, so a nonzero shortfall with nothing *active* is a real state, not a stale
one. What the tester saw as staleness may have been the (now-documented) one-step cache that
serves queries *between* steps. I could not reproduce a genuinely stale value cheaply.
**Severity: confusing at worst.**

## B3. `step years=100000` no longer clamps to the horizon; it errors

rome_100ad_BREAK F13 and han_china_100ad_BREAK F7 both marked the old clamping behaviour
WORKS-WELL. Today:
```
{"cmd":"step","years":100000}
-> {"ok": false, "error": "there are only 500 years left before the horizon at 600.
    Ask for 500 or fewer, or fewer still if you want to see what happens on the way."}
```
**Behaviour change, not a regression** — `state` now also carries `horizon_year` and `years_left`
on every reply, which closes norse_900ad_WEIRD F3's separate complaint that the 1400 AD horizon
was "announced nowhere until you overshoot it". Listed so nobody re-files it as a break.

## B4. The transistor goal is several institutional scales beyond the book's premise

technology_and_prerequisites §8/§12 (*"the words 'transistor', 'semiconductor', and 'germanium'
do not appear anywhere in `book_v5`"*; the tree's own `55_semiconductors.md` calls for *"150-300
skilled specialists … comparable in scale to a legion's engineering corps"*).
**Not a defect — a scope question**, and the researcher says so explicitly. Recorded because it is
the single largest divergence documented between the two artefacts, and because it bears on
whether the reported 458 AD / 542 AD / 1226 AD completion years mean what a reader thinks.

---

# PART C — FIXED (verified against current code / by running the game)

Each of these was a genuine finding when written. All were re-tested today.

- **C-A. Negative and zero `buy` quantities mutating state while reporting failure.**
  rome_100ad_BREAK F1 (`buy forest n:-1000000` → +250,000,000 denarii and −1,000,000 ha), F2
  (`buy manumit n:-1` → 1 slave, −1 freedmen), F3, F8 (`n:0` "unaffordable"). **FIXED** — all four
  now return `{"ok": false, "error": "n must be greater than zero, got -5. Nothing was changed."}`
  with `capital`/`forest_ha`/`slaves`/`freedmen` verified unchanged before and after.

- **C-B. A JSON object or array as `"id"` crashing the whole process.** rome_100ad_BREAK F4
  (`TypeError: unhashable type: 'dict'`, exit 1, whole game gone). **FIXED** — `start`, `why`,
  `stop`, `bounty`, `path` all return `"id must be a name in quotes, not dict."` and the process
  answers the next command.

- **C-C. A valid-but-non-object top-level JSON value killing the process one line later.**
  norse_900ad_BREAK F2 (`AttributeError: 'NoneType' object has no attribute 'get'` on `null`,
  `[1,2,3]`, `42`, `"hello"`). **FIXED** — all four, plus genuinely invalid JSON, return a clean
  error and the session survives.

- **C-D. `why` on a node missing `sus`/`gov` killing the process.** norse_900ad_BREAK F1 and
  norse_900ad_WIN F1 — `KeyError: 'sus'` on `sea_clinker_hull`, `sea_keel_deep`,
  `met_bloomery_bog_iron`, `mat_obsidian_blade`, `exp_import_draught_animals`, `fud_chinampa`,
  `civ_monumental_stone`; three of them Norse's own starting techs. **FIXED at the data layer** —
  all 2,831 nodes now carry both keys (checked directly), and `why` on all seven returns a normal
  explanation.

- **C-E. `{"cmd":"available"}` throwing `TypeError: Sim.start_reason() got an unexpected keyword
  argument '_memo'` under `--fog`.** society_and_economy PART 2, "Observed bug". **FIXED** —
  `available` under `--fog` returns a 75-item summary by subject.

- **C-F. A node's real cost overshooting its quoted `why` price by 50%.** rome_100ad_BREAK F5
  (`hot_air_balloon`: quoted 4,361.5, charged 6,542.2). **FIXED** — the quote is now fixed at
  `start` (`"the_bill_you_have_taken_on"`, with a note saying so) and `spent + still_to_pay`
  equals it exactly through completion (verified on `identity_cover`: 1,223.6 + 356.4 = 1,580.0).

- **C-G. `founder_hours_left` going non-monotonic and negative; `years_in_progress` resetting to
  0.** rome_100ad_BREAK F5, rome_100ad_WIN F3, norse_900ad_WIN (recurrence on
  `zinc_industry_scale`). **FIXED** — `core.py` now clamps `ph_left` at zero and caps every refund
  at `spent_hours - refunded`, with the bug written up in the comment ("*a progress bar reading
  '-67% of your hours spent', with founder_hours_left larger than founder_hours_total*"). No
  negative or increasing-past-total value observed in any run today. (The *reporting* residual is
  A1 above.)

- **C-H. Capital falling with nothing active, zero upkeep and no field explaining it.**
  rome_100ad_BREAK F6 (−216 on the first step of the first turn). **FIXED** — `state` now itemizes
  `revenue / upkeep / living_cost / wage_bill / mine_operating_cost / project_spend_this_year /
  net_after_project_spend / net_per_year`, and six consecutive 1-year steps today reconciled to
  the decimal (`net_per_year 3.5` → capital +3.5 each year), with the one exception explained by a
  logged event (`"fire in the insula district"`, capital × 0.82).

- **C-I. `net_per_year` failing to predict the very next year's capital change.**
  han_china_100ad_BREAK F4 (off by 725.5 den on a one-year step). **FIXED** — verified above; and
  the separate han_china_100ad_WIN F4 complaint (*"`net_per_year` reports a nominal/unthrottled
  income rate, not what is actually banked"* — capital 0.0 for eight years while it showed
  +165,698) is answered by the new `project_spend_this_year` / `net_after_project_spend` fields,
  whose code comment quotes that exact playtest.

- **C-J. `step` silently no-opping after the run has ended.** rome_100ad_BREAK F9. **FIXED** (and
  already re-confirmed by han_china_100ad_BREAK F8) — verified today on Rome at the year-600
  horizon: `step`, `start` and `buy` all return `{"ok": false, "error": "the run has ended (...)"}`.

- **C-K. Insolvency permanently locking a technical prerequisite of the goal out of reach.**
  norse_900ad_WEIRD F3 (*"`identity_cover` remained permanently un-buildable"* for 470 years).
  **FIXED** — reproducing the same sequence today, `identity_cover` completes and stays
  `"done": true`; `fog.py`'s `never_abandon()` now protects anything in the goal's closure plus
  all knowledge categories, with the comment *"you cannot have the game quietly delete a step you
  need and then refuse to fund rebuilding it."* (The softer stall that remains is A2.)

- **C-L. No insolvency consequence at all — 4.1M denarii of debt for 80 years with nothing
  happening.** han_china_100ad_WEIRD F6. **FIXED** — there is now a credit limit
  (`credit_limit`, ~1,367 den on the default Rome kit), interest on arrears (`debt_interest_rate`
  ~10.8%, logged as an event), `CREDIT EXHAUSTED: N projects halted`, debt bondage for civs that
  have it, and `INSOLVENCY SETTLED` write-offs at a reputation cost.

- **C-M. `mothball_mines()` clamping capital to `-abs(revenue())`, forgiving arbitrary debt.**
  norse_900ad_BREAK F4 (proved to the cent: −1,022.40 on two consecutive steps). **FIXED** — the
  clamp is deleted, and the comment records the finding: *"a playtester proved it to the cent …
  Debt is now whatever the arithmetic says it is."*

- **C-N. Topping up a mine before it matures resetting the whole pool's `ready_year`.**
  norse_900ad_BREAK F3 (60 consecutive funded years, `mine_capacity` never left `{}`) and
  norse_900ad_WIN F4 (28 years, 700 t/yr paid for, nothing delivered). **FIXED** — `open_mine()`
  now appends per-tranche `[mat, t_per_yr, year + MINE_LEAD_YEARS]` rows and `commission_mines()`
  matures them independently; the auto-response also subtracts `mine_pending` from what it wants,
  so it stops re-ordering. Both playtests are quoted in the code comment.

- **C-O. `buy mine` silently taking every denarius and delivering a fifth of the order.** (Same
  family; `norse_900ad_BREAK` context.) **FIXED** — a manual `buy` now refuses and quotes the
  price unless `partial` is asked for; there is also a `{"cmd":"quote",...}` command.

- **C-P. Han China's civ file naming a starting tech that does not exist
  (`fud_heavy_plough`).** han_china_100ad_BREAK F1. **FIXED** — the file now reads
  `fud_heavy_mouldboard_plough_coulter`, and all 12 of Han's `starting_techs` resolve against the
  tree (checked directly).

- **C-Q. `done_earned` counting civ-given starting techs as player-earned, exposing them to
  sacking.** han_china_100ad_BREAK F2 + addendum; han_china_100ad_WIN F2 (a Yellow Turban sacking
  stripped `bellows_water_blown`, one of Han's declared starting techs). **FIXED** — at turn zero
  today: Rome `done_granted 137 / done_earned 0`, Han `135 / 0`, Norse `127 / 0`. Starting techs
  are in `granted`, and losses draw from `done - granted`.

- **C-R. The ambient "society already has this" bundle being a single Rome-shaped set applied to
  every civ.** han_china_100ad_BREAK F3, han_china_100ad_WIN F1. **FIXED except for two nodes**
  — see A6.

- **C-S. `_TECH_EFFECTS.json` written, committed and never referenced by any code.**
  technology_and_prerequisites §9.4. **FIXED** — `Sim.apply_tech_effects()` in `society.py` is
  called from `_complete()` and applies literacy/values deltas, logging *"X changes the society:
  …"*. The old comment that described the dead mechanic has been rewritten specifically because
  *"an agent reading the file reported the dead mechanic as a live finding."*

- **C-T. `bounty` pricing at `2.5 × raw base cost`, ignoring the civ multiplier `why` had just
  quoted.** han_china_100ad_BREAK F5 (588 quoted vs 188 × 2.5 = 470 expected). **FIXED** —
  verified today: Han `fud_hay_making_storage` `why total 141.0` → `bounty price 352.5`
  (= 141.0 × 2.5); Norse `why total 329.0` → bounty "needs about 822" (= 329.0 × 2.5).

- **C-U. Han China's declared `cost_multipliers` having no effect on any cost.**
  han_china_100ad_WEIRD F4 (byte-identical `why` output between Han and Rome on eight node/civ
  pairs). **FIXED** — measured today on the same node ids:
  ```
                              rome    han     norse
  mt2_white_cast_iron   base 688.4 → 688.4 / 387.2 / 867.4
  prn_hand_papermaking  base 127.0 → 127.0 /  47.6 / 177.8
  met_investment_casting base 329.8 → 329.8 / 160.8 / 461.7
  blast_furnace   base 315,450 → 268,132 / 166,561 / 436,635
  ```
  `why`'s `cost` block now exposes `base_total`, `civ_domain_factor`, `material_distance_factor`,
  `opposition_factor`, `price_index`, `purchasing_power_of_the_coin`, `total`. `civ_cost_factor()`
  was also rebalanced so a Norse longship is no longer *more* expensive than a Roman one.

- **C-V. `handicap_remedies` existing only as data — the promised remedy never lifting the
  handicap.** norse_900ad_WIN F3 (*"zero matches in the entire file … the block sits in the civ
  JSON as a promise the code never looks at"*), self-described as the report's most consequential
  finding. **FIXED** — `civ_cost_factor()` now reads `handicap_remedies` and substitutes the
  `residual` once the named node is in `self.done`. Measured directly today on Norse:
  ```
  before collegium_licensed:  blast_furnace 0.9845   fin_societas 1.10
  after  collegium_licensed:  blast_furnace 0.8896   fin_societas 1.00
  ```

- **C-W. The buy-slaves-and-manumit reputation/labour pump.** rome_100ad_WEIRD F1 (reputation
  5 → 1,205, artisans 3 → 3,303, all in year 100, at a flat 300 den/head). **FIXED** — today, on
  `--kit absurd`, `buy slaves n:1000` is refused (*"2,801 each after the market moves against a
  purchase this size"*), and one `step` leaves `reputation 4.9`, `eminence 0.56`, `artisans 0.0`.

- **C-X. The volume surcharge being per-call, so splitting the order defeated it.**
  han_china_100ad_WEIRD F1 (13.0x cheaper in n=10 chunks), norse_900ad_BREAK F6 (~19% cheaper in
  n=3 chunks), norse_900ad_WEIRD F1 (16-25% cheaper at n=1). **FIXED** — buying 60 people on
  Norse `--kit absurd --seed 1` in chunks of 1, 2, 5, 10, 20 and 60 all leave capital at exactly
  906,117.8. The batch is now integrated across its own marginal-cost curve.

- **C-Y. `manumit` granting ~82% of a trained artisan instantly, bypassing the three-year training
  lag.** han_china_100ad_WEIRD F2. **FIXED** — verified today on Han: buy 50 → `artisans 0.0`,
  `training_pending [{artisan_capacity 27.5, ready_year 103.0}]`; manumit 50 → `artisans` still
  `0.0`, the pending row *upgraded* to `artisan_capacity 50.0` with `ready_year` unchanged at
  103.0. (This is what han_china_100ad_BREAK F6 marked WORKS-WELL; it now holds for the
  buy-then-immediately-free case too.)

- **C-Z. `knowledge_risk` reporting a live sacking risk for a civ whose only hazard cannot sack a
  site.** norse_900ad_BREAK F5. **FIXED** — Norse `{"cmd":"risk"}` today returns
  `expected_technologies_lost_per_sacking: 0.0`, `better_hedge_available: null`, and the explicit
  note *"no remaining hazard for this civilization sacks a site, so nothing here is currently at
  risk of being forgotten."*

- **C-AA. The "too eminent" death being an undocumented, unsignposted one-shot fail state.**
  rome_100ad_WEIRD F3 (*"`grep -rn "eminen" rome/knowledge/ rome/*.md` returns nothing"*).
  **FIXED** — every `state` now carries a `prominence` block: `{"now": 0.0, "dangerous_above":
  26.0, "settles_at_if_nothing_changes": 0.1, "chance_of_ruin_this_year": 0.0,
  "what_would_change_it": [...], "note": "This is prominence, not scandal. It cannot be bribed
  away…"}`, and `play`'s rendering prints the same line.

- **C-AB. The horizon being invisible until you overshoot it.** norse_900ad_WEIRD F3 (the "1400
  AD" timeout, grepped for and not found anywhere a player could read). **FIXED** — `state` now
  leads with `"horizon_year"` and `"years_left"` on every reply, and `play` prints
  "(500 years to the horizon at 600)". The code comment names the finding: *"A clock you cannot
  see is not a constraint, it is an ambush."*

- **C-AC. The Third Century Crisis knowledge-loss mechanic having no machine-readable signal.**
  rome_100ad_WIN F4 (*"Nothing in `available`, `why`, or `path` carries any field like 'at-risk
  during crisis window'"*). **FIXED** — `state` carries `at_risk` (`technologies_you_could_lose`,
  `hedged_by`, `happening_now`, `hazards_still_ahead`) and there is a dedicated `{"cmd":"risk"}`
  giving each hazard by name, years, `sacks_a_site`, `sack_chance_per_year`, the mitigation, and
  a list of nodes you could begin now toward it.

- **C-AD. The scholar/artisan headcount wall being undiscoverable from the protocol.**
  rome_100ad_WIN F5 (*"`start_blocked_reason` told me *what* was blocking … but never *how* to get
  more scholars"*). **FIXED** (already noted as fixed by norse_900ad_WIN F9) — today, `why
  hot_air_balloon` on a fresh Rome returns *"needs 3 trained craftsmen on your own staff, you have
  0.0. To get more artisans: {"cmd":"hire","trade":"smith","n":3} or any trade in
  {"cmd":"labour"}; or {"cmd":"commission",...}"*.

- **C-AE. `buy` accepting only forest/mine/slaves/manumit, with no way to acquire staff
  legitimately.** rome_100ad_WIN F5. **FIXED** — the protocol now has `hire`, `fire`, `train`,
  `commission`, `work`, `labour`, `close`, `quote`, `mothball`, `restore`, `bribe`, `policy`,
  `money`, `risk`, `save`, `load`.

- **C-AF. `mine_operating_cost` jumping ~20x in one step, from capacity the player never bought.**
  rome_100ad_WIN F6. **FIXED** — `{"cmd":"policy"}` shows `auto_mine: false` and `auto_forest:
  false` by default in manual/agent play (so nothing buys capacity on your behalf), `{"cmd":
  "money"}` itemizes `mines_standing`, `{"cmd":"quote"}` prices a mine before you commit, and
  `{"cmd":"close","material":...}` lets you shut workings down.

- **C-AG. `power_grid` gated on `railway`, dragging a national railway onto the transistor's
  critical path.** technology_and_prerequisites §9.2 (rated HIGH). **FIXED** — today
  `power_grid pre = [en_circuit_breaker, en_frequency_standardisation, en_insulator, en_substation,
  en_switchgear, en_transformer, en_transmission_line, mat_bulk_steel, motor_transformer_ac,
  steam_high_pressure]`. No `railway` edge.

- **C-AH. The garbled `mat_bulk_steel` note.** han_china_100ad_WIN, F-note (*"At 0.75 tonnes of
  charcoal per hectare of coppice per year that is roughly n/a, it burns coal hectares of forest
  under permanent management"*). **FIXED** — the note is now clean prose about the phosphorus
  problem and the basic lining. Searched the whole tree: zero notes contain a literal "n/a" or the
  "hectares of forest under permanent management" template.

- **C-AI. `finery_puddling` stating a hard 2,000-hectare forest requirement the engine never
  enforced.** han_china_100ad_WIN, F-note. **FIXED** — the false claim is gone from the note (the
  template that generated it is gone tree-wide, per C-AH).

- **C-AJ. `"fire in the insula district"` fired as an event string while playing Han China.**
  han_china_100ad_WIN F3. **FIXED** — `society.py` now emits
  `"fire in the %s" % civ.get("fire_quarter", "crowded quarter")` and the comment records the
  finding (*"a tester playing Han China counted nine fires in the insula district of Luoyang"*).

- **C-AK. `--kit destitute` being trivially non-punishing — ~130 free ambient techs handing a
  0-denarii start a comfortable positive cash flow within five years.** norse_900ad_WEIRD F7
  (*"y=915: capital 8,737.00"*). **FIXED** — the same run today: y900 cap 0.0, y905 54.4, y910
  116.8, y915 174.7, y920 228.3, net hovering at +10 to +13/yr. Granted non-practisable nodes no
  longer pay revenue.

- **C-AL. `done_count` giving no way to tell "what Rome already had" from "what I built".**
  rome_100ad_WEIRD F7. **FIXED** — `done_granted` / `done_earned` are in every `state`, correct
  from turn zero (137/0 on Rome), and `play` prints "0 built by you, 137 granted for free".

- **C-AM. `available` and `start` disagreeing.** rome_100ad_BREAK F11 marked this WORKS-WELL;
  re-tested today for regression by fetching `{"cmd":"available","all":true}` (75 ids) and issuing
  `start` on every one: **0 refusals**. Still holds.

- **C-AN. Whether `start`/`stop` refund spent money.** rome_100ad_WEIRD F8 and rome_100ad_BREAK
  F12 appear to contradict each other; they do not. Nothing is charged at `start` (F8's
  observation); money already spent across a step is not refunded by `stop` (F12's). Both are
  still true and both are correct. **Not a defect — a misreading risk, recorded so it is not
  re-filed.**

---

# Notes on the book_v5 comparison files specifically

Most of what these three files record is *the book being wrong or divergent*, not the game. Those
are logged here for completeness but are not simulator defects:

- **The book asserts metallic zinc is available because "zinc is in Roman brass"** — factually
  wrong (cementation brass never isolates the metal; downward distillation is a medieval Indian
  achievement). The tree's `zinc_metal` node is right and the book is not
  (`technology_and_prerequisites.md` §9.1, §12). No game change needed.
- **"China had gunpowder by 100 AD"** — wrong, and the book's own research doc flags it as a
  deliberate character error (§6).
- **The book's own planning documents contradict each other** about what the protagonist knows
  (glass-clarity manganese sourcing; the dynamo insight) — `daniel_pre_rome.md` vs
  `V2_TECH_DEEP_DIVE.md` (§6A). Not a game finding.
- **The book's `TECH_GAP_AUDIT.md` lists a dozen technologies planned as "required" but absent
  from the written chapters** (generator, arc lighting, reading glasses, typewriter, photography,
  …) — `narrative_and_pacing.md` finding 5. Not a game finding.
- **The tree contains real engineering subtleties the book misses** (dynamo self-excitation from
  residual magnetism; `nitre_beds`' import route via `exp_trade_route_extend`) —
  `technology_and_prerequisites.md` §9.5, §11. Points in the tree's favour.
- **The simulator has no representational language for named individual human cost, consent, or
  retrospective moral complicity** — `society_and_economy.md` PART 3 §4, §5;
  `narrative_and_pacing.md` finding 6. Both researchers say plainly this is a difference in kind
  between a novel and a resource model, not a missing feature. I agree.
