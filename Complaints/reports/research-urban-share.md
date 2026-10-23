# Research: what sets a pre-industrial urban share, and how to make it emerge

Prepared for Complaint 603 (urban share is a fixed `urban_fraction` per civilisation). Research only; no code changed.

## Sourcing key

Complaint-wide rule (CLAUDE.md section 6): cite only what was opened.

- **[O]** opened this session and the figure read in the fetched text (a PDF converted with `pdftotext`, or a page fetched and summarised by the fetch tool).
- **[S]** seen only in a search-result summary; the page itself was not opened. Treat as a lead to verify, not a citation.
- **[W]** read on Wikipedia (an [O] of a tertiary source, which in turn cites the named author; the author's own text was not opened).
- **[N]** no source found.
- **[D]** a derivation by the author of this report, not a sourced fact.

Nothing here was recalled from memory without a tag. Limits of the session: JSTOR, Cambridge Core book pages and the Hanson/Scheidel full texts could not be read, so most scholarly figures reach this report through one intermediary. Thresholds differ between sources (towns over 5,000, over 10,000, or any walled place); a validation band must name its threshold.

## 1. How the simulator holds urban share today

- `urban_fraction` is a number typed into each file in `data/civilizations/`: Rome 0.12, Han China 0.10, England 1300 0.12, Norse 900 AD 0.03, Mexica 0.25 (grep of `data/civilizations/*.json`). The schema file lists it under "demography" as an initial condition. None of the lines grepped carries a source for it; Mexica 0.25 has [N] below.
- Consumers: `sim/labour/labour_population.py` (town people by trade, farmers = working people times one minus the fraction), `sim/agents/strata_seed.py` (strata split), `sim/disease/nation.py` and `sim/engine/disease_port.py` (crowding index), `sim/engine/agents_port_budget.py`, `sim/agents/country_view.py` (urban people).
- Complaint 603 already gives people per tile (`state.population.regions`), migration between bordering tiles by the labour market's `move_shares`, and per-tile food eaten over need. Its "still open" list names urban share from the regions.

## 2. Findings

### 2.1 The food-surplus ceiling (what bounds urban share from above)

- Wrigley's argument as reported in a chapter of *The Path to Sustained Growth*: the proportion in towns is a reliable measure of agricultural productivity, and urban growth is possible only if productivity yields a growing surplus above rural needs. The same passage cites Bairoch's estimate that the maximum share in towns of 5,000 or more was 13 to 15 per cent. [S] (search summary of the chapter; the 1985 article "Urban growth and agricultural change", J. Interdisciplinary History 15(4), 683-728, was not opened).
- Bairoch: traditional societies reached their maximum urban share quickly and levelled off at 8 to 15 per cent. [S] (secondary summary; Bairoch's own text not opened).
- Allen (2000, *European Review of Economic History* 4(1)) builds agricultural employment shares from total, urban and rural population, i.e. uses urban share to infer farm labour share. [O] (abstract on ORA). Clark's lecture chapter makes the same link: in the modern world urban share and share in primary production track closely, so one infers the other. [O] (his chapter 4 text, `pdftotext`).
- Clark: about 70 to 80 per cent of the population labored on the land in agrarian economies, and about 80 per cent in the poorest peasant economies. [O]
- Wrigley, as relayed: by 1800 only about two-fifths of the adult male labour force in England worked in agriculture, while population rose more than fourfold from 1600 and stayed largely home fed. [S] (search summary, itself flagged as a secondhand quotation).
- [D] The identity underneath: with food per farm worker F (kcal a year), food each person eats E, and a share f of the food that reaches town (not eaten by farmers, not lost, not seed or rent to rural non-farmers), the urban share cannot exceed (F/E - 1) times the farmer share, times f. It is a ceiling, not a prediction: cities sit below it when demand or transport, not surplus, is the limit.

### 2.2 Transport cost of grain (what bounds the reach of a city)

- Sea transport was 50 to 60 times cheaper than land, per Keith Hopkins. [W] (Wikipedia "Economy of ancient Rome"; Hopkins not opened). River figures: [N].
- Scheidel (2013, ORBIS price paper): the Diocletian edict's sea freight rates track sailing time, and its land and river rates "show no appreciation of varying contexts"; the river rates look compatible with real Egyptian freight rates in wheat equivalent. [O] (`pdftotext` of the paper). The numeric land-versus-sea ratio from the edict itself: [N].
- Von Thunen: rent falls with distance by freight rate times distance; bulky or perishable goods ring close, grain further out, ranching outermost. The page gives no freight numbers. [W] (Wikipedia "Von Thunen model").
- Mexica: overland hauling limited city size in Mesoamerica, while canoes and chinampa canals escaped the limit and provisioned the city. [S] (search summary, no named author).

### 2.3 Urban mortality and migration

- Cities were net population sinks in pre-modern conditions and relied on constant immigration. [W] (Wikipedia "Demographics of the Roman Empire").
- Rome: the "urban graveyard" model is debated. Tacoma (in *Moving Romans*) says applications to Rome treat it as an iron law and finds the classic and the lower-migrant-fertility versions both fit, implying fairly high immigration; Lo Cascio (2016) argues the effect mattered less than commonly held. [S]
- London: burials exceeded baptisms (1735: 16,691 baptisms, 23,707 burials), and about half of England's natural increase was absorbed by London deaths in the century before 1750. [S] (source not named in the summary). The often-quoted "one adult in six" and "8,000 migrants a year" were looked for: [N].
- [D] For the model: an urban population in equilibrium needs a net inflow equal to the excess of urban deaths over urban births. Crowding raises disease mortality; the simulator already has `crowding_index(urban_fraction)`.

### 2.4 Market access, city-size distributions, existing models

- Christaller central place theory: threshold and range set the settlement hierarchy; K=3 (marketing), K=4 (transport), K=7 (administrative) nesting; assumes a flat uniform plain with cost proportional to distance. [W]
- Zipf: rank-size observed by Auerbach (1913) and popularised by Zipf; Gabaix 1999 gives an explanation (not read); recent work disputes its relevance, and a Yule-Simon (preferential growth) distribution fits better in some studies. [W] (the page does not describe Gabaix's argument; do not cite him for the mechanism).
- Krugman (1991, JPE): a country splits into an industrial core and an agricultural periphery depending on transport costs, scale economies and the manufacturing share. [S] It models manufacturing agglomeration, so it fits a trade-and-industry city better than an agrarian-state capital.
- SIMPOP and SIMPOP2 (Pumain, Sanders and colleagues): multi-agent models where each settlement is an agent; rules move a system from scattered farming villages to a hierarchical urban system; drivers are transport speed and connectivity. [S]
- Desmet and Henderson, and a Malthusian-urbanization model beyond a title: [N]. (Oddo and co-authors on Genoa 1300-1800, "Malthusian urbanization": high urbanization with Malthusian stagnation. [S])

### 2.5 State and elite spending as city demand

- Rome: the grain dole served about 200,000 male citizens under Augustus and was 15 to 33 per cent of imported grain in the early Empire (Kessler and Temin); annual imports: Rickman 40 million modii (about 272,000 tonnes), Erdkamp at least about 150,000 tonnes, Mattingly and Aldrete about 237,000 tonnes for a million people; Egypt (largely tax grain) and Africa the main sources; most grain moved as a commodity on loans (Casson) or with senatorial investment (Kessler and Temin). [W] (Wikipedia "Cura Annonae", citing those authors; none opened).
- Rome's size: conventionally about 1 million in the 1st and 2nd centuries [W]; Scheidel: about 1.5 million in the five largest cities of the Greco-Roman world by the 2nd century [O] (Hanson and Ortman's quotation of Scheidel 2007, first page of JRA 30).
- China: the Song capitals reached about 1.4 million (Kaifeng) and 1 million (Hangzhou), yet urbanization "rarely exceeded ten percent". [W] (Wikipedia, source unnamed; fetch covered only the first 100,000 characters).
- [D] A capital is mostly a demand shock: taxes in kind or money are spent in one place, so the city is sized by revenue and the cost of carrying it, not by local surplus. The national ceiling in 2.1 still applies.

## 3. Validation bands by civilisation (threshold stated)

| Civilisation, period | Band | Threshold | Source | Depends on |
|---|---|---|---|---|
| Roman Empire, 2nd century AD | 10 to 15 per cent (7 to 9 million urban of 59 to 72 million) | towns, roughly over 5,000 | Scheidel 2007, quoted in Hanson and Ortman, JRA 30 [O] | surplus, sea transport, annona |
| Roman Empire, newer estimate | about 14 million in about 600 cities over 5,000 [W]; one secondary source reads that as 25 to 30 per cent [S], Wikipedia as "a quarter or a fifth" of the total [W]; not agreed | over 5,000 | Hanson 2016, Hanson and Ortman 2017 | as above |
| Italy under Rome | no opened figure; 32 per cent on an unsourced Wikipedia mention, Morley 25 per cent excluding Rome and nearly 40 per cent including it [S] | mixed | not verified | annona, port access |
| Han China, 2 AD | [N] for a national share. Chang'an about 250,000, Luoyang (Eastern Han) about 500,000, census 57.6 million [W] | n/a | Wikipedia "Economy of the Han dynasty" | state revenue, canals |
| China, Song to Ming | "rarely exceeded ten percent" [W]; Xu, van Leeuwen and van Zanden (2018): fell from 11 to 12 per cent to 7 per cent in the late 18th century [S] | not stated | as cited | state, water transport |
| England c.1300 | up to about 15 per cent in towns (Britnell; Dyer would go further) [S]; all Europe under 5 per cent in 1300 for towns over 10,000 [O] | any town / over 10,000 | Cambridge Urban History conclusion [S]; de Vries via Clark ch.4 [O] | surplus, wool, river trade |
| England 1500, 1600, 1700, 1800 | 3.1, 5.8, 13.3, 20.3 per cent | over 10,000 | de Vries (1984) pp. 39-43, via Clark [O] | London, coal, sea |
| Europe, same dates | 5.6, 7.6, 9.2, 10.0 per cent | over 10,000 | same [O] | as above |
| Netherlands, same dates | 15.8, 24.3, 33.6, 28.8 per cent | over 10,000 | same [O] | trade, water |
| Italy, same dates | 12.4, 14.7, 13.4, 14.4 per cent | over 10,000 | same [O] | trade, surplus |
| Italy, early 1300s | 18 per cent against a European average of 5.3 (Malanima 2009, cited by Chiarin and Marzano); Centre-North peak 21 per cent in 1530, low 15 per cent in 1670 | over 10,000 | CESifo WP 5038 [O] | trade, rural productivity |
| Scandinavia, Viking Age | barely over 0.5 per cent | towns | Helle, Cambridge History of Scandinavia, chapter summary [S] | no state, few markets |
| Scandinavia, end of the high Middle Ages | about 3 per cent in Sweden and Norway; only Denmark may exceed 5 per cent | towns | same [S] | as above |
| Mexica 1500 | Tenochtitlan 150,000 to 250,000 (Seshat), 75,000 to 95,000 (Jimenez Martinez 2022), Valley of Mexico 1 to 1.2 million, Texcoco about 25,000 [S]. National share: [N] | n/a | search summaries | canoe transport, tribute |

Notes: typed Rome 0.12, Han 0.10 and England 0.12 sit inside the bands. Norse 0.03 is high against the only Viking Age figure seen (about 0.5 per cent) and matches the later medieval one (about 3 per cent); check which date the file means. Mexica 0.25 has no source. A baseline is validated against ranges and relationships (CLAUDE.md 4.2), never to a point.

## 4. How to model it

| Mechanism | Simulator has | Lacks |
|---|---|---|
| Food per farm worker and the ceiling | `sim/geography/food_capacity.py` returns kcal and people supported per tile by source; the farm model gives crop kcal per hectare | A per-tile surplus after farmers' need, seed and rent, offered to a settlement |
| Grain carriage cost per tonne-km, land and water | `sim/geography/freight_cost.py` (carrier capital, feed, crew, return leg), `routes_*`, `sea_freight.py`, `carriage_reach.py`, `cargo_cost.py` | A catchment: tiles whose surplus a town can afford to pull, given freight cost against the grain price |
| Von Thunen rings | The two rows above | Rent by distance is not computed; it falls out of a catchment calculation if grain is cleared by place |
| Migration | Per-tile people (603); `sim/labour/market/migration.py` moves workers toward better real income, a day's march costed | Rural-to-urban moves; a tile has three age bands and no urban band |
| Urban mortality | Per-tile mortality via nutrition; `crowding_index` in `sim/disease/nation.py` takes the national fraction | Density-dependent mortality by tile (603 notes endemic disease is still national) |
| State and elite spending | State budget and tax (`sim/agents/`), strata | A capital that receives tax grain and spends it; the annona as an ordinary state purchase at a port |
| City-size distribution | Named tiles; Complaint 536 says tiles are too coarse for a market town | Sub-tile settlements; Complaint 634 (a tile's town population) is related |
| Central place structure | Routes graph, labour market areas | Markets as places; emergent only if towns exist as entities |

Proposed design, cheapest first.

1. **Derive urban share per tile from the surplus ceiling.** A tile's urban population is limited to what its catchment's surplus feeds. Catchment: tiles within the distance where freight cost per tonne equals a set share of the grain price, by the cheapest of land, river and sea carriage already in `freight_cost.py`. Tile surplus: `food_capacity` kcal minus farmers' need, seed and rent. The nation's urban share is the sum over tiles; the civilisation file keeps only the starting tile populations, which are an allowed initial condition under 4.1.
2. **Make migration the mechanism.** Add an urban band to the tile's people. Rural workers move to a town tile when real income there (wage over subsistence, already scored by `move_shares`) beats rural, until the landed food price or the mortality penalty cancels the gain. The urban graveyard then emerges: deaths exceed births in town and inflow holds the size.
3. **State demand as a buyer.** Tax grain and state spending at the capital pull surplus across the catchment, the annona and the Song capital. It uses the same purchase and freight rules, so any actor can do it (CLAUDE.md section 2).
4. **Validate against distributions:** national share inside the section 3 band across seeds; rank-size slope over towns as a check, not an input; share rises when freight cost falls (a river or sea route) and falls when a plague or crop failure cuts surplus.

Heuristics to label (4.4), each needing a `retire`: the freight-to-price cap that defines a catchment, the urban mortality multiplier by density, any town-size threshold.

## 5. Recommendation for 603

- Keep `urban_fraction` in the civilisation files for now only as the **initial condition** and as the **validation target for the starting year** (section 3 bands). Add source and confidence for each; for Mexica record that no source was found.
- Do "urban share from the regions" as step 1: compute each region's urban people from the surplus it can send to a town within carriage reach, and put the readers of `civ["urban_fraction"]` (`labour_population.py`, `strata_seed.py`, `agents_port_budget.py`, `disease_port.py`, `country_view.py`) behind one function so they change in one place. That function is also the regression test the complaint asks for: two regions of unequal food, urban share read from the regions.
- Defer steps 2 and 3 (urban band with migration, the state as a buyer) to separate complaints; they depend on 536 and 634.
- Test the rule directly: build a catchment by hand and check the ceiling (a tile with no surplus feeds no town; halving freight cost enlarges the catchment). Measure baseline shares with a test or a `simulator.py` subcommand, not a script (CLAUDE.md section 5).
- Before relying on any band, open the primaries: Hanson 2016, Scheidel 2007, de Vries 1984 appendix and Malanima 2009 were read only through intermediaries here.

## 6. What had no source

- A national urban share for Han China (any Han or Tang figure); only Song to Qing, from a search summary and a Wikipedia line.
- A national urban share for the Mexica, and the typed 0.25.
- A reliable Italy-under-Rome figure.
- The numeric land versus sea ratio in Diocletian's edict; river freight ratios.
- Wrigley's own 1985 text and Bairoch's own text (13 to 15 and 8 to 15 per cent are secondhand).
- Rome's annual immigration need; London's "one in six" and "8,000 a year".
- Desmet and Henderson, and any Malthusian-urbanization model beyond a title.
- The Norse sub-period split (Viking Age against later) beyond the chapter summary.

## 7. Review note

A second reader opened the Cambridge Core page of Hanson and Ortman (JRA 30, doi 10.1017/S1047759400074134): it shows
the quotation of Scheidel on the five largest cities, but not the 10 to 15 per cent empire-wide share given in section 3.
Treat that row as a lead until the article's text (or Scheidel 2007) is opened and the page recorded.
