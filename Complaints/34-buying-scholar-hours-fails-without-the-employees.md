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
