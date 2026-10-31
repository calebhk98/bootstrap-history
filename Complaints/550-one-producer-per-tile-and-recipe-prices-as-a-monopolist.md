# One producer per tile and recipe prices as a monopolist

**Status:** partly - entrants join as a crowd of price takers and a lone owner prices by Eurace's grid; the opening's producers still count as one workshop

Found by an outside reviewer reading the repository; checked against the code.

## What is wrong now

- The opening places one producer per tile and recipe (`_add_producers` in the opening) although it stands for a whole
  tile of workshops: `Producer.workshops` (`sim/economy/producers.py`) starts at one. Only newcomers raise it
  (`sim/economy/entry_year.py` adds one per newcomer that joins the tile's producer).
- A seller with one workshop chooses its ask by `price_setting.best_price` (`sim/economy/price_setting.py`, called from
  `seller_offers.strategic_offers`): the best price on a grid around its own, from the market's size times its logit
  share against the other sellers' asks, held inside the cost band. The whole-book search is gone. A rival that stands for
  several workshops counts once per workshop (`seller_offers.rivals_of`), so a crowd dilutes a lone owner's share.
- A producer with more than one workshop is treated as a crowd of price takers (`seller_offers.stands_for_many`): it keeps
  its price-taking reservation and neither searches nor raises. So a hundred grain farms at the opening are still one
  strategic seller, and only entry adds price takers. Concentration at the opening comes from the aggregation, not from
  economics. Competition from other tiles and other recipes remains.
- A per-recipe workplace size (crew or plant scale) does not exist in the recipe, `sites.py` or the setup, so the opening
  cannot split a producer into a crowd. A labour-years proxy would make one large mine or furnace look like a crowd.

## What it would take

- A datum per recipe class for how many independent workshops one tile stood for (a grain farm, a smithy, a mill, a mine,
  a furnace): crew size and plant scale as physical data from archaeology and economic history (for example excavated
  workshop counts, Roman Egypt and Pompeii workshop surveys, Han iron foundry sizes, Domesday mills per settlement).
  Nothing has been opened for this yet.
- Either an aggregate that offers a competitive supply schedule (its members' costs, each a price taker), or several
  independent firms per market with their own cash, capacity, expectations, entry and exit.
- A test: splitting one aggregate into many identical small producers leaves the clearing price and quantity unchanged
  within a tolerance. `sim/tests/test_economy_aggregate_producer_pricing.py` covers the crowd taking the price.
- An earlier attempt (per-recipe establishment sizes plus a rising supply schedule for a crowd) was measured and
  reverted; see `Complaints/reports/` for the trace. Measure any new one with
  `python3 sim/simulator.py spin-up-trace --civ rome_100ad --years 60`; none has been run for the Eurace price rule.
