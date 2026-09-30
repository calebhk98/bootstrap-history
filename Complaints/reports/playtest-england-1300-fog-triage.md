# Triage: England 1300 fog playtest (poor_scholar kit, 1300 to 1375)

Inputs (verbatim): `playtest-england-1300-fog-yearly-log.md`, `playtest-england-1300-fog-tester-notes.md`. The tester may have played an older build. Every "reproduces" below was checked on branch `england-fog-playtest-triage` (fast-forwarded to the merge of late-game-performance) with an England 1300 fog game, seed 1, poor_scholar kit, using `python3 sim/simulator.py play --civ england_1300 --kit poor_scholar --fog --seed 1 --session <file>`, unless it says "code reading" or "untested" (needs a late game).

New complaints filed: 196 to 216. Appended "Also reported" paragraphs: 72, 79, 97, 114, 116, 151, 176, 178. Additions for 184 and 194 are listed at the end and not written (another agent owns those files).

## Item table

| # | Item (tester's words, shortened) | Outcome | Reproduces now |
|---|---|---|---|
| 1 | `population` tells the player to see `labour.py` / TRADE_DENSITY | Duplicate of 176 (partly); paragraph appended | No for the file reference (gone). Placeholder counts still unmarked per row: yes |
| 2 | `why tex_horizontal_loom` staff says artisans, `open` demands carpenter FTE | Duplicate of closed 149 | No: `why` now prints "SPECIALIST FOREMAN TO KEEP IT OPEN: 0.25 carpenter FTE (generic artisans cannot substitute ...)". The line above it still says "0 scholars, 0.27 artisans", which reads oddly beside it but is explained on screen. Not filed |
| 3 | `buy school scholar 2` / `scribe 2` misrouted to the mine parser | Duplicate of closed 156 | No: now "REFUSED: cannot afford that trade school" |
| 4 | `available electricity` returns only Signal flags | New 197 | Yes; cause is the `kb` file name `50_electricity.md` being matched |
| 5 | Topic search literal; physics, science, education, health, furnace, literacy, sanitation, water return nothing; wants a thesaurus / related names / categories | New 196 (closed 74 asked for tags and was closed) | Yes |
| 6 | Imperial-edict node offered free in England 1300 | New 198 | Yes; also found: taking it raises scandal to 5.8 with no warning (the tester's "scandal appeared at 5.8, I did not expect it") |
| 7 | Scandal appeared unexplained at 5.8 in 1301 | Folded into 198 | Yes |
| 8 | Resilience score opaque (0.98 to 0.998 while plague loss stays 29 to 40 percent) | New 199 | Yes (0.960 with nothing built at 1310) |
| 9 | Institutions score 0 despite corpus, sanitation, engineers | Folded into 199 | Partly: corpus was finished but closed; counting rule not stated |
| 10 | `changes 10` refuses at 1310 | New 209 | Yes |
| 11 | Famine message "2,336 gone with the trade that stopped" has no unit | New 201 | Yes (code reading) |
| 12 | Public-health softening not attributed | New 202 | Yes (code reading) |
| 13 | Mitigation lapsed without explanation (fields, fodder) | New 202 (182 closed names the closed concern; cause of closure still missing) | Partly |
| 14 | Corpus says CLOSED / not in effect but risk counts it as a hedge | New 200 (04 and 55 closed) | Yes (code reading); designed behaviour, wording contradicts it |
| 15 | `allocate` not suggested when a project is starved | New 205 | Yes (code reading; untested live) |
| 16 | Stale allocations produce repeated DIRECTED HOURS UNUSED | New 206 | Untested (code reading: message repeats each year) |
| 17 | Risk wording "output factor: you take 58%" | New 204 | Yes ("you take 80% of it" at 1310) |
| 18 | Charcoal "about 1 more hectare" repeated year after year | Duplicate of 79 (open); paragraph appended | Yes (code reading; text unchanged) |
| 19 | No pre-opening market-saturation / cannibalisation preview | Duplicate of 178 (partly); paragraph appended | Largely no: `why` now shows "Sells into the textiles market, where N other concerns of yours also sell; it would earn about X% ...". Behaviour with several open concerns untested |
| 20 | Currency (pence) not stated as normalised; wages not historical | New 207 (related 144) | Yes |
| 21 | `save` rejects absolute paths | New 208 | Yes |
| 22 | JSON commands in basic help are noise for a nontechnical player | New 210 (172 closed covered `--help` only) | Yes |
| 23 | Decision journal / yearly retrospective | New 211 (retrospective part also on 97) | Not a defect |
| 24 | Intermediate education ladder between hire-one-scholar and a school | New 212 | Not a defect |
| 25 | Intermediate knowledge hedges below a corpus or school | New 213 | Not a defect |
| 26 | Political attention for a dominant founder (crown, guilds, poaching, espionage, church) | Duplicate of 114 (open); paragraph appended (118 related) | Not a defect |
| 27 | Thematic hints for unknown fog prerequisites | Duplicate of 72 (open); paragraph appended | Yes (design gap) |
| 28 | Debt-service forecast versus formal credit ceiling | New 214 | Untested |
| 29 | Mitigation contribution breakdown on `risk` (silo, vector control, sanitation) | Folded into 202 | Yes (`risk` gives one total) |
| 30 | Pre-purchase hazard-impact preview for resilience projects (silo 12 to 11 percent) | New 203 | Untested |
| 31 | Lead metallurgy quoted about 7 million at 1375 | Duplicate of 151 (partly); paragraph appended; design intent in 184 and 194 | Cost at 1300 is about 409 thousand; the 1375 figure not reproduced |
| 32 | Money easy by 1350 (about 916 thousand capital, 169 thousand a year) | Belongs to 184 and 194; not written (see below) | Not reproduced (needs a played-forward game) |
| 33 | Regional / sector diversification (venture in another town) | New 215 | Not a defect |
| 34 | Personal discovery vs local adoption vs national diffusion; causal attribution of diffusion | Duplicate of 116 (open); paragraph appended | Not a defect |
| 35 | "What changed this year and why" causal summary | Duplicate of 97 (open); paragraph appended | Not a defect |
| 36 | Ledger shows a large aggregate market deduction but names only one saturated concern | New 216 | Untested |
| 37 | `help commands` should be surfaced more when advanced situations arise | Folded into 205 | Yes |
| 38 | Fuzzy / precise numbers look too certain (revenue quotes) | Closed 192 and 195 provide `--fuzzy-estimates`; the tester did not enable it. Not filed | n/a |
| 39 | Household and staff-dominated-market reporting (population screen shows share of reachable pool) | Positive, see below | n/a |
| 40 | Named-staff optional mode (attrition is FTE fractions) | Not filed: tester says the maths is fine; a presentation preference with no evidence of confusion | n/a |
| 41 | Hiring a whole carpenter for a quarter of an FTE leaves expensive slack; "labor substitution previews" | Not filed: a consequence of the supervision model, which the tester praises; the `why` foreman line now covers the planning need | n/a |
| 42 | Intermediate public-health infrastructure before the Black Death (gap between sanitation ideas and disease control) | Not filed: the tester later built a long chain (filtration, chlorination, sludge, registration, contact tracing) and praised it; content request without a specific missing node | n/a |
| 43 | Household should read as a proto-conglomerate; growth identity in the presentation | Not filed: flavour and framing; noted in 114 paragraph for the political side | n/a |
| 44 | Unconfirmed impact questions: farm expansion vs food prices, occupational shares under mechanisation, downstream prices, doubling population | Not filed: open questions, not defects. Belong to 106 (closed demand loop) and 111 (urbanisation) | n/a |
| 45 | Large tree (143 startable at the start, 231 by 1332; transistor closure 181, floor around 142 years) | Not filed: fog design working as intended; the search complaint (196) is the actionable part | n/a |
| 46 | `advance` is not a command (tester error, `step` is) | Not filed: recovery message was good; could add an alias but no evidence it hurts | n/a |
| 47 | Tester mistake: opened archive READMEs in the first minutes | Process note only | n/a |
| 48 | Trained-machinist / engineer leaving stalls sanitation (abandonment clock) | Positive (see below); no complaint | n/a |
| 49 | Ledger looks great after a scholar leaves (financial health versus capacity) | Praised as a feature; no complaint | n/a |
| 50 | Fire, banditry and war supply losses become small relative to capital by 1343 | Belongs to 169 (disasters take cash) and 184; not filed | n/a |

## Severe bugs

None found. The nearest to a real defect is the silent scandal cost of a free node (198) and the misleading corpus wording (200); neither corrupts state. The `buy school` misroute and the loom foreman mismatch, the two functional bugs in the notes, are already fixed on this branch.

## Positive feedback ("do not break")

- New-game flow: clear main menu, fog explanation, kit descriptions, goal scope shown through closure size and theoretical floor without revealing the route, difficulty changing only the deadline, automatic resumable session with the exact resume command.
- `help` teaches a small command model; the tester rarely needed it after twenty years. `help commands` and per-command help are good layering.
- Failure with learning: partial elapsed calendar carried forward, retry risk drops after a failure.
- Knowledge versus capability: atomic theory writable from memory but inoperative without an analytical balance; the analytical-balance to clear-glass to glassblowers to labware to laboratory chain; charcoal from sustainable coppice throttling cementation steel and glass.
- Human capital: scribe and scholar supply as the real limit (arithmetic curriculum, geometry, corpus), hiring moves the whole category wage, `train <trade>` creating a profession, hiring two scribes raising usable supply, opening a university raising scholar supply, share of the reachable pool employed shown in `population`.
- Operating staff: build staff versus keep-open staff, specialist foreman as a share of FTE, warning at start time that a concern can be built but not opened, mothballing one concern to free supervision for another.
- Finance: project-start warning with single-project bill, total commitments, expected credit draw and formal ceiling; arrears interest making leverage dangerous; ledger itemisation; market saturation ledger row; the rich lifestyle increment.
- Hazards: risk screen listing categories of mitigation; multi-layer famine (staff, population, wages, cash); water chain (aqueduct, sewer, filtration only counting once filtered); wartime resilience credited to power not from ships, own land and own roads; Black Death payoff for preparation; national diffusion softening.
- Political gates (patronage needed before Newtonian mechanics) felt earned.
- Venture ramp-up over about three years; founder-idle warnings; `recap`; `portfolio` and `allocate` once found.

## Additions for complaints not edited here (owned by another agent)

To 184 (dated hazards and late money): the tester independently reports the same late-money pattern in a different civilisation, with numbers: capital fell to minus 30 thousand pence in 1335, then about 916 thousand with 169 thousand a year recurring by 1350 (roughly 3.45 million and 709 thousand a year by 1375) from diversified agriculture, power and medicine, despite fire, war disruption and plague. They judge the pace right (money is no longer the bottleneck by 1350) but say costs below about 100 thousand stop being strategically scary. Losses to fire and war supply (54,976 and 52,980 pence in 1341 and 1343) are noise by then. Dated hazards themselves were praised as plannable ("some of the game's best causal modeling"), unlike the Rome player's "scripted" reading.

To 194 (late-game uses for money): the tester's list of things money cannot buy fits the intent: calendar time, professions that do not exist, laboratory ecosystems, mass literacy, political legitimacy, unlimited raw materials. Concrete items they would spend on: intermediate education institutions (212), partial knowledge hedges such as copies deposited with monasteries or universities and paid scribes (213), regional expansion of ventures into separate demand pools (215), patronage of translations and university chairs, and buying down debt-service pressure (214). At 1375 lead metallurgy at about 7 million pence was the one project money could not yet pay for, so cost scaling for industrial nodes is working; the tester's question for the second half is whether costs keep scaling faster than income. A 51.8 thousand pence a year "rich" lifestyle increment was praised as wealth having a running cost.
