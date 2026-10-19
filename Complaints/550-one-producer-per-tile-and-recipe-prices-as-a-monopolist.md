# One producer per tile and recipe prices as a monopolist

**Status:** partly fixed (entrants only; the opening's producers still count as one workshop)

Found by an outside reviewer reading the repository; checked against the code.

- `entry_year.py` (`sim/economy/`): a newcomer to a recipe already worked on a tile joins that tile's
  producer's capacity, so one producer stands for every workshop of that recipe there.
- `seller_pricing.py`: a seller that moves the clearing price picks a profit-maximising reservation
  against the rest of the book (dominant-firm pricing).
- Together: a hundred grain farms are one seller that withholds supply against its residual demand,
  and entry adds capacity without adding a competitor. Concentration comes from the aggregation, not
  from economics. Competition from other tiles and other recipes remains.

## What it would take

- Either an aggregate that offers a competitive supply schedule (its members' costs, each a price
  taker), or several independent firms per market with their own cash, capacity, expectations, entry
  and exit; strategic pricing only for a producer that really is one owner.
- A test: splitting one aggregate into many identical small producers leaves the clearing price and
  quantity unchanged within a tolerance.

## Resolution

`Producer.workshops` counts the independent workshops a producer stands for (entry_year.py adds one per newcomer that joins it). `seller_offers.stands_for_many` treats a producer with more than one as a crowd of price takers: it keeps its price-taking reservation and does not search for a profit-maximising reservation or raise its ask. Defensible because workshops joined are separate owners in effect, each too small to move the price, and each unit then sells at the price-taking reservation (its holding value), the competitive schedule. A producer with one workshop (a founder, a firm, a lone owner) stays strategic. Test: `sim/tests/test_economy_aggregate_producer_pricing.py`. Remaining: opening producers that stand for many workshops still count as one.

Open: opening producers (opening.py `_add_producers`) stand for a whole tile of workshops but start at one. No workplace size exists in the recipe, sites.py or setup (workplaces are named only in comments); deriving one needs a crew or plant-scale datum per recipe, and a labour-years proxy would make a single large mine or furnace look like a crowd. Needs that datum first.

## Workplace sizes: built, measured, reverted

Per-recipe establishment sizes (branch `fix-550-workplace-size`) let the opening count each producer's workshops,
and a crowd's offer as a rising schedule over its workshops' costs (branch `fix-550-supply-schedule`). Measured on
Rome, prices of most main goods moved nearer their cost, but the founder's market rate at a test opening rose
several-fold (savings offered fell and loans asked rose; not traced), a thin sited iron-ore market kept a
scarcity price far above cost, iron opened at its floor, and `economy_innovator_pricing` swung with the schedule's
slicing. The merge is reverted on `economy-accounting-and-speed`; both branches are kept. Entry aggregates still
price as takers.
