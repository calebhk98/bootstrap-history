# Playtest: a new player, Rome 100-600 AD

An AI agent played as a new user: read only the README and what the game prints, no source. `play --civ rome_100ad --seed 1` with the default poor_scholar kit and default goal (point_contact_transistor), one command per `--session` invocation. From about 120 AD a small shell script did the routine yearly moves (open earners, hire when short, start route nodes, step); from 552 AD the goal switched to "research and open as much as possible", played one year at a time with `rush`.

## Outcome
- The transistor was not reached. At 552 AD 108 of 160 route nodes were done; at 600 AD 14 remained (power grid building; industrial zinc and germanium blocked behind it). At 566 AD the agent abandoned the goal after misreading the chain-wide serial floor as time remaining (issue 158).
- 2,227 distinct technologies completed (2,459 known with Rome's 225 granted). 13 of the 17 built-in goals' target nodes reached: experimental science, germ theory, written corpus, imperial patronage, electrical generation, 20% literacy, public health, steam engine, interchangeable manufacturing, modern navy, continental telegraph, synthetic fertiliser, 75% literacy. Not reached: both transistors, stainless steel, broadcasting, powered flight.
- Between 552 and 600 AD (`score`, `values`): technologies 507 -> 2,459, general literacy 49% -> 85%, workforce 180 -> 1,839, institutions 10 -> 22, deputies 0 -> 17; w_magic_fear 0.63 -> 0.49, w_information -0.15 -> 0.09, w_novelty 0.08 -> 0.18, w_labour_saving -0.23 -> -0.18. Religious rigidity, military, commerce, eminence danger and patronage never moved.

## Timeline
- 100-121: first earners (hand ginning, peat, then loom, surgery, horse collar on credit); the trade-route extension carried the economy; foremen deaths closed concerns repeatedly.
- 122-234: blast furnace, steel, water power, precision tools, steam engines, band theory; ~17M den and 91 of 160 route nodes by 234.
- 235-256: the third-century crisis sacked the household six times; technologies built fell from 91 to 21, the route went back to 135 remaining, then two insolvencies (279, 291).
- 303-548: rebuilt, trained chemists, dispersed the corpus and built the academy network, then ~170 cheap earners; bulk steel (14.8M) started in 549.
- 552-600: `rush` with a budget, ~50 completions a year at peak; public health achieved 567, literacy 75% achieved 582; research ran dry by 596-599 (`rush` found 0-8 startable per year).

## Issues filed from this playtest
Bugs: 146 sort form ignored, 147 quote farm, 148 wage work invisible, 149 foreman missing from `why`, 150 mass closures, 151 material price/stock/flow, 152 mine stock accounting, 153 earnings differ between screens, 154 credit freeze vs cash, 155 `rush preview`, 156 `buy school`, 157 `bounty` corrupts the save, 158 serial floor is whole-chain.
Quirks and UX: 159-177.
Feedback and requests: 178-185 (output repetition, market information, route blockers, goal-directed automation, `step N` summary, confiscation risk visibility, final score, design notes, late-game performance).

The agent's raw notes (with more measurements) are in `playtest_notes/` at the repository root.
