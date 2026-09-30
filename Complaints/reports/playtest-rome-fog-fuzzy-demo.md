<!-- Verbatim blind playtest report A: Rome 100 AD, fog + fuzzy estimates, immortal, won 358 AD (plus destitute mortal run). Triage: final-playtests-triage.md -->

# Bootstrap History — Blind LLM Playtest Feedback

**Tester:** GPT-5.6 Sol  
**Version:** Supplied demo (`bootstrap-history-playtest-feedback-and-fixes.zip`)  
**Overall experience:** 8/10  
**Testing method:** Blind, using the root README, in-game help, and ordinary player commands. No source-code inspection, hidden-tree inspection, external walkthroughs, or built-in solver.

## 1. Playtest summary

I completed a Roman transistor campaign, beginning in 100 AD with approximately 2,695 denarii, fog enabled, fuzzy estimates enabled, and an immortal founder.

The point-contact transistor was successfully completed in **358 AD**, following one failed attempt. The final save was made in 361 AD.

I spent approximately 1 hour and 44 minutes of elapsed time on the overall playthrough, including experimentation, conversation, mistakes, and exporting checkpoints. This isn't an exact active-gameplay stopwatch measurement.

I also began a second, destitute mortal campaign to test the early economic difficulty.

The principal victory campaign finished with:

| Metric | Result |
|---|---:|
| Personally developed technologies | 320 |
| Total known technologies | 545 |
| Operating concerns | 111 |
| Employees (FTE) | ~330 |
| Institutions | 22 |
| Treasury | ~451.8 million denarii |
| Annual recurring surplus | ~13.3 million denarii |
| Population literacy | Approximately 75% |
| Achievements | 3/5 |

The supplied catalogue reported 2,883 technologies and 5,310 dependency links. Consequently, I interacted with only part of the available technology system and cannot claim to have audited the entire tree.

**General verdict:** This is considerably more interesting than a large technology tree masquerading as a game. The relationship between knowledge, production, materials, labor, institutions, capital, and historical disruptions is its strongest feature.

However, I encountered several concrete bugs or inconsistencies, substantial late-game economic snowballing, information-presentation issues, and limitations in how the simulation responds to major alterations of history.

---

## 2. Bugs and possible implementation issues

These are observations from actual gameplay or disposable test sessions, not conclusions drawn from reading the implementation.

### BUG 1 — Save browser displays incorrect checkpoint information

**Priority: High**

After creating a valid 110 AD Roman checkpoint, the main-menu load browser displayed its preview as approximately:

- Year: `None AD`
- Technologies developed: `0`

Selecting the save successfully restored the correct 110 AD campaign, including the ten technologies I'd developed.

The underlying save appeared intact; the preview metadata was incorrect.

**Suggestion:** Check how the load browser extracts year and progression fields from the save schema. Ideally, display the year, civilization, founder status, selected objective, save date and current completion state.

Also, provide a clear warning for incompatible or malformed saves rather than displaying misleading zero values.

### BUG 2 — Weight-driven mechanical clock is instant and free

**Priority: Medium; verify whether intentional.**

In a disposable campaign, the weight-driven mechanical clock appeared available with:

- Zero research cost.
- Zero founder-hours.
- Zero calendar duration.
- Zero failure risk.

I successfully started and completed it without advancing time.

This may be an incorrect technology-data entry rather than an engine bug. If it's intentionally granted as a free historical technology, I would suggest representing that explicitly rather than presenting it as a normal project.

### BUG 3 — Rome is still described as being under Trajan in 361 AD

**Priority: Low, but immersion-breaking.**

The population screen continued displaying the civilization as *The Roman Empire under Trajan* in our 361 AD checkpoint.

Obviously, the initial historical setting was no longer current.

If the simulation isn't tracking subsequent emperors dynamically, I'd recommend separating the starting-scenario description from the current civilization label.

Simply calling it the Roman Empire after the start date would be preferable.

### INCONSISTENCY 4 — Different default transistor goals

The normal new-game menu appeared to default to the grown/alloy junction transistor objective, whereas starting through the direct `play` interface defaulted to the point-contact transistor.

Both are legitimate objectives, but different starting interfaces shouldn't silently select different goals unless clearly documented.

### UI ISSUE 5 — Rounded milestone scores can be misleading

Our `score` screen displayed literacy as approximately `0.75`, while the corresponding literacy victory milestone remained `BLOCKED`.

This may simply be ordinary rounding rather than a logic error.

However, when a milestone has an exact numerical threshold, the relevant progress screen should expose enough precision to explain why it hasn't triggered.

For example, `74.96% / 75.00% required` would avoid confusion.

### ADDITIONAL VALIDATION NOTE

The supplied demo passed its technology-data validation during my initial testing, although the validator returned one nonfatal material-pricing warning.

I didn't investigate the underlying data, but it may be worth checking separately.

---

## 3. Economy: convincing early game, excessive late-game wealth

This is probably my largest balance criticism.

The early economy was engaging. Starting with a little money, I had to establish businesses, hire specialists, borrow money, cover recurring expenses, and survive while revenue increased.

It was quite possible to make a bad decision and become financially trapped.

My subsequent destitute mortal campaign demonstrated this particularly well: my loom lost its sole carpenter, production stopped, and I couldn't finance replacement wages under the same credit conditions available for construction.

That interaction was excellent.

However, the normal campaign eventually snowballed to an extraordinary degree.

By 361 AD, I had approximately 451.8 million denarii, annual revenue of roughly 25.5 million, and an annual surplus of 13.3 million.

The game was already rejecting approximately 20.7 million denarii of additional potential annual sales because of market saturation, so this was not occurring in a completely unconstrained market.

The simulation also modeled high-wealth expenses, wages, confiscation, debt, and operating costs. These are good safeguards.

Nevertheless, generating that much revenue from approximately 111 concerns and 330 employee-equivalents made the late-game economy feel disproportionately profitable.

By the final century, I rarely cared about the ordinary price of another invention.

**My suggestion is not simply to make everything more expensive.**

I would rather see the economy's existing systems become more interconnected at industrial scale:

- Industrial supply chains that require ongoing logistical and labor capacity.
- Stronger relationships between the wider population's purchasing power and commercial demand.
- More substantial workforce requirements for large-scale production.
- Independent competitors adopting technologies and affecting market prices.
- Industrial growth generating new economic opportunities while undermining older businesses.
- Increased institutional and infrastructural requirements for operating enormous industrial enterprises.

I particularly like the existing market-saturation mechanic and would prefer expanding it rather than replacing it with arbitrary cost multipliers.

### Exploit testing

I tested two simple potential economic abuses.

Buying half a tonne of iron for approximately 3,369 denarii and immediately reselling it returned approximately 2,695 denarii. No obvious duplication or infinite-money exploit occurred.

Similarly, selling an entire year's founder labor correctly exhausted the available annual hours. Attempting to sell the same hours again was rejected.

The intentionally `absurd` starting-wealth option also works, although that is clearly an intended sandbox setting rather than an exploit.

I didn't discover an infinite-money exploit during these tests. The late-game wealth problem appeared to arise from ordinary economic scaling, not an easily repeatable transaction bug.

---

## 4. Industrial diffusion and calendar gates

**Please do not simply remove the time gates.**

Initially, I found some of them frustrating, particularly the industrial power grid.

At one point, the grid was absorbing investment at only a fraction of the rate I expected. Despite possessing an enormous treasury, I still had many years of effective construction remaining.

However, looking back, I think the time gates are an important part of the design.

I made the mistake of occasionally advancing the calendar while waiting for an important technology instead of diversifying into other research.

A better player would use that period to develop theoretical science, establish schools, expand mining, improve public health, strengthen institutions, and prepare future manufacturing prerequisites.

The actual problem is that **the interface could better distinguish different kinds of delay**.

I would appreciate seeing four separate pieces of information for an ongoing project:

| Information | Purpose |
|---|---|
| Remaining founder-hours | Work I can directly or indirectly provide |
| Remaining investment | Actual financial expenditure required |
| Current industrial absorption | How quickly the economy can utilize that investment |
| Earliest effective completion | Forecast including material, industrial and calendar restrictions |

For example, if a project has a three-year minimum duration but insufficient industrial capacity will make it take twenty years, I'd like the portfolio to explain that clearly.

An optional warning when advancing multiple years with large quantities of unused founder-hours would also be welcome.

Something along the lines of: *You have 12,000 unused hours and 18 currently startable projects. Continue advancing?*

This should probably be optional for experienced players and automated agents.

---

## 5. Material shortages are excellent, but their presentation could improve

Some of my favourite gameplay moments involved discovering that possessing knowledge wasn't sufficient to execute an invention.

Examples from my campaign:

**Sulfuric acid:** Production barely progressed because of inadequate saltpetre supply. Simply knowing how to manufacture nitre wasn't sufficient; I needed actual nitre-bed production capacity.

**Steam machinery and bulk steel:** Both projects were simultaneously throttled because accessible coal and iron supplies were inadequate. Developing private mines fixed the bottleneck.

**Bulk steel:** The technology appeared research-ready, but beginning the project exposed a missing manganese supply.

**Vacuum electronics:** I spent an embarrassingly long time without a suitable platinum supply. Extending Roman trade routes eventually exposed a viable source through eastern trade.

All of these are good examples of what makes the simulation interesting.

I would not remove these material requirements.

However, I suggest making the distinction between *technologically startable* and *physically provisioned* clearer.

A technology could display:

`KNOWLEDGE: READY`  
`SPECIALISTS: READY`  
`MATERIAL SUPPLY: INSUFFICIENT`  
`CAPITAL: READY`  
`CALENDAR: READY`

The existing capacity reports already provide genuinely useful information, including suggested scale for necessary facilities. Surfacing that information closer to the blocked project would reduce repetitive command use.

I'd also appreciate a consolidated bottleneck report covering every active project, ordered by severity.

---

## 6. The technology tree is the strongest part of the demo

The technology dependencies repeatedly rewarded actual reasoning instead of simply progressing through an arbitrary sequence of inventions.

I particularly appreciated relationships involving:

- Industrial charcoal, refractory materials and furnace-temperature capabilities.
- Precision straightness, the three-plate method and accurate machine tools.
- Crank systems, flywheels and mechanically powered machinery.
- Micrometer gauges and reproducible manufacturing tolerances.
- Chemical purity, high vacuum and electronic-component production.
- The distinction between knowing semiconductor theory and actually manufacturing a working transistor.

I also appreciated that existing civilizations inherit historically established knowledge. Rome shouldn't need to rediscover every aspect of ironworking.

However, I would distinguish between two types of downstream importance.

A technology may have very few direct descendants while remaining absolutely essential for the selected objective. Boolean algebra, for example, can be highly relevant to electronic computation despite not necessarily having an enormous raw descendant count.

The existing `why` command reports importance using descriptions such as *a few things* or *almost everything*.

That's useful, but it risks undervaluing narrow, strategically critical prerequisites.

An optional goal-aware planning view could help distinguish general technological importance from specific relevance to the chosen objective, while respecting fog.

Please retain fog as a serious gameplay option. I found it considerably more interesting to reason about currently visible technologies using general engineering knowledge than to traverse a fully exposed dependency checklist.

---

## 7. The alternate-history simulation needs more feedback from the player's actions

This is my biggest conceptual feature request.

I genuinely liked the historical-risk system.

Our public-health improvements substantially reduced the Antonine plague's population losses compared with the modeled unmitigated outcome.

Dispersing our written technical corpus also prevented completed technological knowledge from being erased during destructive historical events.

These mechanics gave institutional development real strategic value.

However, the game continues scheduling familiar historical events even after the player's civilization has diverged enormously from actual history.

For example, the 361 AD campaign still presented subsequent historical risks involving Christianisation, Gothic settlement, fifth-century instability and later imperial conflicts.

By that stage, Rome possessed steam machinery, combustion engines, electrical networks, advanced chemical industries, modern scientific institutions and semiconductor technology.

I understand that implementing fully emergent alternate history is a monumental undertaking, and perhaps outside the intended scope.

Nevertheless, I'd love the historical-event system to acknowledge more explicitly when the player has changed the underlying causes of future events.

Possible improvements:

**Conditional historical events:** Rather than always using the original event, evaluate whether the economic, demographic, military and institutional circumstances supporting it still exist.

**Alternative outcomes:** A historical crisis might become a different challenge for a technologically transformed civilization.

**Dynamic neighboring societies:** Knowledge diffusion, trade, migration and military contact could gradually allow neighbors to adopt technologies.

**Independent domestic adoption:** Technologies successfully demonstrated by the founder could spread beyond their personal businesses through existing markets and institutions.

The current simulation is convincing at showing how history affects an inventor. I'd love more emphasis on how the inventor affects history.

---

## 8. Social, political and institutional systems

I found these more interesting than I initially expected.

The game models reputation, social resistance, attitudes toward novelty, religion, labor-saving, information distribution, patronage, public institutions and government attention.

During my campaign, the Roman state became increasingly interested in my wealth. I experienced substantial losses through attacks and confiscation.

The government also adopted much of my technological work for military purposes.

These mechanics were meaningful, not purely decorative.

However, I'd like further development in three areas.

### Public adoption

How many people actually use the technologies I've introduced?

I could see my own businesses, available specialist labor and broad social indicators, but I had difficulty distinguishing a technologically advanced private organization from an independently industrialized civilization.

A public-adoption dashboard could be enormously useful.

For instance: How many cities have electrical power? How widespread are mechanized workshops? How many children attend schools? How much independent manufacturing exists outside my own holdings?

### Political reactions

The state already notices wealth and technical usefulness. It would be interesting if a major industrial transformation also altered the nature of its demands.

A Roman government might request military production, infrastructure development, communications or medical assistance.

Equally, an influential inventor could become a political liability.

I wouldn't want this to turn into an entirely separate grand-strategy game, but more consequences for becoming economically indispensable would be interesting.

### Mortality and succession

This feels like an especially promising area for the full game.

Creating a civilization that continues technological development after the founder dies is arguably a more interesting achievement than having an immortal founder personally oversee everything for 500 years.

I'd enjoy a system in which former students, employees, schools and independent businesses could preserve or continue parts of the founder's work.

The ideal outcome would be building a society that eventually no longer needs the time traveler.

---

## 9. Workforce management deserves greater visibility

My original campaign finished with only three of the five available achievements.

One missed achievement concerned having a business close due to inadequate staffing.

The game already provides useful `keep` and `reserve` commands, but I didn't use them consistently enough.

In my mortal destitute campaign, the departure of a single carpenter immediately closed my primary business and triggered an economic problem.

That consequence was fair, but it demonstrated the importance of staffing redundancy.

I'd appreciate a consolidated workforce screen showing:

- Critical single-employee dependencies.
- Businesses at immediate risk of closure.
- Current reserve specialists.
- Expected annual attrition.
- Training pipelines and anticipated future vacancies.

The game could also issue a more prominent warning before advancing several years with a critical business dependent on one irreplaceable specialist.

I especially liked the academy and delegation systems. Expanding delegated founder-hours substantially changed what I could accomplish in parallel and made institution-building worthwhile.

That should remain an important strategic tool.

---

## 10. Interface and LLM-specific improvements

The existing command-line interface is generally usable.

I counted approximately 49 top-level commands, excluding aliases and additional arguments.

The `help`, `why`, `available`, `portfolio`, `stuck` and other inspection commands were essential. I appreciated being able to interact through ordinary persistent save sessions instead of needing to write a custom Python agent.

The JSON-oriented interface is also useful, but I generally found ordinary interactive play more engaging.

I have three major suggestions here.

### A. Better interruption and warning handling

Large `step` commands and automated scripts can potentially advance past consequential warnings before the player has meaningfully responded.

I'd like an optional mode that interrupts time advancement when a significant event occurs.

Possible triggers include:

- Major historical risk warnings.
- A critical business closing.
- An important employee category becoming unavailable.
- A project becoming materially blocked.
- A severe project failure.
- A newly completed project unlocking a major objective.
- Reaching the selected victory condition.

This would be useful for both humans and AI agents.

The game could return a structured event explaining why advancement stopped, allowing the player to respond before continuing.

### B. An integrated industrial portfolio

By the late game, a great deal of time is spent moving between finance, research, material supply, employee capacity and the historical log.

I'd love one optional dashboard presenting the most important information together.

This is particularly relevant because `available all` eventually exposed nearly a thousand startable technologies in our campaign.

Filtering exists, which helps enormously, but the volume of information can still become difficult to navigate.

### C. Better save portability

By the conclusion of my campaign, the save file was approximately 917 KB.

That wasn't a problem for the simulator, but it created practical difficulties in an externally hosted LLM environment where temporary container storage may disappear.

Suggestions:

- Clear manual export/import instructions.
- Automatic rotating checkpoint backups.
- Reliable save-browser metadata.
- Save-version compatibility information.
- Optionally compressed saves.
- A brief human-readable save summary stored alongside the complete machine-readable state.

I would not recommend asking LLMs to reconstruct saves from text; there is too much detailed information that can be subtly corrupted.

---

## 11. Victory conditions, score and replayability

I really like having multiple victory objectives rather than making every playthrough a transistor race.

The main campaign took me 258 elapsed calendar years, while the default limit was 500 years.

That feels like a reasonable sandbox duration. A less experienced player has room to recover from mistakes, while someone seeking a challenge can choose a shorter deadline or enable mortality.

However, I'd love to see further support for post-victory and self-imposed goals.

Examples:

**Societal transformation:** Achieve a target level of literacy, public health, workforce development, independent industry and institutional resilience.

**One-lifetime challenge:** Reach an industrial milestone before a mortal founder dies.

**Knowledge survival:** Build institutions capable of preserving modern knowledge through several consecutive historical crises.

**Industrial independence:** Reach a point at which the wider civilization can reproduce essential technologies without the founder's personal enterprises.

**Completionist campaign:** Develop every available technology, rather than just the prerequisite chain for one objective.

The existing scoring categories are well suited to some of these challenges.

I'd also appreciate a way to display progress toward multiple goals during an Endless or post-victory campaign, even if only one goal can be selected for formal victory.

Please consider making score components easier to inspect under fog without revealing undiscovered technology names.

---

## 12. Other observations

### Fuzzy estimates are good

The scientific-method project initially appeared to cost approximately 415 denarii, but its actual expenditure was approximately 1,133.

This was frustrating in a useful way because fuzzy estimates were enabled intentionally.

I wouldn't remove that uncertainty. I'd simply appreciate a clearer presentation of how confidence changes once a project begins.

### Research failures are generally interesting

My four-stroke Otto engine took five attempts.

Other projects failed partway through development, reducing progress and increasing costs.

I liked that a failed attempt could improve the chances of subsequent attempts rather than simply functioning as a random punishment.

### Historical catastrophes need not destroy the campaign

The Third-Century Crisis caused major financial and workforce losses, but dispersed knowledge helped preserve completed technologies.

This was one of the best incentives to invest in institutions rather than exclusively developing new inventions.

### There may be a version/content-count difference worth checking

My installed catalogue reported 2,883 technologies. Another player's reported run used 2,879.

This may simply reflect a different mod configuration or demo revision. I wouldn't classify it as a bug without first comparing the environments.

---

## 13. What I would prioritize as the developer

If development time is limited, these would be my suggested priorities.

| Priority | Improvement |
|---|---|
| P1 | Fix incorrect save-browser previews and verify save reliability |
| P1 | Audit suspicious free/instant technologies |
| P1 | Make material, labor, diffusion and calendar bottlenecks clearer |
| P1 | Provide prominent optional interruptions during long time advancement |
| P2 | Expand late-game economic scaling and industrial demand |
| P2 | Improve workforce-risk and reserve-management visibility |
| P2 | Distinguish public technological adoption from founder-owned capabilities |
| P2 | Make historical events more responsive to substantial technological divergence |
| P3 | Add a consolidated project-management dashboard |
| P3 | Improve multi-objective progress tracking and post-victory support |
| P3 | Deepen social reactions, technological diffusion and institutional succession |

## Final thoughts

I enjoyed the demo considerably more than I expected.

Its strongest quality is that it doesn't simply reward knowing that a modern invention exists. It requires understanding the industrial, economic, scientific and institutional foundations necessary to manufacture that invention.

Some of my most memorable moments involved discovering that I had the correct technology but lacked something seemingly mundane: an adequate nitre bed, a precise machining process, sufficient coal production, a specialist foreman, or geographical access to platinum.

That's where the game feels genuinely distinctive.

I also appreciate that the game rewards preparing for historical disasters through public health, written knowledge, institutions and economic resilience.

My major criticisms concern the presentation of complex bottlenecks, late-game economic scaling, and the limited degree to which major technological changes alter subsequent historical events.

I would not recommend simplifying the technology dependencies merely to make the game friendlier. Those dependencies are the reason it's interesting.

If anything, I'd prefer the full game to build more systems around the existing industrial model, making the ultimate objective less about personally inventing a specific object and more about establishing a society capable of sustaining its own technological development.

**The most compelling part of the premise isn't inventing a transistor in ancient Rome. It's discovering just how much of civilization has to change before ancient Rome can manufacture one.**