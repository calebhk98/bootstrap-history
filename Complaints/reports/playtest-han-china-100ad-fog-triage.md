# Triage: Han China 100 AD fog playtest (poor_scholar kit, 100 AD to 400 AD, goal reached 399 AD)

Inputs (verbatim): `playtest-han-china-100ad-fog-tester-notes.md` (223 numbered items; "T" numbers below are the tester's own) and `playtest-han-china-100ad-fog-yearly-journal.md` (a yearly diary that mostly repeats the notes; its extra observations are folded into the rows). The tester played a blind, immortal Later Han founder with fog on, `poor_scholar` kit, 500-year horizon, and won the junction-transistor goal in 399 AD (299 years elapsed, about 1,000 technologies, 1,860 employees, 838 billion cash). They may have played an older build.

Every "reproduces" below was checked on branch `china-fog-playtest-triage` (fast-forwarded to the merge of `playtest-feedback-and-fixes`, HEAD 23b6480 or later) with `python3 sim/simulator.py play --civ han_china_100ad --kit poor_scholar --fog --seed 1 --session <file>`, or by reading the data or code, or with the test harness (`sim/tests/harness.sim`), as each complaint states. "Untested" means it needs a late game that was not played forward here. Only files under `Complaints/` changed.

Filed as new: 217 to 249 (33 complaints). "Also reported" paragraphs appended to: 72, 79, 90, 93, 96, 97, 99, 100, 101, 114, 116, 125, 126, 127, 128, 151, 169, 176, 178, 180, 184, 185, 194, 196, 197, 199, 202, 204, 205, 208, 216, 235, 244 (complaints 184 and 194 included, as allowed).

## New complaints

| # | Title | Reproduces now |
|---|---|---|
| 217 | `available` mixes a topic with paging and filter words unpredictably; `all:true` ignores `limit` | Yes |
| 218 | `why` quotes one failure loss and a failure charges another (Han pays about twice the quote on its strong domains) | Yes (computed from the two code paths) |
| 219 | `stuck` names a concern as the best to open that `open` refuses for want of a foreman | Yes |
| 220 | `hire`, `open` and `commission` spend cash that is neither previewed nor itemised in the reply | Yes |
| 221 | `close <concern>` and `quote <not a purchase>` answer with the mine parser's error | Yes |
| 222 | `recurring` net includes the one-time hiring-advance credit | Yes |
| 223 | "No concern ever closed for want of staff" achievement reads current state, not history | Yes (code) |
| 224 | Victory is not an ending; the fogged score total stays withheld; no finish-and-score action | Yes (code, by design) |
| 225 | `step N` is silent, and interrupting it loses every year already simulated | Yes (code) |
| 226 | The integrated circuit is startable, and completes, before any transistor | Yes (data) |
| 227 | Large merchant ships cost nothing to learn, open or run and became the largest income | Yes (data and `available`) |
| 228 | The commutator needs high-pressure steam and industrial zinc needs the power grid, contrary to their own descriptions | Yes (data) |
| 229 | `school_founded` requires `freedman_staff`: no paid-labour route to the school | Yes (data) |
| 230 | `rush` and the automatic policies cannot exclude a node or category | Yes (help) |
| 231 | Roman and Mediterranean content is presented as local fact and startable in a Han campaign | Yes |
| 232 | `lens_grinding` says it buys the first patron but needs a workshop that needs a patron | Yes (data) |
| 233 | Staffing closures are reported gross with no cause, and `keep`, `reserve`, `auto_replace_foreman` are never named | Untested live (code reading) |
| 234 | The advertised calendar floor is not the earliest completion (payment schedule binds) | Yes (harness: floor 5.6 years, 10 steps) |
| 235 | "Bone setting has 1.2 spare scholars before it closes" with only the founder as scholar | Yes |
| 236 | Small player-text defects (four-fifths vs 85%, algebra example, six-row list of five, kit and mortality prose, `labour laborer`, and others) | Yes |
| 237 | A forgotten technology is rebuilt at its full schedule, ignoring surviving equipment and dispersed copies (request) | Untested |
| 238 | The capacity dashboard shows generation the capability checks ignore | Yes (data) |
| 239 | The shortage remedy text ignores mines already being sunk | Code reading only |
| 240 | Tiny cash remainders add a whole year | Not reproduced (harness); tester's 20+ cases stand |
| 241 | Failures read generically, and knowledge nodes fail like machines (request) | Untested |
| 242 | Completion messages name the changed fields but not size or reach | Untested (closed 85 covers the intent) |
| 243 | No `map` or `country` command; `move` lists tiles by id only | Yes |
| 244 | Upkeep is displayed at three quarters of what the ledger charges | Yes |
| 245 | Nodes that are "knowledge and also a service" do not say which benefit is permanent (request) | Partly |
| 246 | `ventures` says machinists are scholars; `labour` says craft | Yes |
| 247 | Patron death penalty and recovery unexplained; one-off jump extrapolated as a trend | Untested |
| 248 | `bounty` has no quote: price multiplier, eligibility and judging unstated | Yes (help) |
| 249 | Artillery needs no gunpowder; bastions need almost no materials, yet defeat is credited to guns on walls | Yes (data) |

## Item table (tester's numbers)

Outcome key: **New N** filed; **Dup N (open|closed)** duplicate, paragraph appended for open ones; **closed and gone** means a closed complaint covers it and it does not reproduce; **Not filed** with the reason.

| T# | Item | Outcome | Reproduces now |
|---|---|---|---|
| 1 | Launch needs Python and a terminal | Not filed: packaging and README, not a defect in the game | n/a |
| 2 | `save` needs relative paths; manual save does not change the autosave; save lands in working folder; no export | Dup 208 (open, appended) | Yes (absolute path refused) |
| 3 | `help commands` lists `options: available` as an alias; real options menu missing from the groups | Dup closed 161 for the alias (removed); `options` still missing from `help commands`: New 236 | Alias no; missing entry yes |
| 4 | Invalid input inside a submenu gives only "not a choice right now" | Closed 161 (menu echoes the rejected line now) | Untested (menu is interactive) |
| 5 | Roman wealth categories (equestrian, senatorial) and patch commentary in the Han kit screen | New 231 (kit) and 236 (patch commentary) | Yes |
| 6 | Poor-scholar text versus displayed finances (resolved by the tester: the practice income) | New 236 (kit wording) | Yes (750 thousand cash, 440 thousand a year living cost, "a few months") |
| 7 | Prompt abbreviations `sch 1 art 1` need a legend | Not filed: `state` explains them ("counting yourself and hours you have bought") | n/a |
| 8 | Help index overload | Dup 99 (open, appended) | Yes |
| 9 | Epidemic goal says four-fifths and 85 percent | New 236 | Yes |
| 10 | Fog still shows every goal's prerequisite count and ideal floor | Not filed: design choice, praised in the England triage as the intended information boundary | n/a |
| 11 | Mortality text calls one life "the honest number" | New 236 | Yes |
| 12 | Menu pacing and terminal effort; wants a GUI | Not filed: product request | n/a |
| 13 | `why` omits the specialist foreman | Closed 149 | No: `why` prints "SPECIALIST FOREMAN TO KEEP IT OPEN: 0.25 carpenter FTE" |
| 14 | `stuck` recommends toys that `open` refuses | New 219 | Yes |
| 15, 16 | Hiring prepays the wage; opening deducts unpreviewed cash | New 220 (closed 166 did the price consistency only) | Yes |
| 17 | Cash movement cannot be reconciled | Dup 97 (open, appended) | Yes (no per-year ledger) |
| 18 | One-time advance sits inside "recurring" net | New 222 | Yes |
| 19 | `commission` eligibility only explained after purchase | New 220 | Yes (reply says "this year only" after buying) |
| 20 | Sole employee lost "to death and to better offers" | New 233 (causes not split) | Untested |
| 21 | Han introduction says glass is missing; glass panes are free | Dup 128 (open, appended) | Yes (`mat_glass_soda` in `starting_techs`) |
| 22 | Roman and generic prose in Han play | New 231; Dup 126 (appended) | Yes |
| 23 | Closed-concern earning figure excludes the carpenter; zero-income institutions read like shops | New 219 (net of wages), New 245 (institutions) | Yes |
| 24 | "Spare scholars before it closes" cannot be reconstructed | New 235 | Yes |
| 25 | Money and ventures quote different upkeep | New 244 (closed 153 was the earnings side) | Yes |
| 26 | Standing shifts (scandal 0.79 to 3.8) have no cause line | Dup 97 (appended); closed 85 | Untested |
| 27 | Available labels: "cheapest six" shows five; truncated names; `find glass` returns non-glass rows | New 236 (rows), Dup 197 (open, appended) | Yes |
| 28 | Goal progress needs five screens; literacy only as 0.06 | Dup 96 (open, appended) | Yes |
| 29 | No support for deliberate saving or a planned project | Dup 100 (appended; `stuck` suggests free filler) | Yes |
| 30 | Zero-time nodes finish immediately and are missing from the step report; completion years vs arrival years | Not filed: closed 14 made them immediate by design; the recap part is 97 | n/a |
| 31 | `quote farm` refused | Closed 147 | No: `quote farm 10` prices it |
| 32 | Institution descriptions omit measurable effects | New 245 | Partly |
| 33 | Workforce guidance suggests `hire scholar 2` when one more is enough | Dup 205 (open, appended) | Untested |
| 34 | Algebra example and equation disagree | New 236 | Yes (data) |
| 35 | Failure charge larger than the quote | New 218 | Yes |
| 36 | "People kept on your own staff" prose with no number | New 236 | Untested |
| 37 | `funding_capacity()` and `your_real_ceiling` in player text | New 236; Dup 126 (appended) | Yes |
| 38 | Broad curricula versus separate concept nodes | Not filed: a question, the tester says "not proven duplicate mechanics" | n/a |
| 39 | Fog hides conceptual guidance | Dup 72 (open, appended) | Yes (design gap) |
| 40 | Failure cause generic | New 241 | Yes |
| 41 | Retry calendar ETA not shown | New 234 | Yes |
| 42 | Negative balance, interest estimate, zero paid (the tester later corrected: interest was charged) | Not filed: corrected by the tester (T124 journal, total 73,617); timing is part of 97 | n/a |
| 43 | Departure removes the whole annual wage | Dup 97 (appended) and New 222 | Plausible by design (no wage for someone who left); no settlement line |
| 44 | Corpus ETA ignores the payment schedule | New 234 | Yes |
| 45 | "You take 100 percent of it" hides severity | Dup 204 (open, appended) | Untested (dated event) |
| 46 | Staffing advice ignores the immortal founder | Dup 205 (appended) | Yes |
| 47 | Fire destroyed nothing with negative cash | Dup 169 (open, appended) | Untested |
| 48 | Quoted price and scale contradict the descriptions (case hardening "cheap", three-plate "Iron-Age tools") | Not filed: design request (prototype, workshop, factory); related 115 and 151 | n/a |
| 49 | Arrival orientation hard to value; "no longer a prerequisite" | Dup 126 (appended) | Yes (data) |
| 50 | Permanent knowledge versus operating benefit | New 245 | Partly |
| 51, 52 | Colon pagination dumps everything; subject and category navigation unclear | New 217; Dup 197 | Yes |
| 53 | Free shipping | New 227 | Yes |
| 54 | One staffing shortfall closes unrelated businesses | New 233 (the closer is per resource and minimal, `projects_staffing_shortfall.py`; not reproduced) | Untested |
| 55 | Failure quote inconsistent (chuck 0.94) | New 218 | Yes |
| 56 | Trade classification conflicts across screens | New 246 | Yes |
| 57 | Portfolio predictions hard to trust | Dup 90 (open, appended) | Untested |
| 58 | ETA rounding ("about 2 more years" on an exact balance) | New 234 and 240 | Untested |
| 59 | Static-date prose ("50 years before Ptolemy's 150 AD"); Newtonian mechanics framed against Aristotle | New 231 | Yes (data) |
| 60 | Accuracy and scale need intermediate steps | Not filed: design request (see T48) | n/a |
| 61 | Public-health goals lack a coverage loop | Dup 116 (appended); New 242 | n/a |
| 62 | Reopening prose contradicts retained ramp; opening deductions unpreviewed | New 220 (opening); ramp prose untested | Yes / untested |
| 63 | `labour laborer` refused | New 236 | Yes |
| 64 | Help discovery | Dup 99 (appended) | Yes |
| 65 | Institutional gate hidden under fog | Dup 72 (appended) | Yes |
| 66 | Lens grinding narrative contradicts its unlock order | New 232 | Yes (data) |
| 67 | Granted 1300 C does not satisfy the 1100 C node | Dup 127 (open, appended; Han grants 1300 without 1100) | Yes (data) |
| 68 | Zero-prerequisite node appears late (woodblock carving) | Not filed: visibility gating not shown by the evidence | Untested |
| 69 | Tiny remainders add years | New 240 | Not reproduced |
| 70 | Failure losses differ from quotes (lead 43.6M vs 60.4M) | New 218 | Yes |
| 71 | Reputation-shortened calendar disagrees with money pacing | New 234 | Yes |
| 72 | Commodity substitution and charcoal scale | Dup 151 (appended); substitution later confirmed working (T142) | Untested |
| 73 | Completion effects lack magnitude and reach | New 242 (closed 85) | Untested |
| 74 | Non-Roman campaign text still assumes Rome | New 231 | Yes |
| 75 | Non-coercive route to the school | New 229 | Yes |
| 76 | `close` versus `mothball` | New 221 | Yes |
| 77 | Staffing priorities; automatic reopen with `auto_open` off | New 233; Dup 93 (appended) | Code reading (reopen is unconditional by design) |
| 78 | Patron death recovery unexplained | New 247 | Untested |
| 79 | Training warning versus annual event order | New 236 (bullet 10) | Untested |
| 80 | Portfolio mixes current budget and historical allocations | Dup 90 (appended) | Untested |
| 81 | Search and filter syntax | New 217 | Yes |
| 82 | Scientist ceiling wording (6.2 people) | Dup 235 (appended) | Untested |
| 83 | Option order matters | New 217 | Yes |
| 84 | `auto_hire` duplicates pending graduates | Dup 93 (appended) | Untested |
| 85 | `auto_hire` needs goals, budgets, priorities | Dup 93 and 180 (appended) | n/a |
| 86 | Saltpetre advice scale wrong | Closed 11 and 193 | Not reproduced (code now sizes from the same shortfall with a buffer); older build likely |
| 87 | Copper advice says own workings cover demand with none | Closed 175 | No (clause prints only when a working exists) |
| 88 | Sacking report: 40.5 people gone, then FTE rosters | Not filed: same class as closed 168; not replayed | Untested |
| 89 | State requisition presented as our choice | Dup 114 (open, appended) | Untested |
| 90 | Concrete military adoption model | Positive | n/a |
| 91 | Cannon without gunpowder; fortification with no material bill | New 249 | Yes (data) |
| 92 | `buy housing` versus labour advice; `quote housing` fails | Closed 167 and 147 | No |
| 93 | `buy school` and `quote school` fail | Closed 156 | No (`quote school scribe 10` and `buy school` work; replayed with a rich kit) |
| 94 | Low-margin warnings on inconsistent bases | New 244 | Yes |
| 95 | Calendar versus payment pacing | New 234 | Yes |
| 96, 97 | Closure cascades; `auto_open` priorities, child clinic | New 233 | Untested |
| 98 | Composed browsing syntax | New 217 | Yes |
| 99 | Tiny remainders; misleading floors | New 240, New 234 | See those |
| 100 | Bulk steel paid whole bill immediately | Dup 151 (appended; materials are paid up front) | Untested |
| 101 | Mine suggestions ignore committed mines | New 239; Dup 79 (appended) | Code reading |
| 102 | Mine startup and upkeep timing; 0.75 factor | Dup 244 (appended); closed 66 | Partly |
| 103, 104 | Zinc needs the grid; dynamo needs high-pressure steam | New 228 (see also open 125) | Yes (data) |
| 105 | Patron recovery; no manual succession command | New 247 | Untested |
| 106 | Public-health effects exist; no outcome dashboard | Positive; New 242 | n/a |
| 107 | Maintenance, inspection exist but benefits unquantified | New 245 | Partly |
| 108 | Industrial costs re-tighten money (positive) | Positive | n/a |
| 109 | Separate market mechanisms unexplained | Dup 178 and 216 (appended) | Untested |
| 110 | Requisition again | Dup 114 (appended) | Untested |
| 111 | Export path restriction | Dup 208 (appended) | Yes |
| 112 | Small losses close many concerns | New 233 | Untested |
| 113 | Rush should exclude freedman staffing | New 230 | Yes |
| 114 | Bounty needs an informative preview | New 248 | Yes |
| 115 | Knowledge versus material distinctions; named variants | New 228 | Yes (data) |
| 116 | Adjusted floors understate first-attempt completion | New 234 | Yes |
| 117 | Generation and capability flags disagree | New 238 | Yes (data) |
| 118 | Large losses; warnings rounded to 0 percent | Dup 169 (appended) | Untested |
| 119 | Succession policy pays, recovery unexplained | New 247 | Untested |
| 120 | Correction: dashboard explains mining multipliers | Correction, positive | n/a |
| 121 | Waiting is the least enjoyable part | Dup 101 (appended); New 234 | n/a |
| 122 | Honest scope of the 150-year claim | Not filed: not a defect | n/a |
| 123 | Geography exists but no map | New 243 | Yes |
| 124 | Country-scale versus operating reach | Dup 116 and 176 (appended) | Yes (placeholder counts) |
| 125 | Implementation references (`labour.py`, `--help`) | Closed 172; the `population` pointer is gone | No |
| 126 | Optional research is not padding (tester's own correction) | Not filed | n/a |
| 127 | Diversification improves agency | Positive | n/a |
| 128 | Sub-cash remainders | New 240 | Not reproduced |
| 129 | Grid forecast versus binding schedule | New 234 | Yes |
| 130 | Named electrical variants | New 228 | Yes |
| 131 | Closure cascades persist | New 233 | Untested |
| 132 | Repeated seizures, thin response options | Dup 114 and 169 (appended) | Untested |
| 133 | Culture-specific inventions read as Rome exports | New 231 | Yes |
| 134 | Institutions exist but outcomes need a dashboard | New 242 | Untested |
| 135 | Mechanised agriculture now observed; employment unmeasured | Dup 116 (appended) | Untested |
| 136 | Snapshot ledger needs action-delta attribution | Dup 97 (appended) | Untested |
| 137 | `buy school smith 2` fails | Closed 156 | No |
| 138 | Correction: specialist limits are not absolute | Correction | n/a |
| 139 | Closure cascades, the biggest annoyance | New 233 | Untested |
| 140 | Calendar estimates understate the payment schedule | New 234 | Yes |
| 141 | Grid capability versus physical generation | New 238 | Yes (data) |
| 142 | Material substitution works | Positive | n/a |
| 143 | Military technology has effects | Positive | n/a |
| 144 | Institutions and deputies expand capacity | Positive | n/a |
| 145 | Process knowledge versus obtainable materials | New 228 | Yes (data) |
| 146 | Functional variants and prerequisite errors (semaphore) | New 228; New 231 (`patron_senatorial`) | Yes (data) |
| 147 | Filter and identifier UX | New 217 | Yes |
| 148 | Succession forecast extrapolates a one-off | New 247 | Untested |
| 149 | Political cash losses need prospective uncertainty | Dup 169 (appended) | Untested |
| 150 | Several kinds of market competition | Dup 216 (appended) | Untested |
| 151 | Capabilities versus society-wide deployment | Dup 116 (appended); New 242 | n/a |
| 152 | Knowledge-risk details reveal developer assumptions | Dup 126 (appended); `labour.py` pointer gone | No |
| 153 | `available autoclave` returns nothing though `why` says startable | Dup 196 (open, appended) | Message yes; exact case untested |
| 154 | Civilian technology has explicit effects | Positive; New 242 | n/a |
| 155 | Hazard mitigation is rich and visible | Positive | n/a |
| 156 | Hydro generation works when installed | Positive | n/a |
| 157 | Late infrastructure costs feel small | Dup 194 (appended) | Untested |
| 158 | Research timing and fractional tails | New 234 and 240 | See those |
| 159 | Abstract knowledge "fails" twice | New 241 | Untested |
| 160 | Research duplication and variants | New 228 | Yes (data) |
| 161 | Clinical ethics options (consent, donation) | Not filed: content request with no specific missing node; related 229 | n/a |
| 162, 165 | Integrated circuit before transistors | New 226 | Yes (data) |
| 163 | "Lapsed" protections cannot be reopened | Dup 202 (open, appended): the named concern is to be reopened, not the hedge | Wording yes |
| 164 | `ventures closed` prints everything | New 236 (bullet 11); closed 174 gave paging | Yes |
| 166 | Wage labour as school route | New 229 | Yes |
| 167 | Headquarters expansion is buying housing | Dup 194 (appended) | n/a |
| 168, 169 | Sacking forgets 37 technologies; rebuilding takes decades | New 237; closed 170 (harshness intended) | Untested |
| 170 | Staffing and society react to destruction | Positive; reason codes in 237 | n/a |
| 171 | `auto_commission` useful | Positive; receipts in 93 | n/a |
| 172 | Endowments exist (correction) | Correction | n/a |
| 173 | Calendar reset display did not predict | New 234 | Yes |
| 174 | Search resolved with `find` | Dup 196 (appended) | Yes |
| 175 | Full names work | Positive | n/a |
| 176 | Second sacking | New 237 | Untested |
| 177 | Country population doubled in 25 years | Not filed: realism question with no formula evidence; related closed 45 and open 111 | n/a |
| 178 | National specialist counts are placeholders | Dup 176 (open, appended) | Yes |
| 179 | Reconstruction is a primary-goal gate | New 237; Dup 125 | Untested |
| 180 | Public-service opening supported | Positive | n/a |
| 181 | Named save used as resume path overwritten | Dup 208 (appended) | By design |
| 182 | Bounty works, help omits price and eligibility | New 248 | Yes |
| 183 | Both transistor branches blocked by lost grid | Dup 125 (appended); New 228 | Untested |
| 184 | Whisker note has patch history and fog commentary | Dup 126 (open, appended) | Yes (data) |
| 185 | Fire; patron death repeats | Dup 169; New 247 | Untested |
| 186, 187 | Restoration ignores surviving capability; ETA at launch | New 237, New 234 | Untested / yes |
| 188 | Railway demonstration versus national network | Positive | n/a |
| 189 | Political agency limited | Dup 114 (appended) | Untested |
| 190 | Rush needs persistent exclusions | New 230 | Yes |
| 191 | Portfolio stale allocations | Dup 90 (appended) | Untested |
| 192 | Literal search versus topic expansion; `all:true` overrides `limit` | New 217; Dup 196 | Yes |
| 193 | Useful effects need scale and coverage | New 242 | Untested |
| 194 | Opening a small business recalculates other income | Dup 178 (appended) | Untested |
| 195 | Staff buffers and priority control | New 233 | Untested |
| 196 | Polity still labelled Later Han in the Sixteen Kingdoms | Not filed: fixed civilisation identity, noted by the tester as possibly intended; related 189 | n/a |
| 197 | Score breadth; resilience 3 to 2 unexplained | Dup 199 (England, open, appended); New 224 | Untested |
| 198 | Save path and export friction | Dup 208 (appended) | Yes |
| 199 | Science-to-medicine links rewarding; clinical outcomes | Positive; New 242 | n/a |
| 200 | Defence diffusion has consequences | Positive | n/a |
| 201 | Tiny payment remainder | New 240 | Not reproduced |
| 202 | Retry time poorly exposed (15.9 years shown, four actual) | New 234 | Yes |
| 203 | Allocation warning helped; wants "up to useful work" | Dup 205 (appended) | n/a |
| 204 | Grid retry projection misleading | New 234 | Yes |
| 205 | First transistor milestone well distinguished | Positive | n/a |
| 206 | Last specialist's loss: 210 closures gross, 267 running | New 233 | Untested |
| 207 | Clinical methodology exists (correction) | Correction | n/a |
| 208 | Public-service reopening needs priorities | New 233 | Untested |
| 209 | Reopen quotes and ledger refresh | Dup 178 (appended) | Untested |
| 210 | Long pauses lack progress feedback | New 225; Dup 185 (appended) | Yes |
| 211 | Victory without score; no finish action | New 224 | Yes |
| 212 | Achievement "never understaffed" contradicts history | New 223 | Yes |
| 213 | School purchase parser; school clashes with no-slavery | Closed 156 (parser gone); New 229 | No / yes |
| 214 | Advanced projects versus infrastructure scale; "testing kills the pilot" | Not filed: design request (see T48); the pilot casualty is flavour text | n/a |
| 215 | Public-service maintenance and opaque repricing | New 233; Dup 178 | Untested |
| 216 | Paging past the end | New 217 | Untested |
| 217 | Real benefits from breadth; national delivery unclear | Positive; New 242 | n/a |
| 218 | Final-challenge timing; money and directing capacity easy late | Dup 184 and 101 (appended); New 234 | Untested |
| 219 | `open junction_transistor` after victory changes the snapshot | Dup 178 (appended) | Untested |
| 220 | Hypothesis: `step 200` reveals the score | New 224 | Not tested by the tester or here |
| 221 | `step 200` silent for over an hour | New 225 | Yes (code) |
| 222 | Cancelled after 51 minutes; nothing saved | New 225 | Yes (code) |
| 223 | No new research does not freeze the world (tester correction) | Correction; supports the multi-year preview ask in 225 | n/a |

Journal-only items (not in the notes): year 122 `quote open med_herbal_pharmacy` refused (New 220, 221); year 122 herb text Greek and Roman (New 231); year 130 `arrival_orientation` (Dup 126); year 385 a 10 million `bribe` fixed protection (positive, noted in 247); year 197 the lending library lifted literacy without a school (positive); year 203 and later `auto_open` expanded 9 concerns to 44 (positive, noted in 233); year 227 "closed 45 concerns after 3 artisans and 1 smith" (New 233).

## Severe bugs

None of the kind that corrupts a save, crashes, or loses a game. The tester reports "no corrupted save or blocking crash" across 300 years and 1,000 technologies, and an interrupted multi-year `step` left the session file intact at the old year (verified by code: the save is written once after the command). The items that come closest, in order:

1. **Wrong money shown before a decision (218).** The failure loss printed by `why` is computed on a different base from the charge when a project fails. Replayed: Han pays 1.85 to 2.0 times the quote on its strong domains (corpus, bookbinding), 0.95 times on an opposed node. The tester abandoned a plan over it and lost 172 thousand against 103 thousand quoted. It affects every civilisation with a cost multiplier.
2. **Balance: a free fleet (227).** One zero-cost, zero-upkeep node is about twenty times the starting cash per year and was the largest income for the whole run. It is reachable within a few years (needs five smiths, about 1.8 million). This is the main reason the tester judged late money "easy", and it breaks rule 4.1 of CLAUDE.md (costs must fall out of physical inputs).
3. **Wrong achievement (223).** The "never understaffed" achievement is awarded by reading only the concerns currently shut, so any run that recovers by the end wins it.
4. **Goal integrity (226).** The integrated circuit, the goal's own technology family, completes before any transistor exists, because nothing physical stands behind it.
5. **Lost time, not data (225).** `step 200` gives no feedback and loses everything if interrupted; the tester spent 51 minutes.

Also checked: `buy school` (the tester's most repeated bug, T93, T137, T213) is fixed on this branch (closed 156), as are the foreman line in `why` (149), `quote farm` and `quote housing` (147, 167), and the `options` alias (161).

## Positive feedback ("do not break")

- New-game flow: clear menu, civilisation introductions with advantages, constraints and what is coming, warnings before the irreversible fog and mortality choices, the horizon screen saying only the calendar changes, and an automatic resumable session.
- Knowledge versus capability: a built concern is not running until opened; the foreman and supervision model (toys needing a carpenter, machinists and glassblowers as real gates); the workshop gate revealing a coherent chain (steel, measuring tools, water power, paper, chemistry, microscopy).
- Project finance: combined-commitment warning, borrowing forecast, retry learning (lower next risk, calendar progress carried forward), annual pacing once started, and the reserve and arrears-interest feel.
- Discovery under fog: error suggestions for mistyped ids, full names accepted by `start`, `rush preview` as a survey tool, `available` subject summaries, material substitution that works (coke for charcoal), mine depletion and the yield-boost explanation on the dashboard.
- Hazards and resilience: dated hazards as a plannable causal model; the risk screen crediting hygiene, vaccines, diversified food, walls and guns, and diffusion of military technology to state armies, with attacks repelled citing exactly those; public-health effects on population; property seizures, fires and sackings that make cash matter even when income is huge.
- Automation: `auto_hire`, `auto_open`, `auto_court_heir`, `auto_commission` saved considerable typing and were praised once found.
- Design choices the tester singled out: the point-contact transistor described as a fragile demonstrator distinct from the manufacturable junction; railway "demonstration versus network"; the simulation distinguishing process knowledge from industrial supply; the lending library reaching the literacy goal without the school.

## Where this tester agrees and disagrees with the England and Rome testers

- **Agree with England (196 to 216):** natural-word topic search is fragile (196, 197); `save` refuses absolute paths (208); the corpus and hedge wording and the resilience score are opaque (200, 199); hazard relief is not attributed (202); `allocate` and its stale orders are found late (205, 206); the ledger shows a large market deduction but names few concerns (216); intermediate education and knowledge hedges are missing (212, 213); the foreman mismatch and `buy school` misroute were the two functional bugs, both fixed. Both praise dated hazards as plannable, and both judge money easy after about 50 years, this tester after the free fleet.
- **Agree with Rome (146 to 195):** `buy school`, `quote farm` and the foreman line (146 to 156, all fixed); money stops mattering in the late game (184, 194); the patron and sack events need explanation (170); wealth exposure and confiscation (169); Rome-specific prose where it should not be (136).
- **Disagree or differ:** the Rome tester read the hazards as "scripted", this tester (like England) reads them as a causal model and was impressed; the Rome tester reports an erased civilisation in the third century, this one lost 37 technologies once and recovered, but reports the same unease about restoring a lost node at the full original schedule (237). Unlike England (75 years, hand-managed) this tester played 300 years and used the automatic policies heavily, so the dominant new complaints are about automation and scale: closure cascades, the gross report, exclusions, and the payment schedule (233, 234, 230). This tester also found the most data-level inconsistencies (IC, zinc and grid, heat rung, glass, lens order), because a full run crossed parts of the tree neither shorter play touched.
- **Overall:** all three like the premise and the dependency logic, find the help and information screens the weakest part, and ask for trustworthy previews and one consistent feasibility test before more content. This tester's summary is that the game is winnable under fog in 300 years without buying people, enjoyable when parallel work fills the waits, and that trust in costs, forecasts and staffing is the main obstacle; the claim of a 150-year win was not supported by the run (150 years gave local electricity, not a transistor).
