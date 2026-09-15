# Rome blind-playtest issue summary

The playtest was broadly positive: the player found the game unusually legible, physically grounded, strategically deep, and well suited to a text-first interface. Failures were generally considered fair when risk was shown, and the strongest systems were institutional capability, labor churn, diffusion, calendar floors, and material/precision gates.

The issues fall into four groups.

## Fix first: reproducible defects

1. **Global material throttle — critical.** A shortage of one resource slows every active project, including unrelated projects. It reproduced with saltpetre (all work at 5%) and copper (all work at 60.5%). Material constraints should apply only to consuming projects or real shared facilities.
2. **Expected completion-time math — high.** `expected_calendar_years_with_retries` can be shorter than an irreversible calendar floor (for example, 10-year corpus shown as 6.75 years). This is mathematically impossible under the stated rules.
3. **False specialist-hours block — high.** Projects reported machinist hours booked elsewhere while the portfolio showed spare hours and no oversubscription; the work later advanced normally.
4. **Workshop forecast contradiction — high.** The workshop was described as 0 revenue and 900 upkeep before opening, then immediately produced 1,783 revenue/year after opening.
5. **Search omission — high.** `available find` failed to return a project that `why` showed was legal to start.

## Investigate as model/screen inconsistencies

1. **Plague feedback.** The event promised decades of dear wages and a large population decline, while the economy and population screens stayed unchanged. Either the simulation is disconnected or the labels are wrong.
2. **Freedman capacity.** Opening the institution did not visibly add its promised +8 artisans; clarify whether it was already counted or not applied.
3. **Financial advice.** A loan forecast calls a percentage rate “interest per year”; the long-term “real ceiling” conflicts with the strict project-start affordability check.
4. **Institution effects.** Several technologies have both permanent completion effects and active-only effects, but the blanket “KEEP THIS OPEN” language conflates them.

## UX and command-safety improvements

- Add `capacity` to `help commands`; it is the essential material-throughput dashboard.
- Explain throughput versus inventory earlier.
- Make “waiting on money” distinguish presently unfunded work from work that can progress as income arrives.
- Make `rush` preview its starts or require confirmation; bare `rush` opened 57 projects.
- Clarify training completion timing (“finishes during YEAR,” not “ready in YEAR”).
- Make nominally zero-time projects complete immediately, or say they resolve at the next annual tick.
- Replace opaque annual-scholar and active-institution wording with explicit sources/effects.
- Scale nitre recommendations from the actual shortage instead of suggesting a vastly excessive fixed purchase.

## Balance and tech-tree review

- Generic artisans can supervise very different advanced concerns, making late operating scale cheap and specialist bottlenecks weak.
- Diversified high-margin ventures can snowball faster than wages, shocks, taxes, and political extraction constrain them.
- High-pressure steam appears to bypass thermodynamics and the main steam chain.
- Brayton gas turbines appear under-prerequisited relative to their own stated material, compressor, and thermal demands.
- Plague staff losses may repeat annually; the risk UI should state whether its number is per year, per wave, or cumulative.

## Not filed as game defects

- The player explicitly retracted a sulfuric-supply complaint after rechecking the prerequisite.
- Lost post-206 saves were attributed to the surrounding runtime remount, not the game’s save/load logic; manual save/load had worked earlier.

## Recommended work order

1. Global resource throttle
2. Expected-calendar calculation
3. False trade-hours block
4. Search omission
5. Workshop revenue forecast
6. Plague economy/population consistency
7. Freedman-capacity state check
8. Command and wording cleanup
9. Balance/tech-tree review
