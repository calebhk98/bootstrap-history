# A fantasy equipment mod should price itself from recipes and needs

**Status:** open - an acceptance test, to be worked last, after the other open issues

Stakeholder request, framed as a test of CLAUDE.md 4.3, 4.5 and 4.7. Build a mod that adds the adventuring
equipment, weapons, armour, food and lodging of a tabletop fantasy setting, with its coin and a map, and
check that the game prices every item and runs without engine edits. The setting's own list prices are
balance figures, not physics, so the test is that the engine produces a price for each item from what it
takes to make it and what it is wanted for; the derived prices are expected to differ from the book's.

Use the System Reference Document 5.1 equipment tables (released under CC BY 4.0, with the attribution the
licence asks for) as the item list, and an invented map: the published campaign-setting maps are not under
an open licence, so they must not be copied into the repository.

## What the mod would contain

- Coin: copper, silver, gold and platinum pieces as a civilisation's currency (`currency_words`, and units in
  `data/world/units.json` through the mod's own `data/world/units.json`).
- Materials and production entries (`data/production/*.json`, schema in `data/production/_SCHEMA.md`) for each
  item: candle, rope, lantern, oil flask, rations, bedroll, staff, quarterstaff, longsword, chain mail, plate,
  and so on, each with sourced or labelled inputs and labour.
- Needs and goods (`data/world/needs.json` in the mod) saying what each item is for, where it is bought by
  households.
- A civilisation file and a small map, including taverns, temples and other places that consume goods.

## Questions the test must answer, each with a measurement

1. Does every item get a price on the agent economy, and on the price solver, with no price table and no
   engine edit? Which items fail, and why (an item with no recipe, a recipe whose input has no producer, a
   good with no need)?
2. Is the price the cost of making it, or a scarcity price, and does that match the item's supply?
3. Light. Today light is folded into `warmth_and_light`, measured in megajoules of fuel heat
   (`data/world/needs.json`), so a candle is worth its heating value and nothing for the hours of light it
   gives. There is no candle good in the base data (only wax and wick inputs in
   `data/production/40_organics.json`). A candle's worth should come from burn time and light, without a
   rule that names candles.
4. Institutional consumers. A tavern that lights candles for its customers, or a temple that burns many,
   should demand them because the service it sells or the rite it performs consumes them through its
   recipe or its upkeep, not through a rule naming taverns or temples. Clergy and temples as actors with
   endowments are not modelled yet (`Complaints/110`), so this part may need that first.

## How to close it

The mod loads, `python3 sim/simulator.py validate` passes with it, a short test (under thirty seconds,
building the smallest game the mod allows) asserts that every item has a finite positive price and that
candles are bought by households and by at least one non-household consumer, and every gap the test
found is either fixed in the engine generically or filed as its own issue.
