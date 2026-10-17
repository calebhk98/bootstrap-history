# One producer per tile and recipe prices as a monopolist

**Status:** fixed (see Resolution)

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
