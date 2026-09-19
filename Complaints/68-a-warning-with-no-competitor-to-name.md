# A project can report its trade hours booked elsewhere with nobody else drawing on them

## What the player saw

In the Mexica school project, the start/status output warned that
scholar/scribe hours were already booked by other work, while the
portfolio's own demand table appeared to show the school as the only
project consuming those trades and annual supply sufficient for the
project's yearly draw. The project later progressed.

## Verified against current code

I traced the two code paths and can confirm the START-time version of this
exact complaint has already been fixed by making it reuse `portfolio`'s own
numbers; I could not confirm or rule out the ONGOING, mid-progress warning
the player's wording ("start/status output") most closely matches, and say
exactly why below.

**The start-time oversubscription check is already fixed, and cites this
exact failure mode.** `sim/engine/proto/dispatch_ventures.py:51-82`
computes `_oversub` for the `start` command's `this_oversubscribes_a_trade`
field, and its own comment names the identical bug shape:

    # OVERSUBSCRIBED IS NOT THE SAME AS IMPOSSIBLE. The society may be
    # able to field the trade this wants and STILL not have enough of
    # it left once your own OTHER active work is already drawing on it
    # - "the first workshop/lab sat at 60% until I stopped adding new
    # work for a year"... trade_demand_vs_supply (projects.py) is the
    # CURRENT portfolio's own demand, before this project is added...
    # Same two calls `portfolio` makes to build the aggregate table -
    # reused here, not re-derived, so `start`'s warning and `portfolio`'s
    # own figures can never tell two different stories about the same year.

    _demand_now = s.trade_demand_vs_supply()
    for _trade, _plan in s.trade_draw_plan(node_id, None).items():
        ...
        _existing = _demand_now.get(_trade, {}).get("demand_hours_this_year", 0.0)
        _new_total = _existing + _plan["desired"]
        if _new_total > _supply + 1e-6:
            _oversub.append(...)

This literally cannot disagree with `portfolio`, by construction - it calls
`trade_demand_vs_supply()`, the same function `portfolio` calls, and adds
only the candidate project's own `desired` draw on top. If `portfolio` shows
a trade as fully covered before this project, and this project's own draw
still fits, `_oversub` will not fire for it.

**The ongoing, mid-progress warning is a separate mechanism**, and by my own
reading of it, it *should* also agree with `portfolio` in the single-project
case the player describes - which makes the player's report puzzling rather
than obviously explained. `lab_year_draw()` (`sim/engine/projects_progress.py:218-283`)
sets `short_of_trade`, which reaches the log as "trade hours already booked:"
via `core_step_phases.py:1366-1369`, during `_step_progress`'s priority-ordered
pass over `self.household.active`. Working through the arithmetic: each
project's `desired = min(left, ceiling)` in `trade_draw_plan`, and
`lab_year_draw` draws `min(left, ceiling, have)` where `have` shrinks only
by what earlier-processed active projects on the *same trade* already took
this year (`self.household.trade_hours_used`, reset to `{}` at the top of
every `_step_progress` call, `core_step_phases.py:1451`). If a trade has
only one project drawing on it, and that project's `desired` is already
`<= hours_you_can_call_on(trade)` (i.e. `portfolio` shows it uncontested),
then working through the inequality (`desired <= supply` implies
`drawn = desired` and `drawn/target >= 1`) `worst` should come out exactly
`1.0` for that trade, and `short_of_trade` should never be set for it. I
could not find a code path where this fails when only one project is
genuinely drawing on the trade.

What I could not rule out without running the player's actual sequence: the
`portfolio` reading and the "booked elsewhere" warning are not guaranteed to
be computed at the *same instant*. `trade_demand_vs_supply()` iterates
`sorted(self.household.active)` (alphabetical) while the real allocator uses
`active_sorted`, ranked by `self.order` and by any standing `hour_allocations`
(`core_step_phases.py:1446-1449`) - a different order, though I could not
find a reason the order itself would change which projects appear as
demanding a trade, only which gets served first when a trade genuinely is
oversubscribed. A more likely mundane explanation: a second project the
player had already started (or the un-manual director auto-started) that
also draws scholar or scribe hours, not visible in whatever `portfolio`
snapshot the player is recalling against the warning.

Status: **not reproduced this session**. The START-time instance of this
exact complaint is confirmed fixed. The ongoing, mid-progress warning
appears, by static analysis, to be mathematically consistent with
`portfolio` in the single-project case - so if the player's report is a live
defect rather than a timing/recall mismatch between two separate command
calls, I did not find where.

## Cross-references

`Complaints/07-machinist-hours-false-block.md` - the player names this
overlap themselves, correctly. `07`'s own status note already says
`craft_hands_available()` "closes the general class of bug... The specific
machinist repro was not independently reproduced this session" (from an
earlier audit). This finding is the same situation one level further in: I
can additionally confirm the *start-time* half of this class is fixed
(`dispatch_ventures.py`'s `_oversub`, above, which did not exist or was not
described in `07`'s own note), narrowing what is left unconfirmed to
specifically the ongoing `short_of_trade` warning during active project
progress. Recommend the next person to look at this reproduce with a
minimal two-step scenario: start one project needing scholar/scribe hours,
verify `portfolio` shows it uncontested, advance one year, and check whether
`short_of_trade` was set for that project in that step - which I did not do
this session because it requires driving the interactive/agent loop rather
than reading code, and effort was spent instead on the six code-confirmed
findings in this batch.

## What would resolve it

If the mid-progress warning does turn out to disagree with `portfolio` on
investigation, the fix is the same shape `dispatch_ventures.py:51-82`
already used for the start-time case: make the "trade hours already booked"
message cite the *same* `trade_demand_vs_supply()`/`hours_you_can_call_on()`
figures the `portfolio` command reports, rather than (or alongside)
`lab_year_draw`'s own internal `short_of_trade` computation, so a player can
always cross-check one against the other. This is UI/consistency work, not
a CLAUDE.md SS3.1/SS3.2 question.

## The invariant

    a project's own "waiting on trade X" message should name the same
    demand-vs-supply figures `portfolio` reports for trade X in the same
    year

Testable directly once reproduced: after any step in which a project logs
`short_of_trade` for a trade, call `trade_demand_vs_supply()` for that same
trade and assert it also shows `oversubscribed: true` for that year.
