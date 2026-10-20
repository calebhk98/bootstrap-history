# Household work is not a need, so there are no servants, cooks or taverns

**Status:** open

Owner decision (530, 2026-10-20). Cooking, fetching water and fuel, cleaning, grinding and childcare take hours every
household spends. Nothing in `data/world/needs.json` or the household model books them, so domestic service, cooks and
tavern keepers have no demand, and their hours sit in the generic `labourer` pool (619).

What it would take: a household-work need met by the household's own hours or by hiring, the same choice as own-plot
growing (`sim/economy/households_own.py`), so a richer household hires more as its own hours are worth more. Cooking
needs a hearth and fuel; a household without one (urban tenancy, 551's endowments) buys cooked food, which is the
demand for cooks and taverns. The hours a household needs come from a source (time-use studies), not a typed share.
Land after the opening settles (473), since a new need moves the opening's demand. Tests: a richer cohort hires more
household work; a cohort without a hearth buys cooked food.

Religion as a need is out of scope by owner decision; it is a mod (`mods/TASKS.md`).
