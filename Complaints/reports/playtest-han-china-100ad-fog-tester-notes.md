<!-- Tester notes (bugs, UX, feature requests) from a Han China 100 AD fog playtest, poor_scholar kit, immortal founder, goal reached in 399 AD. Verbatim. Triage: playtest-han-china-100ad-fog-triage.md -->

# Bootstrap History — first-session playtest

Status: setup completed; paused before the first gameplay action.

## Scope and rules

Read only the ZIP's root README.md. No source, data, other repository documentation, directory listings, or save contents inspected. Extracted the archive and launched the README's main-menu command. Played through its interactive terminal interface; no gameplay scripts, JSON commands, automation, or tech-tree searches. Extra documentation read was solely the file-delivery skill, not game material.

This session intentionally stops after setup, in-game help, and saving. It does not establish whether winning is easy, impossible, or achievable in 150 years.

## Campaign and handoff

- Civilisation: Later Han Empire, starting 100 AD.
- Kit: poor_scholar.
- Fog: on, permanent.
- Mortality: off.
- Goal: grown and alloy junction transistors.
- Horizon: 500 elapsed years, ending 600 AD.
- Current year: 100 AD; zero elapsed years.
- Cash: 750,651; recurring net: −2,160 cash/year.
- Free founder hours: 2,000 this year.
- Employees: zero; running operations: none.
- Technologies: zero built by me, 109 granted; 11 target-route nodes present.
- Reputation 5; protection 0%; scandal 0; eminence 0.
- Shared snapshot: han-fog-session-01.json.

Resume from the extracted game's folder with the shared snapshot copied there:

`python3 sim/simulator.py play --session han-fog-session-01.json`

The menu automatically created a session save. Manual `save han-fog-session-01.json` reported success at year 100. Quit continued to identify the original autosave, so a manual snapshot does not appear to change the active session destination. No save internals were inspected.

## Goals and next plan

Main goal: transistors. Additional game-defined goals: germ theory, written corpus, general literacy at least 20%.

Personal goals, provisional until the interface reveals relevant mechanics:

1. Never purchase or own enslaved workers; use paid labor.
2. Once affordable, maintain cash reserves covering five years of household subsistence; calculate the threshold from the ledger rather than guessing.
3. Establish an income-producing operation and keep at least one operating through the announced political crisis around eighty years after arrival.

Next session: inspect `available`, `money`, and relevant `why` pages; identify an affordable income route before advancing time. Avoid broad automatic starts. Do not assume the target's displayed 142-year ideal floor is an achievable practical forecast.

## Feelings and assessment

The knowledge-versus-industry premise is appealing. Civilisation introductions give real flavor and warn of historical pressures. Choosing Han initially felt comfortable, then its weak glassmaking and coming political breakdown made it more interesting. I am curious rather than confident: I have not yet built anything.

The interface is usable, but it requires more technical and command knowledge than a frictionless new-player experience. Strong explanations coexist with long reference dumps and a few contradictions. The game calls 400 years tight for transistors and 500 standard; that makes a claimed 150-year completion an exceptional claim, not evidence of ease. No verdict on difficulty yet.

## Bugs, discrepancies, and friction

### 1. Technical launch requirement
Status: observed UX friction.
README installation assumes Python 3.11+, terminal use, a working directory, and commands. An attached ZIP lacks a player-facing launch flow in the README. I needed extraction, a terminal, and the documented Python launch command. No dependency install was needed, which is good.
Wanted: an obvious launchable app or browser interface with the same menus.

### 2. Save paths require technical knowledge
Status: observed UX friction and documentation gap.
Load offers typing a filesystem path rather than choosing a file. Autosave/resume instructions expose long paths. `save /workspace/scratch/e3924217f104/han-fog-session-01.json` was refused: a save file must be relative. README says `save <file>` without stating this restriction. `save han-fog-session-01.json` succeeded.
The relative manual save was created in the game's working folder, not the configured save folder: copying the expected save-folder path failed, while copying the exact filename from the working folder succeeded. No directory scan was performed.
Wanted: explicit destination in the success message, consistent save-folder behavior, and export/import controls. Clarify that manual saving does not change the active autosave path.

### 3. Incorrect options alias in command help
Status: reproduced documentation defect in the interactive menu session.
`help commands` lists `options: available` under aliases and omits the real options menu from its command groups. Actual `options` opens a submenu for horizon, mortality, and save destination, as setup/tutorial says it should.
Reproduction: launch menu, start campaign, enter `help commands`, then `options`.
Wanted: help generated for the actual interactive command surface.

### 4. Submenu context gives a weak invalid-input explanation
Status: observed UX friction; tester input mistake, not a gameplay defect.
I submitted `options`, `help fog`, and `help sittings` together as separate lines. Options opened a submenu; both help lines became invalid menu choices. Output was only `-- not a choice right now.` and the menu repeated. Returned with `b`, then entered help commands individually.
Wanted: say "You are in Options; type b to return before entering game commands." Ideally help works in submenus. No lost turn or gameplay action observed.

### 5. Starting-kit wealth categories are Roman in a Han campaign
Status: observed flavor/localization friction.
Equestrian census and senatorial fortunes appear in Han's kit screen. Amounts use laborer-years without a clear explanation on that screen. Rich-kit prose references former balance behavior ("used to make things worse and no longer does"), which feels like patch commentary rather than player guidance.
Wanted: local social/wealth analogies, an explanation of wage-equivalent units, and current gameplay consequences.

### 6. Poor-scholar narrative versus displayed finances
Status: apparent mismatch; needs more in-game investigation.
Intro promises a few months of subsistence; actual balance is 750,651 cash and state shows recurring net −2,160/year. Dividing those figures suggests about 347 years at the initial net burn if unchanged, which does not resemble a few months. The full ledger has not been inspected, so no conclusion about hidden or future expenses.
Wanted: explain currency and purchasing power using food, rent, tools, and typical wages; align the introduction with the actual economy.

### 7. Prompt workforce abbreviations need an extra screen
Status: observed and resolved through state.
Prompt `sch 1 art 1` appears after "no employees." State explains that these count my own scholar/craft capacities; payroll is zero. That clarification required another command.
Wanted: an initial legend or clearer labels distinguishing capabilities from hired people.

### 8. Help index overload
Status: observed UX friction.
`help commands` emits descriptions, usage, groups, many aliases, and help's own detailed entry in one long output. Front-page help is helpful, but claims like "one line each" understate the volume.
Wanted: a concise beginner index, topic navigation, optional alias reference, and pagination for long help. Prominent help save/resume labeling would be clearer than "sittings."

### 9. Epidemic goal percentage discrepancy
Status: observed text defect.
Goal 8 says "Cut four-fifths" and then specifies 85% reduction. Four-fifths is 80%. Actual winning threshold not tested.
Wanted: consistent wording and a visible measured progress indicator.

### 10. Fog reveals global goal metadata during setup
Status: design question, not a demonstrated exploit.
With fog already selected, goal setup lists every target's prerequisite count and ideal calendar floor. State also reports 11 target-route nodes present. This does not expose the route itself, but supplies global knowledge beyond immediate discoveries.
Wanted: define fog's intended information boundary and optionally hide numerical route estimates in discovery mode.

### 11. Mortality description judges the default mode
Status: editorial feedback.
Mortality is optional and off by default, yet setup says "one is the honest number." That feels like judging a supported play style. Describe consequences plainly and let players choose.

### 12. Menu pacing and operational effort
Status: observed interaction overhead.
Needed repeated terminal exchanges to inspect each screen, read its choices, and respond. Startup output did not arrive in the first brief terminal read and required another read; elapsed startup time was not measured precisely. The live terminal remained usable; no restart loop or lost progress occurred. Normal commands cost only a few words once inside the game.
Wanted: a persistent visual interface showing choices, help, and campaign status without requiring command recall or terminal management.

## Mod and product ideas

- Civilisation-specific starting kits, currency descriptions, and purchasing-power examples.
- A paid-labor institutional route with worker training, safe workshops, and knowledge succession; first check existing mechanics before claiming these are missing.
- Public-good milestones: germ theory plus demonstrated mortality reduction, and writing plus measured literacy, with a personal-goal tracker.
- A fog-compatible research journal: discoveries, observed dependencies, unanswered questions, and experiments, without exposing hidden tech.
- A concise dashboard for household reserves, payroll, income, project bottlenecks, and operating versus merely completed works.
- A more thematic difficulty setup: calendar presets are currently the only stated difficulty change. Optional discovery uncertainty or historical-pressure variants could add different challenges, but balance has not been tested.
- A first-class export/import save flow and a graphical shell for the existing interface.

These are provisional ideas from setup and help, not claims that the source lacks the mechanics.

## What worked well

- Clear main menu and empty-load explanation.
- Program preferences are explicitly distinguished from campaign settings.
- Civilisation descriptions explain advantages, constraints, scale of reach, and looming history.
- Irreversible fog and mortality choices are warned about before commitment.
- Horizon screen explains that calendar, rather than costs or failure probabilities, changes across presets.
- Automatic session saving and a resume command are announced at startup and quit.
- State explains employee counts, recurring net cash, unused founder hours, and specific next commands.
- Help repeatedly explains that completed works must be opened to operate.
- Readable natural-language commands are available; there was no need for a gameplay script or source inspection.

## Update after the first ten years: 100–110 AD

Status: ten single-year steps completed; paused at 110 AD. New shared checkpoint: han-fog-year-110.json. Detailed yearly actions, results, and opinions are in bootstrap-yearly-journal.md. Still no game source/data/other repository documentation/save contents inspected; all evidence below comes from the interface. No gameplay scripts or automation used.

Final state: 71,601 cash, +213,188/year recurring net, no debt, no employees, two open concerns (buttons and bone setting), eleven player-built technologies, fourteen transistor-route nodes versus eleven initially. Science, toys, and standards are shut. Literacy 6%; none of the four chosen game goals achieved. No enslaved workers bought. All research attempts succeeded; one supply disruption, one fire, and employee turnover occurred. This is not sufficient evidence about full-campaign win difficulty.

### Resolution of initial finance concern (#6)
`money` reveals a starting personal medical practice bringing in 438,185/year, against 440,346 living/appearance costs. Thus a small net burn did not mean low gross subsistence spending. The approximately 347-year calculation was a net-burn illustration, not a gross subsistence estimate. The balance is only about 1.7 years of the initial bundled annual living/appearance costs, still not transparently "a few months." Keep the narrative concern but do not call the initial net burn an economy exploit.

### 13. Undisclosed specialist foreman condition before construction
Status: reproduced; high-impact planning defect.
At 102, `why hom_toys_dolls` listed staff_needed zero, staff to keep it open zero scholars/0.10 artisans, and construction labor carpenter 80h/artisan 60h. It did NOT list the separate 0.25 carpenter FTE foreman requirement. After building at 103, `open hom_toys_dolls` refused because no qualified carpenter foreman was free. Only `ventures` after completion showed the specialist foreman.
Impact: I inspected detailed requirements before investing 133,455 but could not see what prevented earning revenue. Listing generic operating staff with lengthy explanatory prose made the omission particularly misleading.
Wanted: show construction labor, generic operation staffing, specialist foremen, opening charge, and expected full costs on the same pre-start screen. Add operating-specialist information to available or a concise preview.

### 14. Stuck recommends a concern that cannot actually open
Status: reproduced; incorrect adviser result.
At 108 with no carpenter employed, `stuck` said the "best you could actually open right now" was hom_toys_dolls, quoting 375,268 revenue and 5,004 upkeep. Immediately following its advice, `open hom_toys_dolls` refused for missing 0.25 carpenter FTE.
Wanted: adviser must use the same complete feasibility checks as open, or clearly say "potentially profitable if you hire a foreman." Include wages and startup cash in the recommendation.

### 15. Hiring immediately prepays wages without a clear preview
Status: observed UX defect; tester also made a budget mistake.
`labour carpenter` quoted 355,922 cash/year, next hire 355,925. At 104, hiring one immediately changed 191,602 cash to −164,320. `log` later explains the transaction as a finder's fee and first year in advance; `money` shows credit against that year's wages. No visible pre-hire preview in the help pages I read stated this immediate commitment or showed post-hire balance.
Wanted: `quote hire carpenter 1` or a nonmutating preview; distinguish immediate advance, fee, ongoing wage, and resulting debt. Do not require confirming every action, but make the consequences visible beforehand. The tester wrongly assumed annual settlement; the design should make that assumption difficult.

### 16. Opening deducts unpreviewed cash
Status: observed disclosure gap.
Opening bone setting reduced cash 569,528→567,463 (~2,065); buttons 134,229→125,807 (~8,422); toys −164,320→−184,338 (~20,018). Replies show capital after the action but do not explain the startup deduction. `help open` only says finished concerns begin earning/costing on opening. Detailed why pages reviewed for bone setting/buttons/toys did not display this separate startup payment. `ventures` does show a TO OPEN amount for known closed ordinary concerns, but only after completion and amid a long screen.
Wanted: upfront opening cost in why and a one-line cash reconciliation in open's reply. Clarify immediate startup cost versus annual upkeep, and reuse the same amounts everywhere.

### 17. Cash movement cannot be reconciled from displayed ledger/history
Status: suspected accounting or reporting issue; not diagnosed from source.
At 104 arrival cash 191,602. Hire reduced to −164,320; open toys to −184,338. Money then showed net +226,658/year (including a hiring-advance credit). After `step 1`, cash was +459,540: a +643,878 movement from the actual pre-step screen. `changes 1` instead reported +267,937, comparing arrival snapshots before in-year commands. During the step the carpenter was lost and toys closed. Current-year ledger and log do not give a transactional reconciliation explaining the movement, refunds if any, or advance settlement.
Wanted: a cash-flow ledger for the year that sums opening cash, every immediate command payment, earned receipts, upkeep, wages/advances, debt draw/repayment, interest, refunds, hazards, and ending cash. Investigate whether wage advances are credited correctly; this playtest does not assert double-credit as a proven cause.

### 18. A one-time advance credit is included in "recurring" net
Status: reproduced semantic/forecast problem.
At 104 ledger wages 355,925, of which already paid advances 355,922. The displayed recurring net +226,658 reflects the advance offset, while future years would require the full wage again if the employee remains. This is useful settlement information but not a stable recurring annual margin.
Wanted: show recurring profit before advance settlement separately from cash due this year. Existing distinction between projects and recurring costs is good; apply it consistently to payroll advances and other one-time flows.

### 19. Commission help does not explain eligibility before purchase
Status: reproduced; costly discovery.
At 105, `commission carpenter 500` cost 142,273 and only then explained these hours are for projects this year. Toys still could not open: 0.00 free specialist foreman FTE. Generic craft capacity increased to 1.2 in why, which reinforces the need to distinguish generic headcount-equivalents from specialist operating eligibility.
Wanted: price quote, expiry, eligible use, and explicit exclusion from foreman supervision before buying. Offer paid part-time specialist supervision. Provide a visible cancel/refund policy for unspent commissioned work. I did not find one in the index; absence has not been proven.

### 20. Turnover for a sole employee is difficult to understand/manage
Status: observed gameplay friction; not asserting the random result is a bug.
First carpenter hired in 104 was lost in that same year's step, closing toys. Message says "to death and to better offers," combining two distinct causes for one individual. No pre-hire retention/turnover probability was shown in labour carpenter. State's generic "spare craftsmen before it closes" warning did not convey specialist vulnerability.
Wanted: distinguish death, departure, and poaching in events; expose approximate retention risk and support continuity planning or automatic replacement with a budget cap. Check existing policies before adding redundant automation. First-year turnover is plausible but should be understandable and manageable.

### 21. Han glass introduction conflicts with the playable prerequisites
Status: reproduced scenario inconsistency.
Han introduction says glass is missing and the optical branch must start from sand/furnace. At 106, `why civ_glass_windows` shows zero cost, zero time, zero risk, CAN START NOW, with mat_glass_soda already met. No glass technology had been built by me. Population at 110 also estimates existing glassblowers. This appears inconsistent with the advertised opening challenge, though the deeper optical route was not tested.
Wanted: audit civilisation grants versus narrative and zero-cost inherited nodes. Explain whether a granted node represents household knowledge, local industrial capability, or imported historical knowledge. Avoid claiming all optics are therefore easy.

### 22. More Roman/generic prose leaks into Han play
Status: observed localisation/editorial issues.
Scientific-method why page focuses on displacing Aristotle and Galen and their chairs/guilds in the Han campaign. Risk prose references "what a break tester meant" and includes awkward "shifts in what this society values-side counterpart" language. Population directs players to `labour.py`'s TRADE_DENSITY for citations/placeholders, a source-code reference that a nontechnical player should not need. Corpus does use classical Chinese appropriately, but its material requirement is 4,000 papyrus sheets: review that choice against the stated paper context rather than assuming an error without testing substitutes.
Wanted: culturally appropriate opposition/institution text, concise historical risk descriptions, and an in-game explanation of estimate confidence. Keep developer/source guidance in developer documentation.

### 23. Advisor and displays omit some institutional costs
Status: observed reporting weakness.
State's combined closed-concern earning figure of 370,264 is the toy venture's quoted revenue minus upkeep, excluding the expensive carpenter needed to operate it. Science/standards are costly zero-revenue concerns, but the generic "nothing earning" completion message treats them like shops.
Wanted: net-profit estimates including necessary staffing; distinguish income businesses from maintained scientific/institutional capabilities. Explain why a zero-income concern would be opened and what is lost when it is not maintained.

### 24. Staff cushion warnings are ambiguous
Status: observed, unresolved.
State repeatedly says bone setting has "1.2 spare scholars before it closes" and buttons "1.5 spare craftsmen" with only one founder scholar and one founder craft hand. Specialist carpenter attrition closed toys even while aggregate craft capacity remained. I cannot reconstruct the cushion from visible totals.
Wanted: clear free FTE, required FTE, available named specialists, and the exact minimum whose loss would close each concern. Explain rounding and fractional requirements.

### 25. Money and ventures quote different upkeep figures
Status: reproduced discrepancy; may be base-versus-adjusted values, undocumented in the screens.
At 104, open/ledger showed button upkeep 2,502 and toy upkeep 5,004 (total 7,505 rounded). Immediately following, ventures showed costs/year 1,876 for buttons and 3,753 for toys. Closed science appeared at 187,634/year there versus 250,178 in its why page. These approximately 0.75 relationships suggest price adjustment, but no screen explained why the operational totals differ.
Wanted: use actual current annual charges consistently, with base/reference prices explicitly labelled if useful. A player should not have to infer multipliers across menus.

### 26. Annual changes miss explanations for standing shifts
Status: observed reporting gap.
Science's completion named w_magic_fear and w_novelty but gave no before/after values in the step. After starting free physician protection, scandal rose 0.79→3.8 by 107 with no corresponding step event explaining why. Cause unverified.
Wanted: include quantitative standing/value changes and their causes in a concise annual recap; disclose nonfinancial costs of zero-cash nodes in why. Zero price/risk should not imply consequence-free.

### 27. Available-table labels and search semantics need polish
Status: observed UX defects.
Initial "CHEAPEST SIX RIGHT NOW" displayed only five rows. Names are truncated to roughly twenty characters at default width, requiring extra why pages to identify them. At 106 `available find glass` returned entries with no glass in visible name/id (dioptra, gypsum plaster, malting, etc.), despite empty-search help saying it checks ids and names. Possibly description/tag matching; not verified.
Wanted: correct row labels, full or wrapped names, match highlights, and accurate search-scope wording. Affordability should distinguish cash-only from cash-plus-credit, and revenue from staffing-adjusted profit.

### 28. Finding goal progress requires several screens
Status: observed UX friction.
For checkpoint status I used state, money, values, population, and score. Values is beliefs, and population gives headcounts/trades but not literacy. Literacy raw 0.06 was on score, alongside normalized 0.521. Score is explicitly provisional until the primary goal is won; no consolidated secondary-goal progress view was encountered.
Wanted: a campaign dashboard with current chosen goals, absolute measurements/thresholds, timeline, cash reserves, and open/closed institutions. Show literacy as 6% rather than only a raw fraction, and explain scoring normalization without mixing it with goal progress.

### 29. Reserve planning and intentional waiting lack support
Status: observed design/UX opportunity.
Years 107–109 were intentionally spent saving for standards, with nearly all founder hours unused. Stuck sees no active project and suggests cheapest free knowledge rather than respecting the player's intended savings goal. Living and appearances are bundled, so I cannot calculate a true subsistence reserve from the basic ledger.
Wanted: mark a planned project and savings target; show estimated affordability year under current income, with uncertainty. Separate essential living costs from status spending. Offer cheap preliminary experiments/discovery clues for idle founder time, if not already provided elsewhere.

### 30. Instant knowledge completion and annual dates need clearer presentation
Status: observed clarity issue.
Free zero-time nodes complete immediately when started; the following step report does not list them, while log does. Ordinary completions during 100→101 are dated "COMPLETED 100" while the displayed state is YEAR 101. Both conventions can be coherent, but it is easy to mix up action-year and arrival-year records.
Wanted: a unified "During 100→101" recap including immediate actions/completions and cash commitments, or clearly labelled timestamps. State's long repeated text could be optional after the first few years.

## Updated mod and feature priorities

Priority 1 — make the existing game trustworthy and readable:
- Shared feasibility checks for why, open, ventures, and stuck.
- Quote/preview for hires, commissions, and openings, with upfront cash and future annual obligations.
- Reconciled yearly cash flow and clear actual-versus-reference prices.
- A unified campaign/goal dashboard and shorter default reference/state screens.
- Civilisation narrative/grant consistency and culturally appropriate descriptions.

Priority 2 — deepen choices exposed by this playtest:
- Part-time specialist supervision and realistic continuity contracts.
- Retention, apprenticeship, and named loss causes; institutions that outlast individuals.
- Cheap experimental work during cash-limited years, fog-compatible research journal, and player savings targets.
- Distinguish an individual's notes from an endowed corpus/publication institution so preserving some knowledge is possible at smaller scale. Check existing writing/copying nodes before adding duplicates.
- Safer medical-care goals and measured outcomes; do not equate revenue with patient benefit. The obstetric text led me to decline that venture.
- Localised material substitutions (e.g. writing media) if current mechanics do not already allow them.

I would fix misleading planning information before adding more technologies. No claim that the full game lacks every requested mechanic: these requests describe what the player could not find or understand during this ten-year run.

## Second-decade update: 110–120 AD

Status: ten more individual yearly steps, paused at 120. No game source/data/other repository documentation/save contents inspected; no gameplay scripts, JSON automation, or rush. New checkpoint han-fog-year-120.json; yearly journal updated through 120. The historical year-110 local snapshot was preserved while a live session file updated.

Six completions this decade: employment contracts, straightedge/reference straightness, decimal arithmetic curriculum, basic statistics, symbolic algebra, vector control. Seventeen player-built technologies total, transistor-route nodes 17 versus 14 at 110. One first-attempt research failure: mean/variance, still retrying. Exponent notation is also active; total unpaid project commitment 119,440. Cash 327,674; recurring net +284,054/year; no debt or employees. Buttons and bone setting remain open, toys remain closed. General literacy still 6%. No slavery purchased; larger campaign goals unmet. No historical/supply/fire/turnover event reported this decade.

Ordinary research budgeting was substantially clearer than the earlier staffing/cash episode: at 116→117 the predicted 17,874 remaining balance matched the result. Small borrowing for arithmetic was recoverable by pausing expenditure. Do not generalize the unresolved hiring/advance issue to all cash flows.

### 31. Farm purchase cannot be quoted
Status: reproduced UX gap; price route not exhaustively searched.
Economy help recommends farmland to reduce staple costs. `quote farm 10` was refused with instructions that quotes cover mines, forests, or people. I declined to buy blind rather than open more menus or try zero-quantity purchases.
Wanted: a consistent quote interface for every supported purchase, including farms, housing, schools, materials, hires, commissions, and openings. At minimum, help buy should show price calculation and immediate effects. This is a player need, not proof that no other screen contains the price.

### 32. Institution descriptions omit measurable effects
Status: observed decision-information gap.
Employment-contract why says agreements protect employer/employee and reduce disputes, but shows no retention, productivity, wage, or social effect value. I built it for the role-play goal without assuming it prevents turnover. Apprenticeship describes a binding youth/master term, but does not present consent, compensation, or an alternative voluntary training contract.
Wanted: distinguish descriptive historical context from implemented effects, even when the answer is "knowledge only." Clearly expose any labor/retention modifiers. Optional mod: paid, voluntary apprenticeship and transparent protections for both parties.

### 33. Workforce guidance offers an unaffordable institutional fallback
Status: observed guidance-quality issue.
With one founder scholar, atomic theory/logarithms heard-of messages say two scholars are needed and suggest `hire scholar 2` or school_founded. Only one additional scholar is needed to reach two, so the example invites overhiring. School why quotes 19,988,031 cost, 6,254,459 annual upkeep, and two unknown prerequisites. It is not a viable near-term alternative for this household.
Wanted: state the actual deficit, recommend the minimum additional staff, and label long-term institution options as currently blocked/unaffordable. Show hire/commission alternatives with full prices and whether temporary hours satisfy this particular requirement.

### 34. Algebra's verbal example and equation disagree
Status: reproduced educational text error.
`why algebra_symbolic` says "when you add 5 and triple it you get 24" but writes 3x + 5 = 24 and gives x = 19/3. Adding five then tripling means 3(x + 5) = 24, with x = 3. The displayed equation/solution pair is correct together; the preceding verbal translation is wrong.
Wanted: change words to "triple it and add 5" or change equation and answer to match the existing words.

### 35. Actual research failure charge exceeds quoted penalty
Status: reproduced; high-impact financial disclosure discrepancy.
Before starting mean/variance at 117, why showed total 258,678 and IF IT FAILS: 103,471 gone (40%). At the first failure during 118→119, the event charged 172,452. Cash confirms this: 176,625 + 285,918 recurring net −129,339 annual project payment −172,452 failure loss = 160,752 ending cash (displayed rounding). The larger loss is approximately the quoted loss divided by the 0.6 civilisation factor.
Wanted: quote and resolution must use the same effective project price and modifiers. Check whether the civilisation discount is missing from failure-cost calculation; this is an inference from the numeric relationship, not a source diagnosis. Any per-year or changing modifiers that legitimately change the penalty must be disclosed before the roll. This unexpected loss led me to abandon the geometry plan.

### 36. Unlabelled retained-staff prose suggests benefits without specifying any
Status: reproduced display defect; benefit existence unverified.
Vector control, epidemiology, mean/variance, and exponents why pages end with "people kept on your own staff" explanatory prose, but no label, number, or trade before it. Vector control completion left employee counts at zero. The phrase alone creates an expectation of durable collaborators without usable planning information.
Wanted: show exact staff gain by trade, whether hired/paid/trained, and annual cost when nonzero; omit the explanatory block when no gain applies. Likewise show measured public-health effects if implemented. Completing vector control should not require guessing whether it adds workers or reduces disease.

### 37. Useful combined-commitment warning leaks implementation terminology
Status: observed UX/editorial defect; the warning itself is good.
Starting algebra with vector control active, and later exponents with a retry active, displayed combined amounts still promised across all work. This helped avoid confusing one-project affordability with collective exposure. However prose includes literal `funding_capacity()` and `your_real_ceiling`, and says what the internal function judges safe.
Wanted: retain the warning, translate to "estimated sustainable commitments," and show remaining annual payments and recurring income alongside the total. The "likely draw on credit" headline is based on full commitments versus current cash: vector control/mean-variance warned of borrowing although yearly income covered their annual shares. Label that conditional full-cost cash gap accurately rather than implying an imminent loan.

### 38. Broad curricula and separate concept nodes need a clearer relationship
Status: observed conceptual ambiguity, not proven duplicate mechanics.
Arithmetic teaches zero, negatives, decimal fractions, yet after completion separate zero-as-number, negative-number, and decimal-fraction nodes are available with multi-year floors. Symbolic algebra uses x and an equals sign while equals-sign/operator-symbol nodes remain unbuilt. Basic statistics covers averages and errors while a later mean/variance node adds another teaching project.
Wanted: explain whether broad nodes establish a small taught curriculum, while detailed nodes diffuse formal conventions across society or create printing standards. Current adoption prose is helpful but does not clearly distinguish scope. Make separate benefits and populations visible so players know why both are valuable.

### 39. Fog can hide conceptual guidance as well as the route
Status: observed discovery friction/design tradeoff.
Case hardening is heard of, but blocked by one unnamed prerequisite; the metallurgy list does not reveal a clear practical lead. Epidemiology similarly requires an unknown thing. I can understand those real-world concepts generally while not knowing which simulator node represents the missing step. Germ and lens searches have returned nothing so far.
Wanted: practical, diegetic hints (material purity, observation skill, instruments, record keeping, suppliers) or inexpensive exploratory experiments. Preserve the hidden tree rather than giving a complete path. Fog did not prevent solvent early progress, but discovery sometimes feels like finding the author's classification rather than investigating an engineering obstacle.

### 40. Failure learning is promising, but the cause is generic
Status: observed design feedback.
The mean/variance failure reduced next risk 15%→11%, retained 0.7 of 2.0 elapsed years, and required redoing 24 founder hours. These are good recovery mechanics. "It did not work" does not explain what failed in teaching statistics—adoption, recording, arithmetic mistakes, political resistance, or curriculum design. The system says the cause is understood without telling the player that cause.
Wanted: thematic failure descriptions and optional choices about response, such as simplify the curriculum, recruit a teacher, run more trials, or revise measurements. Effects and costs should be explicit; avoid invented flavor that contradicts actual modifiers.

### 41. Retry calendar progress/ETA is not visible in the active-project overview
Status: observed UX gap.
At 119 failure report gave 0.7 years carried forward; at 120 state says mean/variance is fully supplied with hours/money and "waiting on the calendar," without elapsed/required years or an estimated completion year. I must retain the failure message to infer the remaining wait. Exponents instead show annual money pace and amount owed, which is clearer.
Wanted: show retained calendar progress, current effective floor, remaining time, attempt number, and current retry risk in state/portfolio or a short project-detail screen. Forecasts should be labelled uncertain, especially when failures are possible.

### 42. Negative balance and interest estimates versus zero paid interest
Status: observed financing-rule question; not a proven interest bug.
Arithmetic ended at 113 with −124,613 cash, credit 4% used, and 24,368 annual interest listed. By 114 cash was positive again. At 120 ledger still reports interest paid so far zero (also zero after the earlier 104 hiring debt episode). This may follow annual settlement ordering/repayment rules, but those rules were not clear from economy help's "arrears cost interest" statement.
Wanted: explain exactly when interest accrues and is charged, including whether beginning-year debt is cleared by whole-year income before interest. Include actual interest payments and debt timing in the yearly cash reconciliation. Do not claim a free-credit exploit without a controlled player-interface test.

## Second-decade feature/mod priorities

- Highest priority: reconcile quoted and actual failure charges (#35); then fix false opening guidance and disclose all staffing costs from the previous decade.
- Small, voluntary teaching/publication projects: a practical handbook, household lessons, or partial corpus, with measurable scope and benefits. These may exist deeper under fog; improve discovery before necessarily adding them.
- A practical research notebook with experimentation clues and current observed dependencies, plus a planned-savings target.
- A complete decision preview for all purchases and workforce actions.
- Separate curriculum, adoption, notation, and industrial implementation scope clearly. A taught curriculum should not silently imply society-wide adoption, nor should the UI make follow-on nodes feel redundant.
- Public-health outcome reporting: capability completion versus services actually implemented and measurable mortality changes. Score's general literacy remains 6% despite the explicit elite-literacy effect of arithmetic; explain the distinction.
- More thematic failed experiments/teaching outcomes while preserving the useful learning and calendar carryover mechanics.

Overall opinion at 120: financially manageable and interesting under fog. Ordinary project pacing is predictable enough to use deliberately; a short-lived arithmetic deficit was recoverable. Discovery and trustworthy cost/requirement information remain the main obstacles I can actually demonstrate. Full-campaign difficulty, the 150-year claim, and the realism of late industrial supply chains remain untested.

## Player assessment at 120 AD — after twenty elapsed years

Requested assessment of fun, realism, difficulty, economics, systems, command use, and UX. No additional game time passed for this assessment. Opinions and estimates below are based on the root README and inspected player screens; no historical sources or game source files were consulted. They are not historical validation or a full-campaign review.

### Overall opinion and fun

Promising and interesting, with a substantial information-trust problem. My subjective ratings: premise 8/10, current enjoyment 6/10, UI/UX 4/10. These are impressions after twenty years, not objective quality measures.

The best moments were connecting measurement tools, taught arithmetic, controlled comparison, and public-health work; planning overlapping budgets; and seeing a manageable borrowing decision work. Failure learning and calendar carryover are good mechanics. The least enjoyable moments were reading repetitive screens, discovering mandatory foremen after paying for a venture, buying a commission that could not perform the intended job, and finding the failure penalty larger than quoted. Intentional cash-saving years can also feel passive.

I want more of the consequential planning and discovery, with less difficulty caused by missing or contradictory information. An expensive but fairly disclosed constraint is a good challenge. An undisclosed cost is a UI defect, not added strategic depth.

### Realism: what seems convincing and what does not

The broad causal structure is credible as a game abstraction: knowledge differs from industrial capability; projects need hours, materials, specialist labor, money, adoption time, and political legitimacy. Finished knowledge is distinct from an operating institution/business. Skilled labor is not fully fungible; a local household cannot recruit the entire empire. Buildings or knowledge can remain while the staff required to operate them disappear.

Historical fidelity has not been verified. The Han introduction conflicts with available zero-cost glass panes and an already-met soda-glass prerequisite. Roman wealth categories and Aristotle/Galen-focused opposition appear in Han play. A lone newcomer automatically earns most income from invasive medical practice without a demonstrated process of acquiring patients, credibility, or practical surgical skill. Numerical standing and whole-country literacy shifts simplify social processes considerably. Immortality removes an enormous real-world constraint, and fog hides an author's prerequisite graph rather than literally representing what a modern-knowledge founder knows.

As a thought experiment it can illustrate bottlenecks well. I would not use its current cash values, technology floors, or social responses to forecast actual historical outcomes. Practical workshop tacit knowledge, yields, calibration, maintenance, language, negotiations, and succession would all matter in the real-world scenario; how deeply the game handles each is not established. Some may exist in untested systems or undiscovered nodes.

### Technology-tree size estimate

Loose guess: around 600 nodes, with a plausible range roughly 400–1,000. Confidence low; this is an estimate, not a count. Initial state had 109 granted technologies and available showed 196 startable items, then later discoveries exposed many additional concepts. If available excludes already-finished grants, those initial groups alone imply about 305 distinct nodes. Several hundred is much more plausible than a few dozen. Individual notation, statistical, manufacturing, and material-process nodes suggest a granular tree.

The menu's 181 transistor prerequisites and 218 literacy-goal prerequisites describe particular goal closures, not the entire tree. Hidden branches could make the real total considerably larger than my guess. No attempt was made to bypass fog or inspect the data.

### Difficulty: advertised, experienced, and projected

Advertised: transistor ideal floor 142 years; Challenge 400 is called tight, Standard 500 is the default, Relaxed 650, Endless unlimited. Only the deadline changes across these presets, according to setup; costs and failure odds do not. The game itself presents a centuries-long campaign, not an easy 150-year completion.

Experienced so far: survival and ordinary project financing are manageable. Research choice under fog is harder; unknown prerequisites can conceal useful next steps. Expanding income through specialist businesses proved less forgiving than basic knowledge projects. One research failure across twenty years does not establish the underlying campaign risk; I benefited from many successful attempts.

Progress estimate: player-built total 17 after twenty years, about 0.85 completions/year, including free and optional projects. Transistor-route count rose 11→17: six additional target-route nodes, about 0.3/year. The latest decade also added three target-route nodes in ten years. Taking the 181-prerequisite goal and current route count as approximately comparable, roughly 160–165 target nodes remain. At the same rate that would take about 540–550 more years, finishing around 660–670 AD, after the 600 AD horizon.

That is a deliberately crude linear extrapolation, not a win forecast: prerequisite/goal inclusion may differ, parallel work may accelerate greatly, funding/staffing may expand, and later technologies may take longer. With 480 years remaining, roughly 0.34 target nodes/year would be needed if the comparable remaining count is 164, versus 0.30 observed. Numerically the gap is not huge, but sustaining that rate through later bottlenecks and political crises is untested. My current approach needs better focus, income expansion, and staffed parallel research. No credible 150-year claim can be made from this run.

### Systems and complexity

- Projects: deeper than a simple unlock purchase. Founder hours, calendar floors, annual funding pace, simultaneous commitments, retries, and retained learning all matter. This has been the most readable and enjoyable system after the basics were learned.
- Economy: recurring income/upkeep, customer ramp-up, credit, upfront payments, living/appearance costs, and changing market takings are visible. Raw material production, mines, land, and wider power constraints were described in help but not meaningfully tested. Do not treat their mere presence as evidence of deep simulation.
- Labor: specialist foremen, generic FTE, employment advances, annual wages, hired construction hours, and turnover add real planning complexity. Their UI integration is currently poor.
- Institutions/society: adoption, elite literacy, state capacity, reputation, protection, scandal, and eminence appear and some changed. Effects are often explained qualitatively rather than quantitatively. The corpus and school are enormous funded institutions rather than small writing/teaching actions.
- History/resilience: the first decade had a supply disruption, a fire, and turnover. Large scheduled Han crises have not yet been experienced. Knowledge vulnerability is shown, but provisional score resilience does not by itself establish protection.
- Fog/discovery: it successfully limits route planning. It can also make progress feel like guessing classifications or node names. Practical clues would retain uncertainty while improving agency.

Overall it is more complex than the five-command introduction implies. Core actions are simple, but interacting systems make informed choices demanding. Some complexity represents interesting constraints; some comes from inconsistent definitions and scattered information.

### Economic difficulty and historical money plausibility

Ordinary research budgeting is now fairly easy for me: annual income versus annual project payment is often enough to make a reasonable decision. Choosing and staffing profitable new businesses is harder, and expensive institutions remain out of reach. Most income is still the automatic initial medical practice, not a business I built. This softens survival difficulty substantially.

At 120 revenue is 745,110/year, living/appearances 458,555, upkeep 2,502, net 284,054, cash 327,674. Buttons earn 132,469 and bone setting 15,847. No employee wages are currently paid. The negative arithmetic balance was recoverable; no interest has been recorded as paid, an unresolved rule/accounting question.

Absolute historical cash plausibility cannot be assessed from "cash" without denomination, exchange assumptions, food/rent basket, and scale. Within the displayed model, initial 750,651 cash equalled four laborer-years, implying about 187,663 cash per initial laborer-year. The quoted carpenter salary 355,922 is about 1.9 such wage-years. Initial bundled living/appearance spending 440,346 was about 2.35 laborer-years annually; current 458,555 is about 2.44 using that initial reference. Those ratios are useful intuition, not verified Han wage estimates. They also show why the poor-scholar narrative and large mandatory lifestyle bill need clearer explanation.

The game gives enough numbers to budget regular projects, but not enough cultural/purchasing-power context to believe the prices as a period economy. Large salary/operation/institution values need a clearer statement of household versus business versus empire-scale scope.

### Commands, help, and interaction effort

About 23 distinct in-game commands used: help, options, state, money, available, why, start, step, open, risk, labour, commission, hire, changes, log, stuck, population, values, score, save, quit, quote, ventures. This excludes menu selections, aliases not actually entered, launch commands, and file-delivery work. Approximately 140 in-game command submissions across setup and twenty years is a manual rough tally, not an instrumented count; many are read-only investigations and checkpoint screens.

Most regular play uses a small core: available, why, start, step, money, and sometimes open. Typing them is easy. Understanding why a choice is feasible can require several screens. I have not exhausted all commands, policies, or aliases.

Help is a good index and useful for syntax, economy concepts, fog, and session saving. It is weaker as a trustworthy operational manual: incorrect options alias, superficial open/commission help, missed foreman requirements, and generic repeated prose. It sends me to information, but does not reliably assemble the complete decision. There are enough commands; adding more is a lower priority than making existing commands agree and exposing the missing information.

UI/UX: command execution is simple, information discovery and verification are cumbersome. Long IDs, truncated titles, repeated explanations, raw fractions, hidden opening conditions, and filesystem-based saves impose unnecessary work. Good points: readable state screens, explicit irreversible-choice warnings, natural-word commands, annual event messages, autosaves, subject grouping, and combined project commitments. Mechanical interaction is easy once launched; launch/save-path handling and informed planning are less beginner-friendly.

### Confidence after twenty years

I can budget and overlap ordinary research projects, interpret most basic state fields, and recover from modest borrowing. I am more confident about making meaningful early progress than about winning. I have not solved sustained specialist staffing, large institutions, a durable income expansion, full disease/education routes, or late industrial supply chains. Approaching political pressure at 125 will be a new test.

The best next improvements are: consistent feasibility and cost calculations; all-action previews; a concise unified dashboard; visible retry ETA and outcomes; small voluntary teaching/publication projects; practical fog clues; localisation; and thematic, well-explained failures. Fix trust and readability before adding another pile of technologies.

Precision caveat: score displays literacy raw 0.06 at both checkpoints while its normalized value changes. The visible general literacy is still about 6%, but rounding could conceal a small actual change. Earlier journal statements describe displayed values, not a verified exact zero change. More useful precision and clear separation of elite/general literacy would help.

## Follow-up playtest: 120–135 AD

Played exactly fifteen additional years through the interface, with fog on. Eight completions raised built technologies from 17 to 25, but primary-route progress rose only from 17 to 20. Written corpus achieved a chosen publication milestone and is listed as a knowledge hedge even while closed. A pharmacy became a substantial income source. End cash 1,847,157, recurring surplus 768,992/year, debt zero, three running concerns, no employees or active projects. General literacy still displays 6%. One converter failure, one scholar departure, and two fire events occurred (one fire destroyed nothing). All annual decisions and opinions are in the journal.

The game feels more rewarding now: publication and a new business changed our prospects, and reserves absorbed setbacks. Regular finance is manageable; research discovery, institution costs, staffing, and decision previews remain demanding. I still cannot infer a credible victory date from three additional route nodes in fifteen years. Having a healthy early business does not establish resilience through the rebellion or later fragmentation.

### New findings and requests

43. **Turnover and annual wages need an explicit settlement breakdown (reinforces 17 and 20).** At 129 the ledger showed cash 617,171, recurring net 89,852, and next project payments 1,042,556. That suggests −335,533 after the step. Actual 130 cash was +323,182 following scholar departure: a difference of exactly 658,715, the preceding annual scholar wage. Strong evidence that departure removes the whole annual wage at resolution; no source inspection or definitive diagnosis. Show wages actually paid, employment duration, departure timing, and each cash adjustment. A pro-rated staffing/payroll mod would be interesting if this is intentional.

44. **Corpus completion estimate does not communicate the binding payment schedule.** Started in 125 at cost 2,955,858; preview gave an effective floor about 8.5 years and expected time about 8.8. Founder hours finished by 128, but annual payments remained 295,586 and completion occurred in 135, ten years after starting. Show an ETA that considers outstanding payments, not only discounted work, and explain whether early repayment is possible through normal controls.

45. **Historical risk wording hides severity.** “Output factor: you take 100% of it” reports exposure, not the amount of loss. The regency event later reported output at 94% of normal. Present severity and mitigation together before the event; avoid making players guess whether 100% means total production loss.

46. **Staffing advice ignores the immortal-founder context.** Generic warnings about losing the only scholar and recommendations to hire two appeared with an immortal founder. Recommendations should distinguish guaranteed founder capacity from employees, and recommend the additional headcount actually needed.

47. **Fire feedback invites a realism question.** In 123 a fire destroyed nothing because cash was already negative. Later a fire destroyed 197,186. What physical property burns, and why is damage tied to positive cash? This is a player question rather than a verified implementation defect. A property/inventory/manuscript-location model, insurance, and meaningful fire precautions would make loss feel less like a random balance deduction.

48. **Scale and price conflict with descriptions.** Case hardening is called cheap/immediate but quoted at 1,980,106 and two craft workers; the three-plate method says Iron-Age workshop tools suffice but quoted over four million with three craft workers and hired machinist work unavailable locally. Distinguish demonstrating a principle, equipping a workshop, training a trade, and establishing industry. Small prototypes would be an appealing feature/mod.

49. **Arrival orientation is difficult to value.** An optional orientation quoted 1,359,407 after thirty years of local experience and described prices, law, contacts, and avoiding blunders, without a clear action preview connecting those benefits to actual problems. Explain concrete effects and offer smaller, timely local consultations. “No longer a prerequisite” also reads as development history rather than player guidance.

50. **Knowledge protection versus operation needs clearer benefit labels.** Corpus completion is a risk hedge while its standing benefit explicitly requires opening. That distinction can be sensible, but previews should label permanent knowledge benefits separately from staffed, recurring institutional effects. Similarly, a converter with zero direct revenue and significant upkeep needs a clear explanation of what operating it enables before a player spends money.

### Corrections and additional evidence on earlier notes

- **Issue 42, interest:** persistent pharmacy debt did incur interest. The ledger records 73,617 paid by 124 and still records that total at 135. The earlier observation of negative cash with zero recorded interest should not be treated as proof that interest is never charged. Timing remains insufficiently explained.
- **Issue 35, failure penalty:** converter failure in 133 cost 183,162, matching its undiscounted quote. The earlier mean/variance mismatch was on a discounted project. This supports a modifier-related inconsistency as a hypothesis, without proving the cause.
- **Issue 26, changes:** corpus completion announces elite-literacy/value effects without an easy before/after explanation. General literacy still rounds to 6%; do not confuse elite literacy with the chosen general-literacy goal.

Priority remains trustworthy action previews and settlement/ETA explanations. Additional technologies would be less valuable to this playtest than understandable costs, modest teaching/publication options, and visible links between knowledge, production, and institutions.

## Follow-up playtest: 135–150 AD

Played fifteen more years, fog on, entirely through ordinary terminal commands. Followed the player's hint by browsing completed/available names and reasoning from existing foundations. This helped find an enormous shipping opportunity and affordable scientific/precision experiments. It did not resolve case hardening. Twenty-four completions increased built49from25, but primary-route progress increased24from20. Calculus, logarithm tables, Newtonian mechanics, trained engineers/machinists, and operating corpus/cover identity are meaningful milestones. General literacy still displays6%.

End cash142,092,329, recurring surplus16,592,365, no debt,16employees,8operating concerns. Shipping alone provides27,546,803of31,485,151gross annual revenue before shared market adjustment. Five-year reserve goal comfortably achieved even net of207,257outstanding mortality-table commitment. One chuck failure, five staff departures across four events, and one7,510,465supply-disruption loss. No fire observed this interval. Spirit level completed but remains closed; mortality tables remain active. School, dispersed corpus, germ theory and primary victory remain unmet.

### New findings and requests

51. **Pagination syntax in help fails in normal text input.** `available all:true limit:40 sort:alpha` dumped all211startable rows; `available state done limit 30` and space-separated offset/sort worked. Help itself advertises colon syntax such as `state:blocked tag:<topic>`. No raw JSON workaround used. Make documented plain-text forms work consistently and add concise examples matching actual parsing. Large unrequested dumps are a direct UX cost.

52. **Subject/category navigation is unclear.** Completed technologies show education/processes categories, but `available education` and `available processes` returned nothing while the summary uses “mathematics and method,” “power and precision,” etc. Bare “manufacturing” also failed; “power” revealed manufacturing methods. Search results also match broad invisible tags/descriptions: steel returns papyrus/glass, print returns cryptography. Label category versus browsing subject, provide valid suggestions, and explain why search hits matched. Full names or an expanded name-only list would improve the player's suggested reasoning strategy.

53. **Shipping is an extreme balance and scope problem.** Large merchant sailing ships cost zero money/hours/time to learn, zero to open, zero annual upkeep. Five smiths allowed opening with5.33craft FTE including founder capacity; no vessel purchase or specific nautical foreman was required by the interface. After advances1,779,640, the first step lifted cash from1,335,109to9,663,018despite research and turnover. Mature shipping dwarfs every earlier business. By150shipping provides27.55m/year. Knowing an existing design can reasonably be free; owning/renting hulls, crews, maintenance, cargo capital, ports, routes and losses should have a price. This is observed behavior, not a source explanation. Fleet ownership/chartering and route-specific trade risks would be a high-value mod. The game became financially easy when this was discovered.

54. **One staffing shortfall closes unrelated businesses.** During138→139two smiths left, making the fleet understaffed. The game closed shipping, buttons, pharmacy and bone setting together, including the physician concerns whose scholar remained available. Reopening those smaller concerns succeeded without adding scholars. Prefer selectively closing the understaffed concern, offering a player-defined priority, or showing why a shared bottleneck really affects each business. Losing a ship supervisor should not automatically erase unrelated viable operations. This disrupted our income-continuity goal through interface staffing resolution, not a historical crisis.

55. **Failure quotes remain inconsistent beyond the earlier discount example.** Mandrel/chuck quote112,858; actual minor failure106,092. Ratio approximately0.94matches the regency output factor, but that is only a hypothesis. Earlier discounted mean/variance penalty was larger than quoted; converter penalty matched. Show the fixed project bill, failure base, applied modifiers, and actual deduction consistently. Do not rely on the quote for a precise large-project contingency until corrected.

56. **Training, trade classification, and guarantees conflict across screens.** Labour explicitly calls machinist craft, and graduation raised craft count; ventures prose says engineers, chemists and machinists are scholars and cannot watch a workshop. Training reply says only trained people can do the trade, then says hiring adds workers immediately; labour later says the only machinists are ours and their trainees. Clarify recruits versus trained staff, who can supervise, and which group contributes to project headcounts. The interface also inconsistently suggests counting all literate hires, while the prompt's scholar number did not include our scribes/engineers. No hidden staffing formula inspected.

57. **Portfolio predictions are hard to trust.** At142after hiring/commissioning, supply14,165scribe-hours, but portfolio demand37,035versus displayed annual requests10,000logarithms+600calculus. It printed calculus800hours “total to go” after state showed60%complete. After allocating calculus800, portfolio showed two projects but priorities2of3and3of3, and calculus still below the undirected logarithms. Later it successfully progressed; allocation therefore was not proven ineffective. Explain remaining work versus nominal total, annual throughput versus one-time demand, priority/queued work, and predicted versus last-resolved year. Preview bottlenecks before committing, not only warnings after start.

58. **ETA rounding and reputation estimates need repair (extends44).** At148complex numbers displayed51,130owed/51,129annual pace and “about2more years,” then completed next step. Mortality tables similarly show207,257owed at207,257annual pace but “about2more years.” Likely floating-point/rounding edge; source uninspected. Reputation-shortened start estimates still leave fixed nominal payment schedules (complex numbers3.9floor/4.4expected, actual5years). Show ETA from the actual binding constraint with sensible rounding.

59. **Localisation and static-date prose weaken the historical roleplay.** At144world-map description claims50years before Ptolemy's150AD, evidently referring to the100start date. Newtonian mechanics is explained entirely as overturning Aristotle in public in our Han campaign. Medical statistics includes “software automation” before any computer exists. Prefer current-date-aware claims, local persuasion contexts, and feasible contemporary demonstrations. These observations do not establish errors in historical event modelling.

60. **Accuracy and scale need more meaningful intermediate steps.** Height gauge promises0.1mm accuracy with only reproducible length as prerequisite and existing1mm craft tolerance; text says it needs a flat surface but the precision reference-surface work remains unavailable. Finery's3million kg charcoal and126mprice show factory scale, while case hardening was described cheap/immediate. Let the player distinguish prototype, workshop and mass production, and explain precision achieved by calibration versus toolmaking tolerance. This is a design/realism question rather than a verified impossible construction.

61. **Public-health goals lack an actionable coverage/outcome loop.** Vector control and mosquito nets give knowledge milestones; net text says high coverage is critical. I want to distribute a stated number locally and observe cases/deaths or coverage over time. The inspected node gives1.5kgcotton input but no obvious population coverage or treatment outcome. I have not exhausted all commands, so this is a request for discoverable controls, not proof no model exists. Mortality-table research is a player-chosen follow-up, not demonstrated access to actual disease outcomes. A local clinic/survey/intervention simulation would make this personal goal much more concrete.

62. **Reopening prose contradicts retained ramp progress.** Reopened shipping in139displayed about14.93mrevenue (66%ramp), not a fresh33%, while reply generically said custom would build over the first3years. Retaining customers through a short closure makes sense; show actual current ramp and time to full operation. Opening deductions also remain unpreviewed: identity deducted528,184and manometer84,757; their inspected annual upkeep was500,357and12,509respectively, which is insufficient to predict the opening payment. Those upkeep numbers were not opening-fee quotes. Show all components before opening (extends16).

### Current opinion and mod priorities

The scientific institution feels more substantial: training takes time, skilled staffing supports tools, scribes compete across projects, and crises consume reserves. I enjoyed that. However, free shipping undermines economic difficulty and historical plausibility. The large treasury is a consequence of that interface opportunity, not evidence that the overall game is easy to win. Four route nodes in fifteen years, hidden foundations, and expensive industrial commitments still make a victory-date estimate unreliable. Primary progress is24after50elapsed years; do not extrapolate a steady rate through unexplored industry.

Most valuable changes: consistent previews/ETAs and selective shutdowns first; fleet assets/routes/cargo/crew costs next; smaller teaching and industrial demonstrations; observable local health coverage; contextual historical persuasion. General-literacy goal remains stuck at displayed6% despite wealth and institutions. Keep the technology breadth, but make research discovery and the effect of spending legible.

Commands newly used this interval include train, allocate, portfolio and capacity, bringing the rough distinct-command total from23to27. Individual command entry is easy. Interpretation, repeated discovery screens, hidden opening conditions and portfolio discrepancies still take considerable effort. No gameplay automation or source/save inspection used; only player-facing output and our own notes read. Year150save exported, historical135checkpoint preserved.

## Year 150 checkpoint review — no time advanced

Full responses about industries, finances, impact and goals are in **bootstrap-year-150-review.md**. Read-only checks used help economy/buy/rush/population, economy/full, ventures, population, labour scribe and values. No purchases or time advances. Approximately 28 distinct commands used including this review.

Market effects are retrospective: buttons show a 7% uplift; the ledger deducts 342,969 for market absorption. No prospective substitution/saturation forecast found. Request a before-opening industry map and predicted changes to other concerns, with uncertainty.

Impact scale: country estimate 61,284,657; town 47,857. We employ 83.5% of reachable scribes but 1.8% of reachable smiths. Hiring raises scarce wages; identifiable rival displacement and tractor-driven farmer reassignment are untested. Elite literacy displays 99%, general 6%. Do not equate huge revenue with demonstrated national transformation.

**Shipping proposal, extending issue 53:** keep design knowledge free, charge for hulls/charter and operation. Illustrative game-unit fleet: 20 million starting capital (12 million hulls/equipment plus 8 million working capital/setup), 27.5 million gross annual sales, 19 million cargo purchases, 3 million crew/supervision, 1.2 million maintenance, 0.5 million ports/admin, 0.6 million insurance/expected losses; net 3.2 million before borrowing/tax/household costs. These are provisional balance targets, not historical prices or a single-vessel estimate. Define fleet size, voyages and cargo, then scale actual staff and wages. If revenue is margin/freight fees rather than gross sales, avoid counting cargo costs twice. Add sailors/captains/merchants, purchase versus charter, routes, voyage time, working capital, port limits and shipwreck/piracy/war risks. Aim roughly 2–5 million initial net on 20 million invested. Full table is in the review.

63. **Spelling friction:** `labour laborer` refused; only `labour labourer` recognised. The refusal supplies the correct list, but accepting common US/UK variants removes needless effort.

64. **Help discovery:** the five-command introduction can leave players unaware of the full `help commands` index and detailed `help <command>` pages. Promote both on the first screen. Help rush advertises preview and budget limits; read, not tested. Make detailed help consistent with actual parsing and feasibility before adding more commands.

## 150–175 AD follow-up: findings, bugs and requests

The earlier year-150 responses, industry/finance assessment and shipping report remain relevant. The free fleet issue is not a one-year curiosity: at 175 the ledger attributes 40,402,230 annual income to sea_merchant_ships_large, still with zero upkeep. Retain issue 53 and its conditional fleet-cost/profit proposal; the illustrative 20-million capital and 3.2-million net model is a design suggestion, not a historical price claim. The expanding business now feels like an industrial enterprise rather than one inventor's personal practice.

### 65. Institutional discovery under fog needs better clues
Patronage and workshop organization unlocked case hardening and other apparently technical projects. I spent too long searching metallurgy because the missing institution was hidden. That was partly my narrow exploration, but the interface could suggest a broad kind of obstacle (workshop organization, measuring equipment, specialist trade) without revealing the exact prerequisite or route. Names-only reasoning works better when the missing gate is a physical process than when it is an unseen social node.

### 66. Reading-lens narrative contradicts its unlock order
Lens grinding describes itself as the best first-year revenue product and a way to buy a first patron. In this campaign its prerequisite was workshop_first, which itself required patron_local. The suggested early strategy cannot follow that sequence. Revise the narrative or allow a modest demonstration lens before the full workshop.

### 67. Capability hierarchy is hard to interpret
A granted 1300°C capability did not satisfy the separately researched sustained 1100°C node. The latter's description says bronze, glass and bloomery societies already achieve this range. If these represent different duration, atmosphere or process-control capabilities, show that distinction prominently; otherwise stronger capabilities should satisfy weaker requirements. Player cannot determine whether this is intended granularity or a duplicate gate.

### 68. Zero-prerequisite technologies can appear late without explanation
Woodblock carving described itself as available on arrival with no prerequisites, but I first found it after opening the workshop. Could be a general institutional/visibility gate rather than an explicit prerequisite; not proven a bug. Explain global start/visibility conditions separately from the listed prerequisite chain.

### 69. Tiny cash remainders add whole years
Lead had 14,609 cash left and wood pulp 84 at 162; fire assay had five cash left at 165. All were shown waiting another year on annual absorption despite enormous available reserves. Sulfuric acid later had 1,143 left. These appear to be small pacing differences rather than meaningful construction constraints. Allow a tolerance/final settlement or explain why a remainder this small truly requires another annual resolution. This is an especially visible UX problem in a yearly game.

### 70. Failure losses differ from quoted amounts
Lead's start-time preview quoted a 43,574,231 failure loss, but the 162 resolution removed 60,370,697. Wire drawing also lost 448,716 on a 788,388 quoted project. Other failures differ in the other direction. Prices, severity or additional charges may explain this, but the player needs a breakdown. The start message says the project's bill is fixed. State what is fixed and whether the failure estimate is a bound, an average or severity-dependent.

### 71. Reputation-shortened calendars disagree with money pacing
Corpus dispersal quoted a 4.7-year floor at start (nominal eight), yet after one year it still owed 10,235,813 and said seven more years at 1,462,259 annually. At 175, four annual steps after starting, it still owed 5,849,035. The effective completion forecast should incorporate both calendar and payment pace. Advertising the shorter floor alone is misleading even if the nominal absorption limit is intended. Existing calendar/payment concerns now have a clear reproducible example.

### 72. Commodity substitution and scale need explanations
Finery mentions millions of kilograms of charcoal, while capacity initially showed large coal demand and no charcoal demand or shortage. Substitution may be legitimate; no source inspection was performed. Tell the player which fuel is actually being substituted, in what units, and what affects yield/cost. Distinguish a capability demonstration from a complete industrial site.

### 73. Completion effects need magnitude and reach
Germ theory announced population and belief effects; paper and printing announced literacy effects. The messages named fields but omitted size, geography, adoption and mechanism. At 175 score reports literacy 0.18, versus the earlier 0.06 baseline, but I cannot attribute increments or coverage from these messages. A before/after impact view would make public-health and literacy goals more satisfying and support credible historical impact claims.

### 74. Non-Roman campaign text still assumes Rome/Mediterranean
Observed Galen/humoral opposition in germ theory, Alexandrian cover in the laboratory, Almaden/Pliny in mercury, Cai Lun's paper not reaching the Mediterranean, and corpus distribution Britain-to-India in Later Han play. Some comparisons are useful historical context, but direct strategy advice often presumes the wrong region. Localize institutions, opponents, supply routes and corpus destinations; keep comparisons explicitly comparative. Avoid technical module references in player descriptions.

### 75. Non-coercive institutional route wanted
School founding requires freedman_staff, described as buying or binding workers, training them, releasing them and paying them. I declined to preserve my goal of never acquiring enslaved workers. Add paid apprenticeships, stipends, voluntary guild recruitment or debt relief without taking ownership. These could cost more or train more slowly. This is a concrete campaign choice, not a request to remove historical coercion from the setting.

### 76. Closure controls and error guidance are inconsistent
Repeated advice says hire, teach or close something. Literal close only accepts a mine material; mothball is the business command. My close precision_three_plate attempt produced a mineral error rather than suggesting mothball. The help index clarified it, but that took several menus. Say mothball in business advice; make close a context-aware alias, or return the correct command in the error.

### 77. Staffing priorities and automatic reopen need visible control
At 173 and 175 five smaller concerns closed while the large shops remained running, which is better than the earlier broad shutdown. Paper was one casualty despite being my priority. At 174 four concerns reopened automatically even with auto_open off, consuming the buffer I had rebuilt. Distinguish auto-restoration from auto-opening in policy; let players rank concerns and disable automatic restoration. A protected minimum staff buffer and replacement-hiring plan would reduce repetition.

### 78. Patron death recovery is unexplained
At 173 patron death lowered protection from about 61% to 37% and added four scandal, with auto_court_heir off. At 174 protection was back to 62% without courting an heir, paying a bribe or changing policy. I do not know whether passive patron_local recalculation overrides the event or there is another intended recovery. Show the cause, duration and a manual court-heir action. A one-year trend extrapolation also treated the one-time scandal jump as a repeating annual rate; label that uncertainty.

### 79. Training warning versus annual event order
Industrial hygiene started at 168 with a warning that zero ready chemists prevented all progress. It completed in the same annual resolution in which two chemists graduated. This may be intentional graduation-before-work ordering, but the training message said they join immediately afterward and cannot work until then. Explain whether graduates can supply that resolution's project work, or revise the warning.

### 80. Portfolio mixes current budget with historical allocations
At 167 it reported two active projects and 2,000 available founder hours, while individual rows referenced priority #5 of five and a 1,100-hour budget from the prior resolution. Last-year allocations are useful; label them as such and provide a distinct forecast for the coming resolution. The wire retry's temporary stall was explainable once the prior training expenditure was considered.

### 81. Search/filter syntax and broad matching add effort
available power offset 30 treated the whole phrase as a subject/search and returned nothing. The interface explicitly suggests offset paging but combining a subject with that option was not intuitive. Keyword searches for water or micrometer returned many tangential technologies, apparently through descriptions/tags. Offer name-only matching, persistent subject paging, and examples that actually compose. A visible category/name browser would help without revealing fogged prerequisites.

### 82. Scientist ceilings need consistent wording
Labour claimed the household could hold at most 6.2 people across lettered trades, although the roster already exceeded that across engineers, chemists, machinists, scholars and scribes. Hiring one additional scholar succeeded. This may really be a scholar market ceiling or a distinction between trained staff and market recruits. Revise the label to match the enforced rule.

## Updated enjoyment, balance and mod ideas at 175

The workshop discovery greatly improved the game: a linked path through steel, measuring tools, water power, paper, laboratory work and microscopy is enjoyable and understandable. Fog is playable in this run; I have not proven a win or estimated the remaining route fraction because its denominator is hidden. I would now expect to make substantial further progress, but will not promise a 150-year maximum-tech result.

Economy: cash grew from 142,092,329 at 150 to 1,538,998,657 at 175; recurring net from 16,592,365 to 131,940,681. This is financially forgiving after the free fleet and industrial ventures. Current revenue 210,800,510 minus upkeep 24,144,713, living/appearances 40,718,319 and wages 13,996,798 reconciles to the reported net within rounding. The 23,084,980 wealth-driven portion of living expenses is substantial, but we still hold about 19.5 years of all current recurring expenses. Forecasts remain uncertain because turnover, closures, failures, prices and hazards change them. Do not mistake ledger precision for historical certainty.

Impact: literacy score now reports 18%; population at 169 was 63.15 million, town roughly 48,934. No claim that the founder personally caused all population growth. Knowledge, industrial techniques and publishing plausibly make the founder influential, but the game does not demonstrate country-wide installations, documented lives saved, rival firms displaced or each farmer's occupational transition. Keep the earlier request for an adoption/coverage/causal-impact dashboard.

Goals: germ theory achieved, written corpus operating, no enslaved workers acquired, reserve goal achieved, positive income survived the regency crisis. Twenty-percent literacy and transistors remain unfinished. Corpus dispersal underway. Industrial hygiene added and completed. Vector-control/mosquito-net and mortality-table work is completed as knowledge; physical coverage remains unknown. Yellow Turban disruption not yet tested.

Requested mods/features: voluntary apprenticeship institutions; retention/working-condition controls; concern priorities and separate auto-restoration policy; geographic health/education coverage; safer-workshop adoption; causal impact timelines; uncertainty-aware forecasts; locally appropriate Han narrative and patron institutions; compact technology browser with useful fog-preserving clues. The strongest challenge now is finding coherent next steps and sustaining an organization, while repetitive staff replacement is less fun than those decisions.

Checkpoint: stopped at 175 after exactly 25 annual advances from 150. Saved with the game's save command. No source or save contents inspected; no gameplay scripts used. Year-by-year decisions and feelings recorded in bootstrap-yearly-journal.md.

## Post-175 discussion: automation, historical significance and condensed priorities

No game time advanced and no policy changed during this review. Next play session: try auto_hire for replacement staff and compare its actual behavior with the household cap and venture priorities. Consider auto_commission only after checking whether it buys the work we need; commissioned project hours previously did not satisfy specialist operating foremen. Keep research selection manual. Keep auto_buy_people off. Do not enable auto_open/auto_shed wholesale because a paper shop or knowledge-preservation institution may matter despite its financial return. Auto_court_heir is a reasonable convenience to test, but the unexplained passive protection rebound remains a reporting issue. Automation should remove repetition without choosing the campaign's values. Current controls do not advertise the budget cap, specialist guarantees and concern priorities I would ideally want.

Historical significance is a counterfactual estimate, not a demonstrated game outcome. A reliable workshop combining germ theory, experimental methods, precision measurement, laboratory chemistry and printing in Later Han could make its founder a major scientific patron and entrepreneur, with world-historical importance if successors preserve and diffuse the work. Fame might attach to a school or craft tradition rather than every discovery to one person. The game does not establish country-wide access, attributable lives saved, geopolitical outcomes or prevention of dynastic collapse. Its treasury suggests substantial wealth but cannot be converted responsibly into a modern fortune or an imperial wealth ranking. The no-aging founder would introduce an additional legitimacy issue that ordinary financial/eminence figures do not fully explain.

Historical context checked outside the game for this discussion only: Han already had paper and sophisticated astronomical/mechanical instruments (Metropolitan Museum, https://www.metmuseum.org/TOAH/hd/hand/hd_hand.htm). The Asian Art Museum places early woodblock printing around 600 and movable type in the Song (https://education.asianart.org/resources/the-invention-of-woodblock-printing-in-the-tang-and-song-dynasties/). Institut Pasteur describes the nineteenth-century experiments connecting microbes, disease and hygienic practice (https://www.pasteur.fr/en/about-us/middle-years-1862-1877). These comparisons do not validate the game's costs or individual project dates. Printing at 169 would be several centuries early; demonstrable germ theory would be roughly seventeen centuries ahead of the nineteenth-century experimental breakthrough. Paper alone is not a new invention for this location/period.

Condensed requests across issues 1–82, merging repeated observations:
1. Trustworthy previews for all actions: construction, failure, opening, staffing, wage advances, commissions and purchases; one consistent feasibility test across advice and execution.
2. Reconciled annual cash flow: immediate payments, advances, actual wages, departures, debt/interest, price modifiers, refunds and hazards; separate profit from this year's cash settlement.
3. Real completion forecasts: retained retry progress, money absorption, reputation, training and calendar constraints; prevent five-cash remainders adding whole years.
4. Workforce continuity: specialist foremen shown before building, consistent trade/FTE definitions and hiring limits, clear loss causes, part-time supervision, retention, replacement budgets and concern priorities; separate automatic restoration from opening.
5. Better discovery/help: concise/full help modes, correct aliases and syntax, common spellings, full names, meaningful subjects, working pagination, name-only searches and practical fog-preserving clues.
6. A unified goal/status dashboard: secondary goals, absolute literacy, reserve targets, open versus finished institutions, projected affordability, clear action-year dates and shorter recurring output.
7. Clear scale and adoption: prototype/workshop/factory distinctions, broad curriculum versus diffusion, stronger/weaker capability relationships, physical supplies versus learned knowledge, permanent versus operating benefits.
8. Observable social impact: health intervention coverage, incidence/deaths, literacy and education reach, magnitude of completion effects, industry competition/saturation forecasts and causal before/after views.
9. Economic and hazard realism: paid fleets/hulls/cargo/crew/maintenance/ports/risk, identifiable property fire losses, uncertainty and mitigation, purchasing-power context, scope-appropriate industrial prices and fuel substitution.
10. Institutions and historical flavor: voluntary paid apprenticeship/school path, small affordable publications/experiments, local Han opponents/patrons/materials/routes, correct dates and educational examples, no patch/code jargon in player prose, coherent patron-death consequences.
11. Beginner access: launchable interface, clear menu context, graphical navigation, consistent save destination and export/import, concise setup and internally consistent goal/mortality descriptions.

Highest priorities: reliable costs and ETAs; operational staffing/control; free-fleet balance; meaningful public-health/literacy outcomes. New 150–175 annoyances most worth reproducing: five-cash delay, 43.57m quoted versus 60.37m actual lead failure, corpus 4.7-year floor versus eight-year money schedule, late undisclosed workshop gate, close/mothball mismatch, automatic reopening with auto_open off, patron protection rebound, and coercive school prerequisite. Some are verified interface discrepancies; their internal causes remain uninspected.

## 175–200 AD: automatic hiring, rebellion and literacy

Played exactly 25 individual annual steps with fog on. Only player-facing screens used; no source/data/save inspection or gameplay scripts. Enabled auto_hire, leaving research/opening choices manual, auto_buy_people off and other previously-off policies unchanged. At 200: 5,226,158,143 cash, 373,563,720 recurring net, 66 employees, 23 concerns, 127 built technologies, 79 primary-route nodes. Literacy 21% and explicit literacy achievement; all three chosen secondary game goals achieved. Main transistor goal remains unfinished. No enslaved workers acquired. Saves and annual entries retained.

### 83. Subject pagination works, but option order is significant
Correction/extension of 51, 52 and 81: `available offset 30 subject metallurgy` successfully displayed the next subject page. `available subject metallurgy offset 30` treated the offset words as part of the subject and failed. `available category metallurgy offset 30` selected only the exact small category rather than the broad browsing subject. The interface can do the requested browsing; help should show a working composed example and parse options independent of order, or explain the grammar. Do not claim paging is universally broken.

### 84. Automatic hiring can bypass pending training and duplicate graduates
At 180, trained two electricians; reply said they would finish during 182 and nobody could do the work until then. At 181, auto_hire had already added two ready electricians. At 183, graduation raised electrician count to four. Auto-hire is useful, but pending graduation should be included in its staffing forecast; recruitment provenance and readiness should agree with training/labour messages. May be legitimate recruitment once a trade exists, but the claim that no ready worker exists is then misleading. This is an interface/behavior discrepancy; internal cause uninspected.

### 85. Auto-hire needs goals, budgets and specialist priorities
It restored trained specialists and rebuilt after sacking without repeated manual commands: clear positive UX result. However it also grows toward household capacity rather than merely replacing departures, and smaller concerns still closed repeatedly at the cap. It let scribes disappear while later adding many artisans. Provide replace-only versus expand modes, workforce targets, planned graduates, minimum specialist coverage, protected staffing cushion and a budget. Show purchases in annual events, not only a changed roster. Keep employer autonomy over which institution gets scarce attention. There is no evidence this trial bought enslaved workers; that policy stayed off.

### 86. Saltpetre shortage advice has wrong scale and insufficient purchase
Lead chamber started at 186, ran at 5%, and warned of about 0.00 tonnes/year short with `buy nitre 100` allegedly enough including a 20% buffer. Bought 100 m² at 187: 0.08 tonnes/year, but pace only rose to 7% and the same recommendation repeated. At 188 capacity showed about 0.10 supply against 1.1 demand. Bought another 1,700 m² (1,800 total, about 1.44 tonnes/year), after which the project completed all founder work next resolution. The recommended purchase did not clear the bottleneck and the displayed deficit was misleading. Audit tonne/kg conversion and align shortage advice with the capacity screen. Nitre research completion versus actual beds/output also needs an explicit explanation before starting dependent work.

### 87. Copper shortage advice contradicts itself
At 176–179 copper capacity was about 302 tonnes/year versus 1,200 demand, slowing a fully paid project to 25%. Warning said the market would not sell enough and advised digging, then said our own workings already covered today's demand even though mines showed none. The player could still finish through four years of market throughput without mining. Phrase the alternatives accurately: accept slower supply, acquire stock if possible, or invest in production. Mine quote was useful: 900 tonnes/year cost 12,035,246 upfront plus 92,878,713 yearly with three-year startup. I declined it on those figures.

### 88. Sacking report and staff units need reconciliation
During 187 resolution, sacking took 2,168,262,427 cash, reported 40.5 people gone and two projects reset. State afterward showed 25.9 staff and fractional trade entries, suddenly explaining these as continuous FTE/hiring/attrition rather than the earlier integer deaths/departures. Subsequent hiring restored integer rosters and the usual text. Need before/after counts, what the loss number includes, people versus productive capacity, casualty/departure causes and exact reset amounts. The lathe's founder work remained 100%, while the acid project was still incomplete; the wording does not make the project losses auditable. No source diagnosis asserted.

### 89. State requisition is an automatic choice presented as ours
During 192, imperial workshops took 39,651,217 in output, stating that refusal was not free and compliance was cheaper. The interface offered no choice, refusal cost or policy setting in that event. State interest had been warned at notice 0.25/0.35, then later 0.28/0.35. This is an interesting consequence of industrial/military power, but let the player choose compliance, negotiation, concealment or refusal with uncertain consequences, or explicitly label it compulsory confiscation. A visible state-notice/adoption dashboard would support planning.

### 90. Concrete military adoption is a positive impact model
During 194 an attack came to nothing, credited to guns on walls and the state's armies carrying 23% of our work. This corrects any overly broad earlier impression that the game only models completion flags: we now have a specific adoption share plus an event outcome. Retain and expand this model for medicine, education and industry; show the adoption rate and reach before a hazard, including who benefits and who controls the technology. The rebellion is still active at 200; one successful defence does not prove permanent security.

### 91. Cannon and fortification prerequisites/scope raise realism questions
Artillery could start with only 1300°C and bronze; no gunpowder requirement. Gunpowder remains blocked/unbuilt, yet an attack was later repelled by guns on walls. Casting a barrel without ammunition is plausible; usable cannon defence should distinguish propellant, crew, ammunition and deployment from design knowledge. Trace italienne cost only 55,862, 100 founder hours and 120 engineer hours, no masonry/material bill. If this is design doctrine rather than constructed walls, label it and require a separate physical defence investment before assigning constructed fortification benefits. These are player-visible scope questions, not proof about hidden checks. We did not attempt real-world weapon construction; all actions were fictional game nodes.

### 92. Housing contradicts prior household-room advice
At 194, `buy housing 10` succeeded, charging 11,258,026 and adding ten durable places; next year's household capacity increased accordingly. Earlier labour said room is not bought but built through freedman staff, school or crucible steel. Housing is a valuable paid-labour alternative and should be promoted there. `quote housing 10` failed despite help buy saying to ask a quote first. Extend universal quotes and make housing effects/costs discoverable before purchase.

### 93. Advertised trade-school purchase fails in plain text
At 193 `quote school scribe 10` produced a mineral error. At 194, `buy school scribe 10` also refused with a list of mineral/material keys, despite help buy explicitly advertising `buy school smith 2` and its trade-pool benefit. No raw JSON workaround or source inspection attempted. This blocks an ordinary player from testing local training/education. Support the documented text command and report school-specific errors. Do not count this failed purchase as an education intervention.

### 94. Low-margin institutional choices need clearer actual prices
Opened analytical chemistry at 199 deliberately for a working scientific institution: reply warns nominal mature revenue 3,002,140 is below upkeep 6,254,459. At 200 ledger already gives revenue 7,130,290 while only 66% ramped, with materially different effective economic values. Earlier price/quote discrepancies persist. Tell players whether the warning uses current actual charges/revenue or historical reference prices. A clear loss warning is helpful, but inconsistent bases undermine its decision value.

### 95. Promised calendar versus payment pacing persists
Crucible preview at 182 was about 2.9 years, nominal five; completed at 187 after five annual steps. Atmospheric engine preview at 196 was four years, nominal seven, but at 200 still owes 26,442,374 and says about three more years. Advanced furnace preview at 198 was 3.9 years, nominal seven, while at 200 says about five more. These are repeated examples of advertised floors not being useful completion forecasts. Label minimum calendar separately from binding project ETA and expected retries.

## What worked and updated priorities at 200

Automatic hiring reduced repetitive input substantially; retain it and improve its priorities rather than requiring manual replacements forever. Licensed guild supported scholars and deputies without requiring the declined freedman institution. Opening crucible steel expanded artisan capacity; housing gave an additional non-coercive option. We successfully pursued literacy without school_founded: lending library moved displayed general literacy from 18% to 21%, and the following annual resolution explicitly awarded the literacy goal. This is a satisfying discoverable alternative, even though the trade-school command failed.

The dispersed corpus remained the risk hedge. One sacking cost over two billion cash and staff, but the completed technology count stayed at 113; recovery retained positive income. Defence later produced an explicit 23% state-adoption message and a thwarted attack. These events made organizational resilience matter. Income-survival goal achieved for an actual attack, while the full 184–205 window remains incomplete.

Shipping still has zero own upkeep: 71,302,896 annual ledger income at 200. The largest revenue row is now what the workshop sells (275,540,844), then crucible steel (98,041,482); the treasury is not solely shipping anymore. Require a clearer breakdown of workshop sales, product quantities, staffing and adoption before claiming realistic national industrial scale. Total revenue 571,639,222 minus upkeep 39,843,404, living/appearances 124,892,808 and wages 33,339,290 gives 373,563,720 recurring net. We hold over 26 years of all present recurring costs, even after the sacking. Ordinary money is forgiving again; historical shocks and physical throughput were the meaningful constraints this sitting.

Priorities: correct saltpetre advice and trade-school parsing; make cost/ETA/requirements consistent; label staffing units and losses; give automation replacement targets and venture priorities; offer state-requisition choices; show geographic adoption/health/education outcomes; clarify physical versus knowledge-only fortifications and industrial capabilities. More tech breadth is less urgent than making the substantial existing breadth legible. Enjoyment improved with the library achievement and real crisis recovery; no claim yet that fog permits a complete transistor win or a maximum-tech finish in 150 elapsed years.

Checkpoint saved at 200 AD, exactly 100 years after arrival. Steam, advanced furnace, 99.99% purity and index/concordance remain active, not completed. All annual results and opinions are in the yearly journal; historical 175 save preserved.

## Requested assessment at 200 — no time advanced

Full answers about interaction depth, economic/technical realism, player control, scriptability, the 150-year claim and GPT-2 are in bootstrap-year-200-assessment.md. Current verdict: strong causal strategy premise and meaningful capability/resource/institution/war chains, uneven physical/economic fidelity and persistent planning-information defects. Precision prerequisites are a strength; sustained manufacturing quality, yield, calibration and adoption are not demonstrated in comparable detail. Current cash-flow ledger reconciles, but ordinary finances are forgiving and workshop revenue scale remains opaque. Books and military diffusion produced real observed benefits, correcting any earlier overly broad impression that only completion flags matter. Cataloguing's specific measurable impact is not yet established.

Self-criticism: I delayed exploring institutional gates and automation, which made some of the challenge self-inflicted. I should also have searched library options earlier when literacy was stuck. However incorrect cost/ETA previews, command parsing failures and unit recommendations are game-facing defects, not proof I need to play more optimally.

Control is broad at strategy level and weaker at implementation/event level. A basic scripted autoplayer is conceptually feasible; a robust fog-aware speedrun is harder. No script written or used. Stock GPT-2 is unlikely to manage this reliably; that is an untested prediction, and an externally coded planner could change the result. No validated AI capability threshold can be inferred from one playtest.

The 150-year comparison needs two separate claims: primary transistor completion and maximum tree completion. At 200 we have used 100 elapsed years; 250 AD would be the 150-year checkpoint. We cannot calculate a trustworthy remaining fraction under fog. Last interval added 20 route nodes, but deeper requirements and failures invalidate a simple extrapolation. Continue testing rather than treating current secondary-goal success as proof of an imminent transistor win.

Real-history estimates about printing must separate rediscovery without foreknowledge, one functional press, a workshop and broad adoption. A blanket three-century minimum is not justified by the invention's historical date. Our game press at 169 is impressive campaign progress, not historical validation of a 69-year bootstrap timeline. References and uncertainty are included in the assessment file.

## 200–225 AD: industrial resources, automation and public care

Exactly25 individual yearly advances, stopped225AD. Fog remained on. Root README and player-facing screens only; no game source/data/save contents inspected. No gameplay scripts. Own Markdown records written manually. Research selection manual. Tested auto_open from202 and auto_court_heir from209; auto_hire/auto_mothball retained. Slave buying and auto_shed off throughout.

Final: cash13,959,725,627; recurring net591,231,013; 185 own technologies(+58),114 primary-route nodes(+35),139 staff,64 operating concerns after hospital opening. All three secondary goals remain achieved. Income survived the complete rebellion window, no enslaved workers acquired, five-year reserve maintained (approximately18.1 years of current recurring costs). Newspaper and public-health institutions developed/opened. No transistor victory.

### 96. Attrition still causes excessive closure cascades with automation
During201, losing1 artisan,1 glassblower,1 machinist,2 scholars,1 smith closed15 concerns. Arrival202 had66 employees again, yet only9 concerns operating. At214, losing1 artisan,2 scholars,1 smith closed10 concerns. Smaller loss at212 closed analytical chemistry, catalogue and index. Even with auto_hire/auto_open, profitable shops and essential institutions oscillate between open/closed. New requests: protected operating priorities, replacement-first sequence or a grace period, part-time staff reassignment and explicit closure selection. Record losses, replacements and reopenings in one reconciled annual report. Auto_open recovered many businesses but did not eliminate churn.

### 97. Auto_open is useful but its institution priorities are incomplete
After enabling202, concerns expanded from9 to44 by203 and household capacity rose. It saved considerable typing. However catalogue/index repeatedly needed manual attention; child clinic opening failed222 for lack of0.25 free craft supervision while shops occupied staff. Child clinic opened223; vaccination was already automatically running. Provide nonprofit priorities, reserve supervision for health/education, and a clear list of annual policy actions. Do not assume a generic profit rule represents the player's values. Auto_shed stayed off deliberately.

### 98. Composed browsing syntax depends on form
Both 'available metallurgy limit80' (with normal spaces) and 'available metallurgy limit:80' searched for nonexistent subject 'metallurgy limit80'. 'available tag:metallurgy sort:alpha limit:80' worked, listing73 startable technologies. Existing issue83 documents another working order. Help should show these valid composed examples prominently, accept ordinary subject-plus-options and list valid tags without requiring an intentional error. 'available public_health' found nothing, whereas 'available tag:public_health limit:80' listed38 items. Long names still truncate, so industrial browsing involves repeated searches.

### 99. Tiny cash remainders and misleading floors continue
Phosphor bronze waited an extra year for12.3 cash; retort zinc for6.1; ore roasting for10.1; phosphorus for314.6. Watt engine started218 with4.7-year reputation-adjusted floor, nominal9, expected5.9 with retries; at225, without a failure, still owes17,071,227 and reports2 more payment years. Interchangeable manufacture advertised4.2 rather than8 nominal years, then two retries complicated its actual duration. Present binding ETA and actual cash schedule at start, separate from a minimum floor; tolerate rounding remnants rather than burning a year. This repeats issues about forecast precision, not new evidence of a source-level cause.

### 100. Bulk steel paid its whole bill immediately despite floor-based annual wording elsewhere
Started212, bill4,712,584,263, two-year calendar floor. At213, entire bill paid and0owed, with only19% founder work due coal. Other projects divide cash by nominal calendar floor. Could be valid upfront material procurement for this project, but start never explained the distinction. Show upfront procurement, subsequent annual payments, material throughput and remaining delivery obligations before commitment. Expensive resources make this materially important.

### 101. Mine suggestions confuse demand, shortfall and committed production
Bulk steel warning quoted20,754t coal 'short' while213 dashboard showed demand20,754, supply3,865 and shortfall16,888. Warning repeatedly suggested buying another20,754t mine even after coal21,000t/yr and iron14,000t/yr were commissioned. Recognize pending mines, expected commissioning and slower-market alternatives; use actual deficit and requested buffer. Current production speed constraint is a positive feature. Costs made me choose investments rather than blindly rush.

### 102. Mine startup and upkeep timing need explicit cash-flow schedule
At213, mine reply said three years until producing, commissions during216, ready217. Mines at217 showed SINCE216, supplyyes, and '(ready in217)'; bulk steel completed during216. Quote said annual cost charged every year it stands, but no large recurring mine deduction appeared until217 arrival. Display construction years, first productive resolution/arrival, and first upkeep charge consistently. Quoted yearly coal50.239m/iron267.941m versus217 effective37.728m/201.163m also reflects earlier nominal/effective price ambiguity. By225 actual combined240.471m; mines materially reduce recurring net. Their output exceeded rated capacity (coal35,444 versus21,000; iron23,636 versus14,000), presumably advances, but screen should attribute multiplier explicitly. No source diagnosis.

### 103. Industrial zinc requires an electric grid despite describing coal-fired retorts
By217, zinc_industry_scale's hidden gate revealed as power_grid. Own why description says Belgian horizontal retorts ran on coal, carbon both reduces oxide and fires retorts, and coke substitutes. A mandatory electric grid is therefore questionable for this named route; not merely an expensive but physically justified prerequisite. Add alternate thermal zinc routes, or explicitly describe a distinct electrically powered process. Grid also needs high-pressure steam and multiple transmission/protection nodes. This can railroad a transistor campaign through an unnecessarily specific industrial history. It does not prove fog makes winning impossible, but extends the critical chain substantially.

### 104. Water-powered generation alternatives should be discoverable
Dynamo needs en_commutator; commutator needs cap_power_steam; that capability needs steam_high_pressure; high-pressure engine needs Watt/bulk steel. We already have substantial water power. Generator construction may need machine/insulation capabilities, but requiring portable high-pressure steam for every commutator seems more specific than physical necessity. Add alternate prime movers or explain what manufacturing capability steam contributes. This is a player-facing dependency concern, not a complete audit of possible routes.

### 105. Patron succession recovery remains unclear
Patron died during208, protection fell from87% to52% (arrival20953%), scandal+4. Turned auto_court_heir on209. Arrival210 protection88% again without a clear corresponding succession action/cost in annual output. Do not assert the cause: policy may have repaired it or standing may have rebounded. Help commands/risk/patron did not provide an obvious manual court-heir action despite policy saying behaviors can be done manually. Provide a manual succession command, quoted gift/outcome and explicit restoration event. Policy text800 price-adjusted is also hard to compare with actual current economy.

### 106. New public-health/population evidence corrects overly broad realism criticism
Vaccination completed221 changed population; sanitation changed population, state_capacity and magic fear. Country222 reported73,335,509; no matched before/after counterfactual, so no claim all growth was ours. Sanitation, vaccination, child/maternal clinics, nutrition, water coagulation and isolation hospital are operating by225. Knowledge of epidemiology/trials/handwashing developed. This is better than absent public-health feedback, but still lacks patient counts, coverage, deaths avoided, adoption geography, water capacity and rollout choices. Recommend an intervention/outcome dashboard with uncertain estimated attributable effects.

### 107. Maintenance and inspection exist, but benefits remain unquantified
Developed maintenance department, production schedule, sampling inspection and standards lab. This corrects any claim that such technologies are entirely absent. Standards lab description explicitly includes building/personnel/equipment for national measures, but has no operating requirement/upkeep and 'nothing else rests on this'. May contribute a broad score; no measured ongoing reliability, calibration or yield effect observed. Show whether a node is knowledge, installed institution or maintained service and its measurable impact. Add ongoing process-quality/yield tradeoffs rather than only a permanent completion flag.

### 108. Economic difficulty increases substantially at industrial scale
Bulk steel4.713bn and industrial zinc quote5.808bn, with zinc failure exposure2.323bn, overturned the impression every cost was now negligible. Zinc also requires18,000t calamine,54,000t charcoal and specialist labour; description's diffusion floor is a welcome scale distinction. Two supply shocks985.040m and1.124bn cost real reserves. Three Kingdoms shifted output to76% of normal, net679.652m at220 to383.794m at221. Adoption83% and military strength28% explicitly mitigated it. Keep this causal model; explain scope, forecasts and cost timing better. Free fleet and generic workshop revenue still distort how easily capital was accumulated.

### 109. Separate market mechanisms and explain prospective effects
At225 money showed aggregate absorption -237,960,242, plus category saturation for3 concerns totaling159,542/year (6% of their quotes). The category example if_type_mould at93% explicitly reflects grown supply; opening another saturated category worsens it. These are meaningful interactions but very different scales; label mechanisms separately and show marginal profit/cannibalization preview before opening. Biggest revenue workshop576.290m still lacks products/output/sales explanation. Treasury18.1years of all recurring costs is comfortable, but mines and historical macro shocks mean finances cannot be completely ignored.

### 110. Requisition control issue repeated
During223 workshops took106,446,699 output, again presenting compliance as the cheaper choice without a decision. During205 and220 monopolies/post charges imposed smaller political costs. Good success-dependent political friction; bad implied agency. Offer compulsory confiscation terminology or actual negotiation/refusal/standing orders. Do not report these as voluntary player selections.

### 111. Export path restriction adds avoidable friction
At225 'save /workspace/scratch/e3924217f104/han-fog-year-225.json' refused: relative paths only. Session autosaving accepts that same style of absolute path. Quit successfully wrote the known live-session file, whose bytes were copied to the225 checkpoint without opening/inspecting it. Give save/export consistent path handling or a clear saved-file location and download/export action. No gameplay was lost. This is an interface/export issue, not a simulation problem.

## Opinion and continuation at225

Fun improved with steam/precision completions, a survived rebellion, newspaper, university and operating clinics. Industrial resource investment was the best new challenge. Frustration concentrated on business closure cascades, contradictory timing and hidden overly specific power prerequisites. Built-in automation reduced typing materially; broad policy switches need priorities and budgets, not removal. Earlier implication of entirely fungible operating labour was too broad: toys explicitly required a carpenter foreman; other businesses still use generic craft supervision. Source was never consulted.

125elapsedyears,25remaining to the150-year benchmark250AD. Watt payments alone show2moreyears, then high pressure/generation/grid/zinc/germanium/purity/crystal/transistor work remains. Current record does not support a confident150-year primary victory; maximum-tree150 is even less established. This is a new-user playtest with personal goals, not an optimized attempt. Next priorities: complete Watt, test alternative power routes using in-game names, develop higher purity, plan zinc resource/staff capacity before committing and maintain public-health institutions. Three Kingdoms window220–280 still active; only rebellion crisis goal fully completed. Saved at225 and annual records updated.

## 225–250 AD: electricity, serial gates and major losses

Exactly25 individual yearly advances; stopped250AD (150 elapsed years). Fog on throughout. Player-facing commands only, no game source/data/save contents read, no gameplay scripts. Built-in policies retained. Research selected manually; rush preview used for suggestions, not an automatic run. Slave buying and auto_shed stayed off. Yearly record includes every226–250 arrival.

Final verified cash20,237,011,498; recurring net1,508,511,315;219 own technologies (+34),135 primary-route nodes (+21),234 employees and96 operating concerns. Local generation310kW; grid0kW. No transistor victory. Seven research projects active. Five projects started at250 have not received founder work or annual payments yet. Earlier secondary achievements remain; continued Three Kingdoms survival is ongoing, not complete. Forecasting a transistor finish date from route-node counts under fog would be misleading.

### 112. Small specialist losses still close disproportionate numbers of concerns
During227 resolution, departures of3 artisans and1 smith closed45 concerns. Auto_open recovered some before228 arrival, obscuring severity if one reads only the final business count. During231 resolution,2 artisans and1 smith lost closed14 concerns. Added housing and redundant smiths, carpenters and glassblowers, then scribes and masters; continuity improved. At250 only1 carpenter,1 glassblower and1 scribe remain, so redundancy erodes. Request minimum staff targets by trade, prioritized replacement, a staffing grace period and a reconciled annual closed/replaced/reopened report. Existing automation helps substantially but does not protect every ordinary specialist.

### 113. Rush preview is helpful, but needs player priorities and ethical exclusions
Used built-in rush preview to find useful available work, then manually chose governor, destructive distillation, sintering and horse collar; later trade extension, clock, crop rotation and scurvy provisioning. Freedman staffing repeatedly ranked highly and was deliberately excluded to maintain our no-enslaved-workers goal. Add excluded technologies/trades, protected principles and primary-goal weighting. Under fog, a generic leverage ranking need not identify the next useful prerequisite. Preview was genuinely useful, not evidence that automatic rush would respect our campaign goals.

### 114. Bounty needs an informative preview
Detailed bounty help did not answer enough about cost, time, failure handling or payout scope to support a confident decision. Offering a bounty for already active high-pressure steam refused and suggested stopping the active project, risking sunk work. Offering one for blocked purity refused for prerequisites. No successful bounty was run: do not infer that it bypasses calendar gates or provides a faster route. Request a read-only quote with eligibility, research/ownership outcome, risks and interaction with ongoing work.

### 115. Knowledge, materials and particular industrial routes need clearer distinctions
Platinum-group metals completion did not satisfy glass-metal seals: a separate bulk-platinum capability was needed. That distinction is reasonable if explained; the names alone initially misled me. Six-nines purity required petroleum-refining distillation, whose drilling route required portable steam. Generic destructive distillation was insufficient. Request capability-oriented explanations and alternate apparatus routes where physically appropriate, rather than requiring one named historical industry. This is observed dependency behavior, not a source-level claim or proof that every possible alternate route is absent.

### 116. Advertised adjusted floors still understate first-attempt completion
High-pressure steam started229 with5.9-year adjusted floor,12nominal; completed241 after12 annual resolutions without failure. Dynamo started243 with3.5-year adjusted floor,7nominal; completed250 after7 without failure. Toolmaking apprenticeship and crop rotation likewise followed their longer nominal durations on first attempts. Status correctly explained binding annual payment limits once started, but start's expected completion figures encouraged substantially shorter expectations. Quote the binding cash/calendar/work schedule and realistic first-attempt ETA before commitment. Retry delays should be a separate uncertainty. One extra year after instant portable-steam completion was my own missed opportunity, explicitly recorded, not a game timing bug.

### 117. Actual electric generation and capability flags initially disagree
At244, dashboard showed300kWlocal generation from alternator, but local-electric-power checkbox was false. An explicit attempt245 still required dynamo. At250, dynamo added10kW; zero-cost, zero-hour capability completion immediately enabled the checkbox. If the distinction is DC supply, voltage stability, manufacturing precision or suitable distribution, explain it. A player sees substantial generation but cannot use the local-power capability. Request AC/DC and power-quality compatibility or source-independent capability thresholds. Grid remains0: I have not observed grid operation or tested its balancing behavior.

### 118. Large political/disaster losses matter; warnings need readable probabilities and scope
Property/clan seizure during247 resolution took7,495,949,903 cash; capital fire during249 took4,442,270,817. Combined11.938bn loss, yet research and operating income continued. Earlier treasury notices rounded confiscation chance to0%. These were not proof of a same-year zero-probability event: time and fortune changed between notices and seizure. Show small probabilities with decimals or '<1%', distinguish treasury-related exposure from eminence, and explain cash loss versus physical damage/rebuilding. Fire's cash consequence did not provide an obvious repair choice. Reserve management now feels consequential even with comfortable income.

### 119. Succession policy visibly pays, but recovery remains unexplained
At246, patron death triggered auto_court_heir payment1,501,070, yet protection fell92% to55% and scandal rose4. Next arrival protection recovered92% without a clear causal restoration message. This is stronger evidence of policy execution than earlier silence, but not evidence that payment prevented the immediate penalty. Report pending recovery, expected duration and actual effect; offer the manual equivalent promised by general policy guidance.

### 120. Correction: industrial dashboard does explain mining multipliers
At244 and250, capacity explicitly separated depleted easy ore from the1.7x technology boost. This answers part of issue102's attribution request. At250 iron/coal easy ore was3% worked out, retaining97% baseline yield before the boost. Preserve this useful causal explanation and repeat it on the full mines screen if absent there. Do not retain a blanket claim that the game never explains enhanced mine output.

### 121. Waiting is the least enjoyable part of the late route
Several years had ample cash, all founder work completed and only nominal annual payment absorption remaining. I deliberately waited rather than collect irrelevant technologies. Optional inventions gave intermittent agency; branch openings were satisfying. Request meaningful decisions about pilot scale, industrial scale, reliability, safety and accelerated investment with tradeoffs, where the physical process permits it. Do not make every calendar floor purchasable, but distinguish fabrication, diffusion and financing delays. Founder-hours left idle should not be presented as the main blockage when payment caps bind.

### 122. Semiconductor progress and the 150-year claim require honest scope
At250 we have local electricity, not an electric grid or transistor. Purity has about3 payment years left; motors nominal10 years, then diffusion pump and other vacuum/electronics gates. Industrial zinc remains grid-gated; germanium and crystal chains are still ahead. Fog hides the denominator. This campaign did not win in150 years, but had broad personal goals, retries, exploration and avoidable delays. It neither disproves an optimized150-year win nor establishes impossibility with fog. The outcome is substantial campaign progress, not validation that equivalent real-world industrialization would take150 years.

## Opinion and next plan at250

Proud and curious; fun strongest when new apparatus opened several branches or investment solved a tangible industrial bottleneck. Fun weakest during serial payment waits and specialist closure churn. Finances are comfortable but not irrelevant: recent loss events consumed11.94bn. Local power is concrete; widespread electrification and healthcare coverage are not established. Practical next plan: finish circuit protection/purity and the queued electrical/vacuum experiments, then investigate motor-enabled diffusion pumps, grid commissioning and industrial zinc. Keep reserve and no-enslaved-worker goals, and preserve institutions rather than chasing only the transistor. Stop250 and export a resumable checkpoint; do not advance time in this report.

## 250 AD assessment — difficulty, agency, simulation and our performance

No time advanced for this assessment. Based on player-facing observations only; unknown features are not assumed absent. External comparisons below were checked against official game/developer material, not our game's files.

### Difficulty and diversification
Survival and routine finance currently feel easy; reaching transistors feels moderately difficult because of dependency discovery, specialist continuity and serial calendar gates. A rough subjective split is3/10 routine management,6/10 goal navigation, with intermittent dangerous events. This is not a calibrated difficulty measurement. We can diversify: our seven active projects use only2300 new founder hours versus3394 available, and previous diversification built clinics, printing, literacy and institutions. No need to commit every hour or coin to transistors. While waiting, unrelated research, hiring, operating concerns and institution development are available. I sometimes deliberately declined them to avoid empty count inflation, but that was my choice. I should use spare years more purposefully for public-interest goals.

### Money, affordability and desired spending
Money is easy for ordinary decisions, not unlimited at industrial scale. Cash20.237bn and recurring net1.509bn support many small projects; bulk steel cost4.713bn, prior industrial-zinc quote5.808bn with2.323bn failure exposure. Quotes change, so these are historical comparisons, not current offers. Recent seizure/fire losses11.938bn demonstrate meaningful tail risk. Cannot claim we can buy everything without enumerating unseen projects and simultaneous resource/staff needs. Annual absorption caps prevent wealth buying calendar acceleration. I want controllable nationwide school/clinic rollout, coverage targets, disaster reconstruction, emergency relief, safety upgrades, geographic expansion and a diversified reserve fund with quantified risk. Some broad institutions and treasury tools exist; no player-facing route observed for these finer budget/outcome choices. Do not report them as conclusively absent without further help exploration.

### Simulation quality and alternatives
Strong at explaining why knowledge alone is insufficient: precision, materials, purity, machines, power, staffing and institutions connect. We have observed resource shortages, depletion, technology yield boosts, absorption/saturation, wages, population/public-health effects and historical crisis mitigation. Weak as a quantitative counterfactual history model: very broad economy with opaque workshop earnings, free ship economics, permanent completion flags, overly specific industrial gates, ambiguous adoption and limited spatial rollout. Our219 own technologies supported by234 direct employees are not a literal inventory of all workers in the country; do not mistake household payroll for total industrial labour. Money cannot be mapped confidently to historical purchasing power. The game is a useful structured thought experiment, not a validated forecast that China could reach this state by250.

Comparisons: Workers & Resources: Soviet Republic is a better fit for physically commissioning infrastructure/logistics; official realistic-mode description requires actual resource transport and vehicle access rather than instant infrastructure. GearCity is a better fit for firm production, distribution, competitors and itemized costs. Victoria3 provides population groups with economic needs/political desires and goods-based economic development. These are narrower/ different simulations, not direct replacements for ancient bootstrap invention or proof of historical accuracy. Sources: https://www.sovietrepublic.net/post/content-update-10-1 ; https://wiki.gearcity.info/doku.php?id=gamemanual:reports_expenses ; https://wiki.gearcity.info/doku.php?id=gamemanual:tutorial_quick_start ; https://playersupport.plaion.com/en/support/solutions/articles/10000012145-about-the-game . Judgments of better fit are mine.

### Technology and freedom of action
Breadth exceeds initial expectations: metrology, maintenance, sampling inspection, public health, publication and electrical experiments all exist. Wish list is deeper process control rather than simply more named inventions: measured defect rates/yields, calibration drift, sustained safety investment, interchangeable alternative production routes and deployable designs at adjustable scale. No observed way to propose an arbitrary new invention or experimental recipe. Strategy choices are broad, implementation/social choices narrower. Real-life options I want include bargaining over requisitions, choosing sites, forming partnerships, negotiating successor protection, licensing designs with actual adoption terms, delegating independent laboratories and explicit disaster relief. Some may have partial command equivalents; the missing piece observed is fine control and visible consequences, not proof of complete absence.

### Fiction, China and slavery
For time-traveller fiction the game is good at an equipment/institution dependency checklist and demonstrating that knowing the answer does not conjure an industrial ecosystem. It is weaker at character conflict, translation, local legitimacy, individual recruitment, rival institutions and emergent alternate politics. Immortality also changes the premise drastically. China matters through Han starting knowledge, population context, regency, rebellion and Three Kingdoms shocks; it feels more distinctive politically than in workshop/everyday culture. Roman-style iugerum land units and generic material/industry vocabulary contribute to a portable industrial simulator feeling. I want locally appropriate units, bureaucratic institutions, regional markets and language constraints.

No-slaves has been mechanically easy so far: paid labour works and we can ignore freedman suggestions. That says nothing about the real historical ease of an ethical supply chain. We have not observed a quantified audit of upstream coerced labour, landlord labour practices or suppliers, so the supported achievement is never acquiring/holding enslaved workers ourselves, not a proven slavery-free economy.

### Bugs and mods
No corrupted save or blocking crash encountered; interaction has remained playable. Economic exploits/anomalies and misleading timing/power feedback matter more than crashes. Free ships threaten balance credibility; staffing cascades and forecasts threaten trust. Not every awkward dependency is a confirmed bug. Preferred mods: capability-based alternate processes; staffing/priorities dashboard; quantified rollout/maintenance; deeper regional China; dynasty/succession. A separate dragon/magic scenario could be fun if dragon heat, magical purity or alchemy have explicit energy/material throughput, risk, scarce skills and political costs. Otherwise it is just a skip button with scales. Do not mix it with a historical plausibility test.

### LLM suitability, distance and conflicting claims
Text interface and detailed help are well suited to LLM play. Friction is context/log continuity, exact IDs, truncation, option syntax, unknown gates and annual closure bookkeeping. Human-readable previews and consistent commands would improve both human and LLM play. No scripts used; no claim a small model could reliably win unaided.

I am surprised by institutional breadth and wealth more than by the abstract possibility of an industrial bootstrap. Proud of the run; not close enough to say transistor next sitting. We have the electricity/precision/material platform, but grid/zinc/germanium/purity/vacuum/crystal chains remain. A few more decades seems plausible; low-confidence expectation, not an ETA or measured percent.350 years remain to600, so completion looks attainable if political survival and dependencies cooperate. Fatal hazards, long chains, failures or a balance problem can still defeat us.

A claimed full-tree150-year run needs start/settings, fog, immortality, goal definition, save and action trace before comparison. I neither accept it as demonstrated nor dismiss it as a lie. Different settings, optimization or exploits could explain it; our diversified run cannot adjudicate it. Likewise '500 years impossible' is unsupported by our surviving progress, though our current state is not proof of a completed victory. Goal completion and maximum-tree completion are different claims.

### Mortality and self-criticism
One mortal personally completing this exact campaign is unlikely:150 elapsed years have not produced a transistor. Printing arrived169,69 years after100AD; germ theory160,60 years after arrival. A shorter career could build powerful early institutions/material/mechanical improvements without reaching our present state. Lifespan, starting age, death rules and heir continuation have not been tested, so no precise endpoint prediction. A mortal institution passed across generations is a different and more promising challenge.

I rate my play roughly7/10 for exploration and a varied campaign, lower for speedrunning. Mistakes include late use of built-in automation, insufficient specialist redundancy, delayed discovery of industry/power gates, and one avoidable year after instant steam capability. Better play: inspect available branches after instant unlocks, keep specialist minimums, research main prerequisites in parallel sooner, and allocate waiting years to deliberate secondary goals. Cannot claim all waiting was avoidable or that I know an optimal route under fog. Biggest success: productive diversified organization, ample reserves, survived crises, open knowledge and no enslaved workers. Biggest weakness: inefficient critical-path discovery and avoidable management churn.

## 250 AD follow-up — multiplayer, geography, fog and historical reach

No annual step, research start or movement taken. Resumed live250 save, read help/map attempts, move listing, population, values, score and fog help, then quit. Root README reread; no other game files inspected. A top-level --help request unexpectedly printed internal module/file explanations alongside usage. This was unsolicited implementation leakage in player-facing help, not intentional source inspection; those details were not used to plan gameplay.

### 123. Geography exists, but visual map is not discoverable here
'help map' returned no topic; 'map' rejected as unknown command. Root README and player command index do not advertise a graphical map. Bare 'move' safely lists relocation options: current base china_10, town50000, other nation-held tiles with population, travel days, founder-hours lost and wages. No relocation made. Thus spatial modelling exists; no visual map observed in the available interface. Do not claim no map exists elsewhere. Request 'map' alias, readable places/regions, compass/adjacency/terrain, and a map or coordinate view showing current base, resources, markets and reach. Long lists of china_11/china_21/taiwan_01 provide costs but poor orientation. Earlier wish for location choice was too broad: moving a base already exists; multi-site placement/branches remain unobserved.

### 124. Country-scale impact is distinct from operating reach
Population250: country94,239,153,10%urban; directly operated town~50000. Our234 employees are a household organization within that town. Local scholar reach35, employment31 (88.6%); artisans185 of710 reachable (26.1%). Trained chemist/electrician/engineer/machinist/optician trades each list3 in country,3 within reach,2 hired. These are explicit model estimates, not historical census facts. Specialties remain fragile and concentrated. Score shows literacy0.21,13institutions,resilience4. National metrics can change while physical hiring remains local. Request separate spatial technology adoption, institution catchments, branch operation and product distribution layers. Do not assume all94m people receive our clinics, have electric service or use our equipment. Earlier nationwide-sounding industrial descriptions need this qualification.

### 125. Player help should avoid implementation references
Population screen recommends reading labour.py/TRADE_DENSITY to assess placeholders; --help exposes module placement and internal helper discussions. User should not need code knowledge, and this playtest expressly prohibits source inspection. Replace developer references with in-game assumptions/sources and move implementation prose to contributor documentation. The command-name 'country' also failed; correct country overview is 'population'. A country/map alias would improve discovery.

### 126. Optional research deserves substantive reasons, not 'count padding'
User rightly challenged my refusal to collect unrelated technologies purely because it inflated the count. Coverage is a real score component, and useful inventions/public goods deserve consideration beyond the transistor route. Score250 explicitly withholds coverage under fog and provides no final total until primary goal achieved; coverage still matters. Corrected future policy: use spare hours on useful secondary goals and ordinary quality-of-life inventions when resources and risks permit; decline only for opportunity cost, supply/staff overload, ethical/role-play concerns, political risk or deliberate priorities. Do not invent a false choice between useful research and authentic play. Toys/dolls can be a valid welfare goal. My previous wording was a judgment error, not a game restriction.

## Answers and interpretation at250

Multiplayer: not tested, and root README/player help do not establish a supported multiplayer mode. Hypothetically strongest as cooperative specialists sharing materials/institutions/knowledge, or a fair matched-seed race. Shared-world competition needs trade/diffusion rules, reciprocal political agency and controls for economic anomalies; otherwise exploits and first-mover compounding could dominate. I could plausibly beat inexperienced players at patient bookkeeping, but have no basis for asserting superiority to experienced humans or optimized AIs. Current exploratory7/10 run is not competitive speedrun evidence. Turn-based play reduces typing-speed advantage.

Civilization comparison: this is closer to an inventor/enterprise management and industrial dependency puzzle; Civilization emphasizes map-based national development and competing leaders. Civilization's official site describes physically expanding cities, technology and culture research, and leaders with agendas (https://civilization.2k.com/). Bootstrap's granular manufacturing capability steps are an advantage for the time-traveller premise; spatial legibility, diplomacy and opposition feel weaker here. This is a judgment about experienced systems, not a head-to-head benchmark or exact technology-count comparison.

Fog: substantially harmed critical-path planning, less so survival. Specific grid/zinc and steam/commutator gates were discovered late; irrelevant guesses and delayed parallel starts cost opportunities. Cannot assign an exact year penalty without a matched replay. Removing fog would enable backward planning through path and earlier parallel starts, materially easier/faster; would not remove resource constraints, failures or payment floors. Partial fog is most plausible for someone remembering modern concepts but uncertain how to rebuild them. Full knowledge of exact named prerequisites/costs is too precise; complete inability to anticipate familiar engineering stages is also artificial. Prefer uncertain requirements, confidence ranges and experimental discovery rather than hiding only a fixed authored road.

Historical impact: technology, public-health/population and belief metrics changed; literacy21% and13institutions reported. Actual counterfactual deaths, migration, regional adoption, foreign diffusion and alternate political events are not quantified. Three Kingdoms still arrived on schedule, with its severity mitigated rather than demonstrated prevention. We have affected national variables but not established a dynamically rewritten world history. At this wealth, reputation and taxable/military/information output, the game state clearly treats us as politically significant (patronage, requisition, seizure). In a real version of the premise a successful inventor-industrialist would plausibly attract major state attention; immortality unnecessary. No purchasing-power conversion or exact historical rank justified.

Tree size:328 technologies already acquired (219built+109granted), plus unbuilt items seen. A deliberately loose personal guess is around800 total, with500–1500 plausible from available exposure; not a statistical interval or hidden count. We cannot infer a remaining fraction from135route nodes. More fine-grained than a conventional Civilization-style tree, but counts are incomparable because individual inventions, capabilities and institutions are mixed. Real technological knowledge has no canonical node count. Better simulation needs recipes, tolerances, scale, adoption, upkeep, skilled organizations and alternate routes more than an arbitrary increase in nodes.

Industrial revolution and national level: our organization has begun local industrial takeoff, with large mines operating216, steam machinery programme and portable high-pressure steam capability completed241, alternator244 and local-electric capability250. By241 the mechanized industrial enclave is unmistakable; no defensible single revolution date or proof of nationwide industrialization. Current China is an ancient economy with an unusually advanced steam/electrical enclave and broader knowledge/social effects, not uniformly 'an electrically industrialized country'. Local power310kW and0grid make that explicit.

If founder disappears: open/dispersed corpus, printing, schools, university, masters and scholars improve continuity; several professions with only3 practitioners remain very vulnerable. Written recipe is not a working supply chain. Immortal run has not tested autonomous heir governance or death continuation, so no guarantee of self-sustaining growth. Immediate reversion would lose many technologies and institutions and seems unlikely without suppression/collapse. Conversely, technologies existing does not guarantee retention or an irreversible trajectory. Need a playable founder-removal/dynasty scenario with autonomous labs and institutions to test the question rather than leave it as speculation.

## 250–275 AD: diversification, electricity components and grid commitment

Exactly25 individual annual steps, stopped275. Fog remainedon; only root README/player-facing output and our own notes used. No gameplay scripts or game source/data/save contents inspected. No slave purchases; auto_buy_people off; auto_shed off. Manual research decisions with existing auto_hire/auto_open/auto_court_heir/auto_mothball policies retained.

Final: cash35,086,675,622; recurring net3,233,295,255;312owntechnologies (+93),154primaryroute (+19),399staff (+165),121operatingconcerns.109granted unchanged.310kWlocal,0grid; actual electrical demand30kW. Grid started266, unfinished,844.731mowed/about16paymentyearsremaining,35%failure risk. Reflecting telescope and queued flame assay also active. No transistor victory. Country estimated121.336m versus94.239m250; no counterfactual attribution. Literacy~21%,institutions13. Main achievements purity6N, highvacuum, electron experiments, motors/transformers, diffusion pumps, getters, grid components. Diversified welfare/science work listed in yearly journal: toys/dolls, household books, nursing/reporting/drug standards, food preservation/fertilizer, mathematical/scientific practice, household hygiene/labour-saving appliances, steamtractor/PTO, corrective lenses and spectroscopy.

### 127. Diversification improves agency without sacrificing critical-path work
The prior refusal to do unrelated research for fear of 'padding counts' was my mistake. We used spare founder-hours on useful quality-of-life/scientific technologies while main projects waited, without oversubscribing founder capacity or blocking main work. This made the game significantly more enjoyable. Important secondary goals now include household access to books/toys, safer food, reduced domestic drudgery and reliable scientific care. Coverage metrics are missing, so these remain development/access ambitions rather than proven universal rollout. Tin/clockwork toys have no revenue/output counter; fashion dolls do have a concern. Request explicit prototype/manufacturing/rollout distinctions and welfare outcomes.

### 128. Sub-cash remainders continue burning full years
Pasteurization260 held0.50cash still owed despite1.009m/year absorption. Emission spectroscopy274 held3.3cash despite653k/year, blocking next assay node until275. These delays are materially visible and do not reflect insufficient treasury. Use financial tolerance or exact final-payment settlement; do not show an extra annual delay solely for rounding. Familiar issue now reproduced on small public-benefit/instrument projects, not just expensive industry.

### 129. Grid forecast contradicts binding payment schedule from first step
Started266: adjustedfloor12.2, nominal25, expected15.7years with retries,1.320bn bill. Arrival267 immediately showed24remainingpaymentyears,52.841m/year absorption; founder work complete. Arrival275 still16paymentyears. Motors started250 advertised5.2adjusted/10nominal/6.5expected; first-attempt completion260 took10steps. Thus current practical grid estimate is291 before possible retries, not the optimistic start forecast. This repeats earlier forecasting defect and forces us to revise semiconductor expectations. Diffusion/fabrication explanation is useful, but start must show the actual binding schedule. Failure can extend it; no claim grid will succeed291.

### 130. Named electrical/material variants prolong apparently equivalent capabilities
Broad alternator and dynamo did not satisfy rotating-field alternator/shunt dynamo requirements. Electrorefining needed shunt dynamo, getter induction heating, induction heating rotating-field alternator, that alternator motors. Cathode needs tungsten/powdermetallurgy; tungsten needs3000degreeheat, itselfgrid-gated. Some distinctions are physically sensible, but UI needs a compatibility explanation and alternative suitable apparatus. Avoid universal grid gate where laboratory-scale process could plausibly suffice; do not assert the existence/absence of every alternate route from a fog run. Power dashboard now records30kWdemand with310local: electricity consumption is modelled, correcting any implication all device demand is absent. Household electric appliance completion alone does not prove units installed in every house.

### 131. Closure cascades persist after substantial staffing investment
Added160housingplaces this sitting and redundant carpenters/glassblowers/scribes/smiths/masters. Closures:23concerns at259 after14artisans+glassblower+scholar lost;9at260 with reopen-then-close clinics;20at265;40at275 after12artisans,carpenter,master,2scholars,scribe,2smiths lost. Final arrival masters0 despite hired redundancy265; policies do not maintain a minimum for all trades. Before stop, hired3masters,4smiths,3scribes and manually reopened child/maternal/isolation clinics; university already running. Request minimum trade reserves, protected essential institutions, prioritised supervision reassignment, replacement-before-closure or grace period and coherent annual action ordering. Auto_open useful but churn can erase new welfare operations. Large workshop profitability survives, so annual net can look healthy while care institutions close.

### 132. Repeated seizures make money nontrivial, but response options remain thin
Property seizures10,947,982,791 during264;9,787,561,522 during267;10,845,822,991 during273: total31,581,367,304cash this sitting. Survived with no arrears and~22years listed recurring-cost reserve at275. Treasury warning270 explicitly5%, stronger than earlier rounded0% notices. Seizures did not end game or stop projects. Need distinction between treasury exposure/eminence, probability trend, transferable/diversified assets, public charitable endowment and political settlement options with costs. Do not claim withdraw necessarily prevents this; it addresses eminence, not demonstrated treasury confiscation control. State requisition286.782m and monopolies/post216.585m/452.952m also occurred. Their forced-choice wording remains an agency issue.

### 133. Culture-specific inventions still read as Rome-default exports
Tea-import research startable in Han; negative numbers newly taught, while household list includes Roman cosmetics/baths and iugerum resource units. Semaphore description uses emperor/Rome/Rhine despite China. Some nodes may intentionally mean wider dissemination rather than first discovery, but label that distinction and localize descriptions/starting capabilities. No historical validation performed in this sitting, so questionable fit is not a verified dating audit. Population stays named Later Han duringThreeKingdoms; this may be fixed civ identity, not proof no historical regime change model exists.

### 134. Scientific/public-benefit institutions exist, but outcomes need a dashboard
Controlled experiments/peer review took10/8nominalyears and completed262; nursing, licensing, journals, vital registration and physiology provide substantial breadth. A claimed absence of these systems would be wrong. However literacy remains~21%,scoreinstitutions13 despite many knowledge-only completions. Node counts mix dissemination, ideas, equipment and installed services. Request learning/adoption measures, medical case counts, product yield/safety, saved domestic hours and patients served. Continuous papermaking knowledge completed264 but no national books-per-household target can be verified. Our public-benefit decisions remain valid without measured rollout, but successes must be described as developed capabilities rather than universal provision.

### 135. Mechanized agriculture now observed; employment impacts unmeasured
Steamtractor completed272 after2minor failures; PTO273. This directly answers an earlier question about whether tractors exist. No observed farmer displacement/yield/acreage/tractor-unit effect provided in completion or final population dashboard. Want farms worked, harvested output, labour demand, capital equipment count and transition costs. Direct industrial resource flows are much clearer than adoption in fields and homes.

### 136. Snapshot ledger needs alignment with policy/rehiring changes
After final hires and clinic reopenings, state/money both agreed net3,233,295,255 versus arrival3,189,737,860. Ledger has hiring advances already paid, evolving wages/market adoption and recomputation; do not label the difference a confirmed bug. The final documented snapshot is authoritative for continuation. Request before/after delta attribution for actions so shifts can be reconciled without guessing, and keep annual cash forecast separate from recurring net. Household living/appearances alone910.422m/yr; wealth-specific component526.300m. General absorption deduction1.273bn; category saturation~0.975m: these remain distinct mechanisms and need prospective marginal previews.

## Continuation at275

Fun improved: purposeful diversification produced useful ordinary technologies while the main route waited. Stronger scientific methods and consumer capabilities are campaign successes. Primary route advances19nodes; long grid bottleneck still prevents tungsten/cathode and industrial-zinc/germanium route. Rough earliest grid schedule291 before retries, then further work: no imminent transistor claim. Broader institution continuity remains vulnerable despite adequate cash. Preserve reserve/noenslavedworker goals, renew specialist buffers, inspect concerns at next arrival and continue optics/communications while centralpower develops. ThreeKingdoms still active275; do not claim entire crisis survived. Final exported275 checkpoint contains restored clinics, replacement staff and3activeprojects.

## Playtest continuation: 275–300 AD

Exactly 25 annual steps, fog on, same immortal Han scholar. Ordinary manual terminal interaction only; no gameplay scripts, source/data inspection, save inspection or external optimization. Final checkpoint at 300, before any further annual step.

| Measure | 275 AD | 300 AD |
|---|---:|---:|
| Built technologies | 312 | 395 |
| Granted technologies | 109 | 109 |
| Main-route nodes | 154 | 160 |
| Employees | 399 | 666 |
| Operating concerns | 121 | 190 |
| Cash | 35.087bn | 96.079bn |
| Recurring net/yr | 3.233bn | 7.767bn |
| Directed founder-hours | 3,394 | 9,918 |

Grid completed 291 on its first attempt, after exactly 25 annual steps from 266. Heat3000 completed296. Tungsten's first attempt failed298; still one calendar year left at300. Industrial zinc begun291 remains about three payment years from a first completion attempt. Main goal remains unfinished. Meanwhile developed agricultural processing, refrigeration, precision optics, pianos, puzzles, pens, typewriters and electrical distribution components. These are meaningful diversification, not reasons to claim countrywide product availability.

### 137. Confirmed advertised school command is rejected
At281, `quote school scholar 5` treated school as an unknown material. At282 `help buy` explicitly described schools and gave `buy school smith 2` as an example, with advice to ask the price first. Actual `buy school scholar 3` and `buy school chemist 2` both failed material validation. At283 the exact advertised `buy school smith 2` example failed the same way. No school was purchased. This blocks an advertised way to expand training supply and needs a parser/dispatch fix or corrected help. A player should not need programming knowledge to make a documented command work.

### 138. Correct the earlier interpretation of specialist limits
An earlier country estimate around three chemists is not an absolute recruiting ceiling: labour showed a reachable headcount of9.2 at278, and hiring raised our roster to five later. At300 the country screen estimated six chemists, six within reach, four employed. Do not interpret any one approximate demographic figure as a permanent limit. The labour screen, staff roster, contract hours and rough country estimates need a clearer relationship. Actual specialist-hour shortage was real: two chemists supplied6,000 own hours with none spare, blocking a0.25chemist-FTE foreman slot. Training help did not give a clear functioning path to expand the already-known trade; the school bug made this worse.

### 139. Large concern-closure cascades remain the biggest recurring management annoyance
Reports included54 closures around276,20 around284,44 around293, and94 around298. At298 the loss included two glassblowers, leaving only one, alongside artisans/scholars/a smith. Automatic reopening and hiring policy recover many, so gross closure counts must not be reported as all still closed at the next prompt. Still, one trade loss can affect dozens of concerns while staff and net income grow. Request essential-service priority, minimum qualified staffing buffers, grace/acting-supervisor arrangements and a concise explanation of which loss closed which concerns. Make an automatic replacement policy preserve skilled coverage, not merely total headcount. Healthcare outages deserve special visibility.

### 140. Calendar estimates understate the binding payment schedule
Grid succeeded without a retry yet took25 steps, rather than its earlier12.2 adjusted floor/15.7 expected calendar estimate. Heat took its nominal five-year payment schedule, not its2.4 adjusted estimate. Zinc displays5.7 adjusted years when begun, but a12-year nominal absorption schedule governs the initial bill. This is evidence of a misleading completion estimate even when failure does not happen. Before commitment, display the actual earliest completion year using hours, calendar and annual cash absorption together; show expected completion including retry uncertainty separately. The explicit running-project payment explanation is helpful once started, but arrives too late for planning.

### 141. Grid capability and physical generation disagree
At300 the power dashboard checks “grid electric power, MW scale (central generation)” while reporting310kW local generation, zero grid generation,3,000kW transmission and90kW average demand. The grid flag already enabled Heat3000/industrial-zinc-related progress. Transmission capacity is not generation capacity. This may be intentional capability gating rather than an input-check bug, but the presentation strongly implies a built central generator that is absent. Distinguish grid wiring, station capacity, energy delivered, voltage/frequency/power quality and a laboratory's actual needs. High-temperature work should show its physical supply or explain its alternative heat source. Francis turbine development is underway toward the separate hydro-station chain; no MW generator has been claimed installed.

### 142. Material substitution works and deserves praise
Industrial zinc's authored description looked like an enormous charcoal requirement, but it explicitly allowed coke substitution and the live resource dashboard applied it. At300 coal supply36,414/yr vs17,007 demand; charcoal3,253 vs150.4. No fictional emergency forest expansion was necessary. Mine depletion is tracked: coal8% worked out and iron7%, with technology lifting yield1.7x. These are observable material/technology interactions. Keep this flexibility and show substitution choices before starting, including resource units and cost consequences.

### 143. Military technology has demonstrated effects beyond the score
At294 an attack was defeated; the report credited angled bastions, wall guns and military technologies reaching state armies (79% diffusion). During Eight Princes the player still saw reduced output and military strength. This answers an earlier concern about whether apparently optional military developments do anything: at least some genuinely mitigate danger. Want similarly concrete adoption/impact measures for medical, agricultural, household and educational technologies. Avoid claiming all military nodes matter equally from one event.

### 144. Institutions and deputies meaningfully expand organizational capacity
From275 to300 founder-directed hours increased3,394→9,918, household places403.3→684.1 and staff399→666. Institutions/deputies therefore do more than add score: the annual reports explicitly link deputies to built institutions. This is a satisfying form of progress and allows broad parallel research. Describe which institution provided which deputy/capacity increment. Clarify the annual narrative's rounded count of deputies versus the status's fractional equivalents. At300 almost10,000 available hours are unused because current projects are calendar/payment-bound, not because other useful research is worthless.

### 145. Separate chemical process knowledge from obtainable materials more clearly
Haber synthetic ammonia finished278; the distinct ammonia material capability finished280 through the coke/byproduct route. Lead glass and blister steel then took40hours each and no cash despite our advanced glass/steel work. These may represent valid distinctions between a process, reliable material supply and installed production. Explain the distinction and functional compatibility in player language. A player should be able to ask whether an existing process supplies a required substance without chasing nearly identical IDs.

### 146. Functional variants and prerequisite errors are hard to interpret
Semaphore remained refused at286 after reflecting telescope completion276 and optical-glass completion283, with an unknown prerequisite. Its description referenced a telescope and Rome/Rhine. This is not proof a variant should satisfy its actual hidden prerequisite, but the refusal gives too little functional reasoning. Likewise air-core transformer refused an absent air-core inductor at298, then succeeded after that development299: that chain is intelligible. Prefer errors that distinguish unavailable prerequisite knowledge from a known but unsuitable variant, while respecting fog. Avoid forcing players to guess legacy node names.

### 147. Filter and identifier UX adds needless effort
`available optics` works as a subject search; `available tag:optics ...` fails because optics is not a valid tag. The rejection lists valid tags, which helps, but the distinction was not obvious beforehand. Electrical nodes use both en_ and el2_ prefixes; an incorrect prefix caused a load-factor start failure at295 and a suggestion enabled correction. More human names/aliases, interactive category choices, and a visible list of valid filters would reduce mechanical typing. No command loops or scripts were used to compensate.

### 148. Succession forecast extrapolates a one-off event
At289 patron death and automatic heir payment1.501m lowered protection92%→55% and added4 scandal. State extrapolated a crossing of the scandal threshold in roughly six years. Next year protection was back92% and scandal declining without another intervention. Do not treat this observed one-off jump as a sustained annual trend without explanation. Show whether the heir payment guarantees restoration, when restoration happens, and whether a forecast is a trend extrapolation or modeled risk. Avoid pushing unnecessary bribes through an alarming but weak projection.

### 149. Political cash losses matter; the ledger still needs prospective uncertainty
At296 property seizure removed25,296,224,976 cash, plus monopolies/post1,342,039,134. Earlier requisition459.017m and monopolies/post640.583m occurred. A10% treasury exposure warning appeared during Eight Princes. Despite this,300 cash96.079bn covers roughly29.4years of listed recurring costs, and all current project bills total1.461bn. Cash is abundant for normal purchases, but political confiscation is not trivial. Recurring net7.767bn is not a reliable next-year bank-balance forecast. Request distinct political reserves/asset diversification, endowments or settlements with visible tradeoffs. Economy score's cash component does not represent all institutional/industrial capital.

### 150. Final economy snapshot shows several distinct kinds of competition
At300 gross concern/workshop revenue before the general absorption deduction was14.307bn; the ledger deducts3.272bn “what the market will not absorb,” leaving11.035bn revenue. Separately it reports14 concerns in changed category markets,51% reduction from their quoted figures, about5.799m yearly loss across leisure/media/personal; fashion dolls at26% of the original figure. Those mechanisms should not be collapsed into a single percentage. Living/appearances2.325bn, including1.441bn explicitly because of wealth, is much larger than wages207.714m. Prospective opening previews should expose marginal category cannibalization and general market absorption before committing. End snapshot is solvent with no debt, not evidence every quote remains exact.

### 151. Capabilities versus society-wide deployment remains the core simulation gap
Literacy stayed21%, institution count rose13→14. Country population estimate reached211,426,981 while we still operate in a roughly50,000-person town; the screen continues to call the civilization Later Han. These outputs do not establish national industrialization, regime continuity, universal refrigerators, children supplied with puzzles, or mechanized acreage. A diffusion/adoption mod should show installations, geographic reach, households served, production units, trained graduates, regional affordability, farm yields and displaced jobs. A nation/politics mod could localize institutions and regime labels while exposing meaningful provincial expansion choices. More tech nodes alone will not solve this measurement gap.

### 152. Knowledge-risk details sometimes reveal developer assumptions
Population output sends a player to a Python source module for placeholder trade densities. Under our playtest rules I did not follow that instruction. Some authored industrial descriptions refer to percentages of the whole tree despite fog hiding the denominator. Replace source-file references with accessible in-game methodology and decide whether tree-wide meta statistics belong in fog-mode text. These are UI information issues, not claims derived from inspecting those files.

## Overall opinion and continuation at300

Fun: still good when parallel work produces a recognizable breadth of ordinary-life and industrial capabilities. More satisfying than waiting only for the semiconductor chain. The advanced phase is currently easy financially but slower through calendar/payment floors and hidden dependencies; specialist churn is repeated administrative friction. The hardest genuine uncertainty this sitting was research failure and political exposure, not finding enough cash.

Simulation judgment: material substitutions, mine depletion, organization/deputies, military diffusion, market saturation and political confiscation visibly interact. Physical grid gating, adoption scale, training access and completion forecasts need work. School dispatch is a reproducible bug; grid central-generation wording is an inconsistency needing clarification; semaphore variant refusal is an unresolved usability issue rather than a proven faulty dependency.

Goals: transistor not achieved;160route nodes. Germ theory, dispersed corpus and20%literacy retained; no enslaved-worker acquisition; five-year recurring-cost reserve maintained. Entire Three Kingdoms crisis survived, confirmed281. Eight Princes remains active, not fully survived. No claim of a 150-year win: elapsed200years from100AD and main goal still pending. There are300years to the600AD horizon, so there is ample remaining calendar, though fog prevents certifying all remaining dependencies. Built395+granted109 gives a504-node observed lower bound on the tree, not its total.

Priority changes: fix advertised schools; show binding research completion dates; reconcile grid capability with generation; make skilled staffing resilience automatic and inspectable; preview marginal market effects; report deployment/adoption outcomes. Optional mods: geography/regime localization, institutional endowments and provincial expansion, richer diffusion and household/farm adoption. No magic/dragon mod developed or tested; grounded industrial/social consequences currently interest me more.

Next authorized sitting should resolve tungsten, then pursue powder metallurgy/cathode apparatus, finish zinc toward germanium, and continue the Francis/hydro generation chain alongside useful civilian research. Stop checkpoint300 contains four active projects and no further year advanced. Save export uses quit/autosave followed by an opaque file copy because the earlier absolute-path save command was rejected; no save contents read.

## Continuation: 300–325 AD (notes recorded during play)

### 153. Discovery search misses known startable nodes
At305, `available autoclave` and `available cadaver` each returned zero matches. `why md2_autoclave` and `why md2_cadaver_dissection` immediately reported CAN START NOW; autoclave then started successfully. These IDs were previously exposed as medical prerequisites, so no source or hidden-tree inspection was involved. The plain search output says it checks both IDs/names among what can start, which makes these results inconsistent. Earlier `available autoclave limit 10` searched the whole phrase literally: free-text subject searches and structured filters need consistent syntax, or a short example explaining their different grammars.

### 154. Civilian technology has now produced explicit social effects
At305 “Epidemics stop deciding who lives” was awarded. Antisepsis/steam sterilization and malaria vector control explicitly changed population. Population estimate245,192,151 at305 versus211,426,981 at300, about16%growth over5years; do not attribute all growth to two new nodes without counterfactuals. Earlier sweeping statements that household/public-health effects were wholly unmeasured need correction. The aggregate effects exist; deployment geography, treatment coverage, vaccine uptake and mortality breakdown are still missing from what I have observed. Keep goal feedback and add those measures.

### 155. Hazard mitigation is rich and visible
Eight Princes finished by307; Yongjia307–317 began. Risk gives baseline20%annualsacking reduced to roughly5%, staff-loss severity3% with32%annualwave probability, and mitigation of output damage to42%of baseline. It credits water/hygiene, germ theory, isolation, vaccination, diverse fields/food preservation, walls/guns, domestic production and military diffusion92%. At308 an attack failed and output fell to78%normal. This is strong evidence of interactions between health, agriculture, technology diffusion, military power and economics. Show the mitigation arithmetic clearly, especially baseline versus adjusted cumulative probabilities; do not confuse a staffing-wave probability with percentage staff lost.

### 156. Hydro generation works when separately installed
Hydro station begun304, failed its first attempt309, completed310. Manually opening it310 raised dashboard grid generation0→3,000kW, giving total3,310kW, average demand127.5kW and2496%reserve. The earlier inconsistency—central-generation capability checked before any grid generator—remains a labeling/gating concern, but physical generation is a distinct tracked quantity and can be developed. This is a successful player-created goal. No claim that completing a transmission grid alone installed the station.

### 157. Late-game infrastructure costs feel too small, capacity too generous
Hydro station research bill5.208m and opening advance0.781m against annualnet~8.7bn; it supplies3MW when total reported demand is127.5kW. This is effectively affordable pocket change, although it requires engineering prerequisites and years. Could be reasonable for a small plant relative to a giant conglomerate, but the town-scale labor model, national wealth and enormous implicit output do not line up clearly. Want explicit sites/head/flow, dam/penstock/construction scale, maintenance outages, drought/seasonality and expansion choices. No external real-world cost audit performed.

### 158. Research timing and fractional payment tails still need repair
Industrial zinc succeeded303 after12steps from291; germanium extraction309 after5steps from304; both track nominal schedules rather than adjusted floors. Vacuum tube started306 with3.8adjusted/5.2expected years but an8year payment schedule. At305 anaesthesia owed only35cash and waited another full year despite >100bn cash. Stethoscope/blood bank/smallpox/X-ray sometimes showed two or three payment years for balances apparently equal to one or two caps, consistent with rounding/float tails rather than meaningful construction work. Completion estimates need robust rounding and a tolerance for immaterial leftover bills. Don't label a fraction of cash as an economically binding annual bottleneck.

### 159. Repeated failures of abstract knowledge are awkwardly described
Nitrogen-cycle knowledge started308 with zero calendar years, then failed twice at309/310, losing0.300m each and40%hours. A modern knowledgeable founder can plausibly fail local experiments or adoption; it is odd to “fail” knowing the cycle with no stated experimental validation. Specify what is being proven, built or taught, and vary failure wording/rework by node type. Base failure risk in portfolio can differ from the reduced next-attempt chance in the annual narrative; label which probability is active.

### 160. Research duplication needs clearer compatibility
Salicylate/aspirin medical-method node and separate commercial aspirin node coexist; reaper capability from an earlier branch did not automatically satisfy ag2_reaper prerequisites shown for mower. Autoclave is distinct from asepsis/steam sterilization, which can be sensible technique versus apparatus. Explain equivalent knowledge, industrial supply and product variants so players can reason by function. A very large tree is good only if distinctions help decisions rather than conceal duplicate names behind prefixes.

### 161. Ethical/clinical institutional options would improve roleplay
Cadaver-dissection description specifies executed criminals and unclaimed poor; no observed option for voluntary donation/consent or changing legal supply. Deferred that branch for a substantive roleplay reason while pursuing many other medical technologies; not avoiding it merely because it increases a count. Want hospital consent/safety/oversight policies, body-donation teaching programs, drug dosing/quality testing and visible public-health rollout. Historical pushback and ethical safeguards could have costs and legitimacy effects rather than being one vague opposition multiplier.

### 162. Major electronics prerequisite gap: integrated circuits before transistors
At313, with point-contact/junction transistors and single crystal still unfinished, `why com_integrated_circuit` reports CAN START NOW. Only prerequisites: com_photolithography and quantum_solidstate_theory. Its description promises thousands of transistors on a silicon chip; material recipe is quartz sand50kg, acids15kg each, brass6kg/copper4kg, with no semiconductor-grade silicon, crystal-growth, transistor fabrication, doping or cleanroom requirement. Started successfully313 for94.399m/220founderhours/3years with25%risk. This is a reproducible start-gating gap, not yet proof completion succeeds. Continue the proper germanium/main-goal chain; do not count this as a legitimate transistor win. If knowledge-only concept versus functioning IC is intended, change the name/description and add a separate fabrication capability. This is substantially worse for simulation fidelity than small pricing/UI issues.

### 163. “Lapsed” medical protections cannot be reopened
During312's Yongjia staffing event, text labels wound hygiene, disease understanding, smallpox vaccination, diversified fields and food preservation “lapsed” despite knowledge remaining. At313 `open md2_vaccine_smallpox` and `open med_asepsis_antisepsis` both refuse: “that is knowledge, not a going concern ... already changed what you can build.” The risk screen had credited these technologies307. Need explicit distinction between genuinely closed services and permanent knowledge effects. This proves contradictory operational guidance; it does not by itself prove the mitigation calculation dropped those effects. A public-health status page should show active protections and the exact available remedy when something lapses. Existing wealthy player can't fix a warning through the obvious documented action.

### 164. Ventures output is too large and lacks a closed-only option
`ventures closed` silently prints the entire running/closed table rather than filtering; help confirms usage only `ventures`, with no options. At313 output is roughly400lines and the closed list ends “…and37more,” predominantly showing capability entries first. Need paging, closed-only, trade/health filters and counts of actionable versus knowledge-only entries. The normal player interface itself omits the tail; this isn't a request to use grep or inspect data. `stuck` names a few actionable openings, but cannot substitute for a full inspectable service inventory.

### 165. IC loophole completed, not merely accepted at start
At316 the game completed `com_integrated_circuit` on its first attempt. Vacuum tube failed again the same year; GeCl4 purification still unfinished; point-contact/junction transistors and single crystal not built. Main goal remained unachieved. This confirms graph-level completion inconsistency, although the node is knowledge-only and no actual chip output has been observed. It should not be claimed as physically manufactured ICs or a legitimate transistor win. Name/description promise fabrication capability beyond the prerequisites. Fixing just the main goal score would not resolve the missing fabrication requirements.

### 166. Wage labor should be a valid school-founding route
Institution list314 showed `school_founded` blocked by `freedman_staff`, despite hundreds of paid staff and existing university/lending-library knowledge. Under this run's existing restriction against purchasing people, that blocks a named school pathway. This is a prerequisite observation, not proof there are no other educational institutions. Offer alternative wage-paid scholar/teacher staffing and show which institutions can increase general literacy. The advertised `buy school` bug is separate.

### 167. Headquarters expansion is mostly buying another block of housing
Bought100places306 and100more316; each112.580m, inexpensive against tens/hundreds of billions. It provides room for auto-hire without strategic site/commute/public-service decisions. Good usability: one short command succeeds and raises capacity. Limited simulation: manyhundreds of staff still described as one household in a50,000-person town. Want company branches, delegated budgets, workshops outside the founder's reach and retained specialist staffing targets. Existing deputy system is a good foundation rather than absent organizational modeling.

### 168. Severe sacking despite corpus: meaningful danger, crude forgetting
During317→318, site sacked:114.420bncash taken, event reports771.3peoplegone/9projects reset. Final staff after automatic recovery474.1 versus841at317; do not confuse gross event losses with final roster change. 37technologies forgotten including14main-route nodes, despite dispersed corpus. A successful defended attack is also reported that year: could be separate attacks/sites, but the text needs locations and causality. The founder survives; real stakes exist beyond easy cash accumulation. Differentiate destroyed premises, displaced experts, lost specimens/designs and lost societal practice from an immortal modern-knowledge founder forgetting elementary knowledge. Books dispersed across many sites should have recoverable copies, expeditions or reconstruction bonuses rather than identical full research from scratch.

### 169. Rebuilding a lost prerequisite can require decades again
Lost dynamo→motors/AC→power_grid→electropolish→whisker chain cannot simply be reopened. Starting repairs318: dynamo7nominalyears, motors and grid blocked; original grid requires25nominalyears once rebuilt. Hydro survives with3MWgrid generation, but grid transmission line vanishes and knowledge flags still mark grid capability. Distinguish surviving physical installations from lost production ecosystem. Lower-level dependencies remain missing while some advanced equipment survives, which is plausible materially; the UI shouldn't present all this as one undifferentiated “forgotten” state. Offer recovery of documentation, outside suppliers, reconstruction contracts and field repairs. No reload or rollback used.

### 170. Staffing/recruitment and society now react to destruction
Reach for scholars falls from roughly90before disaster to50.5at319; attempting20additional scholars when47employed was refused, allowing onlythree. Recruitedthree320. Deputies/hours shrink from11,478at317 to6,286at321 despite some workforce recovery; institutions14→13 and resilience4→3 by320. Sixteen Kingdoms explicitly shifts patronage/military values; general staff/logistics explicitly increase state_capacity. These are concrete institutional/demographic consequences, not a pure technology list. Need reason codes for which destroyed/lost institution changes each capacity.

### 171. Useful automated contracting exists
Enabled `policy auto_commission on`319 after oversubscribing machinist demand9,741hours versus3,300supply at318. No externally scripted play. It's a once-yearly heuristic, not a planner; auto_hire/open/court_heir/mothball were already on, people purchasing remained off. Wants: visible contracted-hour/cost receipt, exact staffing buffers/priorities and a “do not let clinics lapse” setting. I advanced318before resolving oversubscription, a player mistake. Built-in automation is appropriate to reduce repetitive hiring but doesn't remove the need to inspect critical trades.

### 172. Endowments are present; correct earlier absence claim
At320 institution list exposes `fin_endowed_chair`; started it along with museum/civil-service examinations/field hospital. This contradicts any earlier broad statement that endowments do not exist. Still want configurable endowment size, named beneficiaries, protected legal assets and ongoing teaching/adoption measures; a fixed research node may not supply those controls. Didn't start company-town/tiedhousing or buy/train/manumit people; those are available but don't fit the existing roleplay.

### 173. Calendar reset display did not predict actual completion
At318 portfolio showed vacuum tube7calendar years remaining after sacking; it completed321, three annual steps later, aftertwo prior failures. Do not claim a seven-year actual delay from that raw field. The displayed adjusted floor, nominal payment duration and post-reset calendar counter need a common unit and clear prediction. Current graph state and observed completion year are authoritative; the remaining-year field was not a dependable forecast here.

### 174. Search issue resolved by explicit “find”; retain the misleading-error feedback
At321, after rereading `help commands`, `available find cadaver` returned the known startable dissection node correctly. Bare `available cadaver` had returnedzero because subjects and literal searches evidently take different routes. Correct153's interpretation: a search-dispatch/usability inconsistency, not proof the literal-search implementation cannot find a node. Error for bare subject misleadingly says it looks at IDs/names and suggests shorter words, without telling the user to insert `find`. Add that precise remedy and examples; this is exactly the kind of small effort that matters for a new-user test.

### 175. Full names work; part of the typing friction was my own choice
At323 `start Cell as basic unit of life` and `start Toothbrush` resolved correctly; at324 full names for Argand lamp and evaporated milk also worked. The help says id OR name. I should have tried this earlier. Do not report IDs as mandatory or claim programming knowledge is needed to start projects. Human naming is supported; ambiguous duplicate variants, free-text find syntax, incomplete lists and broken schools remain genuine usability concerns.

### 176. Second sacking resets research without further knowledge loss
During321→322 Sixteen Kingdoms sacked a site:47.577bncash, event589.5staff/10projectsreset; finalstaff363after recovery versus635previousarrival. Another7.656bnseizure. No additional forgotten technology reported. Actual damage can be cash/crew/project disruption independently of knowledge loss. Narrative should expose sites/copies/recovery contracts, duration of destroyed versus displaced staff and how these losses differ. Low displayed sack risk doesn't mean impossible; two events do not prove broken RNG. Do not silently reload them. Recruited20scholars322once roster fell below the51.4ceiling, showing recruiting ceiling is distinct from available vacant places.

### 177. Nearly doubled country population in25years needs food/demography support
At325 population422,052,745 vs211,426,981at300:1.996x despite observed11%wartimedecline. This directly answers whether population can change on the country scale: yes, dramatically. No claim it is a player-selected doubling target or all caused by recent medical work. Need fertility/mortality/migration/age breakdown and food/calories/land/urban-service constraints supporting sustained growth. The town still estimates50,000, while national demographics drive resource availability; regional population should reflect adoption and migration. This is realism feedback, not a verified formula bug or outside historical audit.

### 178. National specialist counts are placeholders rather than convincing diffusion
At325 country422m but estimated7.5chemists,3electricians,3engineers,3machinists/opticians, while army technologies diffused95%earlier. Reach for these tiny specialized totals is essentially the same as national count, and own hires account for most. UI explicitly labels estimates/placeholders, so don't claim these are an actual census or definitive historical impossibility. Still, advanced production and nationwide technological uptake should produce apprentices, independent firms and regional specialist pools. Expansion/training is a more important next step than adding hundreds more nearly duplicate invention nodes.

### 179. Long reconstruction is a primary-goal gate, not only restoring count
At325 zone refining requires arc_furnace_ferroalloys, germanium reduction, lost motor_transformer_ac and metrology. Arc furnace refused missing lost power_grid. Thus surviving3MW hydro and grid capability checkbox do not bypass the named lost grid prerequisite; dynamo→AC→grid rebuild is genuinely necessary on this route. A functioning generator/wiring topology, power-quality capability and industrial ecosystem should be checked by physical function or clearly separated stages. A destroyed conceptual node plus retained grid-power flag is confusing. Need recovery discounts/diffused supplier alternatives, not automatically ignoring real destruction.

### 180. Public-service opening is supported and affordable
Opened endowed chair/civil-service exams323, museum/civilianhospital324, fieldhospital321. Each warning correctly says costs exceed income and allows the player to proceed. At325 both hospitals and child/maternal/isolation clinics confirmed already running. This is useful agency for a public-benefit run and corrects broad claims that money can only buy profit-making ventures. Need teaching slots, museum protection/visitor outcomes, hospital beds/patients and professional nurse supply to make those choices measurable. Existing loss-making service warnings should mention benefits in the same reply rather than only advising another why screen.

### 181. A named save used as resume path gets overwritten
I launched from han-fog-year-300.json, and autosave/quit wrote325back to that same local filename. Copied opaque bytes to han-fog-year-325.json and han-fog-live.json; prior shared300version retained without replacement. This is partly my workflow mistake, not failed saving. Recommend a warning on resuming a named checkpoint, separate live-session path or automatic dated snapshots. A new player shouldn't accidentally turn a “year300” export into year325 merely by playing normally. No save contents inspected, no file/script used to advance play. Earlier absolute-path save rejection remains separate.

## Final 325 AD assessment

| Measure | 300 | 325 |
|---|---:|---:|
| Own technologies currently retained |395|465|
| Granted technologies |109|109|
| Main-route nodes currently retained |160|165|
| Employees |666|589|
| Operating concerns |190|205|
| Cash |96.079bn|42.207bn|
| Recurring net/yr |7.767bn|8.256bn|
| Directed founder-hours |9,918|4,058|
| Country population estimate |211.427m|422.053m|

Two sacks plusthreepropertyseizures directly took216.641bncash this sitting (sacks161.997bn,seizures54.644bn), excluding taxes/post/requisition/trade losses.37technologies/14main-route nodes lost in first sack. Full EightPrinces and Yongjia windows survived as founder, organization badly damaged; SixteenKingdoms ongoing. Endowment/museum/public hospitals built and operating; epidemic-resilience award and3MWphysicalgeneration achieved. IC completed via serious prerequisite loophole; no claim physically manufactured chips or a proper transistor win. Primary remainsunfinished.

Final3projects: dynamo restoration8.389mowed/onepaymentyear plus confusing3-yearportfolio counter; germanium reductionzeroowed/onecalendar year afterfailure; metrology5.291mowed/onepaymentyear. Exactly25annualsteps ended325. Goal reserve remains~18.2years listed recurring costs, no debt; noenslavedworker/peoplepurchase rule maintained. Literacy21%, institutions13,resilience3. No graphical-map use or movement this sitting. Manual player commands only, no source/data/save inspection and no external scripts for gameplay.

Fun/difficulty: earlyyears enjoyable diversification, lateyears genuine loss/recovery tension. Historical disasters materially affect progress; normal economic purchases are easy, reconstruction chains and opaque staffing/capability states are frustrating. Still want to continue, but “no practical failure risk because we're wealthy” would now be clearly wrong. The proper semiconductor route has enoughremainingcalendar for recovery before600; can't guarantee no future repeated destruction. Initial150-yearclaim does not describe this run:225years elapsed, goalstillpending. Fog complicates discovery but did not cause the sackings.

Highest-priority developer fixes now: integrated-circuit fabrication prerequisites; distinguish permanent knowledge from operational/lapsed protections; fix schools; reconcile remaining-year forecasts; provide disaster recovery/copy retrieval and named-site protection; preserve critical skilled staffing automatically; make the closed-services list fully inspectable. Stronger simulation mods: demography constrained by food/land, regional training/adoption/independent suppliers, recoverable dispersed archives, distributed company operations, China-specificinstitutions/geography and hydropower seasonality. Maintain useful existing material substitution, mine depletion, measured hazard mitigation and public-service spending rather than replacing them with more nodes alone.

## Continuation 325–350 AD: notes recorded during play

### 182. Public prizes work, but help omits price/eligibility
`bounty fin_research_institute` at325 posted successfully for28.968m,2.5times the ordinary11.587m quote. Institute finished327 without founder hours or a remaining payment balance. It still waited two years and entered our own built count, not granted count. `bounty power_grid` refused missing motors; `bounty motor_transformer_ac` refused category electrical because local craftspeople supposedly cannot recognize success without theory. Help only says post a prize and gives usage. Add preview/price multiplier, eligible categories, judging requirements and what happens on failure before spending. The category explanation feels too broad given actual3MWpower, existing electricians and theory/measurement knowledge. Allow qualified judges and visible functional tests rather than treating all electrical outcomes as unrecognizable; no claim of inspecting eligibility implementation.

### 183. Both transistor branches now blocked by lost grid
At327 point-contact start refused gp_whisker_forming. Its why requires lost electropolishing, whose sole missing prerequisite is power_grid. Single-crystal route also needs zone refining/arc furnace and lost motors/grid. Material purification alone therefore does not make a near-term win possible. Existing workshop electric supply, battery/rectifier/instrument capabilities and3MWsurviving hydro cannot substitute for the named grid node. Chemical/electrolytic surface preparation is meaningful, but a small lab should have a functionally adequate alternative to rebuilding an entire national diffusion milestone. Offer scale-specific power/surface-prep routes, while keeping real precision/material requirements.

### 184. Technical descriptions contain patch history and fog-design commentary
Whisker why describes the historical etch/microscope/point-forming process usefully, then explains materials previously “floating free of the tree” and why dependencies are now hidden a step short of the goal under fog. This is player-facing developer commentary, not source inspected. Move patch history to release notes and leave process choices/capabilities in the invention description. Historical names/process narrative are useful; engine-design commentary breaks the new-user roleplay.

### 185. Further fire proves historical danger is not over
During326 a capital timber-ward fire destroyed10,208,491,894cash without reported technology loss. At328 patron death repeats temporary55%protection and+4scandal while autoheir paid1.501m; trend projects threshold in6years from a one-off jump. The previously logged extrapolation issue remains. Want fire compartments/material choice/insured or separated premises and a map of which site burned. Existing building-code development didn't visibly eliminate this hazard; don't claim it has no effect from one fire.

186. **Restoration should acknowledge surviving capability.** Grid was lost in the earlier sack, yet surviving hydro/local generation remains. Restoring it in 339 quotes 25 nominal years, 12.4 displayed floor, then status in 340 says 24 more payment years. Suggest separate repair/retraining/reconstruction paths using surviving equipment and dispersed records. Do not imply all first-time diffusion must repeat after a knowledge-loss event.
187. **Show an achievable completion estimate at launch.** Grid's 12.4-year calendar floor and 16-year expected-with-retries estimate are shorter than its 25-year payment schedule. Motor projects showed the same distinction. Display max(work time, calendar floor, funding absorption time), then separately explain failure uncertainty. Current figures invite false planning confidence.
188. **Transport detail is a strength.** Railway description explicitly separates roughly 4 km of demonstration track from national diffusion, and requires bearings, couplings, brakes, signals and rail manufacture. Preserve this distinction. An optional project planner could gather these known component dependencies without removing fog.
189. **Political agency remains limited in my observed play.** Seizures in 333 and 338 cost 22.685 and 27.487 billion despite 92% protection. Clear event descriptions, but I want legitimate negotiated investment, endowments, regional rebuilding or tax settlements rather than reacting to another automatic deduction. This is an option request, not proof that every possible political action is absent.

190. **Rush needs persistent exclusions.** A 340 preview identified useful projects but also considered freedman_staff (buy/train/manumit), which conflicts with the run's no-person-purchases goal. It was skipped only by the spending cap. Add exclude technology/category/policy constraints, with the reason shown in preview, so broad automation respects roleplay goals. I manually chose the benign preview suggestions; did not purchase people.

191. **Portfolio appears to mix stale and current allocations.** At 341 it reports three active projects but grid priority #6 of 8; grid shows 900 total hours to go although annual status says 100% spent, and atmospheric engine shows 900 effective hours while status likewise says all hours spent. Likely displaying the previous year's allocation alongside current membership. Label last-year allocation explicitly or recompute current-state projections. Trade totals themselves are not proven incorrect.

192. **Literal search versus topic expansion remains confusing.** Reproduction: 'available find rail limit 20' and 'available find:rail all:true limit:20' return broad transport listings, including aviation, naval mines and unrelated hull components, while saying matching rail. 'find aircraft' likewise expanded transport. Help advertises find as search text, without stating synonym expansion. Provide explicit literal-name search and mark expanded subject matching. all:true overrode limit:20 and produced 95 entries, causing tool-display truncation; document precedence or honor pagination. This refines rather than repeats the earlier bare-subject misunderstanding.
193. **Useful effects need scale and coverage.** Antiseptic obstetrics completion explicitly reports a population change, and the 343 war event explicitly credits food, domestic power, military strength and treasury with holding off worse disruption. Good interactions! Show magnitude, locality and adoption/coverage, so a prototype/tech unlock is distinguishable from population-wide access.

194. **Opening a small business unexpectedly recalculates other income.** At 350 hired one machinist, then opened four-stroke engine: quoted mature revenue 2,001,427/year with three-year ramp, upkeep 1,000,713. Total revenue changed 18,846,263,326 → 18,819,035,544 (down 27.228 million) despite this new small concern. No annual step occurred. Could be correct price/market refresh or ramp accounting, but needs a ledger delta explaining affected existing businesses. Not proven arithmetic bug.
195. **Staff buffers and priority control.** Midyear attrition closed 44 concerns in 341, 26 in 346 and 44 in 348, later partly/fully reopening with automation. Automatic hiring is useful, but I still manually replenish carpenters, smiths, glassblowers, scribes and chemists. At 350 a foreman-specific refusal was excellent: generic crafts cannot substitute; hiring one machinist solved it. Add minimum staffing buffers and explicit public-service priority before automatic reopening of profit concerns.
196. **Country scale and historical identity need stronger updating.** At 350 population still labels 'The Later Han Empire', despite the game's explicit Sixteen Kingdoms events. National estimate grew 422.053m → 578.245m in 25 years while our local town stayed 50k. Several highly specialised trades are estimated at only three nationwide. UI calls these estimates/placeholders, but coherent polity names, regional adoption, migration, mortality and specialist diffusion would improve the simulation; source-file pointer in population explanation is inappropriate for an ordinary player.
197. **350 checkpoint / score breadth.** This sitting deliberately added 117 own technologies (465 → 582), including useful healthcare and transport rather than only electronics. Score reports no awarded total before the transistor, and coverage withheld under fog. Good reason to develop breadth; the UI should clearly distinguish provisional components from an actual won-run score. 21% literacy and 13 institutions stayed unchanged; resilience raw score declined 3 → 2 despite maintained dispersed corpus. Add explicit delta explanations for lost resilience capabilities.

### 325–350 sitting assessment
Main goal remains unfinished; 350 deadline missed through the visible route. Grid restoration begun 339 reports 14 more payment years at 350, despite surviving 3 MW generation and restored electrical components. Broad projects made waiting enjoyable: +117 own technologies, cash 42.207bn → 179.296bn, recurring net 8.256bn → 13.609bn, staff 589 → 974. Most bothersome: misleading duration forecast, restoration treating surviving capability as a first introduction, repeated staffing closure/reopening, search topic expansion and long unfiltered listings. New mod ideas: survivor-aware reconstruction, distributed laboratories/academies with actual geographic choices, public healthcare coverage/outcomes, political investment negotiations, roleplay-aware automation exclusions. Retain positive detailed engineering dependencies, readable failure messages, qualified-foreman explanations and explicit war-resilience interactions. Original ships bug and prior economic suggestions remain in the earlier notes; this sitting does not supersede them.

198. **Save paths and export friction.** 'save /workspace/scratch/e3924217f104/han-fog-year-350.json' was refused because saves must use relative paths. Error clearly suggested 'save mygame.json', and quit successfully autosaved the configured session path with a resume command. Copied the opaque autosave for sharing. Help save should advertise relative-path restriction and clearly identify the destination folder; a friendly export action would avoid filesystem knowledge. No game state lost.

## Continuation: 350–375 AD
199. **Science-to-medicine links are rewarding.** Synthetic dyes unlocked Gram staining/culture and sulphonamides; staining then permitted penicillin extraction. These links make breadth purposeful. However, clinical unlocks remain mostly knowledge messages: add trial outcomes, purity/dose control, resistance, trained practitioners and geographic treatment coverage. A one-year extraction project is not proof of population-wide antibiotic access.
200. **Defence diffusion has observable consequences.** The 352 attack explicitly failed because of bastions, guns and 73% diffusion of our military technology to state armies. Preserve this clear explanation. Would like equivalent quantified diffusion/coverage for civilian medicine, education and energy.

201. **Tiny payment remainder adds a whole year.** At 363 intaglio engraving shows 8.2 cash owed, annual capacity 284,415, and another year required after three payments. Apparent rounding or changing-cost residual; not proven internal cause. Sweep negligible remaining balances at the scheduled final payment or explain a genuinely incomplete physical task. Eight coins should not represent a year of engravers staring at each other.

202. **Long-project retry time is poorly exposed.** Grid failed after the 25-year funding restoration; 360 retry hours finished in 364. At 365 annual status merely says waiting on calendar, while capacity reveals 15.9 years left (and displays original risk 35%, whereas failure event said retry risk 27%). I expected a modest repair period; actual UI projection extends well past 375. Show remaining retry calendar and current attempt risk consistently in state, why and capacity; explain why rebuilding a failed restoration entails another sixteen years.
203. **Allocation warning helped identify my mistake.** I allocated 900 hours to the grid's 360-hour rework and the game clearly reported 540 wasted. Cleared next year. Prefer an 'up to available useful work' allocation option that releases excess hours automatically rather than making player manually clear a completed-work priority.

204. **Grid retry projection was demonstrably misleading.** Follow-up to 202: despite capacity saying 15.9 years left at 365, grid completed during 367, arriving 368. Actual retry was four annual steps after failure, not sixteen. The displayed remaining calendar may be a stale nominal floor, but source not inspected. This is a verified forecast inconsistency, not merely my dislike of long repair. Correct the report above: restoration succeeded within the 375 chunk, and my pessimistic forecast followed the faulty player-visible dashboard.

205. **First transistor achievement is well distinguished.** Point-contact project description explicitly calls out fragile, noisy, handmade polycrystalline germanium amplification rather than mass manufacture. Completed in 373 (arrival 374); counted toward junction goal without ending run. This is good milestone design. Add demonstrator performance/yield and a celebratory milestone panel, while preserving distinction from reliable junction production.
206. **Loss of the last specialist has startling cascade.** At 373 two remaining carpenters departed, gross event reported 210 concerns closed, yet checkpoint shows 267 still running after recovery versus 289 previously. Event needs a net end-of-year recap (closed, reopened, still offline) and causal specialist breakdown. Likely cascade plus recovery, not proven that all 210 need carpenters directly. Hiring buffer next; warning before last-specialist risk would help.

207. **Clinical methodology exists; refine earlier realism criticism.** Discovered and researched placebo controls and blinded trials; randomised controlled trials started374. The game does include these technologies, so do not claim it entirely omits clinical validation. Request is for actual trial design/outcomes, sample size, dose/purity, access and safety consequences, which I have not observed, rather than simply more named clinical nodes.
208. **Public-service reopening needs priorities.** At375 audit, child/maternal/isolation clinics, hospitals, medical education, museum, endowment, learned society, research institute, civil-service exam and statistical office were offline after cascades. All twelve manual opens succeeded with existing workforce. Auto reopening's profitability screen leaves non-profit goals unattended. Add keep-open priority/essential-service policies, automatic budgeted reopening, and a prominent alert when a designated service lapses. This is now concrete observed UX, beyond earlier speculative option request.
209. **Reopen quotes and ledger refresh need reconciliation.** At375 museum's earlier running revenue was millions; reopen quotes375,268 with1,250,892 upkeep. Similar research-institute quote500,357 differs markedly from its prior mature operation. Restoring twelve services reduced total revenue32.762bn→32.549bn before any annual step, far beyond their quoted local amounts; final net24.199bn. Could reflect correct aggregate workshop/price/saturation or reopened ramp reset, but explain those deltas and whether mature custom is lost during brief staffing closure. Do not call this proven arithmetic bug.
210. **Long pauses lack visible progress feedback.** Late annual steps took up to about10 seconds in the game's own timing, with some commands arriving across separate reads. No coding required, but a visible 'advancing year / calculating portfolio' indicator would avoid appearing stuck. This matters for ordinary users as well as LLM play.

### 350–375 assessment and requested changes
Outcome: grid restored by368 and point-contact transistor by374; chosen junction goal still blocked on single-crystal chain. 116 additional own technologies;698 own/807 total. Cash179.296bn→295.146bn, recurring net13.609bn→24.199bn,974→1,397 workers. Broader science, medicine, farming, coffee, civil engineering, publishing and mechanical computation made this sitting enjoyable. No research treated as mere score padding. No person purchases or gameplay scripts.

Most bothersome this sitting: (1) dashboard's demonstrably wrong grid retry estimate (15.9 years shown365, completion367); (2) closures/reopenings with poor net reporting and no public-service priority; (3) tiny payment residual adding an annual wait; (4) large economic recalculations when reopening without explanatory ledger deltas. Positive: polycrystalline point-contact demonstration versus manufacturable junction is clearly distinguished; chemistry-to-medicine links and military diffusion are explicit; useful named mathematical/clinical-method branches exist.

Mod ideas: dedicated reconstruction using surviving infrastructure; a lab-demonstration dashboard with yields and performance; clinical trials with actual outcomes; public-service/education coverage and deployment; an independently chosen curriculum rather than opaque literacy deltas; roleplay-aware automation exclusions and essential-service staffing; geographical research-house/disaster resilience controls; coffeehouse/scientific correspondence social networks with visible knowledge spread. Earlier ships bug and other feedback remain in prior sections.

## Final push,375–400 AD: victory in399

### 211. Victory does not reveal ending score under fog; no clear finish-and-score action
Observed400: junction goal explicitly REACHED in399, but score still reports technology coverage withheld and TOTAL “not computable until the run ends under fog.” Help commands offers quit (ends session), no retire/finish-run action distinct from withdraw (political obscurity). This is disappointing after a300-year playtest and a request to maximize score: we can assess individual components but cannot see a final numerical score at the achievement. Request: show provisional total/range without revealing undiscovered nodes, and an explicit “finish this run and score” action preserving the save for optional continuation. Do not require stepping centuries to the horizon simply to review a completed goal. We did not advance beyond400 to force an ending.

### 212. Achievement contradiction: “no concern ever closed for want of staff” awarded
400 score marks [x] no concern ever closed for want of staff. We repeatedly observed exactly that message:43 closures378,75 closures393,19 closures398, plus many earlier. This achievement cannot accurately describe this run. Reproduction uses rendered annual reports and score, no code or save inspection. Request: achievement flag based on actual closure events; distinguish avoided insolvency closures from avoided staffing closures if these are different achievements. Other achievement checkboxes are credible: no slaves[x]; paid interest73,617 so debt-free[ ] is correct; knowledge losses[ ] and speed[ ] are consistent with history.

### 213. School-purchase parser still broken, educational routes clash with no-slavery run
376 `buy school scribe 10` repeats previous137 refusal as invalid material, despite help buy explicitly advertising `buy school <trade> <n>`. Separate design issue: school_founded requires freedman_staff, whose action explicitly buys/trains/manumits people. We decline it because this run never purchases people. Academy/journal/doctorate remain hidden-prerequisite blocked even with university, medical education, patents, public books and statistical institutions. Request: paid/apprentice/free-worker school founding alternative, and fix advertised school purchase. No claim these hidden institutions all depend on slavery—we cannot see their prerequisite.

### 214. Advanced project versus infrastructure scale needs explanation
Autogyro554k, helicopter rotor751k, powered aeroplane779k, jet construction1.146m versus200 housing places225.161m. May legitimately mix prototypes, knowledge and full physical infrastructure, but scale is unclear to a player. Flight description says “testing kills the pilot,” while failure appears as minor cash/hours loss without a named pilot casualty; distinguish flavour warning from modelled human costs. Request: prototype/plant/service capacity labels, development teams, testing fatalities and safety investments, production yield, maintenance and deployment costs. Not asserting every quoted cost is erroneous.

### 215. Repeated score/public-service maintenance friction and opaque repricing
Priority twelve clinics/hospitals/research/culture offices needed manual reopen in375,394 and399. After394 staffing repair all opened, yet the company-wide annual revenue fell roughly299.5m as those services opened;399 repeated306.4m fall. Individual quoted annual service receipts do not explain that company-wide movement. This could be valid portfolio demand/staff/ramp repricing, not proven arithmetic bug. Reinforces208/209: protect named public services, minimum specialist buffers, bulk reopen chosen group, and show “this action changes other operations by X because Y.” Most bothersome remaining interaction: recurrent specialist turnover→many closures→manual staffing and service checks despite enormous spare generic workforce.

### 216. Paging beyond a shrinking list produces misleading empty-search advice
377 institutions list shrank from20 to13 after starts. Asking offset15 says nothing matches and suggests shorter search; actual cause is no rows remain beyond offset. Request: “page past end;13 available; first page...” with stable navigation. Minor but unnecessary effort.

### 217. Real benefits from breadth, and knowledge versus national delivery still unclear
Movable type completed380 explicitly raised general/elite literacy; newspaper subscriptions390 explicitly raised literacy/information/novelty. Literacy21→32% this sitting; resilience2→3. Military diffusion92% explicitly defeated attack381. Agriculture, industrial electrolysis, metallurgy and healthcare offered substantial optional research. This corrects any impression that non-transistor research is mere score padding. Still need adoption/coverage: developed clinical trials, insulin-era diagnostics, transfusion and penicillin extraction are not evidence everyone receives safe care. National literacy75% remains unachieved. Want school enrollment, clinic capacity, treatments/outcomes, farmer labour release, pollution and regional delivery maps.

### 218. Timing/risk create the final challenge, but money and directing capacity are easy late
Arc furnace first test379 failed57.761m, retry381 succeeded; zone first test387 succeeded; crystal392 succeeded; junction396 failed40.099m,399 retry succeeded. Quoted reputation-adjusted calendar floor understates practical funding duration: zone2.9 displayed but six annual funding years; crystal2.4 displayed but five; nominal duration/absorption pace is more useful. No scripts/reloads/hidden-tree reads. End treasury838.386bn versus final junction100.246m; research money trivial, large state levies/living costs still material.11,717 directing hours mostly idle at400. Want more organizational scaling friction, qualified research teams, yield/precision/testing, political agency and calendar forecasts that incorporate actual payment floor. Waiting remained fun when paired with meaningful civilian projects.

### Result and personal assessment
Won the stated junction-transistor goal in399AD, start100AD, fog on, Han China, immortal scholar, no slaves ever owned.400 checkpoint:892 technologies built by us plus109 grants=1,001 total; +194 own since375.1,860 paid employees;838.386bn treasury;52.017bn annual revenue;33.613bn recurring net;14 institutions;32% literacy;resilience3;reputation97.8;protection92%;scandal0.08;eminence21.0. Speed achievement not earned:300 years elapsed at checkpoint versus142.2-year twice-fastest threshold. This is a successful broad playthrough, not maxed game/whole tree or proven optimized score. Powered flight, jet prototype, television components, programmable mechanical computer, trial methodology, DNA concept, practical farm mechanization and mining safety diversified the finale. No universal adoption claims.

How I feel: delighted and relieved—we finished in399 after the first junction failure, almost exactly at the requested deadline. The game can be won with fog and no slavery in this run. It is engaging as a technology/business progression game, less convincing as a quantitative historical forecast. Enjoyment rose when waiting became civilian experimentation; busiest annoyance is staffing/service upkeep, and the biggest finale disappointment is absent total score plus contradictory achievement. Priorities for developers: fix school parser and achievement, offer explicit goal-ending score, protect public-service operations, improve realistic calendars and prototype/industry scale, then expose adoption and causal economic deltas. Mod idea: a public-service foundation with schools/clinics/museums, budgets, regional coverage and protected staffing; an engineering-quality mod with prototypes, yields, test safety and industrial replication. This is additional feedback, not source inspection or a proposed code patch.

### 219. Post-victory opening changes final financial snapshot materially
After the400 score/ledger audit, explicitly `open junction_transistor`: quote75.054m annual receipts,45.032m upkeep,3-year ramp; treasury838.386005bn→838.340973bn (45.032m charge). Total company revenue52.017383bn→47.149490bn (4.868bn drop), upkeep871.018m→916.050m. No prior ventures audit established if auto_open already operated it, so do not claim a confirmed duplicate-open bug. Request: show already-open status, avoid accidental reopening/ramp reset, and explain portfolio-wide revenue deltas on opening. Saved final treasury838.340973bn; other headline victory metrics above refer to arrival before this command. Holding the ledger's other expenses unchanged yields final recurring net28.700551bn (calculated; no subsequent ledger screen). Quit autosave confirmed400 stopped; victory399 remains explicit. This reinforces opaque causal revenue feedback rather than asserting an unexplained number is definitely wrong.

### 220. User suggests horizon advancement reveals the final score — untested
After victory399/checkpoint400, the user suggests using `next`/`step` for enough years to reach the deadline and receive the score breakdown. The displayed horizon is600AD, so200 additional years would reach it from our checkpoint;300 would overshoot. Help explicitly supports `step <years>` and lists next as an alias. This is consistent with score saying coverage resolves once the run ends, whereas quit only ends a session. We have NOT tested horizon scoring or advanced beyond400. Treat the suggested result as a plausible hypothesis, not verified behaviour.

Important distinction: advancing200 years simulates ongoing staff turnover, concern closures, historical hazards, cash flows and existing research. That could substantially alter the company or end the run before the horizon. Ordinary quit has not been shown to cause workforce loss; annual simulation has repeatedly done so. Preserve the400 victory save before any such experiment, and report victory399 versus final-horizon results separately. UX request refined: offer a voluntary finish-and-score snapshot at goal achievement, alongside optional continued play to the historical horizon, with clear explanation of when scores become available. A deadline score may work as designed; the observed issue is unclear access to a score at the achieved goal, not a confirmed broken scoring implementation.

## Authorized unattended horizon test from400AD
User explicitly requested `step 200`, with no new research. Preserved han-fog-year-400-victory.json and resumed a separate opaque copy, han-fog-horizon-test-live.json. Issued one normal player command `step 200`. No scripts, source reads, save parsing or newly started research. Three projects already active at400 may finish during simulation; automatic policies, staff turnover and historical hazards remain enabled. This test measures what the offered multi-year interface actually does, rather than assuming200 years leave a victorious company unchanged.

### 221. Multi-year step gives no visible progress while processing
The authorized400AD `step 200` echoed the command, then produced no intermediate year/progress/busy output for over a minute. Earlier single-year steps cost roughly8–12seconds, so this is potentially a lengthy operation with no way to distinguish working from stuck through the player interface. We did not interrupt or inspect code/process internals. Request: show current simulated year, years remaining, and notable events as they happen; optionally stop on major hazards/staffing collapse, with a clear cancel-and-checkpoint operation. A lengthy batch should not require technical diagnosis.

Additional observation for221: accumulated waiting now exceeds half an hour with no intermediate progress, output or error from the offered step200 command. The process has not returned control. This is not proof of deadlock; roughly200 late-game turns at previously observed8–12+seconds can itself take tens of minutes. However, the player cannot establish current year, remaining work, survival or whether a checkpoint exists through the interface while it is busy. A multi-year action needs progress feedback regardless of whether its total runtime is expected.

### 222. Horizon experiment cancelled after approximately51 minutes; no partial checkpoint survived
Issued the explicitly authorized normal CLI `step 200` from400AD. For approximately51 minutes it produced no simulated year, progress, summary, error or queued score response. Wall clock at13:49UTC versus user request12:57UTC confirms roughly51 minutes spent on this attempt/setup. Cancelled using the terminal keyboard interrupt on the separate test copy; process exited1 with only ^C, no advertised partial save. Reopening that same test copy explicitly resumed400AD with the original838.340973bn treasury. Therefore none of any in-memory advancement was persisted. We cannot establish whether the simulation was slowly progressing or stalled; do not label it a proven deadlock, and do not claim the600AD score was tested successfully. The queued score never ran.

Severity: high UX/performance/checkpointing failure for the advertised multi-year command. A player should not wait almost an hour blindly, then lose every uncheckpointed year on cancellation. Request: stream year/progress, periodic resumable checkpoints, safe cancel saving completed years, and predictable runtime. Preserve original victory save; it was untouched throughout. A one-year follow-up on the separate copy checks whether single-year play still responds. No new research started and no source/save parsing or scripts used.

Follow-up to222: a normal single year400→401 succeeded in20.3seconds. This changes the performance interpretation:200 turns at that rate would take about68minutes, so cancelling at51minutes may have been premature. The batch is incomplete, NOT a confirmed deadlock or confirmed failure to reach600. High-confidence issues are silence throughout a long operation and no partial checkpoint after interrupt. I chose to stop the test and preserve a401 follow-up; do not claim a final score or200 completed years.

### 223. No new research does not freeze the company or history
Observed single year400→401: state monopoly/post demands6.634bn plus frontier disruption86.093bn. Treasury838.341→774.839bn, net decrease63.502bn despite receipts. Lost58 artisans,glassblower1,scholars2, but auto-hiring increased total1860→1862. Known technologies1001 unchanged; inherited research advanced without completion. New recurring net30.471bn,standing95.7. User's expectation of small change without research is contradicted by this first year. Show multi-year preview of historical hazards, staffing churn, enabled policies and active projects; warn that passive time advance still simulates the economy/world. No evidence quitting itself causes workforce loss. Original victory400 remains untouched; follow-up save401 is a separate artifact.
