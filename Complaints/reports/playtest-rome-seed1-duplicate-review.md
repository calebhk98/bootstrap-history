<!-- Written by a review agent that compared issues 146-185 against the older issues; it edited nothing. -->
# Duplicate review of Complaints 146-185 against issues below 146

Paths are relative to /home/user/bootstrap-history/Complaints/. Read-only review. Everything below 146 was searched by title, filename and body (open and closed).

## 146 sort-space-form-ignored: NEW
No older issue on `available` sort syntax. (Closed 22 is `available find` omitting a legal project: different.) Adds nothing to compare.

## 147 quote-farm-refused: NEW (adjacent to closed 61)
closed/61-a-quote-that-lies-about-credit.md is about `quote forest` affordability counting credit that `buy forest` refuses ("counts credit that `buy forest` will not take"). 147 is that `quote` does not cover farm/housing/school/material at all. Different defect. The `quote material` part is also in new 178.

## 148 wage-work-invisible-in-ledger: NEW
Nothing on `work`/`allocate work` ledger or log rows. Only false-positive hits (34, 56, 106 use the word "work" generically).

## 149 why-omits-specialist-foreman: OVERLAP
- closed/131-start-does-not-warn-the-finished-concern-cannot-be-opened.md: "A concern's build crew and its operating supervision are different numbers ... `why` shows both numbers, but inside a very long page." Fix covered a warning at `start` only.
- closed/13-generic-artisan-supervision.md is the rule that produces the refusal (specialist foreman required), not the display gap.
- 89-specialist-closure-call-to-action.md wants the specialist named on `state` for closed concerns.
Adds: `why` "STAFF TO KEEP IT OPEN" total omits the foreman trade, and `available` has no marker. Not a clear regression of 131 (131 only promised a start-time warning), but the underlying "surprise after sunk cost" persists.

## 150 mass-closures-on-staff-change: OVERLAP
- 130-no-way-to-name-the-concerns-that-must-stay-staffed.md: "Normal attrition repeatedly closed critical concerns ... because nobody was left to supervise them."
- 89-specialist-closure-call-to-action.md (profitable concern stays shut for a specialist shortage).
- closed/62 and 121 concern the restore-discount timestamp, not the closure rule.
Adds: a distinct mechanism claim (the yearly check closes far more than the shortfall, and `open` then accepts them with no hire), with a reproduction and a regression test proposal. 130 asks for a priority control, 150 asks for the check itself to be marginal. Same area, different fix.

## 151 project-materials-price-and-stock: OVERLAP (partial)
- 139-prices-use-long-run-cost-not-current-market.md: price solver uses long-run cost, not the current market.
- closed/09-global-resource-throttle.md and 92-resource-shortage-remedy-actions.md touch the material-shortage throttle and remedies.
None covers: project material bill is 4-5x the market price of the listed materials, owned stock is never drawn, paying the bill delivers no flow. Mostly NEW. Note: `why` showing time-to-supply per material is a 92-adjacent request.

## 152 mine-stock-accumulation: NEW
Closed 65/66/53 are mine sizing/ready-year/shaft cost. No stock-accounting issue.

## 153 earnings-differ-between-screens: OVERLAP (same class as closed 03)
closed/03-workshop-revenue-forecast.md: "`why workshop_first` and `open` both said the workshop earned 0/year ... Immediately after opening, `money` added 1,783/year." Same symptom class (decision screens understate revenue), but 153 traces to a specific multiplier (1.825) missing in `mothball`/`open`/`why`/`available` and adds saturation not shown on `ventures`. Closed 03 is pinned by test_round2_policy_hazards_options.py for the workshop case only; 153 suggests a broader regression of the class, not the same instance.

## 154 credit-freeze-refuses-cash-starts: NEW
Grep for credit freeze/insolvency finds nothing comparable (only incidental hits in 139, closed 30, 57).

## 155 rush-preview-empty: OVERLAP, likely REGRESSION of closed 21 / 77
- closed/21-rush-unsafe-bare-command.md: "`_cmd_rush` ... now returns a `preview`/`nothing_changed` response and requires `rush force` or `rush limit:N`".
- closed/77-rush-needs-fiscal-controls.md, pinned by sim/tests/test_rush_fiscal_controls.py ("rush preview changes no state").
The tests only assert that preview mutates nothing. 155 says the preview lists nothing ("0 started, 0 not") while `rush limit:3` starts three. Closed 21 was marked resolved, but the preview content is not tested, so this is a regression (or an incomplete fix).

## 156 buy-school-routed-to-mine-parser: OVERLAP, REGRESSION of closed 26 / 87
- closed/26-economic-levers-demographics-inventory.md: "`buy farm`/`buy housing`/a named trade school all exist (`_cmd_buy`)".
- closed/87-school-overload-trading-vs-education.md: status "the training mechanic is now 'trade school'; `buy school` was removed".
Code check: sim/engine/proto/dispatch_money.py registers only "trade_school" and "trade school" (lines ~216-217) while its own help string (~229) and sim/engine/proto/help.py (~223) still advertise `buy school <trade> <n>`. So 156 is real and is fallout from the 87 rename: the documented command falls through to the material parser. Not a duplicate; a regression of the closed items' promise.

## 157 bounty-corrupts-save: NEW
No older `bounty` issue (only an unrelated word hit in closed/63).

## 158 serial-floor-is-whole-chain: NEW (weakly adjacent to closed 08 and 38)
closed/08 (expected calendar time below the hard floor) and closed/38 (`path` judges against a different lifetime) are about other figures. No issue about the `why` "STILL TO BUILD BEHIND IT" serial floor.

## 159 play-session-needs-civ: NEW
Nothing on `play --session` requiring `--civ`. (136 and 135 are about Rome hardcoding, not CLI arguments.)

## 160 default-goal-name-mismatch: NEW
100-goal-path-teaches-wrong-strategy.md is about goal/path UX strategy, not which goal is the default. Different.

## 161 options-alias-and-menu-input: NEW
Nothing on the `options` alias or menu input handling.

## 162 new-concern-upkeep-and-net-column: NEW (adjacent to 153, closed 03)
No older issue asks for NET/PAYBACK columns or the first-year loss of a new concern. Same theme as closed 03 (revenue not shown before opening) but a different request.

## 163 log-missing-year: NEW
Nothing on multi-year `step` logging. (closed/82 is about completion waves.)

## 164 lead-metallurgy-rome-rebuild: OVERLAP
- 128-no-check-that-a-starting-state-agrees-with-itself.md: "Nothing compares a civilisation's briefing, capability rungs and owned techs against each other."
- 127-rome-holds-industries-its-heat-rung-cannot-run.md and 42 (pinned, starting techs vs prerequisite graph) are the same family.
164 is a concrete instance in the other direction (node text says Rome has it; Rome start does not grant it). It would be caught by the check 128 proposes. Instance-level NEW plus root-cause overlap.

## 165 failure-rate-vs-displayed-risk: NEW (adjacent to 124)
124-no-lever-to-trade-money-for-lower-failure-risk.md says effective risk is "node `risk` times a retry multiplier; no other input", which is about lack of levers, not whether realised rates match displayed. Related, not the same.

## 166 reopen-prices-inconsistent: OVERLAP
- closed/62-a-timestamp-that-outlives-its-cause.md and 121-prefer-explicit-state-causes-over-overloaded-flags.md: `restore` can charge the full price off a stale `shut_for_staff` timestamp.
166 is a different symptom: after `mothball`, `open` charges 1x upkeep but `restore` charges 2x, and no help text states either. Could be a leftover of the 62/121 restore rules (121 is still open on making the closure reason explicit). Not a clear regression of 62 (62 is about a stale timestamp), but check that the 2x is not the stale-timestamp path.

## 167 labour-room-advice-omits-housing: NEW
closed/26 confirms `buy housing` exists, which is why 167 is a wording/discoverability defect in the `labour` and `hire` advice. No issue covers that text.

## 168 staff-loss-exceeds-logged-losses: OVERLAP (weak)
closed/19-plague-repeat-wave-disclosure.md ("did not make the repeated-wave cadence clear") and closed/18 (population display). Those were about the risk screen; 168 says the log misses staff reductions (unattributed loss). Different; NEW in substance.

## 169 disasters-take-cash: NEW (adjacent to 118, and to new 182)
118-wealth-notice-saturation-too-flat.md discusses confiscation stakes scaling with wealth. 169 is about fires/banditry destroying cash with no explanation and no way to shelter it. Not the same mechanism.

## 170 crisis-knowledge-loss-cascade: OVERLAP
94-hazard-timing-not-only-relevance.md: "it only showed which mitigations were relevant, not whether they could be completed in time to matter" (risk screen needs timing). 170 asks for an escalating warning with the cheapest hedge and its distance, and questions the compounding. 84 (demographic emergency on state) and 80 (one event per disaster) are adjacent. Adds: the compounding-sack question and 135 years of unchanged warning.

## 171 auto-hire-keeps-idle-taught-trades: NEW (adjacent to 130)
130 is about `auto_hire` not protecting key concerns. 171 is idle taught specialists staying on payroll and being rehired. Same policy, opposite complaint.

## 172 top-level-help-is-developer-docs: NEW
No older issue on `--help`.

## 173 compact-output-longer: NEW (adjacent to 35)
35-playthrough-review-han-china-100-to-400ad.md item 1 requested an agent-oriented compact mode. 173 says the implemented mode is larger than the normal screen. A follow-on defect, not a duplicate.

## 174 ventures-cannot-page: NEW
closed/73 (startable vs blocked) and 75 (batch start) are the nearest. Neither covers paging of `ventures`.

## 175 shortage-message-contradiction: NEW
closed/09 concerns the throttle scope; no issue on the "your own workings already cover" clause.

## 176 population-placeholder-counts: OVERLAP (weak)
126-audit-markers-and-patch-history-in-player-notes.md: developer provenance in player-facing text. 176 adds identical placeholder numbers and a `labour.py` reference on the `population` screen. Closed 58/70 (headcounts exceeding population) are unrelated.

## 177 output-repetition: OVERLAP (mostly covered)
- 102-repetition-audit-interface-class.md, item 4 "FTE/supervision explanations" and item 3 "Project-start boilerplate".
- 78-project-start-boilerplate-repeats.md: "Repeated `start` commands re-explain fixed-price/quote behavior".
- 79-persistent-shortages-status-conditions.md (identical annual messages).
Duplicated parts: the `why` staffing paragraph, the `start` forecast block, the yearly "population below trend" line. New parts: completions printed twice (`COMPLETED` then `DURING`), the per-concern "spare craftsmen" line, NAME truncated to 20 characters, and a verbosity setting. closed/82 (completion waves) is a different pattern, so not a regression.

## 178 market-information-gaps: NEW (partly overlapping 147)
No older issue on market screens. 139 is about how price is computed, not what is shown. The `quote material` and `materials` listing pieces duplicate part of new 147.

## 179 route-blockers-hidden-from-path: OVERLAP
129-blocked-messages-do-not-name-the-kind-of-blocker.md (blocked messages do not say which blocker kind) and closed/73. 179 is specifically that `path` says "nothing on the route is startable" while `stuck` has the reason. Adds a concrete surface (`path`) and the "built but never opened patron" case.

## 180 goal-directed-automation: OVERLAP (weak)
130-no-way-to-name-the-concerns-that-must-stay-staffed.md (a per-concern keep-staffed control, `auto_hire`), 75-batch-start-filtered-multi-select.md, closed/77-rush-needs-fiscal-controls.md (strategy modes for `rush`). The `pursue <goal>` and `rush path:<goal>` requests are NEW; the foreman-replacement and spare-craftsmen reserve items overlap 130.

## 181 step-n-summary: OVERLAP
102-repetition-audit-interface-class.md, "Recommended UI philosophy for mature turns": a `MAJOR CHANGES` structure. Also 79 and closed/82 (summary-first). 181 adds a specific end-of-`step N` list of persistent problems. Same theme, new concrete request.

## 182 confiscation-and-late-threats-hidden: OVERLAP (weak)
118-wealth-notice-saturation-too-flat.md (confiscation stakes) and 94 (risk screen shows relevance but not timing). Neither asks for confiscation chance and protections to appear on `risk`/`state`, or for the concern behind a "(lapsed)" hedge. NEW in substance.

## 183 no-score-without-goal: NEW
No older issue about `score`.

## 184 dated-hazards-and-late-money: OVERLAP (design note)
- CLAUDE.md section 4.2 / 94 / 80 for scripted dated crises; 117-difficulty-curve-strong-snowball.md and 101-idle-directed-hours-late-game.md for late-game money and pace.
- 118 (extreme fortunes).
184 says it is a design note, not a bug. If a tracker item is wanted, it could merge into 117/101. Note the dated-hazards point may conflict with CLAUDE.md 4.2 (a baseline that reliably reproduces dated events is evidence of cheating); no existing issue files this.

## 185 late-game-performance: OVERLAP (same root as 145)
145-yearly-cost-grows-with-built-nodes.md: "the cost of simulating one year grows with the number of completed nodes and running concerns ... the late years take far longer than the early ones." Adds: process-level costs (load and save ~0.5s per command, `open` refusal cost, save growth, `.cache/` written to the run folder and not documented in the README). Best merged into 145 or kept as a session/process-level issue.

## Duplicates among the new issues (146-185)
- 147 and 178: both say there is no way to learn a material's market price without buying (`quote material`, `materials` lists only tracked). Overlap on one line each; 147 is the command-coverage complaint, 178 the information-screen request. Keep both, cross-reference.
- 150 and 180: 180's "`auto_replace_foreman`" and "keep N spare craftsmen" reserve are a response to 150's mass closures and 149's foreman gaps.
- 149 and 150: same subsystem (foreman/specialist staffing). 149 is display, 150 is the yearly closure rule. Not duplicates.
- 153 and 162: both say decision screens hide real earnings and net; 153 is inconsistency between screens, 162 asks for NET/PAYBACK columns. Related, distinct.
- 169 and 182: both concern idle cash losses (disasters, confiscation) and the lack of a way to shelter it. Overlapping in the "protect cash" line. Could be merged.
- 151 and 178: both note the mismatch between project materials and market prices; 151 the project bill, 178 market information.
- 173 and 177: both about output volume, different commands (`compact` vs screens). Not duplicates.
- 174 and 162: both want list/paging/sort features on `ventures` and `available`, on different commands. Not duplicates. (146 is the same `available` sort code path as 162's proposed `sort:net`.)
- 184 and 170: both use the fixed Rome crisis schedule as evidence; 170 is the loss cascade, 184 the design view.
No exact duplicate pairs.
