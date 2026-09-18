# You can buy labourer hours, but buying scholar hours fails for want of scholars

**Type:** Gameplay / economic model
**Priority:** Medium-high. It blocks a legal move a player reasonably expects to work.
**Status: REPORTED, NOT YET REPRODUCED.** Recorded from a playthrough at the
stakeholder's request, deliberately without investigating - see "Before
fixing it".

## What happens

Buying ordinary worker hours on the market works. Trying to buy **scholar**
hours to push a research project along fails, because the player does not
employ any scholars. The market will sell you unskilled labour and will not
sell you skilled labour you do not already have on the payroll.

## Why this is wrong, and not merely annoying

It is inconsistent on its face: if hours are purchasable, the reason one
trade is purchasable and another is not has to come from somewhere, and
"you have no employees of that trade" is a statement about the player's
household rather than about the market.

More to the point, it is backwards historically. A scholar, a physician or
an architect is exactly the kind of labour a pre-modern principal DID buy by
the commission rather than employ by the year - you retained a man for a
survey, a translation or a course of treatment. Unskilled field labour is
the case that was more often organised as a standing household. The model
appears to have the two the wrong way round.

There is also a plausible real constraint hiding behind the bug, and it
should not be lost when the bug is fixed: scarce skilled trades genuinely
should be hard to hire at short notice, and the same playthrough raised that
separately (`Complaints/35`, "instantaneous hiring pools" - typing `hire
artisan 25` and getting 25 master craftsmen inside one year). The right
answer is probably that skilled hours ARE buyable and are priced by their
scarcity, not that they are refused.

## Before fixing it

Reproduce it first and find out which check is failing. The stakeholder's
instruction was to record this and not work on it, so nothing here has been
run. Three things to establish, in this order:

1. The exact command and the exact refusal message, in a save that has cash
   and no scholars.
2. WHICH check refuses. A market-side check ("nobody is selling scholar
   hours") and a household-side check ("you employ no scholars") are
   different bugs with different fixes, and the message may not distinguish
   them. Search the labour and market paths rather than assuming.
3. Whether it is trade-specific or applies to every trade above unskilled.
   If unskilled is the only purchasable one, the rule is probably a single
   condition rather than a per-trade table.

Then the smallest scenario that reproduces it becomes a regression test,
per CLAUDE.md 8.

## Related

`Complaints/35` collects the rest of that playthrough, including the hiring
question above, which shares a root: the model has no notion of how scarce
a particular skill is in a particular place at a particular time.

## Traced

Reproduced against the real protocol, as the reporter would have played it:
`python3 sim/simulator.py agent --civ rome_100ad --kit equestrian` (a rich kit,
so an affordability refusal on the commission itself cannot be confused with
the bug - see "ruled out" below), one JSON command per line on stdin.

**Path to a live repro.** `calculus` (sch=2, art=0) has a five-node closure -
`sc2_notation_positional`, `arithmetic_positional`, `algebra_symbolic`,
`geometry_analytic`, `calculus` - reachable from the start with no employees
at all, and every node up to `calculus` needs at most 1 scholar, which the
founder alone satisfies (`effective_scholars()` counts the founder as one).
`calculus` needs 2, which the founder alone does not.

**Commands and exact output**, in order, after finishing the four
prerequisites (`{"cmd":"start","id":"..."}` then `{"cmd":"step"}` until each
reports `done` on a `{"cmd":"why","id":"..."}` check):

    {"cmd":"start","id":"calculus"}
    -> {"ok": false, "error": "needs 2 trained scholars, you have 1.0 (you
        are one of them). To get more scholars: {\"cmd\":\"hire\",
        \"trade\":\"scholar\",\"n\":2} hires literate men by the year; see
        {\"cmd\":\"labour\"}; build school_founded (the school produces
        scholars in quantity, and grants more every year it runs); build
        academy_network eventually (three academies produce more than one
        school) - but it is itself waiting on scholars, so hire or
        commission first."}

    {"cmd":"commission","trade":"scholar","hours":2000}
    -> {"ok": true, "commissioned": "2000 hours of a scholar bought for
        1280 denarii", "capital": 69714.7, ...}

    {"cmd":"start","id":"calculus"}
    -> {"ok": false, "error": "needs 2 trained scholars, you have 1.0 (you
        are one of them). To get more scholars: ..."}
        (byte-identical to the first refusal)

The commission visibly succeeds - capital drops by the 1,280 denarii quoted,
`commissioned` confirms 2,000 scholar-hours were bought - and `start` refuses
`calculus` a second time with the exact same message it gave before any
hours were bought. The 2,000 purchased hours make no difference whatsoever
to whether the node can start.

(On the `--kit equestrian` run above the commission succeeds outright. A
cheaper `--kit merchant` run hit an affordability refusal on the commission
instead - "you have 177 in hand ... You are 207 short" - which is
`spending_power("buy")` in `commission()`, an ordinary and correct cash
check, not this bug. Re-running richer removes that confound, which is why
the exact numbers above are quoted from the equestrian run.)

**Which check refuses, and where.** `sim/engine/projects.py`, function
`start_reason()` (defined at line 1948), the staffing gate at line 2153:

    if node["sch"] > self.effective_scholars():
        return False, (("needs %d trained scholars, you have %.1f (you are
                        one of them). %s" % ...))

`effective_scholars()` (`sim/engine/labour.py:1674`) is
`self.household.scholars + (1.0 if self.founder_alive else 0.0)` - a pure
headcount of standing employees plus the founder. It does not read
`self.household.contract_hours` at all, so hours bought under `commission()`
never reach it.

**This is the household-side bug, not the market-side one**, and the two
are provably different code paths, not merely different messages. Twelve
lines below the scholar gate, the *artisan* gate at line 2177 reads:

    if node["art"] > self.craft_hands_available():

and `craft_hands_available()` (`labour.py:2731`) explicitly folds in
`self.household.contract_hours` for craft trades ("a year of a carpenter's
time IS a carpenter" - its own docstring), plus the comment immediately
above the artisan gate in `projects.py` records that this was *already*
fixed once for exactly this reason: "CRAFTSMEN YOU HAVE UNDER CONTRACT COUNT
TOO... work you had already paid an outside shop to do could not satisfy the
requirement - and the refusal's own advice was to go and commission it.
`commission` could not unblock the gate that recommended commission." That
history is what deadlocked the Norse `workshop_first` run in that same
comment.

**The scholar gate never received the matching fix.** There is no
`effective_scholars()`-equivalent of `craft_hands_available()` - no function
that adds `contract_hours` for scholar-family trades to the standing
headcount. The bug labour.py's `commission()`/`market_supply()` NOTE already
ruled out (Complaints/34's market side: nothing there gates on employees) is
confirmed absent; the refusal is a household-side staffing gate in
`projects.py::start_reason()` that only recognises scholars on the payroll,
exactly the asymmetry the artisan fix's own comment describes but never
extended to the other trade family.

**Not fixed here, per instructions** - scope for this trace was
`sim/engine/cli.py` and `sim/engine/data.py` only, and this bug lives in
neither. The fix, when someone takes it, is likely small and has a working
precedent to copy: give `effective_scholars()` (or a new
`effective_scholars_available()` used only at this gate, if scholars should
not always count contract hours - e.g. `venture_foreman`-style ongoing
supervision might reasonably need a standing employee rather than a one-off
commission) the same contract-hours credit `craft_hands_available()` already
gives artisans, and update this gate's own refusal message so it stops
telling a player who already commissioned the hours to go and `hire` instead.
