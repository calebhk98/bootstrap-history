# Most ancient occupations have no trade, and their hours are booked as farming

**Status:** open - split into 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619 (closes when they do)

An outside list of the twenty commonest occupations in classical civilisations (Rome, Greece,
Mesopotamia, Egypt) was checked against the trade registry (`data/world/trades.json`) and the
`labour_hours` of `data/production/`. The list was written without reading the code; it is a
validation reference under DESIGN 4.2, not a target to hardcode.

## Covered

Grain farmer (`labourer`, owned by the farm-labour logic), fisher, miner, potter, smith, carpenter,
mason, merchant, sailor, carter, soldier, scribe. Quarrying is `mason` plus `labourer` (`stone_kg`).

## Missing

| Occupation | What the data does now |
|---|---|
| Herder, shepherd | `wool_kg`, `milk_kg`, `hide_kg` are `labourer` hours: herding is not told apart from crop farming. |
| Vine and olive tender | `wine_common_kg` and `olive_oil_kg` are `labourer` hours and land, with no inputs (no grape or olive crop, no press, no jar) and no `holding_years` for the years before vines and trees bear. |
| Spinner, weaver | `thread_kg` is `labourer`, `fabric_kg` and `linen_kg` use `artisan`, the generic craft placeholder (`legacy_trade_defaults.GENERIC_CRAFT_TRADE`). Textiles, the largest non-farm work of the period, have no trade. |
| Fuller, dyer | `cloth_kg` and `dye_kg` are `labourer` hours. |
| Tanner, leatherworker | `leather_kg` is `labourer` plus `artisan`; no shoes, harness or scabbard goods. |
| Miller, baker | `flour_kg` is `labourer` hours and is eaten as is (`data/world/needs.json` goods); there is no bread, oven or bakery. |
| Cook, tavern keeper | No prepared-food good or service, so town households without hearths are not modelled. |
| Porter, dockworker | No trade; loading at ports was not traced here. |
| Shipwright | No ship recipe; ships are a state budget line paying `carpenter` and `sailor` hours (`sim/agents/budget_lines.py`). |
| Domestic servant | No trade and no need it serves. `sim/agents/group_servants.py` is the state's office-holders and army. |
| Charcoal burner, forester | No trade; `charcoal_kg` and `firewood_kg` are `labourer` hours (forest stock is 539). |
| Salt worker | No trade; the salt recipes are `miner` and `labourer` (demand is 535). |
| Lime burner | No trade; `lime_kg` is `furnaceman` and `labourer` (fuel is 534). Glassblower exists. |
| Landowner, financier, tax farmer | Actors, not trades: 538. |
| Priest, diviner | No trade, no need for ritual, no temple object, no sacrificial animal demand. |

Goods the list names that do not exist as goods: fish (the fisher's catch is calories in
`sim/labour/food_gathering.py`, not a traded good), garum, bread, amphorae, ships.

## Why it matters

Every `labourer` hour in every recipe is dropped from the non-farm need shares
(`sim/labour/workforce_spinup.py`, `total_by_trade.pop(FARM_TRADE, None)`). Spinning, fulling,
dyeing, wine, oil, brick and milling labour therefore never shows up as a non-farm trade, and the
non-farm workforce is sized from what is left: mostly furnacemen and miners. Measure:

    python3 -c "from sim.tests.harness import sim; lab=sim(civ='rome_100ad').labour; print(sorted(((round(v,3),k) for k,v in lab._non_farm_need_shares().items()), reverse=True))"

At the Rome opening furnacemen and miners together take more than half of non-farm need, and the
country holds far more furnacemen than masons or potters (`lab.population_report()['trades']`).
Historically textiles, building and food preparation were the largest non-farm employers.

The farm share is also far below the reference's 80 to 90 percent:

    python3 -c "from sim.tests.harness import sim; print(sim(civ='rome_100ad').labour.farm_share_of_hours())"

The two are different measures (hours needed to grow the food against where people lived and what
they called their work), so the gap is not by itself a defect. It is the seasonal by-employment the
real peasant household did (spinning, weaving, herding, carting, building), which the model has no
place for. Related: 513 (farm labour sized exactly to feed the people), 434 (need shares).

## What it would take

- Trades in `data/world/trades.json` where skill, training or danger differ: weaver, fuller/dyer,
  tanner, herder, miller/baker, cook, shipwright, porter, domestic servant, priest. Data only: the
  registry is read without code (4.7).
- Re-book recipe hours from `labourer` and `artisan` to those trades, and add the missing chains:
  bread from flour, fuel and an oven; fish as a good from the fishery; garum; amphorae; ships.
- Separate the farm trade from the unskilled fallback trade, which are one id today (`FARM_TRADE`
  is `labourer`), so processing and herding hours stop counting as farming.
- Owner decision: whether domestic service and religion become needs in `data/world/needs.json`
  (a household that buys service, a society that pays for ritual), or stay out of scope.
- A baseline check under 4.2: the occupational distribution of a Rome run falls in a plausible
  range (most households on the land, textiles and building among the largest non-farm trades).

## Regional divergences (second note from the same source)

- **Mexica porters.** Land carriage on foot is a route mode (`sim/geography/routes_rates.py`,
  `_porter`), but its hours are `labourer` (the `carter` note in `data/world/trades.json` says
  "porters on foot stay labourers"). In a society without draught animals, porters were one of the
  largest labour groups and the hiding above makes them invisible.
- **Obsidian and flint knappers.** `mat_obsidian_blade` is a tree node (`data/branches/00_core.json`)
  with no recipe, no obsidian good and no knapper trade. The `implements_and_arms` need lists only
  metals (`data/world/needs.json`), so Mexica tools have no stone route. Whether Mexica households
  can buy the metals was not checked.
- **Han salt and iron monopolies.** Stated only in prose (`han_china_100ad.json`, the state and
  requisition notes); its `state_monopolies` lists only silkworm eggs, and a monopoly there only keeps
  a good from export (`sim/agents/policy.py`). State works, mine revenue and the state's iron
  workforce are Complaint 492.
- **Seasonal labour and corvée.** The flood or winter slack season, when farm hands built canals and
  monuments under corvée, has no place: farm labour is a yearly total, and corvée exists only in
  Han prose. This is the same gap as the by-employment above.
- India (caste, cotton weaving) and Egypt have no civilisation in `data/civilizations/`; nothing to
  file until one is added.

## Moved from 535: salted fish

Once a fish good exists, add a salting recipe (fish and salt in, a keepable good out) and a spoilage row in `data/world/spoilage.json` far below the fresh fish's, as `salted_meat_kg` does for meat. Salt is already a need and an input to cheese and salted meat.

## Sizing (no change made)

List the candidates with one pass over `data/production/*.json`, filtering `labour_hours` for `labourer` and `artisan`;
most such entries are extraction and chemistry, out of scope here. The complaint's rows split into:

- **Data only, sourceable:** spinner and weaver (thread, linen, fabric, canvas, felt, sailcloth, twine, cordage,
  backstrap fabrics), fuller and dyer (cloth, dye), tanner (leather, vellum, parchment), charcoal and lime burner,
  salt worker, herder (wool, milk, meat, herd and draught animals), miller (flour variants). Each needs a trade in
  `data/world/trades.json` (training, tool basket, fatality source) and the hours re-booked with a source.
- **New goods and research:** grape and olive crops with presses, jars and `holding_years`; baker and bread; a fish
  good with salted fish and spoilage (from 535); garum; amphorae; shipwright; leather goods.
- **Owner decision:** cook and tavern keeper, domestic servant, priest and diviner each need a need or good.
- **Engine:** porter and dockworker live in the route modes (`sim/geography/routes_rates.py`); `FARM_TRADE` and the
  unskilled fallback are both `labourer` in `sim/labour/legacy_trade_defaults.py` and must be separated.

## Split

Children, in order of work:

- 609: The farm trade and the unskilled fallback trade are one id, so processing and herding hours count as farming
- 610: Spinners, weavers, fullers and dyers have no trade, though textiles were the largest non-farm work
- 611: Herders and millers have no trade: herding is not told apart from crop farming
- 612: Tanners, charcoal burners, lime burners and salt workers have no trade, and leather has no goods
- 613: Porters and dockworkers have no trade, so the largest labour group of a society without draught animals is hidden
- 614: There is no bread, oven or bakery, and no cooked food at all
- 615: Fish is calories, not a good, and there is no salted fish or garum
- 616: Wine and olive oil have no vine or olive crop, no press and no jar, and no years before trees bear
- 617: Ships have no recipe and no shipwright: they are a state budget line paying carpenters and sailors
- 618: The implements need lists only metals, and obsidian blades have no recipe, good or knapper
- 619: No check that the occupational distribution of a baseline run is plausible

Kept here as decisions, not work: whether domestic service and religion become needs (owner decision), and cook, tavern keeper, servant, priest and diviner, which wait on it. The Han salt and iron monopolies are 492; seasonal labour and corvee are 542 and 600.

## Owner decision (2026-10-20)

Domestic service, cooks and tavern keepers come from household work as a need met by own hours or hired (645).
Religion is out of the base game and left to mods (`mods/TASKS.md`); priests and diviners wait on a mod.
