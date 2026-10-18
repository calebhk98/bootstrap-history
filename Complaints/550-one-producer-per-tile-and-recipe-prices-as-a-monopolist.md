# One producer per tile and recipe prices as a monopolist

**Status:** fixed for the recipes that state a crew (`establishment_workers`); recipes without one still open as one workshop

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

Opening producers: a recipe may state `establishment_workers`, the crew of one workshop, farm or gang (`_SCHEMA.md`, ESTABLISHMENT SIZES, with the source and which figures are from memory). `sim/economy/establishment.py` turns it into the runs one establishment works a year (crew times hours per person-year over labour hours per run); `opening._add_producers` opens capacity over that as that many workshops, at least one. A recipe without the field opens as one. Tests: `sim/tests/test_economy_establishment_size.py`.

Measured on Rome (`ROME_SPIN_UP_YEARS=2,1`, four years, price over variable cost per unit for 19 main goods): opening producers with more than one workshop 0 before, about a third after; median price over cost 3.09, 2.57, 2.70, 2.66 before and 2.57, 2.15, 2.41, 1.85 after (years 0 to 3). Mean absolute log of price over cost, 16 of 19 goods closer to cost; wheat 4.9 to 2.8, millet 3.9 to 2.0, wine 3.4 to 1.9, thread 1.3 to 1.05 in year 0. Worse: stone, firewood and copper ore. The small fixture is unchanged within noise (its capacities are under one establishment for mines and smelters). Prices stay well above variable cost for staples, so strategic pricing was not the only cause.

Open: the figures are estimates (confidence C); sizes for the remaining recipes; stone, firewood and copper ore rose with the change and want a look.
