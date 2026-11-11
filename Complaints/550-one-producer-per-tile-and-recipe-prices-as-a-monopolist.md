# One producer per tile and recipe prices as a monopolist

**Status:** partly - entrants join as a crowd of price takers, a lone owner prices by Eurace's grid, and a producer counts its workshops from its capacity (`workshop_count.py`, at the opening and each year's close) for a recipe with a plant, a crop (household holdings) or a herd (herder-years); a producer of a seam, pit, quarry or wood still opens as one workshop

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

## Done

- `sim/economy/workshop_count.py`: a recipe's plant parts each turn out `runs_per_year` runs (one kiln, press, loom), so one
  workshop works as many runs as its smallest part; a producer's capacity over that, rounded, at least one, is its workshop
  count. `refresh_workshops` applies it to every producer of a recipe with a plant after the opening's capacities settle and
  after each year's close writes capacity, so a shrunk producer does not keep a count from its past size. Test:
  `sim/tests/test_economy_workshop_count.py`.

- A crop with no plant counts workshops as its cropped land over a household's holding (`household_holding_hectares`: the land
  `farmland_for_population` gives `PERSONS_PER_HOUSEHOLD` people, from Columella's labour days, the harvest window and
  Laslett's household size, all already declared). A herd with no plant counts a herder's working year of its herding hours
  (`setup.working_hours_per_year`). Tests: `LandRunsPerWorkshopTests`.

## What is left

- A seam, pit, quarry or wood has nothing in the data that bounds a workshop (no crew per working, no output per pit, no
  holding of woodland), so its opening producer still counts one and only entry adds to the count. Needs a sourced crew
  or output per working by deposit class. Searched and not found: Agricola, De Re Metallica (Hoover translation, Project
  Gutenberg ebook 38015), gives the shift length (Book IV: three shifts of seven hours), the kinds of workmen, and the
  crew of one windlass (Book VI: "Two robust men turn the windlass", or one, or three at greater depth), but no number of
  men for a shaft or a mine ("the number of workmen which the mine or tunnel requires", Book IV, is left unstated); a
  windlass crew is one hoist, not a working unit, so it is not used. No source found for a quarry gang or a woodcutter or
  charcoal-burner crew in an opened text. The rule once a crew is sourced: runs per workshop = crew size x working hours
  per year / the recipe's labour hours per run (the herd rule times the crew), wired in `land_runs_per_workshop`.
- A crop's holding is the reference crop's (wheat, default toolkit); a recipe on other crops uses the same holding.

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
