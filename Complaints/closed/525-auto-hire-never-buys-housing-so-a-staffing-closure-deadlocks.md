# Auto-hire never buys housing, so a staffing closure can deadlock a rich household

**Status:** closed (auto_hire and its replace-only mode hire through `Labour.hire_buying_room`, which buys room through the `buy housing` price and purchase budget when `hire` is refused only for room; tests in `auto_hire_buys_room`; the `arrears_hours` housing fixture is gone)

Found fixing `arrears_hours` (merge fix-round-regressions-3): when attrition shuts a concern for want of staff and the
household has no supervision room left (the shut concern carried it), `hire` refuses and `auto_hire` never buys
worker housing (`worker_housing_places`) to make room, so nothing reopens, even for a household holding a large
purse. The topic's fixture now hands the household housing to exercise its claim.

What it would take: when auto-hire is on and hiring is refused only for want of housing or supervision room, the
policy buys the room it needs if the purse allows (through the same quote a player sees), then hires. Test: the
`arrears_hours` scenario without the housing fixture reopens its closed concerns once the household can pay for room.
