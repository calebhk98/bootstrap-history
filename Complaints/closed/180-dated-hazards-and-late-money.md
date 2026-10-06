# Design: dated historical hazards, and money that stops mattering

**Status:** closed - recorded in docs/architecture/DESIGN_PRINCIPLES.md

- Every Rome run meets the same named crises in the same years (Antonine plague 169, third-century crisis 235-279, debasement 205/220/235, Cyprian 249, sack of Rome 410/415, Justinianic plague 541, Lombards 568). `risk` lists them decades ahead. Plannable, but it reads as scripted history.
- Late game (after ~570 AD) money was irrelevant: 40-240M cash, +20-37M/yr, and the pace set entirely by prerequisite chains and "diffusion" calendar floors (`rush` found 0-8 things to start per year at the end). Large idle cash only raised confiscation risk.
- Concerns earn fixed tree figures (times saturation) with no buyers; one household reached 241M den.

Not bugs; recorded as a player's view for the design documents.

Found in a new-player playtest (Rome 100 AD, poor_scholar kit, seed 1, played through `play --session`), report: `Complaints/reports/playtest-rome-seed1-new-player.md`.

## Stakeholder decisions

- Dated historical crises stay as they are until the dynamic systems can produce them for each country: debasement and inflation from the economy work in progress, plagues from the population and medical systems, sacks after multiplayer. Do not replace them with random draws.
- The late-game surplus is intended: advancing the whole society makes far more money than working only for yourself. What is missing is things to spend it on; that is filed separately as 190.

**Also reported (England 1300 fog playtest, `Complaints/reports/playtest-england-1300-fog-triage.md`):** the same late-money pattern in a different civilisation. Capital went negative in the 1330s, then diversified agriculture, power and medicine made money no longer the bottleneck by about 1350, despite fire, war disruption and plague; fire and war supply losses became noise. The tester judged that pace acceptable. They praised the dated hazards as plannable causal modelling, the opposite of the Rome player's "scripted" reading.

Also reported (Han China 100 AD fog playtest, tester item(s) 53, 138, 150, 218, 223; `Complaints/reports/playtest-han-china-100ad-fog-triage.md`): the same late-money pattern in another civilisation: cash 142 million at 150 AD (Han), 1.5 billion at 175, 5.2 billion at 200, 20 billion at 250, 838 billion at 400 AD, recurring net 33 billion, all research and staffing costs trivial against it. Two causes stand out: a free fleet (223) and workshop revenue of hundreds of millions with no product line. Seizures of 7 to 74 billion, sackings of up to 114 billion, fires and requisitions were the real limits, and the tester judged them meaningful. They also noted that cheap research "never threatens solvency" from about 140 AD. Reproduces: the free fleet yes (223); the rest needs a played game.

Also reported (final playtests, A, B and C; `Complaints/reports/final-playtests-triage.md`): A and B repeat that dated events fire regardless of divergence (Christianisation, Gothic settlement, 235 crisis, Decian edict, Diocletian); both also praised the dated hazards as plannable and felt the preparation reward (public health cut the Antonine plague to about 4% empire-wide instead of about 28%; a dispersed corpus meant a 283 AD sacking took 326 million denarii and 3,641 people but no knowledge). C: the Mexica invasion (90% a year for three years) felt predetermined and the tester's own best defence reached 66%; part of that is the fixed default seed (250). The divergence readout and conditional events asked for are filed as 266. Late-money pattern confirmed again: B reports money irrelevant from about 125 AD.
