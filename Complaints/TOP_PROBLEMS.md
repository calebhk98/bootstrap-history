# TOP PROBLEMS — Blind Later Han playthrough

## Run context

- Blind first full playthrough; no source code, data files, docs, or prior-session notes were used.
- Civilization: Later Han China, not Rome.
- Fog of war: on.
- Immortal founder: on.
- Starting income: merchant / middle-ish option.
- Result: **WIN — grown and alloy junction transistors completed in 575 AD**, 25 years before the 600 AD horizon.
- Final road: **168 / 168** required nodes complete.

This list is ordered by **damage to a player trying seriously to win**, not by how easy the issue is to fix.

## 1. Point-contact transistor requires single-crystal material even though its own text says it historically did not

**Damage: Critical.** This forced an entire post-1947 manufacturing programme into the mandatory path and nearly cost the run through repeated long-calendar failures.

The point-contact page says:

> "POLYCRYSTALLINE germanium ... with no pulled crystal and no zone refining, neither of which existed yet."

But the game still refused to start it until I had a semiconductor supplied by `single_crystal` or `silicon_path`.

The `single_crystal` page then says:

> "Teal and Little pulled the first germanium crystals in 1948, the year AFTER the point-contact device was demonstrated on ordinary polycrystalline material."

So the player-facing historical explanation explicitly contradicts the prerequisite graph.

**Why it matters:** To satisfy this contradictory gate I had to build X-ray diffraction, interferometric metrology, gauge blocks, semiconductor metrology, a 12-year arc furnace, zone refining, controlled-atmosphere equipment and a crystal puller. The arc furnace failed twice, zone refining failed twice, and single-crystal growth failed twice. This was the largest avoidable threat to finishing by 600.

**Recommendation:** Let `point_contact_transistor` accept the already-purified polycrystalline germanium route. Keep `single_crystal` mandatory for the grown/alloy junction transistor and later manufacturable devices, which matches both the text and history.

## 2. Long calendar floors combined with high unmitigable failure rates can dominate the game more than strategy

**Damage: Critical/High.** Several mandatory projects can erase 5–12 years per failed roll even when the player has solved every economic, staffing, material and scientific problem.

Examples from this run:

- High-pressure steam: **12-year floor, 40% failure**, failed twice before succeeding.
- Arc furnace: **12-year floor, 35% failure**, failed twice before succeeding.
- Zone refining: **6-year floor, 45% failure**, failed twice.
- Single-crystal growth: **5-year floor, 45% failure**, failed twice.
- Vacuum tube: 8-year floor, 40% failure; luckily succeeded first try.
- Power grid: 25-year floor, 35% failure; luckily succeeded first try.

Late in the run, money became almost irrelevant while these rolls controlled the outcome. There was often nothing left for me to improve before retrying.

**Recommendation:** Keep uncertainty, but give players some way to trade resources/preparation for lower failure risk: pilot plants, extra prototype work, redundant teams, quality-control spending, or a visible "spend more to reduce risk" option. Even a partial reduction would turn calendar failure back into strategy rather than lottery.

## 3. Platinum supply is extremely hard to discover and the economy UI gives misleading signals

**Damage: High.** This blocked vacuum tubes, which blocked the transistor, for decades.

What I tried as a knowledgeable blind player:

- completed platinum-group metallurgy;
- commissioned a platinum mine;
- commissioned a mine using the exact material key `platinum_g`;
- built fire assay, ore dressing, chemical leaching and electro-refining;
- searched for platinum sponge, aqua regia, chloroplatinate, Wollaston, palladium and related terms.

The game still said I had **no platinum supply**.

The actual hidden route appeared only after **"Extend the existing eastern trade routes"**, exposing `mat_platinum_bulk`. The platinum page then said the Urals were reachable through those routes.

Worse, the page told me:

> "See data/world/geography.json for where it is and what reaching it costs."

That directs the player outside the game into a data file. I deliberately did not follow it.

**Recommendation:** When a known project says it needs "a platinum supply," give an in-game breadcrumb such as "known deposits are far to the northwest; better eastern caravan access may make them reachable." Mines producing `platinum_g` should either count or clearly explain why they do not.

## 4. Platinum acquisition becomes a 95% failure lottery with almost no player agency

**Damage: High.** After finally discovering the platinum node, it had 0 cash cost, 0 calendar floor, and **95% failure risk**. I failed repeatedly for years. There was no visible way to improve the odds.

This felt less like historical difficulty than a repeated dice roll. Eventually I restarted it and succeeded on the next attempt without changing any strategy.

**Recommendation:** Tie the failure chance to visible trade-route/logistics investment, money, escorts, multiple expeditions, or distance-reduction infrastructure. If the intended answer is "send enough expeditions," let the player buy several attempts in parallel rather than consuming one year per 5% roll.

## 5. Bounty commands leak fog-hidden prerequisite IDs, and one bounty message directly suggests an impossible action

**Damage: High for fog integrity; medium for run outcome.** Normal `why` correctly hides unknown prerequisites, but `bounty` sometimes names them.

Examples:

- industrial zinc leaked `power_grid`;
- getter leaked `el2_induction_heating_inductor_coupling`;
- vacuum tube leaked its hidden cathode prerequisite.

The worst UX case was platinum. The game told me:

> "mat_platinum_bulk is already active; stop it first if you want to switch to a bounty instead."

I stopped it, then `bounty mat_platinum_bulk` refused because the node was **not bounty-eligible**.

**Recommendation:** Make bounty prerequisite reporting use exactly the same fog filter as `why`. Never recommend switching to a bounty until eligibility has already been checked.

## 6. The game does not teach parallel research strongly enough, even though parallelism is essential

**Damage: High.** I was winning economically but playing the research programme too serially. A user hint materially changed the run:

- long calendar projects can remain in the background;
- free founder-hours should be spent preparing multiple next layers;
- staffing/economic capacity should be built before it becomes a formal blocker.

Once I changed approach, I built controlled atmosphere, crystal puller, mirrors, potentiometer, valve voltmeter, opticians, X-ray diffraction and metrology while the arc furnace diffused. That compressed years of serial work into the same calendar window.

Without that realization, repeated late-game failures could easily have pushed the finish past 600.

**Recommendation:** Add a prominent early help/tutorial message when the first multi-year project starts: "Calendar floor is not exclusive research time. If you have free founder-hours and staff, start other projects in parallel." Consider showing "unused founder-hours this year" more aggressively in the prompt when a player has only calendar-limited work running.

## 7. `available sort nearest` is misleading for goal navigation, and `stuck` becomes nearly useless near the endgame

**Damage: High/Medium.** With the explicit goal set to junction transistors, `available sort nearest` repeatedly began with agriculture. Near the end, `stuck` told me I had hundreds of affordable things and suggested cheap/profitable work rather than identifying the one actual goal blocker.

`rush` is better documented because it explicitly says it has no idea what I am building toward. `nearest` does not explain what "nearest" means and therefore looks like a target-path planner when it is not one.

**Recommendation:** Either make `nearest` actual graph distance to the current goal, or rename/explain it. Add a goal-aware command that says: "Of the prerequisites you have heard of, these are the currently buildable nodes on paths to your target."

## 8. Finished knowledge versus active supply/capability is strategically good but inconsistently surfaced

**Damage: Medium/High.** The distinction is one of the game's best systems, but it repeatedly surprised me.

Examples:

- knowing sulfuric-acid chemistry did not count as having sulfuric-acid supply;
- completed lead chamber had to be open for downstream supply;
- corpus/school/patron/academy capabilities can lose benefits while closed;
- power grid repeatedly auto-closed from attrition;
- a project can be DONE while its earlier prerequisite is later forgotten in a sack.

**Recommendation:** In every blocked prerequisite message, explicitly distinguish:

- "knowledge missing";
- "known but concern is closed";
- "material supply missing";
- "staff/supervision missing."

The underlying model is excellent; the UI should make the state type unmistakable.

## 9. Attrition silently closes critical concerns and can create large downstream changes

**Damage: Medium.** The power grid, lead chamber, zinc industry and other major concerns repeatedly closed because normal attrition left nobody supervising them. This could crash recurring income or silently remove a supply/capability.

The auto-close message itself is clear when it happens, but with many concerns it becomes maintenance whack-a-mole.

**Recommendation:** Provide a "critical concerns" staffing reserve or a policy like "prioritize keeping these N concerns open." `auto_hire` exists but is intentionally simplistic; a small priority list would reduce repetitive babysitting without automating strategy.

## 10. Build staffing and operating staffing can differ sharply, producing post-completion surprises

**Damage: Medium.** Examples included the lead chamber and several large concerns. A player can afford and complete a project and then discover the operating supervision requirement is larger/different enough that it cannot be opened.

The `why` page does display both numbers, which is good, but in a huge description it is easy to miss.

**Recommendation:** On `start`, warn prominently when current free staff would be insufficient to operate the completed concern: "You can build this now, but with today's staffing you could NOT open it when finished."

## 11. Zero-year / zero-cost capability nodes still require a time tick

**Damage: Low/Medium.** Examples such as local/portable power capabilities showed 0 years, 0 hours, 0 cost, yet after `start` they waited until the next yearly step to complete.

**Recommendation:** Either complete true zero-time capabilities immediately or display a minimum "next tick" duration rather than 0 years.

## 12. Some player-facing text leaks development/audit notes or out-of-civilization assumptions

**Damage: Low, but immersion-breaking.** Examples during the run included:

- a furnace description containing a bracketed **"FIXED after independent audit"** note;
- academy/institution descriptions heavily framed around Rome even while playing Han;
- the platinum page explicitly telling the player to inspect `data/world/geography.json`.

**Recommendation:** Keep developer provenance, internal file references and patch-history comments out of normal player text. Civilization-specific flavor should either adapt or stay generic.

## 13. The selected merchant start appeared as 4,000 den, but the playable state began with 3,000 cash without explanation

**Damage: Low/Medium early-game trust issue.** I chose the merchant option because it was the recommended middle-ish income. The first playable prompt then said I arrived with 3,000 cash. If 1,000 is intentionally consumed by setup/travel, the game should say so.

---

# What worked well — protect these

These are a smaller part of this report, but I would be careful not to lose them while fixing the problems above.

## A. The physical/industrial causality is often excellent

The best chains felt like engineering rather than a tech-tree checklist:

- coal and iron shortages physically throttling bulk steel;
- lead metallurgy enabling galena, acid plumbing and batteries;
- 3,000 C electric heat revealing artificial/high-purity graphite;
- GeCl4 distillation making ultra-pure germanium chemically plausible;
- measurement capability gating purity claims;
- grid power enabling electropolishing, vacuum systems and industrial zinc.

When fog reveals the next step through a physically sensible dependency, the game is very satisfying.

## B. Historical hazards and mitigation are one of the strongest systems

The risk screen is excellent. It explains dates, yearly probabilities, cumulative danger and exactly how prior choices mitigate output, sacks or staff losses.

The best example was Hou Jing: rebuilding/opening plague preparedness changed expected staff loss, and the actual event later reported only 7% loss versus 25% unmitigated. That made preparation feel real rather than cosmetic.

## C. Institutions compound in a rewarding way

Schooling, academy networks, deputies and literacy transformed the run over centuries. Founder-hours grew from roughly 2,000/year to well over 10,000/year. This made the civilization feel like it was learning to carry the programme rather than remaining one immortal inventor forever.

## D. Economy, staff and technology genuinely interact

The early game nearly collapsed under debt; later, businesses financed science; then industrial mines and grids changed the cost structure again. Large staff pools can be both expensive and productive. This made economic strategy matter without turning the game into only an economy simulator.

## E. `why` pages are usually excellent once a node is visible

They often explain:

- the historical/physical reason for the node;
- build staff versus operating staff;
- materials;
- calendar floor;
- failure risk;
- exact currently-known blockers.

The text was often good enough for me to reason from real-world science/history to the correct next step.

## F. Intermediate milestones are motivating

The **galena detector** was particularly good. The game explicitly framed it as a working semiconductor device achievable in a pre-industrial economy. That gave the long transistor programme a tangible midpoint rather than hundreds of years of abstract prerequisite accumulation.

## G. `rush` is honest about what it is

The game explicitly says `rush` is a rough high-leverage heuristic, not a plan, and that a careful player should beat it. Keep that candor.

---

# Difficulty conclusion

On this run, the game is **not too easy**. It is also not unwinnably hard.

I won blind as immortal Later Han in **575 AD**, 25 years early, but the margin depended heavily on:

- building a strong economy and institutions early;
- learning to run many projects in parallel;
- keeping staff buffers above future thresholds;
- preparing for known historical hazards;
- surviving several huge sacks;
- getting through repeated mandatory failure rolls.

The biggest source of unfair-feeling difficulty was not complexity itself. The complexity was usually the fun part. The dangerous parts were **opaque critical gates** and **long mandatory projects where repeated failure offered no meaningful strategic response**.

If the prerequisite contradictions, fog leaks, platinum discoverability, and goal-navigation issues are fixed while preserving the physical chains, hazard system and institutional/economic depth, I think the game would be substantially stronger without becoming easier in a shallow way.
