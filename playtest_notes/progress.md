# Playtest progress

Game: `play --civ rome_100ad --seed 1` (poor_scholar kit, default goal point_contact_transistor).

| Year | Money | Net/yr | Route steps done | What happened |
|---|---|---|---|---|
| 100 | 2,695 | -297 | 0 | Arrive. Built hand ginning and peat (the only earners visible on page 1). |
| 101 | 1,320 | -341 | 1 | Wage work cost more than it paid. Started scientific method. |
| 102-104 | down to -13,431 | about 0 | 8 | Borrowed to build loom, ligature surgery, horse collar. Learned each needs a named foreman trade. |
| 105-112 | back to +19k | +10k | 15 | Positional notation, units, identity, patron, arithmetic, algebra, statistics. Carpenter died twice; concerns closed. |
| 113-121 | 49k | +41k | 22 | Trade route extension (big earner), first workshop, lenses, case hardening, crank. Many first-attempt failures. |
| 122-128 | 389k | +163k | ~39 | Water power, bellows, 1100/1300 C heat, glass, porcelain, telescope, steel, phosphorus. |
| 129-130 | 55k | +194k | ~39 | Route narrows to charcoal_industrial / zinc_metal / lead_metallurgy (330k-470k each). Paid 464k for lead; found bugs #6 and #7. |
| 130-149 | 1.0M | +396k | ~45 | Lead, charcoal, zinc, coke, blast furnace (1.81M, failed once). Staff churn closes concerns often (bugs #5). |
| 150-169 | 6.0M | +341k | ~53 | Bessemer converter, puddling, copper, voltaic pile, calculus. Route stalled ~9 years until `stuck` said to open the town patron. |
| 169-206 | 14.9M | +1.05M | 83 | Newtonian mechanics, EM theory, machine tools, vacuum, thermodynamics, 1600 C furnaces. Turned on `auto_hire`, which stopped most churn. |
| 206-234 | ~17M | +1.2M | 91 | Interchangeable parts, Newcomen and Watt engines, band theory. Fires took 3.6M and 3.8M. |
| 235-256 | -88k | +1.2k | 25 | Third century crisis: 6 sackings, debasement. Most cash, most staff and 70 technologies lost. Roughly back to 110 AD. |
| 257-303 | 47k -> 15k | -16k to -1k | 10 | Credit frozen twice (my script borrowed with no income), insolvency settled in 279 and 291. Idle machinists on payroll. Plague of Cyprian, Diocletian. |
| 303-341 | 72k | +30k | 34 | Rebuilt the basics with a cash-only routine: method, units, patron, maths, lenses, trade route, steel, water power, 1300 C. |
| 341-417 | -181k | +15k | ~60 | Rebuilt through blast furnace, Bessemer, puddling; route stalled 30 years on an ID my script could not parse (cap_pure_2N). Sack of Rome (410, 415) took 1.1M and 43 people. |
| 417-507 | 3.17M | +388k | 106 | Trained chemists; steam engines, chemistry, acids, dispersed corpus, academy network. Knowledge hedged (sack knowledge-loss chance 80% -> 12%). |
| 507-546 | 11.2M | +0.9M on paper, ~0.3M/yr actually saved | 107 | Built ~170 cheap earners; ~200 concerns running, but ~60 close and reopen every year (bugs #5). Justinianic plague and banditry take ~1-2M a year. Forest purchase cut zinc smelting from 63M to 26.7M. Bulk steel (14.8M) refused for lack of funds three years running. |

Outlook at 546 AD: the 53 remaining nodes cost ~48M (bulk steel 14.8M, industrial zinc 26.7M after the forest, power grid 4.0M, the rest ~3M), before 25-30% failure risks on the two biggest. With 54 years left, that needs ~0.9M/yr actually saved; the real rate since 529 is ~0.3M/yr.

## New goal from 552 AD: research and open as much as possible, change the society
| Year | Money | Net/yr | Techs (score raw) | Literacy | Concerns running | What happened |
|---|---|---|---|---|---|---|
| 552 | 1.3M | +0.9M | 507 | 49% | ~130 | Baseline. Reopened 79 concerns via the log workaround; `rush` with a budget. |
| 566 | 11.5M | +2.4M | - | 60% | ~200 | 2 deputies; bulk steel done; transistor ruled out, WRONGLY: I read `why`'s "131.2-year serial floor" as time remaining; it is the whole chain's floor (bugs.md #13). |
| 567 | 19.8M | +5.5M | - | 60% | - | **Achieved: Epidemics stop deciding who lives** (curb epidemic mortality). |
| 572 | 37.3M | +7.0M | 1,381 | 62% | ~250 | 5 deputies, 44 scholars, 598 craftsmen. Found the bounty save-corruption bug on a copy. |
| 582 | 86.3M | +17.6M | - | 81% | ~480 | **Achieved: A nation that reads** (75% literacy). Telegraph, newspapers, movable type shift w_information and w_novelty. |
| 585 | 111.2M | +18.9M | - | 81% | ~480 | Scholars are the binding limit (65 needed, 0 free, town cap ~67); training 10; frontier narrowing (rush starts only 16). |
| 594 | 91M | +30M | - | 84% | ~850 | Treasury confiscation chance reached 5%/yr; moved ~170M into 100,000 ha forest + 10,000 ha farm (no warning since). Draught animals move w_labour_saving. |
| 600 | 41.7M | +36.7M | 2,459 | 85% | 827 | **Run ended at the horizon.** `rush` found nothing left to start in 598. |

### 552 -> 600, measured with `score` and `values`
| Measure | 552 AD | 600 AD |
|---|---|---|
| Technologies (score raw) | 507 | 2,459 (2,234 built by me) |
| General literacy | 49% | 85% |
| Workforce | 180 | 1,839 |
| Institutions | 10 | 22 |
| Deputies (founder-hours/yr) | 0 (2,000) | 17 (33,792) |
| w_magic_fear | 0.63 | 0.49 |
| w_information | -0.15 | 0.09 |
| w_novelty | 0.08 | 0.18 |
| w_labour_saving | -0.23 | -0.18 |
| bribability | 0.55 | 0.50 |
| unchanged | | religious rigidity 0.78, military 0.95, commerce 0.25, eminence danger 0.85, patronage 1 |
Goals achieved in the run: A literate people (484), Epidemics stop deciding who lives (567), A nation that reads (582). I declared the transistor out of reach at 566 by misreading the chain-wide 131.2-year floor as time remaining (bugs.md #13). At 600 the route had 14 nodes left (power grid active, zinc smelting and germanium blocked behind it), so with the route prioritised from 566 it may have been reachable; I did not test that.
