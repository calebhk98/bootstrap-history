# Sweep of the first two naive rounds, re-checked against today's engine

Source notes: `rome/playtest/naive/` (rome_100ad A/B/C/BREAK/WEIRD,
han_china_100ad BREAK/PLAY/WEIRD) and `rome/playtest/naive2/` (norse_900ad
PLAY/WEIRD/BREAK). Every distinct bug, defect, inconsistency or false statement
the testers reported — or that their transcripts reveal whether or not they
noticed — is below, de-duplicated across the eleven notes.

Each entry was re-tested against the code in `rome/sim/engine/` as it stands,
mostly by running the game. Nothing in the repository was modified.

**Result: 31 STILL PRESENT, 47 FIXED, 4 UNCLEAR.** Most of what the first two
rounds found is gone. What is left is concentrated in three places: the fog
mode can be undone with `save`/`load`, freeing bought people is strictly the
best labour strategy in the game, and several fields still state as fact
things the object beside them contradicts.

Verification commands throughout are the JSON agent protocol, e.g.

    printf '{"cmd":"state"}\n' | python3 rome/sim/simulator.py agent \
        --civ norse_900ad --fog --session /tmp/probe.json

---

# PART 1 — STILL PRESENT

## S1. `save` + `load` is unlimited undo, and it switches fog of war off
**severity: defeats the mode the run is being played in**

Reported by norse_900ad_WEIRD ("Exploit 5") and listed in FINDINGS_ROUND2 §H/M.

Reproduction, run just now against `rome_100ad --fog`:

    {"cmd":"save","file":"sp1.json"}   -> {"ok": true, "saved": "sp1.json", "year": 100}
    {"cmd":"step","years":500}         -> year 600
    {"cmd":"state"}                    -> "year": 600, ended
    {"cmd":"load","file":"sp1.json"}   -> {"ok": true, "loaded": "sp1.json", "year": 100}
    {"cmd":"state"}                    -> "year": 100, "ended": false

The tester's own words: *"Since the whole design of `--fog` is that 'you cannot
see where anything leads', and since `load` restores the game but not the
player's memory, a player can save, build a node, look at what appeared in
`available`, load back, and keep the knowledge. Fog of war is one command away
from being off."*

Where: `load_state` / `save_state`, `rome/sim/engine/protocol.py` ~2500-2600;
dispatch at ~2190.

**Judgement: real defect.** Not because saving is wrong, but because the fogged
mode makes a specific promise (`help fog`: *"You cannot see where anything
leads, and there is no way to view the whole tree"*) that a two-command loop
falsifies. Every other route to the same information — `why`, `path`, and now
`start` — is gated; this one was not. A save-slot count, or refusing `load` to
an earlier year while `--fog` is on, would close it.

**Severity: loses the integrity of a fogged game.** It cannot corrupt state.

## S2. Buying people and freeing them is the cheapest and best labour in the game
**severity: contradicts the game's own stated reason for modelling slavery**

Reported in three notes: rome_100ad_WEIRD §5, norse_900ad_WEIRD ("Buying people
and freeing them is a small reputation machine"), norse_900ad_BREAK FINDING 21.

Clean reproduction just now, `norse_900ad --fog`, no other staff:

    (year 908: artisans 0.0, freedmen 0, annual_wage_bill 0.0, living_cost 278.9)
    {"cmd":"buy","what":"slaves","n":3}   -> {"ok": true, "bought": 3, "capital": 495.6}   (1,529 den)
    {"cmd":"buy","what":"manumit","n":3}  -> {"ok": true, "manumitted": 3, "freedmen": 3}
    {"cmd":"step","years":4}
    (year 912: artisans 6.0, freedmen 3, annual_wage_bill 0.0, employees {},
               reputation 6.2 -> 6.5, living_cost 398.7)

Three people bought once for 1,529 denarii become **6.0 artisans** — twice their
own headcount — with `annual_wage_bill: 0.0` and `employees: {}`, for +120/yr of
living cost against roughly 210/yr *each* to hire the same people, plus a
reputation dividend. Payback against hiring is about fifteen months and the
labour is then free for five centuries.

Where: `manumit()` and the freedmen training rows in `rome/sim/engine/labour.py`;
`artisans` is credited from `training_pending` rows whose `trade` is null.

**Judgement: real defect, and the sharpest one in the notes.** The welcome text
says freed people *"work better"*, which justifies some premium — it does not
justify two artisans per person at zero wage. The design intent is legible and
the numbers invert it: the help says the model exists so that it does not *"lie
about the cost of everything"*, and as implemented buying people is the cheapest
labour available, which is the lie in the other direction.

**Severity: misleads a player about the model's own values and unbalances the
labour economy.** No state corruption.

## S3. `why` says a node is not bounty-eligible; `bounty` then accepts it
**severity: a flatly false statement, one command apart**

Found by norse_900ad_BREAK FINDING 15 in an older form ("80 of 86 refuse"); the
refusal text and the eligibility rule were both fixed, and this residue was not.

    {"cmd":"why","id":"sea_skeleton_first"}
      -> "bounty_eligible_by_type": false,  "cat": "ships", "tier": 1
    {"cmd":"bounty","id":"sea_skeleton_first"}
      -> {"ok": true, "posted": "sea_skeleton_first", "price": 2836.1}

Where: `rome/sim/engine/protocol.py:653` computes `bounty_eligible_by_type` as
`tier <= 2 and cat in (glass_optics, metallurgy, precision, power, agriculture,
information, instruments)` — the old Rome-only allow-list. The real rule is
`Sim.bounty_eligible`, `rome/sim/engine/projects.py:107-132`, which was widened
so that anything a civilisation is measurably good at (`civ_cost_factor < 0.95`)
also qualifies. `why` was never updated to match.

**Judgement: real defect.** Two implementations of one rule; the explanatory one
is the stale copy. It is the exact shape of the 1.4x cost-breakdown bug the same
tester found (FINDINGS_ROUND2 §J) — an explanation that does not reconcile with
the thing it explains — and that one was fixed.

**Severity: misleads a player** into never trying the one action their
civilisation is best placed to use.

## S4. `resource_throttle: 1.0, throttle_binding: null` while every project is frozen
**severity: false statement about the thing the field exists to report**

norse_900ad_WEIRD §9, and again in the "Insolvency" section: *"the top-level
summary said `resource_throttle: 1.0, throttle_binding: null` — i.e. 'nothing is
limiting your work' while eight projects were frozen for lack of money."*

Reproduced just now (`norse_900ad`, four projects started against 400 capital,
stepped three years into arrears):

    {"cmd":"state"}
      -> "resource_throttle": 1.0, "throttle_binding": null
         active: fin_ferry        waiting_on "your hours"
                 why_underfunded  "in arrears: after fixed costs there is nothing
                                   left to draw on, so the hours offered this year
                                   did almost nothing"
                 fin_inn          same
                 fin_trading_post same

Where: `throttle_binding` in `_agent_state`, `rome/sim/engine/protocol.py` ~220;
set in `rome/sim/engine/core.py` around the material-throttle pass only.

**Judgement: real defect, partially mitigated.** The per-project `why_underfunded`
field (new since these rounds) now tells the truth, so a reader who opens `active`
gets the answer. The summary line still says the opposite. The PROTOCOL calls
`throttle_binding` *"what is limiting work, if anything"*, and money limiting
work is not represented in it.

**Severity: misleads a player** at exactly the moment they are trying to work out
why nothing is happening.

## S5. `waiting_on` names the wrong constraint
**severity: mislabel, contradicted by a sibling field**

Same reproduction as S4. A project reports:

    "waiting_on": "your hours",
    "hours_offered_this_year": 100.0,
    "hours_effective_this_year": 0.0,
    "why_underfunded": "in arrears: ... the hours offered this year did almost nothing"

The hours were offered and did nothing; money is the constraint. `waiting_on` is
computed in `rome/sim/engine/protocol.py:60-65` from `ph_left` and the bill alone,
and falls through to `"your hours"` whenever `ph_left > 0`, regardless of whether
those hours can actually be spent.

**Judgement: real defect**, small and adjacent to S4 — `waiting_on` should read
`why_underfunded` before it decides.

**Severity: misleads a player.**

## S6. Rubber is priced at a sentinel the player is never shown, and the sentinel is buyable
**severity: false statement in the price data, and a cost that reads as a unit error**

norse_900ad_PLAY, "Costs that look like unit errors": *"A tourniquet is a stick
and a strap... `md2_tourniquet` at 210,340 I cannot [believe]."*

Confirmed as still true and diagnosed:

    md2_tourniquet      210,340.9      md2_surgical_drape        302.3
    md2_surgical_glove  210,298.9      md2_catgut_suture         305.2
    tx2_ballpoint_pen 1,232,234.1      ag2_milking_machine  7,001,168.3

All of them, and 22 nodes in total, require `rubber_kg`, priced in
`rome/data/prices.json:590` at **99,999.0/kg** with the note:

> "UNOBTAINABLE, priced at an absurd number deliberately so that any recipe
> depending on it shows up instantly as impossible. Natural rubber is American.
> There is no route."

Two problems. First, nothing renders that intent to the player: `why` prints a
`materials` dict and a `total`, with no "unobtainable" flag, so the sentinel
reads as a scaling bug — which is exactly how the tester read it. Second, the
claim "there is no route" is false in the model: `md2_tourniquet` is `tier 1`,
`cat surgery`, prerequisite `sanitation_antisepsis` only. It is not tier 9 and
not `cat: "unobtainable"`, the two things `rome/sim/engine/projects.py:222`
actually blocks, and none of the 22 rubber nodes requires `mat_synthetic_rubber`
or an Atlantic crossing. A rich enough player simply pays 210,340 denarii and
buys 1.5 kg of American rubber in the second century.

**Judgement: real defect wearing a design choice's clothes.** The sentinel is a
deliberate and good idea; it is unenforced (money defeats it) and undisclosed
(the player sees a number, not a reason). Contrast `ag2_maize_newworld`, which
*is* correctly gated behind `exp_atlantic_crossing`.

**Severity: misleads a player** and, for anyone wealthy, lets them build things
the data says are impossible.

## S7. `start` has no affordability ceiling at all, while `buy`, `hire` and `train` do
**severity: an inconsistency the game never explains**

han_china_100ad_WEIRD §7 ("THE BIG ECONOMIC EXPLOIT"), norse_900ad_BREAK
FINDING 11, rome_100ad A/B/C all hit this.

Reproduced now, `norse_900ad`, opening capital 400:

    {"cmd":"start","id":"fin_inn"}          -> ok, "the_bill_you_have_taken_on": 5579.1
    {"cmd":"start","id":"fin_ferry"}        -> ok, "the_bill_you_have_taken_on": 6246.7
    {"cmd":"start","id":"fin_trading_post"} -> ok, "the_bill_you_have_taken_on": 2622.0
    {"cmd":"step","years":3}                -> capital -1406.0
    {"cmd":"start","id":"fin_gambling_house"} -> ok, "the_bill_you_have_taken_on": 3253.3

17,701 denarii of commitments on 400 denarii, in arrears, with no refusal.
Meanwhile `{"cmd":"buy","what":"mine",...}` refuses with a price, `hire` refuses
with a supervision and literacy cap, and `train` refuses with a feeding cost.

**Judgement: half-fixed, and the remaining half is defensible.** The worst part
of the original finding is gone: `start` now returns
`"the_bill_you_have_taken_on"` (it used to report hours and years and hide the
money entirely, which the tester correctly called *"an oversight"*), arrears now
accrue interest, and the credit limit does eventually refuse large new work. What
remains is that a first-time player can still commit forty times their capital
in four commands without a single warning, and the interface's own philosophy is
inconsistent across `start` / `buy` / `hire`. `help economy` does say *"You may
spend past what you have, as far as somebody will lend you"* — so it is disclosed
in one place and unenforced at the point of use.

**Severity: can lose a game** for a player who does not read `help economy`.

## S8. `completed` mixes society diffusion with things you paid for, and `events` disagrees with it
**severity: misleads a player about what they achieved**

rome_100ad B: *"a second, distinct completion fired with no corresponding
`events` entry — `cap_measure_len` auto-completed as a side-effect, silently.
`completed` list showed it but `events` was empty that turn."* Also rome_100ad C
(*"I'd want free starting knowledge... reported separately from earned
completions"*), han_china_100ad_BREAK FINDING 2, and FINDINGS_ROUND2 §H
("A granted capability appears in `completed` mixed in with things you paid for").

Reproduced now, `rome_100ad --fog`, first command of the game:

    {"cmd":"step","years":1}
      -> "completed": [2 entries], "events": [], "done_granted": 137 -> 139,
         "done_earned": 0

`step 500` on an untouched game likewise returns `civ_amphitheatre` and
`civ_vault_barrel` in `completed`, neither of which was started.

Where: `rome/sim/engine/protocol.py:2338-2339` builds `completed` from
`sorted(s.done - before_done)` with no flag for whether the id is in `s.granted`.

**Judgement: real defect, greatly reduced.** The catastrophic version — 139
freebies dumped in one array on the first `step`, with turn-0 `state`
undercounting by 128 — is fixed (turn 0 now reports the full 137). What is left
is that two feeds describing the same event disagree, and that the entry a player
paid 6,000 hours for is shaped identically to one the society picked up on its
own. One `"granted": true` key would settle it.

**Severity: misleads a player**, cosmetic in scale now.

## S9. Anachronistic nodes that are still gated by nothing but materials
**severity: undercuts the premise; no mechanical harm**

Reported by every tester in both rounds. Most of the list is now fixed (see
F14). These survive:

    rome_100ad, year 100, turn one:
      air_observation_balloon_tethered   cost 1137.6
        {"cmd":"why","id":"air_observation_balloon_tethered"}
        -> "direct_prerequisites": ["mat_beeswax","mat_linen","mat_silk"],
           "tier": 1, "can_start_now": true
      ag2_guano                          cost 119.0
        -> "direct_prerequisites": [], "tier": 1

    norse_900ad, year 900, turn one:
      air_observation_balloon_tethered   cost 3372.8   (same, no prerequisites)
      ag2_guano                          cost 388.1
      tex_hand_ginning  "Hand ginning cotton"  cost 100.1   — in Scandinavia

A manned hot-air balloon needs no combustion, no buoyancy theory and no
ballooning prerequisite; guano is a Peruvian seabird deposit with an empty
prerequisite list; cotton is not grown within two thousand miles of Norway.

**Judgement: real, and the residue of a mostly-completed fix.** Mustard gas,
the trench, the general staff, the trace italienne, the atomic bomb, plate
armour against firearms, chinampas and the New World crops are all now properly
gated (verified: `mil_atomic_bomb` needs `sc2_physics_nuclear_fission`,
`mt2_uranium_thorium_extraction` and `in2_ultracentrifuge`; `ag2_maize_newworld`
needs `exp_atlantic_crossing`). These three were missed.

**Severity: cosmetic / immersion.**

## S10. Roman institutions are still on offer to a Norse founder
**severity: cosmetic, but it was the loudest finding of round two**

FINDINGS_ROUND2 §A, "The setting is Rome wearing a hat", from all four round-two
testers. The expensive half is fixed — they are no longer free — but they are
still in the list:

    {"cmd":"available","all":true}  (norse_900ad, year 900)
      civ_arch_roman       "Roman masonry arch"                   1017.8
      fin_annona           "Annona grain dole and administration"  6371.6
      fin_argentarii       "Deposit bankers (argentarii)"          2328.5
      fin_collegium        "Professional associations (collegia)"  1398.3
      fin_societas         "Partnership (societas)"                 468.2
      hom_cosmetics_roman  "Roman cosmetics"                        112.0

**Judgement: design choice, arguably.** One shared dataset across civilisations
is a reasonable trade, and "a Norseman introduces the Roman arch" is not absurd
the way "a Norseman is handed the Roman arch for free" was. Listed because five
testers independently called it out and because the names, not just the
mechanics, are Roman.

**Severity: cosmetic.**

## S11. Node and trade notes still address a Roman audience in a Norse game
**severity: cosmetic**

    {"cmd":"why","id":"hom_toothbrush"}   (norse_900ad, 900 AD)
      "note": "... Romans use twigs and charcoal powder for dental cleaning. ..."
    {"cmd":"labour","trade":"plumber"}
      "note": "Lead worker. Skilled and numerous wherever lead pipe-making is
               already an established trade (Roman plumbarii are the best-attested
               case); scarce or nonexistent elsewhere."

**Judgement: mostly fixed, residue remains.** The worst offenders are gone —
mason no longer says *"Rome has these in abundance and they are good"*, and the
bounty refusal now reads *"a craftsman in Scandinavia in the Viking age"* rather
than *"a Roman artisan"*. The plumber note is now careful and generic with Rome
as a cited example, which is fine. The toothbrush note is not.

**Severity: cosmetic.**

## S12. `electrician`'s note leaks internal authoring jargon
**severity: cosmetic, breaks the fourth wall**

norse_900ad_BREAK and WEIRD both flagged it.

    {"cmd":"labour","trade":"electrician"}
      -> "note": "DOES NOT EXIST. Cannot exist until Module 50 does.",
         "exists_here": false

Where: `rome/data/prices.json:843`. "Module 50" is a knowledge-base file number.

**Judgement: real defect.** Sibling case, the `[AUDIT: ...]` note that
han_china_100ad_WEIRD found on `water_power_scale`, has been properly fixed —
those 398 annotations now live in an `_internal` key that `_node_explain` never
returns. This one was left in a note the player reads.

**Severity: cosmetic.**

## S13. `why` hands a fogged player a source-file name
**severity: small fog leak**

norse_900ad_WEIRD: *"`why` replies carry a `"kb": "97_military.md"` field
pointing at source files I am not supposed to be reading."*

    {"cmd":"why","id":"hom_toothbrush"}  ->  "kb": "91_household.md"

Where: `rome/sim/engine/protocol.py:658`.

**Judgement: real but minor.** Under `--fog` the point is that you cannot see
the shape of the tree; a filename tells you which subject module a node belongs
to, which is a weak signal, but it is a pointer out of the game and into the
repository the player is told not to read.

**Severity: cosmetic.**

## S14. `air_compass_magnetic` is a ship's compass filed under aviation
**severity: cosmetic**

norse_900ad_WEIRD: *"a needle on a thread that points north — is in category
'aviation'. In 900 AD. It is a ship's compass."*

    {"cmd":"why","id":"air_compass_magnetic"}
      "cat": "aviation", "tier": 0,
      "note": "A magnetized iron needle on a silk thread points north. ...
               A compass in an aircraft allows navigation when landmarks are
               obscured. Mount it in a card marked with degrees."

**Judgement: real data defect.** The category also feeds `civ_domain_factor`, so
a seafaring civilisation is charged an aviation multiplier for a compass.

**Severity: cosmetic, with a small pricing consequence.**

## S15. `tl_windscreen_wiper`'s knowledge-base anchor points at a muffler
**severity: cosmetic**

han_china_100ad_BREAK: *"suggesting the content entry was cloned from another
one and not fully edited."* Still true:

    tl_windscreen_wiper  "kb": "86_transport_deep.md#tl_muffler"

**Judgement: real, trivial.** Evidence for the tester's wider point that some
entries are cloned rather than authored.

**Severity: cosmetic.**

## S16. The founder never ages, in any civilisation, unless you pass `--mortal`
**severity: the largest realism gap in the model; every tester raised it**

rome_100ad A/B/C, han_china_100ad PLAY/WEIRD, norse_900ad PLAY/WEIRD/BREAK.
norse_900ad_WEIRD's version: *"The same man was sold into debt slavery
thirty-three times and freed thirty-three times over four hundred years, and
never aged a day."*

    rome/sim/engine/core.py:133   self.life_left = (1e9 if self.cfg["immortal"] ...)
    rome/sim/engine/cli.py:957    --mortal  "turn the founder's mortality back on
                                             (default: immortal, ...)"

**Judgement: design choice, now honestly disclosed.** The machinery exists
(`founder_alive`, `dead_reason`, `life_left`, an end reason for dying) and is
deliberately switched off by default. What has changed since these notes is that
the game now says so unprompted: `state` reports `"founder_ages": false` and the
readable view prints *"You: alive (you do not age)"*. The opening text no longer
promises a mortal lifespan it does not model.

**Severity: cosmetic** now that it is stated; it was misleading before.

## S17. Ambient events take money and never say how much
**severity: misleads a player about their own ledger**

norse_900ad_WEIRD: *"'fire in the longhouses by the shore' took exactly 255
denarii off me in 926 and the message was four words with no figure."*

Where: `rome/sim/engine/society.py:547-556`

    if r.random() < 0.03:
        self.capital *= 0.82
        self.log.append((yr, "fire in the %s" % self.civ.get("fire_quarter", ...)))
    if r.random() < 0.02:
        self.capital *= 0.9
        self.log.append((yr, "banditry or a frontier war disrupts supply"))

An 18% haircut on capital, announced without a number. Confirmed in play: the
event line is `"fire in the insula district, where the tenements stand six
storeys in wood"` and nothing else.

**Judgement: real defect, and inconsistent with the rest of the file.** Two
functions further up, plague now says *"staff -%d%%, and %s denarii gone with the
trade that stopped"*, and interest says *"interest on 316 denarii of arrears at
11.8%% a year"*, both added in response to exactly this complaint. The two
ambient events were missed.

**Severity: misleads a player** who is trying to reconcile capital.

## S18. `load` accepts values no game could have produced
**severity: cheating your own game; a corrupt file still fails late**

norse_900ad_BREAK FINDING 22. Reproduced now: take a save the game wrote, set
`capital` to 1e12 and `year` to 50, and load it into a `rome_100ad` session that
starts in 100:

    {"cmd":"load","file":"doc.json"}  -> {"ok": true, "loaded": "doc.json", "year": 50}
    {"cmd":"state"}                   -> "year": 50, "capital": 1000000000000.0,
                                         "living_cost": 15000000224.0

Where: `_validate_save`, `rome/sim/engine/protocol.py` ~2495-2555.

**Judgement: mostly fixed; range checking is the gap.** Validation is now real
and runs to completion before a single attribute is touched: required fields,
`_version` type, `year`/`capital` types, civilisation match, and the shape of
`active`. What it does not check is whether the values are *possible* — a year
before the civilisation begins, a capital larger than the world.

**Severity: cosmetic.** A save file is the player's own; the value of fixing it
is that a corrupted session file fails at `load` with a sentence rather than
later with a `TypeError`.

## S19. `heard_of_but_cannot_begin` is promised and empty
**severity: misleads a player about what fog shows them**

norse_900ad_PLAY: *"`heard_of_but_cannot_begin` was **empty**, even though
fog-of-war explicitly promises 'things you have heard of but cannot yet begin'.
That stayed empty all through the opening."*

    {"cmd":"help","topic":"fog"}
      -> "ON. You can see what you have built, what you could begin today as a
          one line summary, and things you have heard of but cannot yet begin."
    {"cmd":"available"}      (year 903, four projects running)
      -> keys: ok, count, showing, subjects, cheapest_six, most_rests_on_these,
               to_see_more, note      — no heard_of_but_cannot_begin at all
    {"cmd":"available","all":true}  (year 900)
      -> heard_of_but_cannot_begin: 0 entries

**Judgement: real, small.** The block exists (`protocol.py:580`, `:628`) and does
populate later once a node has some but not all of its prerequisites. At the
opening it is empty, and in the default summary view the key is absent entirely,
so a new player is told about a feature they cannot find. han_china_100ad_PLAY's
biggest regret was not reading this field, which suggests it matters.

**Severity: misleads a player.**

## S20. `training_pending` cannot name what it is training
**severity: cosmetic**

norse_900ad_WEIRD: *"`"trade": null, "people": null` — the pending-training
display cannot name what it is training. And five people become '3.66 + 1.34
artisan capacity'."*

Where: `rome/sim/engine/protocol.py:127-131` reads `row[2]`/`row[3]` defensively
and yields null for the two-wide rows that manumission creates
(`rome/sim/engine/core.py:975-986`, the `else: self.artisans += cap` branch).

**Judgement: real, cosmetic.** Manumitted people are still trained through the
old anonymous path; hired and taught trades now carry their names.

**Severity: cosmetic.**

## S21. Message pluralisation
**severity: cosmetic**

norse_900ad_BREAK: *"'1 optician finish their training'; 'some of them go' when
all of them go; 'ABANDONED 1 works'."*

    core.py:982   "%g %s%s finish their training"      -> "1 optician finish their training"
    core.py:451   "ABANDONED %d works you could no longer maintain"  -> "ABANDONED 1 works"

The verb is not agreed; only the trade noun is. *"some of them go"* was fixed —
`auto_shed` and the creditors' seizure now name the works they took.

**Judgement: real, cosmetic.**

## S22. Numeric arguments accept strings inconsistently
**severity: cosmetic**

norse_900ad_BREAK FINDING 1's tail and FINDINGS_ROUND2 §H: *"`hire` accepts `"5"`
as a string where `buy` and `start` type-check."*

    {"cmd":"hire","trade":"labourer","n":"5"}  -> {"ok": true, "hired": "labourer",
                                                   "n": "5", "you_now_employ": 5.0}
    {"cmd":"buy","what":"forest","n":"5"}      -> "cannot afford 5 ha ..."   (accepted)
    {"cmd":"buy","what":"forest","n":[1,2]}    -> "n must be a number"       (rejected)
    {"cmd":"train","trade":"smith","n":"3"}    -> {"ok": true, ...}
    {"cmd":"start","id":123}                   -> "id must be a string, got int."

**Judgement: fixed in substance, inconsistent in form.** The dangerous half —
`NaN`/`Infinity` walking through every guard and poisoning `capital` — is
properly closed (`"n must be a real number; NaN and Infinity are not
quantities"`). What is left is that `"5"` is coerced everywhere while a list is
refused, and the reply echoes the string back untouched.

**Severity: cosmetic.**

## S23. `policy` coerces truthy non-booleans
**severity: cosmetic**

norse_900ad_BREAK FINDING 19. The dangerous case is fixed:

    {"cmd":"policy","set":{"auto_hire":"false"}}  -> "changed": {"auto_hire": false}   FIXED

The residue:

    {"cmd":"policy","set":{"auto_bribe":7}}       -> "changed": {"auto_bribe": true}

**Judgement: acceptable.** `7` is not a plausible attempt to switch something off
the way the string `"false"` was. Listed for completeness.

**Severity: cosmetic.**

## S24. There is no way to start a new run from inside the program
**severity: friction**

norse_900ad_WEIRD: *"Once `ended: true` is in the session file, every command
refuses forever. The only way to play again is to delete the program's save file
from outside the program."*

`{"cmd":"nosuchcmd"}` now lists 26 commands (the round-one complaint that the
error listed 10 while `help` documented 24 is fixed); none of them is `restart`
or `new`. `rome/sim/simulator.py menu` is the front door added since, which is
probably the intended answer.

**Judgement: design choice, with a documentation gap** — the ended-run refusal
does not tell you where to go next.

**Severity: cosmetic.**

## S25. `why <unknown id>` replies "did you mean: no idea"
**severity: cosmetic**

rome_100ad_BREAK: *"reads like a debugging placeholder/joke rather than a real
suggestion (compare `start`'s much more useful unknown-id message)."*

    {"cmd":"why","id":"nonexistent_zzz"}
      -> "unknown node 'nonexistent_zzz'. did you mean: no idea"

**Judgement: real, cosmetic.** It is a joke, and it lands, but it is the reply
to the most common typo in the game.

## S26. `PROTOCOL.md` still describes bounty by the old rule
**severity: cosmetic documentation drift**

`rome/sim/PROTOCOL.md:69` — *"post a public prize instead of building it yourself
(tier <=2 crafts only ...)"*. The rule in `projects.py:107` is tier ≤ 2 **and**
(a category allow-list **or** the civilisation being measurably good at it).
norse_900ad_BREAK FINDING 15 caught the discrepancy in its older form.

**Judgement: real, cosmetic.** Same document, `--manual` section, also still
promises *"Nothing becomes active except what start_project() was explicitly told
to start"*, which is contradicted by the zero-cost society diffusion in S8.

## S27. `save` with a relative path writes wherever the process was launched
**severity: cosmetic**

norse_900ad_WEIRD: *"My first `{"cmd":"save","file":"SAVEPOINT_921"}` dropped a
file into the repository root."* The dangerous half is fixed:

    {"cmd":"save","file":"/etc/zzz_probe.json"}
      -> "a save file must be a relative path, not an absolute one."
    {"cmd":"save","file":"relative_probe.json"}
      -> {"ok": true, "saved": "relative_probe.json"}   (lands in the CWD)

(I removed the probe file; the repository is clean.)

**Judgement: acceptable behaviour, now that absolute paths are refused.**

## S28. Cheap business nodes still repay in under a year
**severity: balance; the game stops asking questions**

norse_900ad_PLAY's central complaint: *"A horizontal loom that pays for itself
three times over every year is not an economy, it is a money printer... I think
this is the single biggest balance problem in the game."* And: *"From about year
905 to the end I never once had to choose between two things I wanted."*

Reproduced now, `norse_900ad`, one node:

    {"cmd":"why","id":"tex_horizontal_loom"}  -> cost 323.4, upkeep 30.0, revenue 400.0
    {"cmd":"start",...}  {"cmd":"step","years":6}
    {"cmd":"money"}      -> where_the_money_comes_from: {"tex_horizontal_loom": 409.0,
                                                         "med_cataract_couching": 170.4,
                                                         "med_trepanation": 68.2}
                            revenue 232.7 -> 641.4

One 323-denarii project raises annual income by 379 net, permanently.

**Judgement: design/balance, not a bug**, and the tester's own diagnosis is the
right one: *"the fix is not more hazards, it is making revenue nodes compete."*
Two round-one balance outliers of the same family have been properly fixed —
`el2_sonar_acoustic_detection_ranging` went from 15,000/yr revenue to 163.3, and
`fin_seigniorage` from 1,000/yr to 16.7 — so the sweep of outliers happened; the
general shape did not change.

**Severity: no state harm; it flattens the game.**

## S29. Quoted revenue is not first-year revenue, and nothing says there is a ramp
**severity: cosmetic**

norse_900ad_PLAY: *"`why tex_horizontal_loom` promised revenue 400.0, but
`where_the_money_comes_from` afterwards lists it at 272.6. Something scales the
quoted number down and nothing says what."*

Still true in kind, much smaller in degree: the loom ramps to 409.0 over about
three years against a quoted 400.0, so the end state now slightly *exceeds* the
quote. The first year still does not match it, and `why` does not mention a
ramp-in.

**Judgement: real, minor.**

## S30. `step` cannot advance less than a year, so sub-year calendar floors are unobservable
**severity: cosmetic**

rome_100ad A: *"`step` refuses fractional years below 1 even though plenty of
projects have a `least_years` well under 1 (0.0, 0.1, 0.3...). You can never
actually watch one of those complete on its own timeline."*

    {"cmd":"step","years":0.5}
      -> "years must be a whole number of years; 0.5 is not. Nothing was changed."

**Judgement: design choice.** The turn is a year; the message now says so
clearly rather than the old bare `"years must be >= 1"`. Listed because the
`least_years` field advertises a granularity the clock does not have.

## S31. Fractional people are still displayed
**severity: cosmetic, now explained**

FINDINGS_ROUND2 §D: *"1.32 artisans, 0.07 engineers... Either say what a fraction
of a person means or do not show one."*

    {"cmd":"labour","trade":"smith"}  -> "you_employ": 0.9,  then 0.81 three years later

**Judgement: fixed in the way the tester asked for.** `state` now carries
`staff_are_fractional_because`, which says: *"these are continuous full-time-
equivalents, not a count of whole people: hiring phases in, training takes years,
and attrition (about 3.5%/yr) trims everyone a little rather than dismissing one
person at a time. 1.32 artisans is the wage and output of one artisan plus a
third of another's."* Listed only because the fractions themselves remain.

---

# PART 2 — FIXED

Verified not to reproduce. Grouped by what they were.

### Catastrophic, and gone

**F1. `--session` reload permanently bricked the save.** rome_100ad A, C and
BREAK; BREAK reproduced it 3/3 and 8/8. `{"cmd":"state"}`, then a second process
against the same file, gave `TypeError: type NoneType doesn't define __round__
method` — and `available` gave `'>=' not supported between instances of NoneType
and int` — for ever after, with the message *"The game is intact; try something
else"*, which was false. Two testers abandoned the documented workflow and drove
the game through a FIFO instead. Now: two consecutive processes against one
session file both answer normally. The cause and the fix are documented in
`load_state`, `rome/sim/engine/protocol.py`: *"NEVER restore a null over a live
default... A naive tester hit this on the very first save-and-restart."*

**F2. A failing `step` minted money for ever.** rome_100ad_BREAK FINDING 3: 12
consecutive `ok: false` steps added +811 denarii while `save` proved the year
never moved. It was a consequence of F1 and cannot arise now.

**F3. `NaN`/`Infinity` poisoned `capital` and wrote invalid JSON into the save.**
norse_900ad_BREAK FINDING 1. Now: `{"cmd":"hire","trade":"labourer","n":NaN}` ->
`"n must be a real number; NaN and Infinity are not quantities. Nothing was
changed."`

**F4. Deficit was an unrecoverable softlock.** norse_900ad_BREAK FINDING 18, the
one the tester said he would fix first: at a deficit of -148/yr the engine
destroyed eleven works earning 2,700/yr, kept `workshop_first` (900/yr upkeep, 0
revenue) and `identity_cover`, ignored `auto_shed: false`, and refused to
mothball the thing causing it. `rome/sim/engine/core.py:428-451` now sheds only
`up > rev` works, honours the switch, stops when shedding stops helping, names
what it took, and adds it to `mothballed` so `restore` can buy it back. The
comment in place records the tester's verdict verbatim.

**F5. `auto_shed` destroyed the profitable estate.** norse_900ad_BREAK FINDING 17,
same fix.

**F6. Repossession made the founder forget things he knew.** FINDINGS_ROUND2 §C.
`enforce_credit_limit` (`economy.py:212-238`) now only takes works whose upkeep
exceeds their revenue, so a pure-knowledge node with no upkeep can never be
seized, and what is taken is mothballed rather than erased.

**F7. Silent slave acquisition.** rome_100ad B and C: slaves appeared with no
command and no log line, repeatedly, in direct contradiction of the game's own
stated reason for modelling slavery. `core.py:459-470` now gates it behind the
`auto_buy_people` policy, off in manual mode, and logs *"bought %d people for
the workshop"* when it does fire. The code comment quotes the tester.

**F8. `buy mine` took every denarius you had and delivered nothing.**
han_china_100ad_BREAK FINDING 4, norse_900ad_WEIRD "Exploit 4", norse_900ad_BREAK
FINDING 16, FINDINGS_ROUND2 §L. A gold mine cost 38,151 in one command, returned
`ok: true` with `commissioned_t_per_yr: 0.0` and *"Nothing was wasted"*, never
appeared in `state`, and charged 28.1/yr for ever with no way to close it. All of
it is fixed:

    {"cmd":"quote","what":"mine","material":"coal","n":50}
      -> "to_sink_it": 630.0, "every_year_it_stands": 105.0,
         "years_before_it_produces": 3.0, "you_can_afford_about": 262.307,
         "note": "The yearly cost is charged whether or not you use the output,
                  and goes on until you close it."
    {"cmd":"buy","what":"mine","material":"gold","n":1}   (400 capital)
      -> "1 tonnes a year of gold costs 224,000 denarii to sink and you have 400.
          Nothing was changed - ask for what you can pay for, or check the price
          first with {"cmd":"quote",...}"
    {"cmd":"close","material":"coal"}
      -> "the coal workings are closed. You stop paying 105 a year."

`ready_year` is now populated (911.0 for a 3-year sink) rather than `null`.

### Fog of war

**F9. `start` was a free prerequisite oracle for undiscovered nodes.**
norse_900ad_BREAK FINDING 4 crawled 163 nodes — the whole ancestor closure of the
goal — from one seed with a 20-line script. Now: `{"cmd":"start","id":
"point_contact_transistor"}` -> *"you have never heard of that."*

**F10. A locked node's name and description leaked through a downstream node's
prerequisite list.** rome_100ad A: `corpus_dispersed`'s `why` named and described
`printing_press` in full while `why printing_press` was refused.

**F11. `state` named `corpus_dispersed` as the better hedge while `why` denied
knowing it.** rome_100ad A, B and C.

**F12. The advice strings named nodes the game said you had never heard of.**
norse_900ad_PLAY (*"the single most confusing thing in the game so far"*) and
BREAK: `how_to_grow_staff` recommended `workshop_first`, `freedman_staff`,
`school_founded`, `academy_network`, and `why` on each replied *"you have never
heard of that."* `{"cmd":"labour"}` now returns commands, not node ids:
*"To get more artisans: {"cmd":"hire","trade":"smith","n":3} or any trade in
{"cmd":"labour"}; or {"cmd":"commission",...}"*

**F13. The run ended on a goal the game said did not exist.** norse_900ad_PLAY
called this *"the biggest problem in the game"*: `"goal": null, "goal_reached":
false` for 362 years, the welcome text saying *"There is no score but the state
of what you have built"*, and then a hard stop 138 years early. Now the goal is
stated everywhere from turn one — `state` carries `"goal_in_words":
"Point-contact transistor"`, `help` says *"Build point-contact transistor, before
the horizon at 1400"*, and the readable view prints *"Aiming at: Point-contact
transistor"*. `state.goal` is still deliberately null under fog
(`protocol.py:228`) so the node *id* stays hidden; the name does not.
han_china_100ad_PLAY's *"'Without reaching the goal' is a strange note to end on
when I was never offered a way to set a goal"* is answered by the same change.

### Anachronism and civilisation data

**F14. Twentieth-century content startable in antiquity with no prerequisites.**
The single most-reported family across both rounds:

- `sc2_physics_nuclear_fission`, completed **in 103 AD** by rome_100ad_BREAK
  (FINDING 5) for 252 denarii, one scribe and 140 hours, `direct_prerequisites: []`
- `sc2_physics_wave_mechanics`, `sc2_statistics_anova`,
  `el2_photomultiplier_single_photon` — rome_100ad_BREAK FINDING 2
- `el2_sonar_acoustic_detection_ranging` — rome_100ad_WEIRD's headline finding
- `mil_atomic_bomb` in 978 for 341.6 denarii — norse_900ad_PLAY
- `mil_chemical_mustard`, `mil_trench`, `mil_general_staff`,
  `mil_trace_italienne` — FINDINGS_ROUND2 §B
- `mil_plate_armour_firearms` in 900 AD — norse_900ad WEIRD and BREAK
- `fud_chinampa` in Norway, `ag2_maize_newworld`, `ag2_potato_newworld` — §A/§B
- `tl_windscreen_wiper`, `mil_naval_mine`, `in2_joule_thomson_valve`,
  `tx2_corrugated_box` in Han China — han_china_100ad_BREAK FINDING 1

All verified gated now. `mil_atomic_bomb` needs `sc2_physics_nuclear_fission`,
`mt2_uranium_thorium_extraction` and `in2_ultracentrifuge`; `mil_chemical_mustard`
needs `mat_chlorine`, `mat_sulfur`, `mil_artillery_shell`; `mil_trench` needs
`mil_machine_gun_recoil`; `mil_plate_armour_firearms` needs `mil_matchlock`;
`fud_chinampa` needs `exp_americas_factory`; the New World crops need
`exp_atlantic_crossing`. Turn-one `available` fell from 299/250 items to 75/85,
and `why sc2_physics_nuclear_fission` in year 100 now replies *"you have never
heard of that."*

**F15. Six to nine nodes cost 0.0 money, 0 hours and 0 years.** FINDINGS_ROUND2
§A, norse_900ad WEIRD ("Exploit 1") and BREAK (FINDING 3): starting all six and
stepping twice took reputation 5.0 -> 11.7 and the credit limit 1,912.9 -> 4,276.9
for nothing. Now zero free nodes in either civilisation's opening list; the arch
costs 1,017.8.

**F16. ~139 "ROME ALREADY HAS THIS" grants dumped on the first `step`.**
rome A/B/C/WEIRD, han_china BREAK/PLAY/WEIRD. Turn-0 `state` undercounted by 128
and the first `step` returned a 139-entry `completed` array. Now turn 0 reports
`done_count: 137, done_granted: 137` before any command, and the first year adds
two by diffusion.

**F17. Revenue appeared from nothing.** rome_100ad_WEIRD: *"666.7/year of
revenue... with zero buildings, zero trade, zero mines... no in-fiction source
for it."* Now turn-0 revenue is 233.5, and `{"cmd":"money"}` itemises it:
`where_the_money_comes_from: {"med_cataract_couching": ..., "med_trepanation": ...}`.

**F18. `[AUDIT: ...]` developer annotations shown as flavour text.**
han_china_100ad WEIRD ("the single most 'unrealistic' thing I found") and PLAY.
The 398 annotations now live under an `_internal` key that `_node_explain` never
returns; `water_power_scale`'s player-facing note is clean.

**F19. "Fire in the insula district" in a Han or Norse game.** Each civilisation
file now names its own quarter (`fire_quarter`), and the code comment credits the
Han tester who counted nine of them in Luoyang.

**F20. Rome-flavoured labour notes throughout a Norse game.** *"Rome has these in
abundance and they are good"* (mason), *"Rome has military and hydraulic engineers
under state employ"* (engineer). Rewritten generically.

**F21. The bounty refusal cited "a Roman artisan" in a Norse game, and refused
shipbuilding.** norse_900ad_BREAK FINDING 15. Now: *"not bounty-eligible (tier 1,
category personal): a craftsman in Scandinavia in the Viking age could not
recognise success at this..."*, and `sea_skeleton_first` is accepted.

**F22. A hazard could only be four numbers, so Christianisation was a no-op.**
FINDINGS_ROUND2 §P; norse_900ad WEIRD and PLAY both lived through 995-1100 twice
and saw nothing. `_shocks` (`society.py:495-520`) now applies a `values` delta,
spread evenly across the hazard's years, and `norse_900ad.json` carries
`"values": {"w_religious_rigidity": 0.45, "w_magic_fear": 0.35, "w_novelty": -0.2}`
for Christianisation plus a second hazard (the Norwegian civil war era) that did
not exist.

### Numbers that did not add up

**F23. The `why` cost breakdown was short by exactly 1.4x.** norse_900ad_BREAK
FINDING 2, verified across seven nodes; diagnosed in FINDINGS_ROUND2 §J as
`_node_explain` printing `money_real` in a field labelled `price_index`. Now the
breakdown reconciles: `hom_toothbrush` shows `base_total 30.3 x civ 1.0 x
distance 1.0 x opposition 1.0 x price_index 1.4 x purchasing_power 1.0 = 42.4`,
and `purchasing_power_of_the_coin` is a separate, correctly named field.

**F24. `project_spend_last_year` was ~89x too large and never refreshed.**
han_china_100ad_BREAK FINDING 5: 16,354.2 reported against a project ledger of
184.0 and a capital movement of 400, then frozen at 16,354.2 after the project
completed. Now traced clean: start `fin_inn` (bill 5,579.1), step one year ->
`project_spend_this_year: 1557.6`, `active.fin_inn.spent: 1557.6`, capital
400 -> -1149.9; step again -> `project_spend_this_year: 0.0`.

**F25. `capital` sat at exactly 0.0 for years while net figures were positive.**
rome_100ad A and C. Capital is no longer floored at zero; it goes negative and
accrues interest, which is reported.

**F26. `founder_hours_left` went negative and stayed negative** (-776.8, -1,250).
norse_900ad PLAY and BREAK FINDING 9, rome_100ad B (-1,200 on `corpus_written`).
`core.py:726` is now `st["ph_left"] = max(0.0, st["ph_left"] - per)`.

**F27. Founder hours were double-spent between `work` and projects.**
norse_900ad_BREAK FINDING 8/8b — *"I had zero hours left for the year — `work`
said so itself — and the project still consumed 50 of them"* — and WEIRD
("Exploit 6"), which got 4,650 hours out of a 2,400-hour year. Now:

    {"cmd":"work","trade":"labourer","hours":100}  -> "your_hours_left_this_year": 2300.0
    {"cmd":"work","trade":"scholar","hours":2400}  -> "you have 2300 of your own hours
                                                       left this year, not 2400"
    {"cmd":"state"}  -> "founder_hours_available": 2300.0

and a new `hours_this_year` block reports `{available, wage_work, teaching,
offered_to_projects, effective_on_projects, unused}`.

**F28. `train`, `work` and `state` gave three different answers for the same
year's hours.** norse_900ad_WEIRD ("Exploit 2"). Same fix; teaching hours are
committed hours now.

**F29. `interest_paid_total` decreased** (1,096.7 -> 443.5 -> 0.0).
norse_900ad_WEIRD. `economy.py:181` only ever adds to it and it is a save field.

**F30. Projects stalled `waiting_on: "money"` with 2.3 denarii to pay while
capital was 696,350.** norse_900ad_PLAY. Diagnosed in the code
(`core.py:764-776`): the trades were fully booked, so almost nothing could be
paid *for*. The mechanic was right and the label was wrong; there is now a
`short_of_trade` field and `waiting_on` reads *"nobody to do the work: <trades>"*.

**F31. Four projects each showed exactly half their founder hours left with no
explanation.** FINDINGS_ROUND2 §F. Answered by `hours_this_year` and the
per-project `hours_offered_this_year` / `hours_effective_this_year` /
`why_underfunded` fields.

**F32. Reputation slid from 10 to 0.2 over a century and a half with no event
ever explaining it.** rome A, B, C and han_china PLAY. `core.py:922-931` now
decays toward a `standing_floor()` rather than to zero, and the comment names the
three testers who reported it.

### Labour and the market

**F33. You could be paid to work as an engineer, chemist, electrician, machinist
or optician in the year 900**, in trades `labour` said did not exist — and
`engineer` was the best-paid job in the game. norse_900ad_BREAK FINDING 6. Now:
*"nobody here will pay you to be a engineer: the trade does not exist in this
society, so there is no employer for it. Teach it first with train."* (The
article is still "a engineer".)

**F34. Wage arbitrage: work as a scholar for 1,416/yr, hire one for 625.**
FINDINGS_ROUND2. Both sides read the same table.

**F35. `train` bypassed the supervision cap and pumped the labour market without
limit** (smith supply 6,469 -> 36,433). norse_900ad_BREAK FINDINGS 12 and 13.
`train` now charges a real feeding fee — *"you must keep them fed while they
learn: 1489 denarii, and you have 164"* — and literate trades are bounded by the
society's literacy: *"this society's literacy will not supply more than 5.9
scholars in total, ever, at any price."*

**F36. The `hire` cap error offered `hire` as the remedy for being unable to
hire.** norse_900ad_PLAY. Replaced by the literacy message above, which names a
different lever (printing, schools, libraries).

**F37. Scholars were pinned at 1.0 for 500 years with no way to grow them.**
han_china_100ad_PLAY. `hire trade:scholar` exists and is bounded by literacy.

**F38. "IN ARREARS: staff are leaving" while `employees_total` was 0.**
norse_900ad_PLAY. The arrears message now fires on a threshold tied to actual
staff attrition, and `staff_are_fractional_because` explains the 3.0-artisans-
with-no-employees case.

### Guards and validation

**F39. `step years: 100000` was accepted and silently ended the run.**
norse_900ad_WEIRD: *"The single most destructive input in the game has no guard
on it at all."* Now: *"there are only 500 years left before the horizon at 1400.
Ask for 500 or fewer."*

**F40. `step years: true` stepped one year.** Now: *"years must be a number, not
true or false."*

**F41. `bribe` worked after the run had ended.** norse_900ad_BREAK FINDING 7. Now
refused with the end reason. Bribing away 0.00 scandal is also no longer nothing —
it buys protection, and the reply says so, or says *"you had no scandal to answer
and are already as protected as money can make you, so this bought nothing."*

**F42. `policy` read the string `"false"` as true.** norse_900ad_BREAK FINDING 19.

**F43. `save` wrote to any absolute path, confirmed into `/etc/`.**
norse_900ad_WEIRD. Now refused.

**F44. `buy forest` refused without quoting the price.** norse_900ad_PLAY. The
`quote` command covers forest and mine, and the mine refusal states the price.

**F45. The "unknown cmd" error listed 10 commands while `help` documented 24.**
norse_900ad WEIRD and BREAK. Now lists all 26.

**F46. `available` returned one huge object** — 299 entries at the start, 186
real ones mixed with 113 zero-cost background facts, and no upkeep or revenue on
any line, so *"under fog you must `why` all 86 nodes one at a time"* to avoid a
permanent liability. rome A/B/C, norse WEIRD (§27), FINDINGS_ROUND2. Now a digest
by subject, and every line carries `earns_per_year` and `costs_per_year_after`:

    {"id": "hom_toothbrush", ..., "earns_per_year": 30.0, "costs_per_year_after": 40.0}

**F47. There was no human-readable view.** FINDINGS_ROUND2 §I/§N, asked for by
two testers. `simulator.py play` now takes plain words on stdin and prints a
formatted board.

---

# PART 3 — UNCLEAR, or the tester was misreading

**U1. "Stepping time completes 128 technologies for free, contradicting the
game's own rule 'Nothing happens until you make it happen'."**
han_china_100ad_BREAK FINDING 2 and WEIRD §2, norse_900ad_PLAY. Half real, half
misread. The bulk grant was real and is fixed (F16). The residue — a couple of
zero-cost nodes completing each year without being started — is society
diffusion, correctly modelled and correctly counted as `done_granted` rather than
`done_earned`. It is only a defect insofar as `completed` does not say which it
is (S8) and `PROTOCOL.md` claims otherwise (S26).

**U2. "The Pharos lighthouse is marked `done` for a Han Chinese founder."**
han_china_100ad_BREAK. Not a bug: `done_granted` means the society has it, not
that the founder built it. The tester's real complaint stands and is fixed
elsewhere — the *content* was Roman in a Han game (F19, F20), and the word
`done` did not distinguish the two (S8).

**U3. "The tech tree is mostly flat; three hub nodes matter and `available` gives
you no way to spot them."** rome_100ad C. `available` now carries
`how_much_rests_on_this` per line and a `most_rests_on_these` block, so the
information exists. Whether the tree is too flat is a design question the notes
cannot settle from outside.

**U4. "The session file ended up in a half-written, crash-looping state after I
killed the driver mid-command."** rome_100ad C flagged this as possibly the
tester's own plumbing. It was almost certainly F1 rather than a torn write, and
F1 is fixed. Atomic save writes were never confirmed either way; not retested.

---

# The three worst still-present findings

1. **S1** — `save`/`load` is unlimited undo, so a fogged run can be rewound from
   its own terminal state. Fog of war is the mode's whole premise and two
   commands switch it off.
2. **S2** — buying three people and freeing them yields 6.0 artisans at a zero
   wage bill and a reputation bonus, making manumission strictly the best labour
   strategy in the game and inverting the model's own stated reason for including
   slavery at all.
3. **S6** — `rubber_kg` is priced at a 99,999/kg sentinel whose own note says
   "there is no route", but the sentinel is undisclosed in `why` (so a tourniquet
   reads as a 210,340-denarius unit error) and unenforced by the tree (so a rich
   player buys American rubber in the second century). Twenty-two nodes are
   affected.

Runners-up, all in the same family as each other: **S3**, **S4** and **S5** are
three separate fields that state as fact something the object printed beside them
contradicts.
