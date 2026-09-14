# Sweep of naive3 + naive4 playtest notes — every bug, defect, inconsistency and
# false statement by the game, de-duplicated and re-checked against the current build

Sources swept, in full:

- `rome/playtest/naive4/A/PLAY_A.md`   (England 1300, fog, "play it properly", 809 lines)
- `rome/playtest/naive4/B/BREAK_B.md`  (England 1300, fog, "break it", 611 lines)
- `rome/playtest/naive4/C/WEIRD_C.md`  (England 1300, fog, "play badly on purpose", 483 lines)
- `rome/playtest/naive3/mexica_1500_PLAY.md`   (847 lines)
- `rome/playtest/naive3/mexica_1500_BREAK.md`  (229 lines)
- `rome/playtest/naive3/mexica_1500_WEIRD.md`  (117 lines)

Every finding below was re-run against the build as of this sweep, using
`python3 rome/sim/simulator.py play --civ <civ> --fog` with commands on stdin, in
throwaway directories outside the repository. No repository file was modified.
Where the transcript alone was not decisive I read `rome/sim/engine/` to confirm
the mechanism.

**Headline: 26 findings still reproduce. 24 have been fixed. 1 is unclear.**

The three worst still-present findings are S1 (catastrophes *pay* an indebted
player), S2 (you can commit 30x your stated credit limit in one turn) and S3 (a
missing session file silently starts a different game and then overwrites the
named save).

---

# PART 1 — STILL PRESENT

## S1. Every multiplicative capital loss becomes a *gain* when you are in arrears — sackings, fires, banditry and plague all pay a player in debt

**Severity: corrupts state / exploitable / silently rewards the worst play.**

**Where reported:** `naive3/mexica_1500_PLAY.md`, "Turn 21" and summary item 4
("Unexplained, possibly a feature"). The tester saw it three times and could not
explain it; they guessed "getting sacked forgives debt in this engine". They were
right about the effect and wrong about the cause — it is a sign error, not a rule.

**Reported repro (quoted from the notes):**

```
SURPRISE #2, the bigger one: capital JUMPED from -4,154 den to -1,727 den in a
single step where `money` shows net/yr was only +305.8 and project spend was
only 90 den ... That is an unexplained ~2,211 den windfall landing in the exact
same step as "a site is sacked."
```
and, one turn later:
```
Capital AGAIN jumped far beyond what net income explains: -1,727 -> -324.3 den
in one step (net income was only +252.4, no project spend) ... both times
landing on "a site is sacked" events.
```

**Re-verified now, two independent ways.**

Mexica, forced into arrears before the invasion window:

```
$ printf 'step 18\nhire smith 6\nhire mason 6\nmoney\nstep 1\nmoney\nstep 1\nmoney\nquit\n' \
  | python3 rome/sim/simulator.py play --civ mexica_1500 --fog

EVENT 1519: INSOLVENCY SETTLED: most of the debt is written off and you still owe about 251 denarii...
EVENT 1519: Spanish invasion: a site is sacked
Capital: -100.5 den
```
The settlement left the player at −251. The sack then *halved and a bit* the
debt, to −100.5. Being sacked was worth +150 denarii.

England, in arrears, hit by an ordinary ambient fire:

```
$ printf 'hire smith 3\nstep 1\nmoney\nstep 1\nmoney\n...' \
  | python3 rome/sim/simulator.py play --civ england_1300 --fog

Capital: -629.2 den            (1303)
EVENT 1304: fire in the thatched lanes behind the market
Capital: -569.4 den            (1304)
```
The fire paid 59.8 denarii.

**Mechanism (current code).** `rome/sim/engine/society.py`:

- line ~433, sacking: `self.capital *= 0.40`
- line ~549, fire: `self.capital *= 0.82`
- line ~556, banditry: `self.capital *= 0.9`
- line ~415, epidemics/plague: `cash = self.capital * loss * 0.6` then
  `self.capital -= cash`

All four are written as "take a fraction of your money". All four are
sign-blind. With `capital < 0` each one *reduces the debt* by that fraction.
The plague path additionally hides it: the log prints
`"{:,.0f}".format(max(0.0, cash))`, so a plague that just paid you 60% of your
arrears reports `and 0 denarii gone with the trade that stopped` — which is what
produced this line in a fresh England run:

```
EVENT 1349: Black Death: staff -45%, and 0 denarii gone with the trade that stopped
```
while capital was −29.

**My judgement: real defect, not a design choice and not a tester misreading.**
The comment block above the plague path was written *specifically* to make the
money loss visible and honest ("A plague empties the market as well as the
workshop; that is real, and it has to be said") — the intent is unambiguous.
Whichever way one argues about conquest cancelling obligations, a *fire in a
quarter you own nothing in* cannot plausibly pay down your loans. The practical
effect is that the deepest hole in the game is also the safest place to be
standing when a catastrophe lands.

---

## S2. `start` accepts unlimited projects and commits many times the credit limit the game displayed a second earlier

**Severity: loses a game.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 21.

**Reported repro:**
```
(fresh 1300 game, 400 den, "Credit limit: 1,503")
> start <each of the 102 available ids>
> step 1
102 projects accepted with no cap and no warning; `Still owed on work in hand: 44,063`
against 400 den.
```

**Re-verified now** — scraped the 104 startable ids from `available all` and
started every one of them:

```
Money: 400 den    net +2.8 den/yr
Credit limit: 1,503     interest on arrears: 12%     paid so far: 0
Still owed on work in hand: 43,914          <- against 400 den and a 1,503 limit
> step 1
Money: -3,672 den    net -3,416 den/yr (after 4,439 den into projects this year)
```

**Judgement: real defect.** `help economy` states the contract in so many words —
"You may spend past what you have, as far as somebody will lend you and no
further." One step past a decision made against a displayed limit of 1,503 the
player is at −3,672, i.e. 2.4x that limit, because `credit_limit()` is
recomputed upward afterwards from the reputation the completions earned. The
number the player made the decision against did not exist when the money was
committed. There is no confirmation, no cap, and no warning at `start` time.

Related and genuinely intended (so *not* a bug): `naive3/WEIRD` Action 1 saw
`start identity_cover` accepted at 1,264 den against 400 capital and called it
surprising. Committing to a project you cannot yet afford is realistic project
accounting and the engine draws the cost down over time. The defect is only the
absence of any aggregate limit.

---

## S3. `play --session <file>` on a file that does not exist silently starts a brand-new default game, and then writes it over that filename

**Severity: destroys a save / loses a game.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 1 (Repro B) and
`naive4/C/WEIRD_C.md` BUG 1. B re-verified it still reproduced at 06:38 on the
day of testing.

**Reported repro:**
```
printf 'state\n' | python3 rome/sim/simulator.py play --session /tmp/does_not_exist_xyz.json
Reply begins:
   You arrive in 100 AD with 400 denarii ...
[100 AD | 400 den | ...]
```
C's version is worse: the new Rome game was written **over the England save**
(8571 bytes -> 8783 bytes). "If I had been forty years in, my whole game would
have been gone with no warning."

**Re-verified now:**
```
$ cd <empty dir>
$ printf 'state\nquit\n' | python3 rome/sim/simulator.py play --session nope_does_not_exist.json
   You arrive in 100 AD with 400 denarii and nothing else...
[100 AD | 400 den | you:2400 hr | sch 0 art 0 | rep 5] >
YEAR 100   (500 years to the horizon at 600)
$ ls
nope_does_not_exist.json         <- a Rome game now lives at that name
```
No warning of any kind.

**Judgement: real defect.** Every other file path in the program is careful
(absolute paths refused, `../` escapes refused, malformed saves refused with a
precise message naming the required keys). This one case silently substitutes a
different civilisation, a different century and a different fog setting, and then
persists it. The correct behaviour is obvious and the loader already knows how to
say it: refuse, and name the file.

Note: two neighbouring complaints from the same finding are now **fixed** — see
F1 and F2 in Part 2.

---

## S4. `risk` states two contradictory things about knowledge loss in consecutive lines, and `state` repeats the wrong one every turn

**Severity: misleads a player.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 7.

**Reported repro:**
```
> risk
KNOWLEDGE AT RISK
technologies at risk: 4     chance lost if a site is sacked: 80%
hedge: none yet
no remaining hazard for this civilization sacks a site, so nothing here is
currently at risk of being forgotten
```

**Re-verified now, England 1300, turn one:**
```
> risk
KNOWLEDGE AT RISK
technologies at risk: 3     chance lost if a site is sacked: 80%     fraction lost when it happens: 40%
hedge: none yet
no remaining hazard for this civilization sacks a site, so nothing here is
currently at risk of being forgotten
```
and `state` reinforces the false half every single turn:
```
AHEAD: 3 technologies at risk if a hazard lands, hedged by nothing yet
```

**Judgement: real defect (a false statement by the game).** England has no
`sack_chance` hazard at all — the disclaimer is the true line. The headline
counter, the 80%, the 40% and the `state` "AHEAD:" line are all computed
unconditionally and are simply not applicable to this civilisation. A player is
told to spend money hedging a risk that does not exist here. The `state` line is
the more damaging of the two because it is printed every turn and the disclaimer
is not.

---

## S5. The Great Famine is sold as a dated certainty twice and is actually a per-year dice roll that never fires in the default idle game

**Severity: misleads a player (it is one of only two things the scenario tells you to plan around).**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 13 and `naive4/C/WEIRD_C.md`
Phase 1 item 2 and Phase 8. B ran six identical fresh games; C ran three.

**Reported repro:**
```
for i in 1..6:  printf '4\ny\npoor_scholar\nn\nstep 60\nstate\n' | python3 rome/sim/simulator.py
Every one produced: EVENT 1348: Black Death ... and **zero** Great Famine events.
```

**Re-verified now.** A pure-idle 60-year run produces no famine:
```
$ printf 'step 60\nstate\nquit\n' | python3 rome/sim/simulator.py play --civ england_1300 --fog
  COMPLETED 1300: Sails on ships
  EVENT 1304: fire in the thatched lanes behind the market
  ... EVENT 1337: Hundred Years War ...
  EVENT 1348: Black Death: staff -45%, and 90 denarii gone with the trade that stopped
  EVENT 1349: Black Death: staff -45%, and 64 denarii gone with the trade that stopped
(no Great Famine anywhere)
```
Whereas starting a single project first perturbs the stream and it does fire:
```
$ printf 'start cap_measure_time_s\nstep 500\nquit\n' | ...
  EVENT 1316: Great Famine: staff -12%, and 20 denarii gone with the trade that stopped
```

**Mechanism:** `rome/sim/engine/society.py` ~line 405 —
`if "staff_loss" in h and r.random() < 0.32:` inside a per-year loop. The Great
Famine window is `[1315, 1317]`, three years, so P(fires at all) ≈ 0.69, and on
the default (deterministic) stream of a do-nothing game it lands on the 31%.

**Judgement: real defect in the *text*, arguably fine in the mechanic.** The
scenario briefing says "Fifteen years to the Great Famine" and `risk` prints
`[1315-1317] Great Famine / staff loss after what you have built: 12%` with no
probability anywhere. Both read as certainty. Either the window should be
guaranteed to fire at least once, or `risk` should state the annual chance. B's
secondary observation is also correct and still true: **which of the two headline
catastrophes you get depends on incidental earlier commands**, because the hazard
roll shares one RNG stream with everything else.

---

## S6. "COMPLETED <name>" is printed for technologies the society was granted, which the player never started

**Severity: misleads a player (it is the game's only score line, and it is wrong from turn one).**

**Where reported:** `naive4/A/PLAY_A.md` ("SURPRISE: 'COMPLETED 1300: Sails on
ships' — something I never started completed itself... Nothing explained it. I
still don't know what that was") and `naive4/C/WEIRD_C.md` Phase 1 item 1 and
Phase 8 ("it is labelled with the same word the game uses for *my* finished
projects, which is the confusing part").

**Reported repro:** fresh game, `RUNNING: nothing`, first `step`, and the log
announces a completion.

**Re-verified now** — it is the first line of the first step of every England
game:
```
$ printf 'step 1\nquit\n' | python3 rome/sim/simulator.py play --civ england_1300 --fog
  COMPLETED 1300: Sails on ships
...
  technologies: 0 built by you, 135 granted for free (135 total)
```

**Mechanism:** `rome/sim/engine/protocol.py` ~line 2338 builds the `completed`
list as a raw set difference `sorted(s.done - before_done)`. `s.done` also
receives the ambient grants added each step by `grant_ambient()`
(`rome/sim/engine/core.py` ~line 495-512), which are separately recorded in
`s.granted`. The renderer at line 983 prints all of them as `COMPLETED`.

**Judgement: real defect.** The engine already knows the difference — the very
next line of `state` correctly says "0 built by you, 135 granted for free". The
step reply just does not consult `s.granted` when labelling. C is also right
that this is what makes the world look like it is secretly playing for you.

**Related, same root cause and also still present:** `naive4/C/WEIRD_C.md` BUG 4
— `available` grows from ~75 to 103 startable items over 300 idle years and whole
new subjects appear, while `help` says in as many words "**Nothing happens unless
you make it.**" Confirmed: the granted count moves 134 -> 135 during a pure-idle
run, and the newly granted nodes unlock further items. Either the help line needs
a caveat or ambient grants need to be announced as what they are.

---

## S7. The `REVENUE` figure in `why` is a base number that is never what you are paid, with no caveat

**Severity: misleads a player (it is the number every investment decision is made on).**

**Where reported:** `naive4/A/PLAY_A.md` ("REVENUE IS NOT WHAT `why` QUOTES.
Quoted vs actual, all scaled by exactly 0.711") and `naive4/C/WEIRD_C.md` BUG 8
("`why` says `REVENUE: 200 den/yr`, the `money` ledger says `med_trepanation
72.6`").

**Re-verified now, turn one, nothing done:**
```
> why med_trepanation
UPKEEP: 0 den/yr     REVENUE: 200 den/yr
STATUS: DONE

> money
Capital: 400 den     Revenue: 232.8 den/yr
  from:
    med_cataract_couching        166.7
    med_trepanation              66.7
```
200 quoted, 66.7 paid. A 3x gap on the very first screen a player reads.

**Mechanism:** `rome/sim/engine/economy.py` `revenue()` applies, in order: an
age-based ramp, a `practice_attention()` factor for practices (which is why A saw
income *rise* year on year and why spending your hours on `work` collapses it), an
`economy_index()` multiplier, a market-saturation curve, and `output_factor`. The
`why` renderer (`protocol.py` ~1114) prints `n["rev"]` raw.

**Judgement: real defect, in the presentation rather than the model.** The model
is good and A eventually worked most of it out. But `why` is under fog the *only*
source of the number, it is labelled flatly `REVENUE: 200 den/yr`, and it is
wrong in both directions at different times. Even "about 0.3x of this at present"
would fix it.

---

## S8. `Net/yr` omits interest on arrears, so an indebted player watches a positive net while capital falls every year

**Severity: misleads a player.**

**Where reported:** `naive4/C/WEIRD_C.md` BUG 9 saw the symptom from the other
side ("`state` insisted `net -43 den/yr` ... while my capital rose by about 85 den
a year"). The interest half is the part that survives.

**Re-verified now:**
```
Capital: -570.2 den   ...   Net/yr: 7.8     spent on projects last step: 0
> step 1
Capital: -629.2 den   ...   Net/yr: 8.7     spent on projects last step: 0
```
Net/yr says +7.8; capital fell 59 denarii. The difference is exactly the arrears
interest, which the same `money` screen reports on a *separate* line
("interest on arrears: 12%   paid so far: N") but does not net off.

**Mechanism:** `rome/sim/engine/protocol.py` ~line 121 —
`"net_per_year": round(s.revenue() - s.upkeep() - s.living_cost() - s.mine_operating_cost(), 1)`.

**Judgement: real defect.** A `net_after_project_spend` field was already added
in response to an earlier tester for exactly this class of complaint; interest was
missed. In arrears — the state where the number matters most — it is systematically
wrong in the flattering direction.

---

## S9. The founder's starting practice is simultaneously "yours" (DONE, paying you) and "the society's, not yours" (cannot be mothballed)

**Severity: misleads a player; makes one legitimate style of play impossible.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 17 and `naive4/C/WEIRD_C.md`
BUG 6 / BUG 8. C found it after 302 in-game years of trying to be poor.

**Re-verified now, one line apart:**
```
> why med_trepanation
STATUS: DONE
UPKEEP: 0 den/yr     REVENUE: 200 den/yr

> mothball med_trepanation
REFUSED: that is something the society has, not something you maintain;
         there is no upkeep of yours to stop

> money
    med_cataract_couching        166.7
    med_trepanation               66.7        <- your entire income
```

**Judgement: real defect, but narrow.** The revenue itself is intended and
defensible (`economy.py revenue_sources()` carries a comment saying testers
repeatedly could not find where the money came from, and the practice is the
cover identity). What is wrong is that two commands in the same session give
opposite answers about ownership, and that there is no way to decline the income.
The framing in the setup screen ("about enough money to eat for a few months")
also never mentions that you arrive with a ~230 den/yr surgical practice; only
`money` reveals it, and `state` now at least signposts `money` in its footer.

---

## S10. `buy slaves 1` charges 354 denarii and produces a fractional person of trade `None` that appears on no roster

**Severity: corrupts state (money is taken for something that half-exists) / misleads.**

**Where reported:** `naive4/C/WEIRD_C.md` BUG 7 and "BUG 7 continued".

**Re-verified now:**
```
[1300 AD | 400 den] > buy slaves 1
bought: 1 / slaves: 1 / capital: 45.9          <- 354 den

> labour
ON YOUR STAFF:
  nobody
IN TRAINING:
  None x0.55, ready 1303.0                     <- trade literally "None"
Total employed: 0     annual wage bill: 0 den

> state
EMPLOY: 0 people, 0 den/yr in wages
  nobody

> step 1
[1301 AD | 37 den | you:2400 hr | sch 0 art 1 | rep 5] >     <- header says art 1
> state
EMPLOY: 0 people, 0 den/yr in wages
  nobody                                       <- but EMPLOY says nobody
> labour
Total employed: 0                              <- and labour agrees with EMPLOY
```

**Judgement: real defect.** Three of the game's own displays disagree about
whether the person exists: the prompt header counts them as an artisan, `state`
and `labour` do not, and the training queue names their trade `None`. Whether
the 0.55 conversion factor is intended, the `None` label is not.

This also drags in a fourth, still-present cosmetic problem: with 0.55 artisans
on the books, `state` prints its fractional-staff footnote *underneath the word
"nobody"* —
```
EMPLOY: 0 people, 0 den/yr in wages
  nobody
  these are continuous full-time-equivalents ... 1.32 artisans is the wage and
  output of one artisan plus a third of another's.
```
(reported by C as "A worked example about a number I do not have, printed under
the word 'nobody'").

---

## S11. The hire-cap refusal answers a question you did not ask, and recommends the exact action it is refusing

**Severity: misleads a player. A called it "the worst text I have hit".**

**Where reported:** `naive4/A/PLAY_A.md` §1308 ("That error message is a loop")
and `naive4/C/WEIRD_C.md` BUG 12, third bullet.

**Re-verified now:**
```
> hire labourer 6
REFUSED: you can supervise, house and teach 0.99 more people, not 6 - you have
no room for even one. To get more artisans: hire smith 3 or any trade in labour;
or commission smith 400 to buy one job instead of employing anybody; buy slaves N
then manumit, though they are untrained for three years.
```
I asked for labourers. It answers about artisans, and its first remedy is
"hire smith 3" — another hire, which the same rule will refuse for the same
reason.

**Mechanism:** `rome/sim/engine/labour.py` ~line 500 —
`self._staff_advice("artisans")` is hard-coded regardless of the trade requested,
and `STAFF_SOURCES["artisans"]` (`society.py` ~138) leads with `HIRE`.

**Judgement: real defect.** Two fixes in the same string were already applied
(the off-by-one and the raw JSON — see F13 and F14 below), so this is a
half-repaired message. The remaining half is the part that made the tester give
up on the supervision system entirely.

---

## S12. There is no way to ask what your supervision/housing capacity is, or what raises it

**Severity: misleads a player (it is a hard cap on the whole mid-game).**

**Where reported:** `naive4/A/PLAY_A.md` §1308 and its "THINGS I WANTED TO DO AND
COULD NOT FIND A WAY TO DO" list: "The refusal quotes a number ('you can
supervise, house and teach 0.2 more people') that appears nowhere else."

**Re-verified now:** `state`, `labour`, `labour <trade>`, `policy`,
`help labour` and `help commands` were all checked. None of them reports
`staff_capacity()` or `supervision_room()`. Grepping `rome/sim/engine/protocol.py`
and `cli.py` for `supervision_room` / `staff_capacity` returns nothing — the
figures are computed in `labour.py` and surfaced only inside the refusal string.

**Judgement: real defect (a missing affordance rather than a wrong statement).**
The comparable literacy ceiling, which A praised as "a perfect refusal", names
the limit, says it is societal, and names three levers. The supervision cap does
none of those things anywhere a player can look before they hit it.

---

## S13. `available find X` filters the startable table and then dumps the entire unfiltered "HEARD OF" list underneath it

**Severity: misleads a player.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 11.

**Reported repro:**
```
> available find transistor
AVAILABLE: 0 startable now
1-0 matching 'transistor'
(empty table)
HEARD OF, CANNOT BEGIN YET:
  cap_measure_time_ms ... chm_continuous_batch ... fin_company_town ... (all 9, unfiltered)
```

**Re-verified now**, on a save that has a populated HEARD OF list:
```
> available find thermometer
AVAILABLE: 0 startable now
1-0 matching 'thermometer'
ID ... (empty)
HEARD OF, CANNOT BEGIN YET:
  balance_analytical ...
  case_hardening ...
  civ_bridge_timber_truss ...
  ... 18 entries, only one of which matches 'thermometer'
```

**Judgement: real defect.** The header says "1-0 matching 'thermometer'" and then
lists seventeen things that do not match. It also under-reports: `thermometer`
*is* in the list the command just printed, so "0 startable / 0 matching" is not
the whole truth either.

---

## S14. `mothball` / `restore` is free, instant and unlimited, so upkeep is optional

**Severity: exploit, low.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 16.

**Re-verified now:**
```
> mothball cap_measure_time_s
mothballed: cap_measure_time_s shut down; you stop paying 20 a year for it,
and you stop getting what it gave you
> money
  upkeep of what you built       0
> restore cap_measure_time_s
restored: cap_measure_time_s back in service for 0 denarii
> money
  upkeep of what you built       20
```

**Judgement: real, but the mildest kind.** It is a design choice that restoring
something you shed in ruin should be cheap (A explicitly liked that: "Restore
prices are ~10% of build cost... That is a merciful design"). But a *voluntary*
mothball costing zero to reverse means a player who cycles it around the annual
tick pays no upkeep at all. Note the game already models this correctly for
mines — `quote mine` says "Mothballing is not free to reverse: the shaft floods
and the crew disperses" — so the asymmetry looks like an oversight rather than a
decision.

---

## S15. "waiting on money" is reported while the player is rich, because of an unexplained per-project annual instalment cap

**Severity: misleads a player.**

**Where reported:** `naive4/A/PLAY_A.md` CONFUSION #7 ("projects report 'waiting
on money' while I am sitting on 31,000 denarii ... the phrase 'waiting on money'
is exactly wrong when I have thirty thousand of it") and `naive4/B/BREAK_B.md`
FINDING 23 ("Project status says 'waiting on money' for a 10.2-den project while
holding 1,084 den").

**Mechanism (current code), `rome/sim/engine/core.py` ~line 795:**
```python
money = min(st["cost_left"], self.project_cost(k) * frac)   # frac = 1/n["yrs"]
```
A project with a multi-year floor can absorb only `cost/years` per year no matter
how much cash you hold, and `protocol.py` ~line 63 then labels the residue
`"money"` whenever `ph_left <= 0 and bill > 0.5`.

**Judgement: real defect, partially repaired.** The *worst* version of this was
fixed: the trade-shortage case now says `waiting on nobody to do the work:
scribe` instead of blaming money, and the code comment records the 696,350-denarii
tester who hit it. The instalment-cap case is still labelled "money" and the cap
is documented nowhere.

---

## S16. The RUNNING line truncates a project name mid-bracket, and a project needing zero founder hours reports "100% of your hours spent"

**Severity: cosmetic, but it produces an unparseable sentence.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 8 and `naive4/C/WEIRD_C.md`
Phase 4 ("A project needing 0 of my hours reports 100% of my hours spent; 0/0 is
being rendered as 100%. The name also loses its closing bracket to truncation, so
the line reads as one broken sentence").

**Re-verified now, verbatim:**
```
RUNNING (1):
  Time to the second (pendulum 100% of your hours spent, 0 den still owed - waiting on the calendar
```
Both faults intact: the name is cut at 28 characters exactly where the `)` was,
and `cap_measure_time_s` requires 0 founder hours yet reports 100% of them spent.
There is also no closing punctuation.

**Judgement: real defect, cosmetic.**

---

## S17. `bounty` says it pays somebody else to do the work, then reports "waiting on your hours"

**Severity: misleads a player, low.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 12.

**Re-verified now:**
```
> bounty fin_employment_contract
posted: fin_employment_contract
> state
RUNNING (1):
  Contract of employment        65% of your hours spent, 0 den still owed - waiting on your hours
```
`help commands` says "bounty <id>: pay someone else to solve it instead".

**Judgement: real, and half-explicable.** `rome/sim/engine/projects.py` line 149
sets `ph_left = n["ph"] * 0.35`, i.e. a bounty does 65% of the work and leaves
you the last 35% — so "65% of your hours spent" is arithmetically the intended
figure. But calling the bounty-winner's labour *your* hours, on a command
advertised as buying you out of exactly that, is a false statement about who did
the work. B's own note that it completes without consuming founder hours is
consistent with this: the hours are notional.

---

## S18. `why` says "you have 1 scholar" while the prompt, `state` and `labour` all say you have none

**Severity: misleads a player, low.**

**Where reported:** `naive4/C/WEIRD_C.md` Phase 4, first display fault
("**I have 1 scholar?** The status bar says `sch 0 art 0` and `EMPLOY` says
`0 people ... nobody`. Something counts the founder as a scholar and something
else does not").

**Re-verified now:**
```
[1300 AD | 400 den | you:2400 hr | sch 0 art 0 | rep 5] > why med_trepanation
STAFF NEEDED: 1 scholars, 0 artisans   (you have 1, 0)
```

**Judgement: real inconsistency.** The founder plainly *is* counted as a scholar
for the purpose of satisfying staff requirements — that is why a solo founder can
run a surgical practice. It is just never said anywhere except inside this one
parenthesis, where it contradicts three other displays.

---

## S19. `labour <trade>` prints an hourly wage that neither `hire` nor `work` uses

**Severity: misleads a player, low.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 23 last bullet — "The founder
earns 0.28 den/hr doing `work scholar`, while `labour scholar` says the market
wage for a hired scholar is 0.35 den/hr. The man with all modern knowledge is
paid 20% below the going rate."

**Re-verified now:**
```
> labour scholar
a year of one: 550 den     wage: 0.35 den/hr
> work scholar 1000
earned: 281.9                                  <- 0.282 den/hr
```
550 den a year at 0.35/hr implies a 1,571-hour year. The model's year is 2,000
hours (`economy.py`: `HOURS_PER_PERSON_YEAR = 2000.0`), which gives 0.275/hr.

**Mechanism:** `rome/sim/engine/protocol.py` ~line 2079 computes `a_year_of_one`
from `ANNUAL_WAGE` and `wage_per_hour` from a *different* table, `WAGES`.
`work_for_wages()` (`labour.py` line 362) uses `ANNUAL_WAGE / 2000`. Three
numbers, two tables, one screen.

**Judgement: real defect.** The docstring at `labour.py` line 355 says explicitly
that a previous 2.3x version of this spread was fixed so that "there is no
arbitrage in either direction". The residual ~25% spread between the *displayed*
hourly rate and every rate actually charged or paid is the same bug, smaller. B's
reading of it as a deliberate insult to the founder is a tester misreading — but
the number they were reading is genuinely wrong.

---

## S20. `INSOLVENCY SETTLED` fires every ten years for ever, with the identical figure

**Severity: cosmetic / log spam. The false-statement half of this is fixed.**

**Where reported:** `naive4/B/BREAK_B.md` FINDING 18 & 20, `naive4/C/WEIRD_C.md`
BUG 2 & BUG 3 ("fired eight times ... It reads like a cooldown timer firing on an
effect that does nothing").

**Re-verified now**, 500-year idle-ish run:
```
EVENT 1363: INSOLVENCY SETTLED: most of the debt is written off and you still owe about 215 denarii...
EVENT 1373: INSOLVENCY SETTLED: ... you still owe about 86 denarii...
EVENT 1383: ... 86 ...   1393: ... 86 ...   1403 ... 1413 ... 1423 ... 1433 ... 1443 ... 1453 ... 1471
```

**Judgement: design choice with a cosmetic problem.** The message itself is now
honest (see F8) and the ten-year cooldown is deliberate and documented in
`economy.py` ("A write-off is a once-in-a-life humiliation, not an annual
accounting entry"). But settlement resets you to `-limit * 0.35`, from which a
household whose fixed costs exceed its income returns to `-limit` in about ten
years, so the cooldown is precisely the cycle length. The result is the same
sentence, with the same number, once a decade, indefinitely. It is not a lie any
more; it is still noise.

---

## S21. `help money` prints `help economy` verbatim

**Severity: cosmetic.** Reported by all three naive4 testers
(`A` CONFUSION #3, `B` FINDING 8, `C` "Other small things").

**Re-verified now:** the two outputs are byte-identical (`diff` returns nothing),
while `help` advertises both as separate topics. `money` is also a *command* with
different behaviour from the `economy` topic, which is what A tripped over.

---

## S22. The printed resume line is a relative path that works from no directory

**Severity: cosmetic.** Reported as `naive4/B/BREAK_B.md` FINDING 2.

**Re-verified now**, from a scratch directory:
```
Saved to england_1300.json. Come back with:
   python3 rome/sim/simulator.py play --session england_1300.json
```
The save is written to the CWD; `rome/sim/simulator.py` only resolves from the
repository root. There is still no single directory from which the printed line
runs. (The `--civ` half of this complaint is **fixed** — see F1.)

---

## S23. `step 1; step 1` executes the first command and silently discards the rest of the line

**Severity: cosmetic.** Reported as `naive4/B/BREAK_B.md` FINDING 23.

**Re-verified now:** `step 1; step 1` advanced 1300 -> 1301 only, with no note
that anything was dropped.

---

## S24. Node ids are case-sensitive; the game names the correct id in the refusal and refuses anyway

**Severity: cosmetic.** Reported as `naive4/B/BREAK_B.md` FINDING 23.

**Re-verified now:**
```
> WHY AG2_MARLING
REFUSED: unknown node 'AG2_MARLING'. did you mean: ag2_marling
```

---

## S25. A 3,000-character id is echoed back in full inside the error message

**Severity: cosmetic.** Reported as `naive4/B/BREAK_B.md` FINDING 23 ("`why
AAAA...(5,000 chars)` echoes the whole 5,000-char string back inside the error").

**Re-verified now** with a 3,000-character argument: the whole string comes back.

---

## S26. Small numeric and grammatical faults in the shared displays

**Severity: cosmetic.** All re-verified now.

- **"You built 1 things of your own"** — `protocol.py` line 38 has no plural
  handling. (`naive4/B` FINDING 15.)
- **Prompt header and body disagree by one denarius** — `[1302 AD | 411 den ...]`
  against `Capital: 412 den` in the same reply; the header truncates where the
  body rounds. (`naive4/B` FINDING 8, `naive4/C` Phase 4.)
- **`fire smith 100` with 1 smith employed** replies `let go: smith` and clamps
  to zero without saying how many actually went. (`naive3/BREAK`.)
- **`state`'s footer reads like a list of node ids** —
  `more: knowledge_risk -> risk; how_to_grow_staff -> labour; ...` — and A typed
  `why knowledge_risk` because of it. It is a topic-to-command map and the arrow
  reads as "leads to". (`naive4/A` CONFUSION #4.)
- **`available` suggests a budget you do not have** — `what you can pay for:
  available afford 1,151` while holding 400 den. The figure includes credit; the
  phrasing does not say so. (`naive4/B`, "Note on the first `available` output".)

---

# PART 2 — FIXED

Each of these was reported in naive3/naive4 and no longer reproduces. Listed
because several were the testers' headline findings.

**F1. Resume without `--civ` no longer fails.**
Reported by all four England testers (`A` CONFUSION #1, `B` FINDING 1b,
`C` BUG 1). Now: `play --session england_1300.json` prints
`Resumed from england_1300.json: 1300 AD.` and loads England. B recorded the fix
landing mid-session (commit "A save knows what game it is").

**F2. "Saved to X" with no file written.**
`A` CONFUSION #2 / `B` FINDING 1a: setup followed by EOF claimed a save and wrote
nothing. Now the file exists (8,592 bytes) after the wizard alone.

**F3. `bounty <hidden id>` leaked the hidden tree — the single worst fog-of-war hole.**
`B` FINDING 9 (CRITICAL) crawled 134 hidden ids and the whole dependency graph
backwards from the goal in six rounds. Now:
```
> bounty point_contact_transistor
REFUSED: you have never heard of that. You know what you have built and what you
could begin next; nothing tells you what lies beyond that.
```
`bounty`, `why` and `path` now agree.

**F4. `quote mine coal 500` and `buy mine coal 500` were unparseable.**
`B` FINDING 5 / `C` BUG 14 ("the whole mining subsystem is unreachable" — C's
most consequential finding). Both now work; `quote coal 500` works too.

**F5. `buy mine` silently spent 100% of capital for a fraction of the order.**
`B` FINDING 19. Now refused outright:
`REFUSED: 500 tonnes a year of coal costs 4,950 denarii to sink and you have 400.
Nothing was changed`. `protocol.py` calls `open_mine(..., partial=False)` with a
comment naming this exact complaint.

**F6. `path` under fog blamed the wrong thing.**
`naive3/BREAK` finding 4 — it told the player they had "not discovered"
technologies they had already completed. Now:
`REFUSED: route planning is switched off under fog of war ... whether or not you
have built this particular thing already.`

**F7. `work <trade>` ignored trade-existence gating.**
`naive3/BREAK` finding 1 (their top-ranked defect) — the founder drew wages as a
chemist in 1500 Tenochtitlan. Now:
`REFUSED: nobody here will pay you to be a chemist: the trade does not exist in
this society, so there is no employer for it.`

**F8. "the debt is written off" while leaving you in debt.**
`B` FINDING 20 / `C` BUG 2. Now: `INSOLVENCY SETTLED: most of the debt is written
off and you still owe about 215 denarii. Your name is worth less for it
(reputation -12), and you keep your knowledge and your practice.` (The repeating
cycle survives — S20.)

**F9. `auto_shed` on by default silently deleted built works.**
`A`'s "THIS IS THE WORST THING I HAVE FOUND"; also `B` FINDING 15. Now
`auto shed: False` by default in manual play, and every loss is named in the log:
`creditors took what they could: 1 works let go: cap_measure_time_s`,
`ABANDONED N works you could no longer maintain ... : <names>`,
`stopped maintaining N works ... : <names>`. The step reply also carries a `lost`
list alongside `completed`, which was A's specific request.

**F10. Staff force-fired to zero with `auto_shed` explicitly off.**
`naive3/BREAK` finding 2. Now 3 hired smiths survive the step at 2.9 FTE with
`auto_shed: false`, and unaffordable payroll produces a named event
(`you cannot pay everyone: 0.4 of your staff leave for work that pays`).

**F11. Project hour-progress froze, reset, and went negative ("-67% of your hours spent").**
`naive3/PLAY` finding 1, their top-ranked defect. `core.py` ~line 715 now clamps
refunds to `spent_hours` with a comment quoting this tester verbatim
("You cannot be refunded work you never did"). The asymptotic `still_to_pay`
(their finding 2) is also handled: completion needs `cost_left <= 0.5`, not 0.

**F12. Deep arrears silently stalled all projects with no explanation.**
`naive3/PLAY` finding 3. Active projects now carry `why_underfunded`:
"in arrears: after fixed costs there is nothing left to draw on, so the hours
offered this year did almost nothing".

**F13. Off-by-one in the hire cap.**
`C` BUG 12 — refused `n` when the room was exactly `n`. Now truncated and
explicit: `you can supervise, house and teach 0.99 more people, not 1 - you have
no room for even one`.

**F14. Raw JSON in plain-word prose.**
`A` CONFUSION #6, `B` FINDING 10, `C` BUG 12. The hire refusal now reads
"buy slaves N then manumit"; `start ../../etc/passwd` now says
"use available or why ... to find valid ids"; `help` now says "One command per
line, in plain words" instead of instructing a human to send JSON (`B` FINDING 3).

**F15. "dangerous above 26" with no subject.**
`A` CONFUSION #5 and #8 (logged twice over 500 years), `naive3/PLAY` (guessed
wrong twice before finding it in raw JSON), `B` FINDING 25. Now:
`EMINENCE is dangerous above 26 (settles near 0 ...)`. `suspicion` has been
removed from the display entirely, which also retires B's "suspicion pinned at 30
with 0% ruin for 23 years".

**F16. The goal was a secret until the run ended.**
`A`'s number-one requested change and `C` BUG 10. `state` now prints
`Aiming at: Point-contact transistor` every turn under fog; `help` says
"what you are trying to do: Build point-contact transistor, before the horizon at
1800"; and the ending no longer claims "There was no target to hit" — it reads
"the horizon at 1800 AD is reached. You built N things of your own and did not
reach point-contact transistor."

**F17. The 1800 horizon was invisible until you overshot it.**
`C` BUG 5. Every `state` header now reads `YEAR 1300   (500 years to the horizon
at 1800)`, and the agent state carries `horizon_year` / `years_left`.

**F18. Only one command worked after the run ended.**
`C` BUG 11. `state`, `money` and `available` all executed in sequence post-1800 in
my re-run.

**F19. `available` hid revenue, upkeep and downstream weight.**
`A`'s "biggest single usability gap" — they scripted 461 `why` calls to
reconstruct it. The table now carries `EARNS/YR`, `UPKEEP` and `RESTS` columns,
plus a `MOST RESTS ON THESE` section that surfaces `identity_cover` and
`units_standards` (RESTS: ALL) on turn one, which was the exact thing A said the
interface steered players away from.

**F20. The Black Death took ~28% of capital and said only "staff -45%".**
`C` BUG 13. Now: `Black Death: staff -45%, and 90 denarii gone with the trade
that stopped`.

**F21. `train` destroyed the save.**
`A`'s "fatal" finding, with a one-command minimal repro. `train optician 1`
followed by a reload now resumes cleanly at the right year. (This was an artefact
of the tech tree being edited underneath a live save while A played; the
trained-trade ids no longer poison the file.)

**F22. `state` reported 2,400 founder-hours after they had been spent.**
`B` FINDING 6. Now `work scholar 2300` leaves `you:100 hr` in both the prompt and
`state`.

**F23. Assorted validation and text faults.**
- `frobnicate` no longer prints a stale 10-item command list (`naive3/BREAK`
  finding 5, `naive3/WEIRD`); it says "Type 'help' for the list."
- `step 1.99` is now refused ("years must be a whole number of years; 1.99 is
  not") instead of being silently floored (`naive3/BREAK` finding 6).
- `train machinist -3` now says "n must be greater than zero" instead of "hours
  must be greater than zero" (`B` FINDING 8).
- `state full:true` now differs from `state` — it itemises the hazard list
  (`C`, "Minor").
- `state.living_cost` no longer bundles the payroll: `protocol.py` reports
  `living_cost - wage_bill` with `wage_bill` as its own field (`naive3/BREAK`
  finding 3).
- The Hundred Years War no longer prints an identical line every year for 40
  years; it fires roughly every 20 (`C` Phase 1 item 4, Phase 2).
- `bribe N` at scandal 0 is no longer a pure money-burn: it now buys protection
  (`bribed: scandal 0.00 -> 0.00 for 200 denarii; advocacy and piety bought as
  well: protection 0.00 -> 0.32`) (`B` FINDING 14).
- The purse menu no longer claims "the medians sit inside the noise band anyway",
  which B disproved with a 8-vs-143 spread; it now says money "buys perhaps a
  tenth off the time, not a different game. What money changes most is the
  OPENING" (`B` FINDING 22).

---

# PART 3 — UNCLEAR

**U1. Quoted COST going stale over decades.**
`naive4/A/PLAY_A.md`, §1341: "`finery_puddling` was quoted 106,567 and billed
207,811 forty years later ... This is the single most expensive misunderstanding
available in the game and nothing flags it." A lost the run to it.

I could not reproduce it and I believe it is now fixed, but I cannot demonstrate
the negative cheaply. `rome/sim/engine/projects.py` line 336 now locks the bill at
`start` time (`cost_left=self.project_cost(k)`), so the total billed is the cost
as of the moment you commit, not the moment you finish. `why`'s COST line also
now exposes the multipliers that move — `COST: 3,627 den total (40 labour + 0
materials + 4,000 capital, then x0.82 your civ, x1 distance, x1.1 prices)` — so a
stale quote is at least visible as a changed `x prices` factor. What remains true
is that a quote you read in 1331 and act on in 1371 can be wrong, and nothing says
so; that is a weaker complaint than the one A filed.

---

# PART 4 — REPORTED, BUT NOT DEFECTS

Recording these so they are not re-litigated. Each was raised as suspicious by a
tester and each is, in my reading, working as designed.

- **"Nothing can be built by the deadline" / statelessness beats the hazards.**
  `naive3/PLAY` finding 5, `naive3/WEIRD`, `naive4/C`. Owning nothing and
  employing nobody makes staff-loss hazards a no-op. This is a genuine emergent
  property of keying catastrophe to staff and sites, and the testers themselves
  concluded it was "the simulator telling me something true". Worth a designer's
  attention; not a bug.

- **Roman framing in every civilisation.** Denarii in 1300 England and 1500
  Tenochtitlan, "the equestrian census", "four senatorial fortunes", a chattel
  slave market in Edward I's England (which ran on villeinage), and papyrus /
  groma / annona / Roman cosmetics in the England tree. Reported by `B` FINDING 4
  & 24, `C` Phase 5, `naive3/BREAK`. Confirmed still present. I read it as an
  acknowledged shared-engine scope decision — `help economy` defends the slave
  market explicitly — rather than a defect. It does cost the England and Mexica
  scenarios a lot of credibility.

- **`clock_pendulum` granted in 1300**, three centuries early (`naive4/A`). The
  ambient-grant rule grants every tier-0, zero-cost, zero-hour node whose
  prerequisites are met. That is a deliberate rule, not a data error about
  pendulums.

- **The founder is immortal.** `naive3/WEIRD` item 4 called this "the most
  unrealistic thing I've seen". `founder_ages: false` was the tester's own answer
  to the setup wizard's "Let the founder age and die? [y/N]".

- **`start` accepts a project you cannot afford.** `naive3/WEIRD` Action 1. Costs
  draw down as work proceeds; committing before you can pay is the intended
  shape. (The absence of an *aggregate* limit is a real defect — S2.)

- **Fog reveals exact hazard years.** `naive3/WEIRD`. `risk` deliberately tells
  scripted history regardless of fog; fog covers the tree, not the calendar.

- **`bounty` refusals that read absurdly for simple items** — a breadcrumb
  eraser and tier-0 obstetrics both refused because "a craftsman in England under
  Edward I could not recognise success at this without understanding the theory"
  (`B` FINDING 23). The rule is category-derived and the wording is category-wide;
  every tester who quoted it also called it the best-written refusal in the game.
  Cosmetic at worst.

- **Revenue lines called "technologies".** `naive4/A`: "Building an umbrella
  business and building the puddling furnace score the same way." A framing
  objection, and a fair one, but not a defect.

---

## Method note

All re-verification was done through the game's own interface with commands piped
on stdin, in `/tmp/claude-.../scratchpad/`, exactly as the notes describe. I read
`rome/sim/engine/` freely to confirm mechanisms and to distinguish "fixed" from
"did not happen to fire on my seed" — the engine's source carries unusually good
provenance comments, several of which quote these very testers, which made the
FIXED column much easier to establish than the STILL PRESENT one. No repository
file was modified.
