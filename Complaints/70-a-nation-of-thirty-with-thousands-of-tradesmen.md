# Event-visible headcounts can exceed the population they are drawn from, and the likely cause is the same floor as `Complaints/58`

## What the player saw

After the national population had collapsed to extremely low values, event
text could still describe tens of thousands of staff/tradespeople affected.

## Verified against current code, and the judgement call this batch asked for

I looked specifically for an absolute-headcount event generator independent
of `population_report()` (the mechanism `Complaints/58` in this same batch
documents) and did not find one. My conclusion: **this is very likely the
same root cause as `Complaints/58`, not a second, distinct defect** - argued
below, per this audit's instruction to make that call explicitly rather
than merely filing both.

**What I checked first: does the hazard/mortality event narration itself
print absolute national headcounts?** `_shock_staff_loss()`
(`sim/engine/society_hazards.py:633-767`), the function that narrates a
plague or famine year, reports everything as *percentages*, never as raw
people counts:

    msg = "%s: %s" % (hazard.get("name", "hazard"), ", ".join(_hit))
    # e.g. "staff -%d%%" (household), and separately
    msg += (". Empire-wide, population -%d%%%s - wages ..." % (raw * 100, ...))

I read the full function and found no absolute-count formatting anywhere in
it - `%d%%` throughout, not `{:,.0f}` against a headcount. I also checked
every other file that mentions "staff", "craftsmen" or "tradespeople"
(`grep -rln "staff" sim/engine --include=*.py | wc -l` -> 42 files) for a
large-scale absolute-count message and found only household-scale figures
(single digits to low hundreds - hiring refusals, venture staffing gates,
training completions), never a national-scale count.

**The only place a large absolute trade/population count is surfaced to the
player at all is `population_report()`** - `sim/engine/labour_population.py:563-637`,
the function behind the `population` command, confirmed as the sole
production call site of `reachable_trade_population()`/
`national_trade_population()`/`home_town_population_estimate()`:

    grep -rn "national_trade_population(\|reachable_trade_population(\|home_town_population_estimate(" sim/engine/proto/*.py
    sim/engine/proto/dispatch_inspection.py:531:    return {"ok": True, **s.population_report()}

That is exactly the mechanism `Complaints/58` traces in full: at
`pop_scale`'s floor of 0.05, `home_town_population_estimate()` is pinned at
14,375 regardless of how far `self.population.total` has actually fallen
(verified there against national population 30), and `reachable_trade_population()`
for common/abundant trades is pinned at roughly 100-200, regardless of what
`national_trade_population()` (which does read the real, unfloored
`self.population.total`) says the whole country holds. "Tens of thousands"
is consistent with this same mechanism read through a different trade class
or a different civilisation's own `TOWN_POPULATION_REFERENCE`-scaled figure
- the `population` command's own text presents this as a screen a player
would naturally describe as "the game telling me about thousands of people"
even though it is not phrased as a discrete "event."

I could not find a separate, independent generator of large-scale headcount
"event text" anywhere else in the engine. Given that, and given the
player's own hedge in their write-up ("this may disappear once the
local/national labor coupling is fixed"), I am treating this as the *same*
underlying defect as `Complaints/58`, observed from a second angle (a
screen the player experienced as narrative/event-adjacent rather than as
the dedicated `population` command), rather than filing it as an
independently-confirmed second mechanism. If a future audit finds an actual
event-log line with an absolute national headcount that I missed, this
complaint's own diagnosis would need revisiting - but I read every file
that plausibly could contain one and found none.

Status: **not independently reproduced as a distinct mechanism** - traced
to the same code `Complaints/58` already fixes-for; filed as instructed,
clearly marked, so the record shows both the observation and this session's
reasoning about why it is very likely one defect rather than two.

## Cross-references

**`Complaints/58-a-town-that-outlives-the-country.md`**, this same batch -
see that file's own cross-reference section, which makes the same pointer
in the other direction. Fixing `58`'s floor (whichever of the two options
that complaint lists) should, by the reasoning above, resolve this finding
too, since I found no separate code path for it to survive in. No other
open complaint in the index addresses this.

## What would resolve it

Whatever resolves `Complaints/58` - either bounding `pop_scale`'s floor to
track the real collapse, or capping `home_town_population_estimate()`/
`reachable_trade_population()`/`national_trade_population()` at the live
`self.population.total` directly - resolves this finding as well, since
every large headcount the player could have been reading traces back to
those same three functions. No separate fix is proposed here. If the "event
text" the player specifically means turns out (on a future session actually
driving the interactive loop, which this session did not do) to be a
literal log line rather than the `population` screen, the fix would instead
be to route that log line's numbers through the same, now-fixed functions
rather than reconstructing a headcount independently - but I found no
evidence such a separate line exists today.

## The invariant

    affected_national_people <= population.total
    affected_trade_people <= plausible trade population
    household staff losses <= household staff

The player's own ARCH-002 phrasing, and directly the same invariant
`Complaints/58` states for the `population` command specifically:

    home_town_population_estimate() <= population.total
    reachable_trade_population(t)   <= plausible national_trade_population(t)

If a regression test is written for `58`'s invariant, it already covers this
finding's own invariant for every headcount this session could locate. A
genuinely separate event-log test would only be needed if a distinct
absolute-count generator is found later; none was found this session.
