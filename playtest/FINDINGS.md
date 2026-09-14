# Playtest findings, and what was done about them

One row per finding that changed the code or the documents. Countries are played
one at a time, three testers each: one trying to win, one hunting bugs, one
being deliberately strange.

The rule for this file: a finding is only closed when the fix is verified by
reproducing the tester's exact commands. "Probably fixed" is not closed.

---

## Rome, 100 AD

### Fixed

| # | Finding | Severity | What was wrong | Fix |
|---|---|---|---|---|
| W1 | Buy people, free them instantly, get labour and reputation from money | EXPLOIT | `buy_slaves` added 0.55 artisans per person and `manumit` added another 0.55 for the SAME person. One human yielded 1.1 workers. | Manumission raises the same person 0.55 to 1.0, so it adds 0.45. |
| W2 | Flat price at any volume | EXPLOIT | 300 den each whether you bought 1 person or 3,333. | Price rises against local market depth. That purchase now quotes 43.9M and is refused. |
| W3 | Purchased people were productive instantly | EXPLOIT | Ten bought and freed became eleven trained artisans in the same tick, with no founder hours. It strictly dominated `freedman_staff`, which models the same thing at 900 founder hours and two years. | Three year training lag before they count. |
| W4 | Manumission reputation had no ceiling | EXPLOIT | Out-earned taking a patron. 240 people minted 96 reputation. | Saturates; the same 240 now yield 25. |
| B1 | **Money from nothing** | BUG, severe | `buy forest n:-5` returned `ok:false` and moved capital 400 to 1,650. Negative quantity made a negative cost, which passed the affordability test, credited the money, and only then reported failure. | One guard at the top of the dispatcher, before anything is touched. |
| B2 | **A malformed command killed the session** | BUG, severe | `{"cmd":"why","id":{"a":1}}` died on an unhashable-type TypeError and took the process with it, losing the whole game. Five id lookups had the same hole. | One central guard. A bad command costs you the command, never the game. |
| B3 | Money vanished with no explanation | CONFUSING | Capital fell 400 to 184 on the first step with nothing active and revenue and upkeep both reported zero. It was living cost, always charged, never shown. | `state` reports `living_cost`, `mine_operating_cost`, `net_per_year`, `training_pending`. |
| B4 | `step` silently no-opped after game over | CONFUSING | Indistinguishable from a working game that had stopped progressing. | Says so, and points at `state`. |
| W5 | The eminence mechanic was undocumented | CONFUSING | A tester was killed by "too eminent", went looking, and `grep -rn "eminen"` returned nothing across the whole knowledge base. The module listed exactly three ways to die and the game had four. | Fourth threat written up in `03_SOCIAL_POLITICS.md`, including that every other defence in that module is a shield and this hazard is caused by the shields working. |
| W6 | `done_count` credited players with work they had not done | CONFUSING | 139 "the society already has this" nodes complete in year one and were counted identically to earned ones. | Split into `done_granted` and `done_earned`. |
| N1 | **The protocol showed one graph while the guide insisted another governs you** | CONFUSING, the best finding of the batch | The WIN tester read the warning about the Third Century Crisis, then reasonably skipped the academies because `path` said, correctly, that no academy is a technical prerequisite of a transistor. They lost 25 technologies in one year, 24 nine years later, 16 after that. The risk existed only as prose, attached to the mitigation rather than to anything visible while deciding. | `state` carries `knowledge_risk`: technologies exposed, chance per sacking, fraction lost, expected number, current hedge, better hedge, and dated hazards ahead. |
| N2 | A staff wall halted everything and the refusal named the shortfall, not the remedy | CONFUSING | Staff is not a technical prerequisite so it never appears in `path`. The player had no way to discover the answer. | Refusals now name the nodes that produce scholars and artisans, and the buy-and-manumit route with its training lag. |

### Not fixed, with reasons

| Finding | Why not |
|---|---|
| ~~`start` does not check affordability~~ | **I was wrong, and the naive round proved it.** I closed this saying projects are paid progressively and you stall if the money runs out. They were not, and you did not: the yearly charge was clamped at whatever you happened to have, and completion tested hours and calendar only, so the rest of the bill was forgiven. A tester finished a 4,361 denarius balloon having paid 984 of it; another started 93,690 denarii of work against 6,415 in the treasury and finished six of the seven. Money was decorative and only hours were real. Fixed properly in the naive round below: a project now carries a bill and cannot complete until it is paid. |
| Negative capital has no bankruptcy floor | By design. Mines mothball automatically when you cannot pay, which is the safety valve, and the WIN tester marked that WORKS-WELL. |
| The founder never dies | The default is an immortal founder; `--mortal` turns it on. The briefing oversells survival as central, which is a documentation problem rather than a model one. |
| Calendar floors overrun by 2 to 4x | Reported as unconfirmed by the tester. Under investigation. Floors are minimums, and throttling by money, staff or materials legitimately extends them, but the size of the overrun deserves checking. |

### Results

| Role | Outcome |
|---|---|
| WIN | Reached the transistor in **458 AD**, 358 years, playing straight through the protocol. The optimizer's median is 348 to 363, so a player choosing their own path does about as well as the planner. That was the single most reassuring result of the batch. |
| BREAK | Two severe bugs, two transparency bugs, and four things it attacked hard and could not break. |
| WEIRD | One compound exploit worth four fixes, plus the undocumented death. |

### A note on process

The first WIN attempt was killed by a rate limit and produced no report at all,
while its parting message claimed it had reached the transistor in year 226.
That claim was discarded rather than reported: no file existed, and 126 years
would have been three times faster than anything recorded. Every tester since is
told to write the report file FIRST and append as it goes.

---

## The naive round: no briefing, no commands, fog on

Eight testers across Rome and Han China, told only that this is a civilisation
simulator and where the file lives. No protocol document, no examples, no hints
about what to look for. This round found more than the briefed one did, and most
of it was structural rather than incidental.

### Fixed

| # | Finding | Severity | What was wrong | Fix |
|---|---|---|---|---|
| M1 | **A project completes whether or not it was ever paid for** | BUG, the worst in the model | The yearly charge was clamped at your balance and completion tested hours and years alone. 4,361 denarii of balloon for 984 paid; 93,690 of projects started against 6,415 in hand, six finished. | Projects carry `cost_left`. Nothing completes until the bill is paid; you can spend into debt as far as somebody will lend, and no further. `state` says what each project is waiting on: your hours, the calendar, or money. |
| M2 | **People appeared in the household that nobody bought** | BUG, and against the model's own stated principle | A tester found 20 slaves they had never bought, then 24 more after ten untouched years, with no prompt and no line in the log. As they put it, the game's justification for modelling slavery at all is that hiding it lies about the cost of everything. | You arrive with nobody. Buying people is a policy switch, off for a player, on and logged for the unattended optimizer. |
| M3 | You were handed three artisans on arrival | REALISM | A floor of four craftsmen that no one hired and no one paid. | Zero employees, zero slaves. Hire by the year, buy a single job, teach a trade, or buy a person. All of it explicit. |
| M4 | Every skilled trade was the same person | REALISM | A skilled smith and a skilled scribe were one number. The wage table has said otherwise in its own notes all along and nothing read them. | Per-trade staff and per-trade market supply. Trades that do not exist here (engineer, machinist, chemist, optician, electrician) must be taught into existence out of your own hours, and the machinists you made are no use when you need a chemist. |
| M5 | No way to shed the upkeep of a finished work | BUG | Three testers hit this from the same direction: deep in debt, the only lever offered was to start MORE things. `stop` only cancels work in progress. One wrote "your agency basically disappears". | `mothball <id>` and `restore <id>`. |
| M6 | Automatic behaviour with no switch | CONTROL | Staff growth, buying people, manumission, mining, woodland, mothballing, shedding, bribery all happened on their own. | `policy`, with a switch for each and a manual command for each. |
| M7 | Hazards were weather | MODEL | The plague arrived on the year you were told it would and nothing you could build changed it. | Gold and silver you dug against debasement; walls, firearms, powerful friends and dispersed copies against a sacking; clean water, quarantine and inoculation against a plague; land and your own power against a war. `state` says what you already take off each hazard and what kind of thing would help. |
| M8 | `downstream_count` under fog | SPOILER | "Slightly cheaty", said one tester unprompted. Two others found the three hub nodes by calling `why` on guesses and reading the number, and said the game was solved after that. | Under fog it is a phrase, not a number: "almost everything" down to "nothing else; this is worth having for itself". `chain_size`, `chain_cost` and `critical_path_years` are hidden too, for the same reason. Exact figures remain with fog off. |
| M9 | Reputation drained to zero for no stated reason | MODEL | 10.5 to 0.2 over 150 years with no logged cause. "Less like a lever I could manage and more like a clock running out." | It decays toward what you are actually known for, not toward zero: a corpus in three libraries, a school, a senator who will receive you. |
| M10 | Roman institutions in Han China | REALISM | `citizenship` sat in a Han tester's list for 500 years; the annona and the argentarii with it; and the fire was in the insula district of Luoyang. | Each society names its own crowded quarter. Foreign institutions are not granted free. And `citizenship` turned out to be the harder problem, below. |
| M11 | Where does the money come from? | LEGIBILITY | Asked three times, answerable by nobody. It was the physician's practice, which is the cover identity the game tells you to adopt. | `state` itemises revenue by source. |
| M12 | The founder never dies, in a game about one lifetime | REALISM | Still true, and still the default, but `state` now says `founder_ages: false` rather than leaving testers to infer a mortality system that was switched off. |
| M13 | An institution of a different society could not be built, including by societies that had one | BUG, mine, from the fix for M10 | Blocking anything with "collegium" in the name cut Han China off from the licensed association, the school, the endowment, the academy network and both patronage tiers. It finished 156 of the 168 nodes the transistor needs and failed for want of eighteen craftsmen it had 320 million denarii to hire. | The tree called legal standing "Roman citizenship by grant". It is now what it always modelled, and names the Han household register, the free man's standing at the thing, the burgess of a borough and the calpulli alongside provocatio. |

### What it cost, and what it bought

Enforcing payment made everything slower, and the numbers that had been reported
before were partly an artefact of the bug. Rome used to reach the transistor in
a median 315 years; it now takes 312 to 325 under an economy where the money
actually leaves. The difference is smaller than expected because two things
landed at the same time: a standing staff now costs wages, and a standing staff
now produces and sells, which it always did implicitly inside node revenue.

All five civilisations reach the transistor in every run, in an order that says
something about them: Rome 312 years, Han 331, Mexica 372, England 377, Norse
405. The poorest and smallest takes a century longer than the richest and
largest, which is the result the whole civilisation model exists to produce.

### Not fixed, with reasons

| Finding | Why not |
|---|---|
| `step` will not advance less than a whole year | The engine steps in years throughout. Projects with a floor under a year still complete; you cannot watch them do it. |
| The founder is immortal by default | Deliberate, and `--mortal` turns it on. Now reported in `state` rather than left to be discovered. |
| Capital reads one year behind revenue | True and now stated: the rate fields describe the year about to happen. |
