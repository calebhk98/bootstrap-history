# Non-tech-tree complaint resolution audit (01–26)

This audit covers the numbered, non-review complaints in this directory. It
records the current implementation rather than treating the presence of a
complaint file as proof that the issue remains open. The focused regression
modules named below are part of the normal `sim.tests` runner; a fix is not
considered protected if its test merely exists on disk.

| # | Status | Current resolution and regression evidence |
|---:|---|---|
| 01 | Fixed | `ventures` reports total, held, and free supervision in FTE, explains that free capacity is clamped at zero, and states the 0.50-FTE anti-churn margin. |
| 02 | Fixed | An active project that cannot fund its next instalment but retains spending power says it may fund opportunistically as revenue arrives; a household with no cash or credit headroom is separately labelled “fully blocked until funding is available.” Covered by `test_complaints_09_16`. |
| 03 | Fixed | `why` labels its number as direct concern revenue and explicitly warns that institutional capacity, reachable staff, practice output, and other indirect income are excluded. |
| 04 | Fixed | `why` separates `permanent_on_completion` from `only_while_open`, including the stronger warning for capability institutions. |
| 05 | Fixed | The school description says the immediate grant is four scholars and the subsequent annual effect expands the household training/reachable pool rather than incrementing the headline count directly. |
| 06 | Fixed | `auto_court_heir` is a documented policy. It defaults off in manual play, and the event reports whether the price was paid and how protection/scandal changed. |
| 07 | Fixed | Project waiting reasons and `portfolio` use the same trade-demand/supply accounting; “booked” is emitted only when aggregate demand actually exceeds supply. |
| 08 | Fixed | Expected calendar time includes the first attempt's full floor plus retry exposure and is tested never to undercut the floor. |
| 09 | Fixed | Material throttling is applied per consuming project, not globally. Covered by `test_complaints_09_16`. |
| 10 | Fixed | `capacity` is listed in `help commands` and distinguishes annual throughput from durable stock shown by `materials`. Covered by `test_complaints_09_16`. |
| 11 | Fixed | Nitre advice derives bed area from the live deficit plus a stated 20% buffer instead of recommending a fixed 20,000 m². Covered by `test_complaints_09_16`. |
| 12 | Fixed | Institution capacity is conditional on the institution running, and staffing/capacity reports expose its contribution. Existing people/capacity regressions cover the grant. |
| 13 | Fixed | Advanced ventures require an appropriate specialist foreman with bounded FTE; generic artisans and unrelated specialists cannot substitute. Covered by `test_complaint_13_specialist_supervision`. |
| 14 | Fixed | A zero-cost, zero-hour, zero-risk, zero-floor capability completes immediately on `start`. Covered by `test_complaints_09_16`. |
| 15 | Fixed | Credit forecasts expose both `interest_rate_percent` and calculated `estimated_annual_interest`. Covered by `test_complaints_09_16`. |
| 16 | Fixed | Affordability uses the shared committed-spend/funding-capacity rule and distinguishes the strict start limit from forecasts. Covered by the affordability regression suite. |
| 17 | Fixed | Mortality deficits immediately update the wage index used by hiring. Covered by `test_complaints_17_24`. |
| 18 | Fixed | `population` shows current population separately from the pre-simulation reference population. Covered by `test_complaints_17_24`. |
| 19 | Fixed | `risk` identifies staff loss as an annual wave and reports remaining checks and cumulative chance. Covered by `test_complaints_17_24`. |
| 20 | Fixed | Training says it finishes during the named year's annual resolution and joins staff immediately afterward; resolution occurs before that year's work allocation. |
| 21 | Fixed | Bare `rush` is non-mutating preview; `rush force` is the explicit action. Covered by `test_complaints_17_24`. |
| 22 | Fixed | Phrase search matches normalized words without requiring adjacency and includes legal lapping-plate work. Covered by `test_complaints_17_24`. |
| 23 | Fixed | High-pressure engines require the safe-steam chain, thermodynamics, and bulk steel. Covered by `test_complaints_17_24`. |
| 24 | Fixed | The Brayton turbine requires thermodynamics, compressor/jet concepts, hot alloys, and suitable tooling. Covered by `test_complaints_17_24`. |
| 25 | Fixed | Wages derive visible food, housing, tools, skill/difficulty, demographic scarcity, and local trade scarcity components. Covered by `test_dynamic_wages`. |
| 26 | Fixed | Farm, housing, and named trade-school investments are actionable; population connects national/reachable/employed counts; durable material stock can be inspected, bought, and sold. Covered by `test_economic_levers_inventory`. |

## Audit result

All 26 reported behaviors now have an implemented resolution. This pass found
one remaining defect in the resolution itself: complaint-focused tests 09–26
were not registered in the full-suite topic list, so a normal full run skipped
them. The runner now imports those modules, and complaint 10's promised
discoverability is explicitly asserted rather than inferred from the command's
existence.
