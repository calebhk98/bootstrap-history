<!-- Tester notes (bugs, UX, feature requests) from the same England 1300 fog playtest, 1300 to 1375, poor_scholar kit. Verbatim. -->

# Bootstrap History blind playtest notes

## Session/tooling mistakes
- My first README command used an archive wildcard and accidentally streamed multiple README files. This violated the blind-test restriction. I will ignore all non-root README content and base play decisions only on the root README and in-game UI.

## UX / bugs / feedback

## First-impression notes
- Main menu is clear: New / Load / Options / Quit. Program-level Options explicitly distinguishes itself from per-playthrough settings.
- Load screen clearly states the save directory, handles an empty save folder well, and allows loading by arbitrary path.
- Startup civilisation descriptions communicate different strategic bottlenecks well enough to make a meaningful choice without outside knowledge.
- Fog explanation is clear and appropriately irreversible.
- Starting kits explain both flavor and mechanical scale; poor_scholar reads as the intended baseline.
- Mortality is framed clearly as a different kind of test; irreversible once enabled, but can be enabled later.
- Goal selection is excellent at communicating scope via closure and theoretical floor without revealing the route under fog.
- Horizon/difficulty is unusually transparent: difficulty changes only the deadline, not costs or RNG.
- New game auto-creates a resumable session and prints the exact resume command. This works especially well for one-command-per-invocation play.
- Top-level help is concise and actionable; it emphasizes annual upkeep, opening finished concerns, and the stuck command.
- Minor UX nit: mentioning pasteable JSON commands in basic help is technical noise for a nontechnical first-time player.

## Campaign setup
- Civilisation: England under Edward I, 1300
- Fog: ON
- Starting kit: poor_scholar
- Founder mortality: OFF
- Main goal: grown and alloy junction transistors
- Horizon: Standard, 500 years (ends 1800)

## Emerging self-imposed goals
- Reduce epidemic/famine mortality before the Black Death if the game makes that realistically reachable.
- Raise literacy substantially, not merely unlock a school.
- Build institutions/economic activity resilient enough that plague does not erase the campaign.
- Save UX friction: `save` rejects absolute paths and requires a relative filename. That is probably deliberate, but it adds a step when a player/tester needs to export a save somewhere specific.

## Logging / Test Process
- Added a separate `yearly_log.md` campaign diary at user request.
- I will record at least one entry for every in-game year that passes, including goals, decisions, surprises, UX friction, and changing opinions.
- Because the chat interface may suppress intermediate messages during long play sessions, I will deliberately stop at sensible intervals and report progress instead of running the campaign continuously for a long span.
- Content/modeling note: `med_legal_physician` is described as an imperial edict yet is offered in England 1300 as a 0-cost, 0-time, 0-risk start. This may be intentional generic inheritance, but it reads historically/contextually wrong to a blind player.
- Positive: revenue-bearing concerns ramp toward full custom over several years rather than instantly producing their quoted mature revenue.
- UX/immersion issue: the normal `population` screen tells the player to “see labour.py's TRADE_DENSITY” and says some values are placeholders. This is developer/source-code language in the player UI. A nontechnical player should not need or be encouraged to inspect code to interpret population estimates.
- Positive: failed projects retain some elapsed calendar progress and reduce repeat failure chance after the failure mode is understood. This makes failure meaningful without feeling like arbitrary total-reset punishment.
- BUG/UI inconsistency: `why tex_horizontal_loom` said STAFF TO KEEP IT OPEN was `0 scholars, 0.27 artisans`, but `open tex_horizontal_loom` refused because it actually requires 0.25 **carpenter** FTE and explicitly says generic artisans cannot substitute. The pre-purchase detail screen concealed/misstated the specialist operating requirement, which can cause a player to buy a venture they cannot run.
- UX/taxonomy issue: `available electricity` returned only `Signal flags for maritime communication`. Subject/category browsing can therefore be semantically misleading; a player asking for electricity reasonably expects electrical technologies, not optical/semaphore signaling.
- Modeling/clarity concern: `score` at 1310 reports resilience raw 4, normalized 0.980, while `risk` still shows no knowledge hedge and severe staff-loss exposure to the coming Great Famine/Black Death. The resilience score may be valid, but its meaning is opaque enough to look contradictory. Explain the component or its inputs.
- Positive: `arithmetic_positional` exposed a real human-capacity bottleneck. The player had sufficient money and founder-hours, but reachable scribe-hours constrained progress. This is exactly the kind of institutional/tacit-capacity limit that makes the premise believable.
- Minor UX: `changes 10` at 1310 refuses because the run record only goes back to 1301 and asks for 9 or fewer, even though the campaign began in 1300. Not serious, but “first ten years” and recap-window counting are slightly unintuitive.

## Ten-year retrospective / mod ideas
- Add stronger civilisation-specific wrappers or substitutions for generic inherited nodes. An “imperial edict” appearing free in 1300 England is jarring even if mechanically equivalent to a legal privilege.
- Tighten subject taxonomy. Signal flags appearing as the sole `electricity` result undermines confidence in category browsing.
- Make every `why` screen show the exact specialist FTE needed to operate a venture. The horizontal loom purchase screen said generic artisan supervision; `open` later demanded carpenter FTE.
- Consider a clearer distinction between personal discovery, local adoption, and civilisation-wide diffusion. The game already hints at this through venture ramp-up, household reach and labour markets; leaning further into diffusion would make alternate-history acceleration feel more believable.
- Expand explicit institutional routes for scribe/scholar supply, schools, copying/printing and archives. The arithmetic bottleneck made this immediately interesting.
- If famine mitigation intentionally includes sanitation/quarantine/inoculation because secondary disease drives deaths, explain that causal chain on the hazard screen; otherwise the mitigation list reads like an epidemic template attached to a famine.

## 1311–1320 tester notes
- Positive modeling: the labour screen distinguishes a society-wide literate-labour ceiling from the player's household reach. It explicitly says schools/academies/patronage are the large way to expand scholar capacity while printing/paper/libraries broaden literacy more gradually.
- Positive modeling: hiring scarce literate labour moves the wage for the whole category. A scholar around 1314 would have cost ~21,974/year once hired; after the famine shock the equivalent was ~23,821/year. This made 'just hire another scientist' a meaningful strategic decision.
- Positive modeling: `school_founded` is optional, extremely expensive, slow, and converts founder time into future scholar capacity rather than simply unlocking a tech node. The description explicitly says money cannot buy down the generational diffusion floor. I have not unlocked its two hidden prerequisites yet.
- Positive modeling: theoretical knowledge can precede practical capability. `atomic_theory` says I can write the periodic table from memory immediately but it does not become operational until an analytical balance exists.
- Positive modeling: the Great Famine had multi-layer effects: player staff loss, empire-wide population loss, persistent wage inflation, and a separate supply-disruption cash shock. Population remained ~10% below trend the year after the famine event and wages stayed ~9% high.
- Positive modeling: workforce attrition is represented as FTE shrinkage rather than integer people popping in and out. After the famine my carpenter fell to ~0.91 FTE, and the UI explained why.
- Positive/balance: the tempting rope-walk business did not become a money printer. At 1320 the ledger explained that the loom and rope walk saturate the same textile market; saturation removes ~32,550/year from their combined quoted revenue, and the loom is only earning ~36% of its tree quote. This is a strong anti-exploit mechanism and should remain visible.
- Positive: venture `why` screens now clearly distinguish BUILD staff from `STAFF TO KEEP IT OPEN`, with an extended explanation of FTE supervision. This is the right UX. The earlier horizontal-loom mismatch therefore appears to be a node-specific data/UI inconsistency, not a general failure of the interface.
- Balance/modeling observation: Silage and the silo cost ~76,531 pence but reduced Great Famine staff-loss estimate only from about 12% to 11% (90% of unmitigated impact). I like the modest effect, though the hazard screen could communicate expected benefit before purchase more explicitly so players can judge a huge resilience investment.
- UX/modeling question: during the 1317 famine, the event text says '2,336 gone with the trade that stopped' after staff -8%. The unit/meaning of 2,336 is not immediately clear from the message; it reads like people, money, or labour-hours without a label. Add a unit or clearer noun.
- UX/modeling question: the famine event says 'the country's own public health has spread far enough' to soften national mortality. It is unclear whether that reflects baseline English institutions, my discoveries, passive diffusion, or something else. A short attribution would help a player understand whether their actions mattered.
- Strategy/feedback: filtering `available` by natural concepts like `education`, `public_health`, `water`, `sanitation`, `library`, or `literacy` often returns zero even though related systems clearly exist and are referenced elsewhere. This is not necessarily wrong under fog, but discoverability feels brittle because subject/name matching is literal enough that sensible player vocabulary can fail.
- Economy/UX: the ledger's market-saturation explanation is excellent and should arguably be surfaced earlier on `why` or `open` when the player already operates another concern in the same category. Right now the player can only discover the magnitude after opening and checking `money`/`ventures`.

## New mod / feature ideas after 1320
- Add a **founder journal / decision log** inside the game: auto-record starts, failures, openings/closures, staffing changes, major events, and optional player notes. Long campaigns need an answer to 'why did I build this 40 years ago?'.
- Add clearer **causal attribution for national diffusion**. If personal technologies are spreading into national public health or productivity, show which discoveries/institutions contribute and by roughly how much.
- Add **regional/sector diversification** choices for businesses. The market-saturation system is good; it would be even better if the player could deliberately open a venture in another town/region, paying logistics/management costs in exchange for a distinct demand pool.
- Add richer **education ladders** between one hired scholar and a 450k school: tutoring circles, scriptoria, guild schools, cathedral schools, bursaries, translation programs, etc. The current gulf makes the human-capital bottleneck interesting but very binary.
- Add a clearer **pre-purchase hazard-impact preview** for resilience projects: e.g. 'at current conditions this would reduce expected famine staff loss from ~12% to ~11%'. This does not need to reveal hidden tech-tree information and would make large resilience investments easier to reason about.

## 1320 retrospective — after 20 years of play

### Overall impression
After 20 in-game years, the game is more interesting and more systemic than it first appeared. The opening looked as though it might collapse into a broad tech tree plus money management, but labor scarcity, market saturation, recurring upkeep, demographic shocks, project failure, staffing requirements, and institutional bottlenecks have begun interacting in ways that force tradeoffs.

### Realism
The game models the *shape* of historical technological development better than literal historical quantities. Strong points include separating knowledge from operational capability, requiring specialized labor, making institutions expensive, allowing hazards to damage both population and economic capacity, and making ventures compete for the same markets. Atomic theory requiring analytical capability is a particularly good abstraction: remembering a modern concept is not the same as having the instruments and institutions to make it useful.

The monetary scale does not look historically literal if the unit is intended to be an actual English silver penny. By 1320 I had about 44,094 pence (~£184 at 240d/£), while one carpenter costs about 9,400 pence/year (~£39/year). Surviving medieval accounts show ordinary paid workers often earning only a few pence per day; a 1313 Kenilworth account records garrison tenants at 2d/day, while later medieval skilled building workers are recorded around several pence/day. So the game's pence behave more like normalized gameplay currency than strict historical pennies. That is acceptable, but the game should probably say so if intentional.

The generic/shared tech tree can also create contextual oddities, e.g. an 'imperial edict' in Edward-I England, and some subject categories are loose (signal flags appearing under electricity).

### Tech-tree size and difficulty estimate
The initial fog-on position still exposed 143 immediately startable items, while the transistor goal reports a prerequisite closure of 181 and a theoretical best-case floor around 142 years. This is a large tree for a terminal strategy game, especially because fog hides the route rather than hiding most available actions.

At 20 years I have roughly 16 technologies identified as on the transistor road. A naive linear projection (16 road nodes / 20 years) would put 181 nodes around 226 years, but that is almost certainly misleading because capacity should compound and many later projects can overlap. My current rough estimate for this blind fog-on run is still about 200–350 years, with a wide error bar. Reaching ~150 years now looks possible only with much better routing/capital deployment than I am using, or with very strong later compounding.

The game currently communicates difficulty well through explicit costs, staffing, failure probabilities, hazard forecasts, recurring upkeep, and goal floors. It is strategically harder than it is mechanically difficult. The interface rarely makes me fight syntax; the hard part is deciding what not to do.

### Systems and complexity
The game is more complex than I expected from the README, but mostly in a good way. Systems encountered so far include:
- personal founder time vs calendar time;
- specialized labor and labor scarcity;
- recurring wages and upkeep;
- venture revenue ramp-up;
- market saturation/cannibalization between ventures;
- project failure with partial retained progress and improving retry odds;
- debt/credit;
- population shocks and wage effects;
- historical hazards with mitigation;
- literacy/lettered-worker ceilings;
- knowledge risk / lack of institutional hedging;
- scientific-method and measurement foundations;
- explicit distinction between discovery and operating/maintaining a capability.

The best surprise is that money is not the universal bottleneck. By 1320 I can afford many things in principle, but scarce scholars/scribes and institutional capacity block progress. That makes the economy much more interesting than a simple earn-spend loop.

### Economic system
Difficulty is moderate so far. The early game punished poor cash-flow planning, then became easier after profitable medical/textile ventures, but market saturation stopped the obvious strategy of repeatedly opening the highest-return business. Debt is useful without being free, and historical shocks can remove staff or damage supply.

Economically, the game feels internally coherent even though the nominal pence values are not historically literal. The important ratios—wages, startup capital, upkeep, debt burden, demand saturation, and scarcity—are producing plausible strategic behavior. I care more about those ratios than exact medieval currency fidelity, but an explicit note that currency is normalized would avoid false precision.

### Commands, help, and information
In normal play I am using a relatively small core command set repeatedly: `state`, `available`, `why`, `start`, `advance`, `open`, `ledger`, `labour`, `population`, `hazards`, `score`, `recap`, `save`, and occasionally subject/category browsing and `help`/`stuck` style guidance. Despite the large game, the practical command vocabulary is manageable.

`help` was genuinely useful at the start because it explained the core loop, yearly costs, finished-vs-open behavior, saving, and recovery when stuck. After ~20 years I rarely need it because the command grammar is consistent. That is a UX success: help teaches a model rather than forcing constant reference lookup.

There is generally enough information, but several outputs need tighter units/causal explanations. Examples: the famine message's '2,336 gone with the trade that stopped' lacked an obvious unit; public-health mitigation was not clearly attributed; the loom's `why` staffing description disagreed with the actual `open` requirement. Those are more damaging than missing commands because they undermine planning confidence.

### UI / UX and interaction difficulty
The terminal UI is surprisingly good. Interaction difficulty is low: most actions take one short command, feedback is immediate, and the game usually tells me why something cannot be done. Fog creates strategic uncertainty without making the controls obscure.

The main UX weakness is information density and consistency rather than command count. With 100+ possible actions, filtering/category views are essential, and category taxonomy needs to be trustworthy. Planning would improve with a built-in decision/history journal, clearer resource units, better labor substitution previews, and an explicit 'what changed this year and why' causal summary.

### Fun
Yes, it is fun now. The fun is coming less from unlocking technologies and more from making tradeoffs under uncertainty: taking debt for a silo before famine, watching one carpenter leave and shut a venture, discovering that two textile businesses cannibalize each other, or deciding whether one ruinously expensive scholar is worth most of the annual surplus.

It would be substantially less fun if fog merely hid prerequisites while the optimal route remained obvious. So far, however, the interaction between labor, markets, shocks, and institutions gives fog meaningful teeth.

### What would make it better / mod ideas
1. Intermediate education institutions between 'hire one scarce scholar' and an enormous full school/academy.
2. Deeper knowledge diffusion/tacit-skill mechanics: apprenticeships, textbooks, professional communities, regional diffusion, decay after practitioner loss.
3. Stronger causal reporting: tell the player exactly why a hazard was softened, why wages changed, and what caused a venture to shut.
4. A built-in decision journal and yearly retrospective.
5. Cleaner region/government contextualization so generic technologies do not produce oddities such as an imperial edict in medieval England.
6. Explicit statement on whether monetary units are historical pennies or normalized gameplay currency.
7. Better category taxonomy/filtering for the very large visible action set.
8. More granular political/social resistance if not already deeper later in the game: guild resistance, elite interests, legitimacy, adoption problems, and losers from technological change.
9. Regional logistics/diffusion if absent: possessing a technology nationally should differ from deploying it across England.
10. More intermediate public-health infrastructure before the Black Death; right now the gap between basic sanitation ideas and national disease-control capability feels large.

### Current confidence
I now feel competent at the interface and moderately competent at the economy, but not at the hidden progression. I expect fewer stupid UI mistakes and better financial decisions from here onward. I still expect strategic mistakes under fog, especially around institutional prerequisites that need decades of lead time. My confidence that I can finish within the 500-year standard horizon is fairly high; confidence in a sub-200-year finish is much lower.

## 1320–1335 playtest observations

### What improved my opinion
- **Creating a missing trade is excellent.** `train machinist 1` spent founder time and money, clearly told me the trade did not yet have a trained practitioner, gave a future completion year, and automatically added the trained machinist to staff when finished. This is a strong abstraction of tacit skill transfer.
- **Project finance warnings are unusually good.** Starting a large project shows the single-project bill, total outstanding commitments across all work, expected credit draw, formal credit ceiling, and a plain-language warning that individually affordable commitments can still be collectively ruinous.
- **Build staffing vs operating staffing is now much clearer.** Large ventures such as crop rotation warn at start time when I can build them but could not currently open them. This is the right time to surface that information.
- **Local power as resilience is a good systems link.** The war-risk screen explicitly points toward power/land/roads that do not depend on vulnerable trade. That made the overshot wheel and post mill feel like strategic infrastructure rather than generic income buttons.
- **`recap` is useful.** The 1335 recap summarized 1330–1335 changes, completed technologies, newly heard-of branches, and notable events without exposing the hidden goal path.
- **Founder-idle warnings are useful rather than nagging.** The state screen repeatedly explains when projects are calendar/money constrained and founder-hours could be spent elsewhere.

### UX / information issues
- Correction to my earlier notes: the time-advance command is **`step`**, not `advance`. I misremembered it and the game immediately returned "no command called 'advance'. Type 'help' for the list." This is my tester error, not a game bug; the recovery message was good.
- Topic search is sometimes unintuitive. Queries such as `available physics`, `available science`, `available education`, `available health`, or `available furnace` can return nothing even while conceptually related blocked items exist elsewhere. Because the tree is huge, players need reliable natural topic discovery rather than having to guess the internal subject/category vocabulary.
- Fog can sometimes degrade from uncertainty into **adjacent-branch fishing**. Example: `case_hardening` remains blocked by one completely unheard prerequisite. I tried reasonable player-facing searches around metallurgy/steel/furnace/charcoal and still had no actionable clue. Hidden routes are good; completely unreasoned hidden prerequisites may become frustrating if there is no thematic hint.
- Public-health attribution is still weak. I completed vector control, sanitation-related work, and famine preparation, but the risk screen still reports 40% Black Death staff loss without a clear contribution breakdown. I want to know whether vector control helped 0%, 2%, or 20%, especially before spending six figures on another mitigation.
- The **resilience score remains opaque**: it is ~0.994 normalized while Black Death staff loss is still 40% per wave, 28 technologies are unhedged, and the household is heavily leveraged. Whatever that score measures, the UI needs to define it.
- `available` is powerful but the visible action set is enormous: by 1332 there were **231 startable things**. Sorting/filtering saves the interface, but category reliability is therefore critical.

### Economic observations
- The economy is now meaningfully hard. At 1335 I have roughly **-30k capital**, only ~+1.3k/year recurring before project spending, and ~56.7k still owed on crop rotation plus ~2.1k on infinite series.
- Debt did not become dangerous because of one huge purchase alone; it emerged from the interaction of a large long-duration project, specialist wages, several overlapping calendar projects, and ~19% arrears interest. That feels much better than a simple "loan penalty" mechanic.
- A scholar's departure made the ledger temporarily look spectacular because it removed a huge wage bill. This is a very good example of why financial health and technological capacity should not be the same metric.
- The post mill finishing exactly as the balance sheet becomes ugly creates a nice strategic recovery opportunity. It currently quotes 66,430/year revenue and 2,554/year upkeep if opened, but I have learned not to trust headline revenue until ramp-up and market saturation are visible.

### Complexity / realism after 35 years
- The game is modeling more layers than I expected: theory vs instruments, professions that must be created, national labor-market scarcity, venture supervision shares, demand saturation, population/wage recovery after famine, hazards, project absorption rates, credit ceilings, interest, institutional knowledge risk, and long diffusion calendars for notation/mathematics.
- The simulation still feels strongest at **structural realism**, not literal historical detail. It is increasingly convincing that I cannot simply "remember modern science" into existence because the limiting factors are trained people, measurement, institutions, and operating capacity.
- The main missing realism layer I now want is **knowledge preservation/diffusion**. Thirty-five years in, all 28 things I personally built are still hedged by nothing, yet the school/corpus ladder remains very distant. Intermediate mechanisms (scriptoria, apprentices, distributed copies, guild teaching, cathedral schools, university chairs, patron-funded translations) would make this less binary.

### New mod / feature ideas
- Add a **topic thesaurus** for `available`: searching "physics" should surface mechanics/wave/energy-related heard-of items even if their internal subject tag differs.
- Add **thematic hints for unknown fog prerequisites** without naming them outright, e.g. "you are missing a heat-treatment control idea" or "this depends on a better way to judge temperature." That preserves fog while reducing random branch fishing.
- Add a **mitigation contribution breakdown** to `risk`: "silo -1.0 pp, vector control -X pp, sanitation -Y pp," or at least rough qualitative contributions.
- Add more **intermediate knowledge hedges** below a full school/corpus: duplicate notebooks, deposit copies with monasteries/universities, train named apprentices, pay scribes to copy one field, etc.
- Consider a **debt-service forecast** that separates "formal credit ceiling" from "sustainable debt at current recurring surplus." The current warnings are good, but the 216k ceiling can look reassuring even when 19% interest makes a much smaller debt economically dangerous.
- Add an optional **decision journal** generated from player actions and yearly recap; by 1335 the campaign already has enough moving parts that remembering why I started a five-year project is nontrivial.

## 1335–1350 retrospective / new observations

### Tech-tree discovery under fog
- Following the user's suggestion, I switched from interrogating blocked nodes to **browsing wider visible-name sets and reasoning from names**. This feels much better. For case hardening I looked for heat/carbon/furnace/temperature/steel/precision concepts; nothing obvious emerged, so I left the branch alone rather than trying to reverse-engineer the prerequisite.
- Name-based reasoning successfully produced a plausible public-health branch: mortality table → case series → medical statistics. It did **not** fully unlock epidemiology, which is good evidence that domain reasoning helps without making fog trivial.
- Boolean algebra naturally exposed binary arithmetic and felt like a sensible transistor-adjacent detour even without route visibility.
- Suggestion: `available` could offer optional “related names” or a broader synonym search without exposing prerequisite chains. That would preserve fog while rewarding conceptual reasoning.

### `allocate` discoverability
- Starting the written corpus caused it to monopolize all 2,000 founder-hours/year, starving several tiny active projects. `portfolio` made the problem clear, but neither `state` nor the starvation message directly suggested the existing `allocate` command.
- Once discovered, `allocate` works well and makes multi-project management much better.
- UX suggestion: when an active project gets 0 founder-hours because another project is consuming the pool, print a one-line hint such as: “Use `allocate <project> <hours>` to reserve founder time.”
- Minor annoyance: fixed allocations can become stale and produce repeated “DIRECTED HOURS UNUSED” warnings after the target project's annual pace drops. An optional auto-release of unused directed hours, or a clearer reminder to clear completed/overallocated standing orders, would reduce noise.

### War and resilience
- Hundred Years War started in 1337 and the simulation explicitly credited **power that does not come by ship**, later **self-feeding agriculture** and **own roads**, with softening the output shock. This is one of the clearest examples of systems interacting usefully.
- Risk wording like “output factor: you take 58% of it” is ambiguous. It is not immediately obvious whether 58% means I retain 58% of output, suffer 58% of the penalty, or something else. The 1337 event text (“trade and output fall to 88% of normal”) is much clearer.

### Sanitation / plague modeling
- Roman sewer + aqueduct did **not** by themselves count as clean water. The hazard screen subsequently exposed **sand filtration**; only after opening filtration did Black Death household-loss projection improve from ~34% to **29%** and explicitly credit filtered water.
- This is excellent structural modeling: conveyance, waste removal, and purification are separate layers.
- The 1349 Black Death wave reduced household staff by 17% and national population by 24%, while the event said country-wide public-health diffusion softened a would-be 45% population loss by 45%. This is a strong payoff for preparation.
- However, causal attribution remains incomplete: the event says “fields that do not fail together” and “fodder that keeps through a bad winter” had **lapsed**, without making it obvious what caused the lapse or whether an operating concern shut, timed out, or lost sufficient supervision.
- New feature request: a hazard-impact breakdown showing each active mitigation and its exact current status, including why any protection has lapsed.

### Written corpus consistency issue
- On completion in 1349, the game explicitly said **corpus_written is CLOSED / NOT OPERATING and not in effect until open**.
- At the untouched 1350 checkpoint, before opening it, both `state` and `risk` already report the corpus as an active knowledge hedge, reducing sack-loss chance from 80% to 45% and fraction lost from 40% to 22%.
- This is either a bug or a wording/model distinction that is currently impossible for the player to understand. If merely existing copies provide knowledge protection while “opening” only provides standing/literacy effects, the completion message should say so explicitly.

### Economy after 50 years
- The economy has become **easy in cash terms**. From -30k capital in 1335, diversified agriculture/power/medicine produced ~916k capital and ~169k/year recurring by 1350 despite fire, wartime disruption, and plague.
- Market saturation still prevents trivial duplication of one venture, but diversified high-return concerns compound very strongly.
- I do not yet think this is necessarily a balance bug because the real bottlenecks have shifted to scholars, scribes, household places, professions, founder-hours and institutions. Still, the capital curve is steep enough that late-game money may cease to be strategically meaningful unless institutional/industrial projects scale into the millions.

### Labor and human-capital modeling
- Training an engineer from nothing worked very well. At 1350 England's estimated total engineer population is only ~1.2 and I employ 0.82 FTE after plague; same for the machinist. That makes created professions feel genuinely scarce.
- Plague attrition converts workers into continuous FTEs rather than deleting whole named people, which is mechanically smooth but emotionally abstract. A named-staff optional mode could make catastrophic years more memorable without changing the underlying math.
- The population screen still exposes implementation-oriented text: “see labour.py's TRADE_DENSITY for what is cited and what is a placeholder.” This should not appear in a normal player-facing interface and violates the otherwise strong nontechnical UX.

### Score clarity
- At 1350 resilience is ~0.998 normalized even though an active Black Death still threatens 29% staff loss per wave and one epidemic check remains. This score remains too opaque to interpret.
- Institutions remain exactly 0 despite a finished written corpus, operating sanitation network, trained engineer/machinist, and several maintained standards/capabilities. If the score intentionally recognizes only specific formal institutions, the score screen should explain what counts.

### Fun / current campaign feel
- Still fun. The 1335–1350 period produced a strong arc: rescue from debt → war-resilient diversification → human-capital bottlenecks → deliberate public-health buildout → Black Death actually landing → corpus finally finishing.
- The campaign now feels less like “invent technology” and more like **construct enough social/industrial capacity that remembered technology can survive history**. That is the game's strongest identity.

## 1350 systems retrospective — markets, commands, impact, realism
- **Market/industry prediction:** I can now recognize ex post that ventures share demand pools (e.g. horizontal loom + rope walk saturating textiles), but I do not currently have a reliable pre-purchase view of the exact market bucket, remaining demand, or expected cannibalization. I can infer likely collision from names, but not quantify it before opening. This should be surfaced on `why`/`open` whenever an existing concern shares the same market.
- **Parallel research:** Multiple projects can absolutely run at once. They compete separately for founder-hours, calendar time, money, specialist labor, and broader absorption capacity such as scribes. Priority order can starve small projects; `allocate` can reserve founder-hours and is essential once the portfolio gets large.
- **Help system correction:** I previously judged the practical command vocabulary mainly from the dozen-ish commands I use repeatedly. `help commands` exposes a much broader advanced command surface, and detailed `help <command>` pages appear to be the intended way to learn tools such as allocation and other management actions. This is good capability but the game should surface `help commands` more aggressively when advanced situations arise.
- **Goal status at 1350:** transistor is still distant (19 confirmed route nodes; 45 personally built total). Public-health/resilience goal is going well: preparation materially reduced Black Death household/national losses. Literacy goal is going poorly (~6%, still nowhere near 20%). Knowledge preservation has improved with the completed written corpus, but institutional score remains 0 and the closed/open hedge behavior is unclear. Electrical generation, interchangeable manufacturing, synthetic fertilizer and 75% literacy are not yet achieved.
- **Difficulty source:** most difficulty now feels like the logical consequence of the premise—scarce literate labor, professions that must be created, founder attention, long diffusion times, shocks, market saturation—rather than arbitrary stat inflation. Economic balance was meaningful early but money has become easy by 1350 due diversified compounding ventures.
- **Economic scale concern:** by 1350 capital is ~916k pence with ~169k/year recurring income. Costs below ~100k are no longer strategically scary. Large institutional projects and scarce human capital remain meaningful. Late-game economic challenge will depend on costs scaling far above current levels or on non-monetary bottlenecks continuing to dominate.
- **Civilizational impact:** the player is no longer functioning like one private scholar. The household operates medicine, textile, power, agricultural and infrastructure concerns; has created rare professions; affects labor demand; and has public-health technology diffusing broadly enough that national plague mortality is reportedly reduced. Mechanically this feels closer to a proto-conglomerate/research institute/patronage network than an individual artisan.
- **Degrees of impact:** confirmed systems include labor scarcity/wage changes, population shocks affecting wages, venture demand saturation, business supervision allocation, technology/public-health diffusion, national mortality mitigation, trade/war output penalties, local infrastructure resilience, and profession creation. I have NOT yet confirmed whether very large farm expansion lowers national food prices, whether hiring most of one trade meaningfully harms third parties beyond raising wages/availability, or whether labor-saving machinery visibly reduces national occupational shares such as farmers.
- **Financial legibility:** `ledger` makes recurring revenue, wages/upkeep, market saturation and shocks reasonably understandable, but exact one-year cash is not deterministic because venture ramp, market demand, failures, supply shocks, hazards, interest and project spending can change it. I can forecast direction and rough magnitude, not an exact penny total. By 1350 I can ignore many small costs, but not labor/institutional constraints.
- **Knowledge realism:** the game usually gives startup cost, founder-hours, calendar time, failure chance and staffing needs with considerable precision, but revenue is a range/quote rather than guaranteed realized income, and realized demand can be reduced by ramp-up and saturation. This is better than pretending perfect foresight, though some displayed numerical precision can still look more certain than a medieval innovator plausibly could know.

### Additional 1350 retrospective — scale of the founder and unresolved economy questions
- By 1350 the founder no longer feels like a lone inventor. Mechanically the household resembles a **proto-conglomerate + research institute + medical practice + infrastructure operator + patronage network**. The game systems imply this transition more strongly than the presentation acknowledges; an explicit household/institution growth identity could make that arc clearer.
- In a real historical analogue, a person whose enterprises, sanitation work, mathematical/scientific methods, rare-profession training, and public-health diffusion measurably reduced Black Death mortality would almost certainly become nationally and internationally famous and politically important. The current game has not yet made crown/church/guild/foreign-interest reactions proportional to that apparent impact.
- Strong mod/system idea: once the founder becomes economically or technologically exceptional, add **political attention**—patronage offers, taxation, monopolies/patents, guild hostility, attempts to poach staff, espionage, foreign invitations, church scrutiny, and demands from the crown.
- Confirmed player impact so far includes market saturation, scarce-trade wage pressure, profession creation, national hazard mitigation, wartime resilience from local infrastructure, and population shocks feeding back into wages. Still UNCONFIRMED: whether expanding farms lowers food prices nationally; whether hiring nearly all reachable members of a trade harms unrelated NPC production beyond wage/availability changes; whether mechanization changes occupational shares; whether large supply increases shift downstream prices; and whether the player can deliberately bend long-run population growth enough to double national population.
- By 1350 finances are legible enough for rough forecasting but not deterministic. `ledger` explains recurring revenue/costs and major saturation effects, while failures, attrition, hazards, project absorption, ramp-up and market realization prevent exact one-year cash prediction. This is preferable to perfect foresight.
- The economic system currently feels broad rather than literally macroeconomic: strong household/market/labour interactions are demonstrated, while national commodity-price and occupation restructuring still need to be tested later.
- **BUG at 1350 — documented `buy school` syntax misparses:** `help buy` explicitly says `buy school <trade> <n>` and gives `buy school smith 2` as the model, but `buy school scholar 2` was refused with a completely unrelated material/mining error (“material must be one of coal, copper…”). Either scholar schools are intentionally unsupported and the error is wrong, or the command dispatcher is routing this syntax to material purchasing. This is exactly the sort of advanced-command discoverability failure that makes a player think a documented feature is broken.
- **Confirmed broader `buy school` bug:** `buy school scribe 2` produces the same unrelated materials/mining error as `buy school scholar 2`. This is not a scholar-specific restriction; the documented trade-school purchase syntax appears broken/misrouted in this interface.

## Retrospective / tester notes after 75 years (1375 checkpoint)

### Command/help discoverability
`help commands` materially changed my understanding of the UI. The beginner loop can stay small, but there is a much larger advanced command layer (`materials`, `capacity`, `portfolio`, `bounty`, `buy`, `sell`, `allocate`, `commission`, `rush`, `mothball`, etc.) and per-command help such as `help buy`. This is good layering. The weakness is discoverability: when a portfolio is starving for founder-hours, materials, housing, or a specialist trade, the relevant normal output should point directly to the advanced command that solves or diagnoses it.

CONFIRMED BUG: `help buy` documents `buy school <trade> <n>`, but both `buy school scholar 2` and `buy school scribe 2` were parsed as material/mine purchases and rejected with the mineable-material list. `buy housing` and `buy forest` worked normally, so this looks specific to the school subcommand/parser rather than the whole buy command.

### Institutions and human capital
The university/collegium chain substantially improves the model. Opening the university increased the reachable scholar ceiling (roughly from the low-2s to about 3 in the local market), demonstrating that institutions alter real capacity rather than merely award score. By 1375 the institution score is 6 rather than 0. General literacy, however, is still ~6%, so elite institutions have not magically created mass literacy. That distinction is good.

Hiring two scribes earlier raised usable scribe capacity from roughly 1,260 to ~5,260 hours/year. The game therefore models project throughput as a function of actual reachable specialists. There remains an enormous gap between elite scholarly capacity and mass education, which is historically plausible and strategically important.

### Politics/social legitimacy
Newtonian mechanics exposed a political rather than technical barrier: even after assembling enough scholarly capacity, I needed patronage before I could safely begin a socially threatening theory. This was one of the most satisfying constraints in the run because it followed from the historical premise rather than feeling like arbitrary tech gating. The game should lean further into this kind of reaction as the founder becomes richer and more disruptive.

### Materials / industrial supply chains
Cementation steel and later clear glass were throttled by charcoal. The game explicitly connected the shortfall to sustainable coppice acreage and let me quote/buy forest. I eventually accumulated five hectares and still encountered charcoal throttling while building clear glass/labware. This is excellent: buying a technology does not summon its industrial feedstocks.

The visible chain from controlled heat/precision -> cementation steel -> analytical balance -> clear specification glass -> specialist glassblowers -> laboratory glassware -> working laboratory feels much more convincing than a flat chemistry-tech ladder.

Minor feedback: the annual message repeatedly says “about 1 more hectare” even after buying additional hectares in successive years. It may be correct because demand keeps changing, but showing `supply X / demand Y tonnes` would make the causal picture much clearer and prevent it looking like a stuck recommendation.

### Labor-market impact / macro impact
The 1375 population screen finally answers an earlier open question about degrees of labor-market impact. The game estimates both country totals and the much tighter specialist pool within this household's reachable town market. I currently employ roughly 66-69% of the reachable chemists, engineers, machinists, glassblowers, and opticians. This makes wage pressure and specialist scarcity concrete. My organization is effectively dominating several new professions locally.

This is much better than an infinite hiring pool. It also supports an important interpretation of the campaign: I am no longer simply an individual inventor. Mechanically I still have personal founder-hours, but economically I am a proto-conglomerate / research institute / university / infrastructure operator whose hiring can reshape tiny specialist labor markets.

Still to test: whether large-scale technology changes economy-wide occupational structure (e.g. mechanized agriculture reducing farmer share), commodity prices, urbanization, or downstream NPC industries rather than just my reachable labor market and concern revenues.

### Economy at 1375
Capital ~3.453m pence; recurring net ~+708.6k/year. Money is now easy for small/medium projects, but it is not universal purchasing power: lead metallurgy alone is quoted around 7.01m and cannot currently be financed even with credit. Thus late projects can still outrun the snowball.

The ledger is unusually legible. It itemizes concern revenue, upkeep, wages, living/appearance costs, project spending, credit, interest, and market saturation. It also explicitly says the market will not absorb ~857k/year of nominal output across concerns. Only the rope walk is currently called out as a directly saturated category concern (~73% of tree quote), while a much larger aggregate `what the market will not absorb` deduction exists across the whole ledger. I would still like a pre-opening demand/market preview by category so collisions can be anticipated instead of mostly diagnosed afterward.

The organization now pays a `rich` lifestyle increment (~51.8k/year) within living/appearances. Nice touch: wealth itself creates recurring social cost.

### Knowledge realism
Strong. Knowing ideas is repeatedly separated from operational capability. Atomic theory needed measurement; chemistry needed an analytical balance; analytical chemistry now needs controlled clear glass, specialist glassblowers, labware, and a functioning laboratory. Founder knowledge gets me the concept, not an industrial ecosystem.

The game also models diffusion/calendar floors independently of founder effort: at 1375 I can have 2,000 idle founder-hours and millions in cash while polynomial mathematics or lab equipment simply needs time to spread/complete. This prevents late-game wealth from collapsing everything into instant clicks.

### Public health goal
Public-health progress is substantial but incomplete. The campaign has built filtered water, sewerage/sewage separation, chlorination, activated sludge, vector control, vital registration, case records, mortality/statistical methods, cohort and case-control studies, notifiable-disease reporting, and contact tracing. The Black Death hit materially less hard than the early risk estimate, and the game explicitly credited country-level public-health diffusion.

Epidemiology statistics is still one unseen concept away. Reasoning from the names led me toward probability; visible probability prerequisites then led to polynomial -> binomial -> combinatorics -> probability axioms. I began polynomial equations in 1371 and they completed in 1374. This is an excellent fog experience: domain reasoning produces a plausible route without showing the hidden graph.

### Goal progress at 1375
- Main transistor: 82 personally built technologies; 37 confirmed on-road. Still nowhere near a speedrun, but progress accelerated from 19 on-road at 1350 to 37 at 1375.
- Epidemic mortality/resilience: major success. Resilience normalized score ~0.997; public-health goal itself has not yet triggered.
- Literacy >20%: still failing badly at ~6%.
- Durable institutions: meaningful progress; institution score now 6, university/collegium/corpus/workshop operating.
- Knowledge preservation: written corpus operating and used as hedge.
- Electrical generation: not reached. Electromagnetic theory is known, but practical electricity is still blocked chiefly by metallurgy/apparatus; lead metallurgy is visible but ~7m.
- Interchangeable manufacture: not reached.
- Synthetic fertilizer: not reached.
- Economic resilience: overwhelmingly successful; now arguably the easiest part of the campaign.

### UI / realism rough edges still active
- `population` still leaks implementation detail by telling the player to inspect `labour.py` / `TRADE_DENSITY`; this belongs in developer documentation, not player UI.
- `buy school` documented syntax appears broken.
- Pre-opening market-category collision information remains too weak.
- Advanced command discoverability could be better contextualized.
- Corpus closed/open hedge semantics remain ambiguous from the earlier checkpoint.
- The game increasingly implies that I should attract intense political/geopolitical attention, but the social reaction still feels small relative to an organization dominating newborn professions, running a university, and visibly changing mortality/industry.

### Overall after 75 years
The economic snowball is much faster than the human/material/institutional snowball. That currently feels more like a consequence of introducing high-productivity techniques into a low-productivity society than pure balance failure, because money still cannot directly buy calendar time, professions that do not exist, laboratory ecosystems, mass literacy, political legitimacy, or unlimited raw-material throughput. The key question for later play is whether the game continues scaling industrial costs and social constraints enough that millions of pence do not trivialize the second half.

The game remains fun. The strongest moments are still consequences produced by interacting systems: an engineer leaving stalls sanitation; a university changes scholar supply; glass production consumes more charcoal than local coppice can support; a new trade's tiny labor pool means hiring two people makes me the dominant employer; chemistry only becomes real after building the measurement-and-glass ecosystem. That is substantially more interesting than simply traversing a tech tree.
