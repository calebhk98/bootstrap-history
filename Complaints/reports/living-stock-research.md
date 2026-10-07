# Living stock: feed, breeding loss, theft and export policy (research for Complaint 366)

Research report only; no code or data changed. Source tags: **read** (the page was opened this session and the figure seen in it), **snippet** (seen only as a search-result excerpt or in a fetch summary that did not quote the text), **recalled** (from memory, to be verified before a number is committed to data). Per CLAUDE.md 4.1 to 4.5, every mechanism below derives an outcome from biology, geography or an actor's choice; no rule reads a historical result, and the historical cases are used to test relationships, never as dated events. Numbers appear only in tables with a source and tag; measure anything else with the commands given.

## 0. What the repo does now (read from the code)

- `data/world/living_stock.json` holds one row per held material with `natural_increase`, `annual_loss`, `breeding_minimum_units` (fractions of the holding, in the material's unit, live weight for animals). `sim/world/stock_dynamics.py` `next_units` applies them as expected values; `sim/engine/living_stock_yearly.py` `step_living_stock` loops over held materials. The increase is not limited by feed, land or labour.
- The founder's ledger is `Sim.stock_held(material)` and `Sim.change_stock`. A herd has no tile and no owner other than the player, so a herd cannot draw on a tile's pasture and no other actor can hold, breed, sell or lose stock.
- Pasture is per tile: `sim/geography/food_pasture.py` `usable_forage_kg` gives dry matter per year the tile's open land offers grazers; `herd_contributions` splits it among the herd animals whose envelope fits, with one shared intake fraction per day (`food_livestock_intake_fraction_per_day`, a single value from the FAO/ILCA tropical livestock unit, graded C, from memory) and each species' `adult_mass_kg`. Herd rows exist for cattle, sheep, goat, horse, camel, yak, reindeer (`data/world/geography/resources/animals.json`); there are no rows for pig, llama or chicken.
- The export refusal is the civilisation field `will_not_sell`, read in `sim/engine/foreign_economies.py` and `civ_basket_check.py`; `Han` lists `silkworm_eggs_kg`. `sim/agents/policy.py` already has the shape a smuggling choice needs: `Option(subject, worth, cost, chance)` with `net = worth * chance - cost`, and `ValuePolicy` that takes the best net value within a budget, so a smuggling run is an `Option` and any actor (human, AI, mod policy) can be handed it.
- Existing rates, checked against the FAO traditional-systems figures in section 1 (computed with the same arithmetic the file's basis uses: breeding females share times calving rate times young survival): draught animals and goats are in range; two assumptions are not sourced (the share of the herd that breeds, and that rates by head carry over to rates by live weight, section 5 question 1).

## 1. Figures per species

Units of the target fields: `natural_increase` and `annual_loss` are per year as a fraction of the holding. Proposed new fields (added to `living_stock.json` rows when the feed stage is built): `intake_fraction_per_day` (dry matter per day as a fraction of body mass), `adult_mass_kg`, `grazed_share_by_climate` (a map from a climate class or growing-season share to the grazed share of intake), `years_to_first_yield`, `yield_per_head_year`.

### 1a. Feed (dry-matter intake)

Annual intake per head follows from one formula, so the table gives the fraction and the formula computes the rest: `intake_per_head_year = adult_mass_kg * intake_fraction_per_day * days_per_year`. Measure a species with `python3 -c "..."` over the animal rows; no number is stored beyond the fraction.

| Species | Figure | Units | Source | Tag | Target field |
|---|---|---|---|---|---|
| All grazers (reference) | 2.5 kg dry matter per 100 kg live weight per day; reference animal 250 kg | fraction of body mass per day | FAO tropical livestock unit; summarised in Frontiers Vet Sci 2020 "Tropical Livestock Units: Re-evaluating a Methodology", https://www.frontiersin.org/journals/veterinary-science/articles/10.3389/fvets.2020.556788/full | snippet | `food_livestock_intake_fraction_per_day` (existing); per-species `intake_fraction_per_day` |
| Cattle, sheep | 2 to 3 percent of live weight on average-quality pasture or hay; lactating cows 2.5, dry cows 1.5 | fraction of body mass per day | AHDB, https://ahdb.org.uk/knowledge-library/calculating-dry-matter-intakes-for-rotational-grazing-of-cattle ; Forestry Commission Scotland woodland grazing toolbox, https://forestry.gov.scot/woodland-grazing-toolbox/grazing-management/grazing-regime/season/forage-intake | snippet | `intake_fraction_per_day` for cattle (draught, dairy), sheep |
| Horse | 450 kg horse at moderate activity eats 9.0 kg dry matter per day (2 percent) | kg per day | OTCO "DMI Resources", https://tilth.org/app/uploads/2022/02/OTCO-DMI-Resources.pdf | snippet | horse `intake_fraction_per_day` |
| Goat | milking goat of 60 kg eats 3.4 kg per day (high, lactation); maintenance is lower | kg per day | same OTCO table | snippet | goat (cashmere, angora) |
| Llama, alpaca | consume 20 to 40 percent less per unit metabolic weight than sheep and goats; earlier proposals up to 3 percent of body weight | fraction | Tropentag 2023 abstract, https://www.tropentag.de/2023/abstracts/links/Goacutemez_Bravo_2blOluHR.php ; Obregon et al 2024 (INIA Peru) | snippet | llama row (new) |
| Camel | about 2 percent of body weight per day, strongly lower in dry season (low-quality browse, long water intervals) | fraction | not found this session | recalled | camel row |
| Pig | not a grazer: village pigs scavenge, eat crop residue and household waste; intake is a draw on a grain or residue pool, not on the pasture pool | kg per day | not found this session; the rearing-system literature is https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8444231/ (reproduction only) | recalled | pig row, `feed_source: residue` |
| Chicken | scavenging village birds take a fraction of intake from the ground and the rest from household grain; intake of a laying hen is of the order of a hundred grams per day | g per day | not found this session | recalled | chicken row |
| Grazed versus fed by season | In temperate Europe hay and leaf fodder carried stalled stock through winter; communities slaughtered or sold surplus in autumn to cut the number overwintered. Winter and spring feed is the binding limit on steppe herds | qualitative | Internet Archaeology 27, https://intarch.ac.uk/journal/issue27/5/3.4.5.html ; Mongolian steppe papers in the food-potential report section 2 | snippet | `grazed_share_by_climate`; `cold_months` layer (Complaint 411) |

### 1b. Breeding and loss (check of the existing rows)

The existing rows follow the form `natural_increase = breeding_female_share * young_per_female_year * (1 - young_loss)`; the check recomputes that form from the sourced values.

| Species | Figure | Units | Source | Tag | Target field |
|---|---|---|---|---|---|
| Cattle (draught and dairy) | calving rate 58.7 percent (range 28.0 to 89.9); calf mortality 21.7; adult cow mortality 6.3; replacement mortality 7.5 mixed, 6.4 pastoral; age at first calving 47.9 months; milk offtake 252 kg per lactation | fractions per year | FAO, "Production parameters of ruminants in traditional systems", https://www.fao.org/4/y4176e/y4176e08.htm | read | `dairy_cattle_kg` (already sourced), `draught_animal_kg` `natural_increase`, `annual_loss` (existing 0.2 and 0.05 are unsourced) |
| Sheep | lambing rate 109.8 percent (pastoral 96.1, mixed 114.9); prolificacy 1.12; lamb mortality 26.7 (range 6.5 to 51.5); adult ewe mortality 11.1; age at first lambing 17.5 months | fractions per year | same FAO page | read | new `sheep_kg` row |
| Goat | kidding rate 121.1 percent; prolificacy 1.34; kid mortality 27.8; doe mortality 12.2; age at first kidding 16.4 to 16.5 months | fractions per year | same FAO page | read | `cashmere_goat_kg`, `angora_goat_kg` (existing 0.3 and 0.08; adult loss in the source is higher, 0.12) |
| Small ruminants, SW Nigeria | goat litter 1.50, kidding interval 259 days; sheep litter 1.23, lambing interval 322 days; preweaning mortality up to 40 percent of kids and over 30 percent of lambs; adult mortality 10 to 12 percent a year | per year | FAO small ruminant chapters, https://www.fao.org/4/x5464b/x5464b0o.htm | snippet | cross-check of sheep and goat rows |
| Horse | foaling rate 50 to 70 percent of mares; foal mortality 2 to 33 percent in feral populations, 35 percent in traditional Gambian systems | fractions per year | rangelands and Finnish studies, https://journal.fi/afs/article/view/89440 ; https://rangelandsgateway.org/node/21436 ; Gambia figure via the same search | snippet | new `horse_kg` row, `draught_animal_kg` |
| Draught ox working life | training age 2.8 years and service life 13.8 years in Ethiopia; horse 20 to 25 years against ox 15 to 20 | years | https://sidalc.net/search/Record/dig-cirad-fr-404247 and ILRI Ethiopia oxen traction record, https://buscador.una.edu.ni/Record/CGSpace51094 | snippet | adult loss floor of `draught_animal_kg` (cull at end of work life) |
| Camel | calving interval about 2 years; age at first mating 3 to 5 years; calving rate about 50 percent; calf mortality 30 to 50 percent in East Africa, 5.4 percent in one Moroccan pastoral study | fractions per year | CIRAD Revue d'elevage, https://publications.cirad.fr/une_notice.php?dk=591642 and https://revues.cirad.fr/index.php/REMVT/article/view/9754 | snippet (the two estimates of calf mortality disagree widely) | new `camel_kg` row |
| Village pig | litter size at birth 6.8 to 8.5; litters per year 0.87 free-scavenging, 1.4 confined; preweaning mortality 15 percent, up to 50 percent, over half from crushing or starvation | per year | Reproductive performance of indigenous Lao pigs, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8444231/ | snippet | new `pig_kg` row |
| Village chicken | 30 to 60 eggs per hen per year; hatchability 82.6 percent (77 in another study); chick death 43 percent, growers 16, adults 3; main causes seasonal disease and predation | fractions per year | LRRD 14(2) 2002, https://lrrd.org/lrrd14/2/miss142.htm ; FAO W8989E04, https://www.fao.org/3/w8989e/W8989E04.htm | snippet | new `chicken_kg` row |
| Disease and winter loss | winter and spring feed shortage, and drought crashes, are the main losses in non-equilibrium rangelands; epidemic murrain is a separate shock | qualitative | food-potential report section 2 (Ellis and Swift 1988 snippet); `Complaints/reports/epidemic-model-research.md` for the shock model (not re-read here) | snippet | feed shortfall term (section 2a), not a flat rate |

Reading: the existing draught-animal and goat rows sit near the sourced values; adult loss in small ruminants is understated against the source; sheep, horse, camel, pig, chicken and llama have no row. Per head and per kilogram differ: calves, lambs and foals weigh little at birth, so a live-weight rate is lower than the headcount rate (open question 1).

### 1c. Rubber (Hevea brasiliensis)

| Figure | Units | Source | Tag | Target field |
|---|---|---|---|---|
| Propagated by seed (seed now used mainly for rootstocks) and, since the early twentieth century, by budding onto a seedling stump; green, brown and crown budding | method | Purdue NewCrop, https://www.hort.purdue.edu/NEWCROP/hort_403/pp_pdf/pp_22.pdf (the file did not open as text; the claim is from the search summary) | snippet | two rows: `hevea_seed_kg`, `hevea_budded_stump_kg` |
| Seeds are recalcitrant: lose viability quickly when drier than about 30 percent moisture; in paper bags viability lasts days; polythene bags keep it to about 180 days; room-temperature storage up to about two months | days to months | Storage behaviour of seeds of Hevea brasiliensis, https://agris.fao.org/search/ar/records/647473a5425ec3c088f34db6 ; Embrapa, https://apct.sede.embrapa.br/pab/article/view/16532 | snippet | `hevea_seed_kg` `annual_loss` close to one; the transit window is in months |
| Tapping begins about 4 years after planting under favourable conditions, often only after 6 to 9 years; high-stump budding shortens immaturity by a year and a half, to 3.5 years | years | search summary of agris.fao.org record 6472344de17b74d2224ea335 and the Purdue reading | snippet | `years_to_first_yield` |
| Seedling plantation yields 632 kg dry rubber per hectare per year at 400 plants per hectare at age 24 to 27 years; culling the worst 75 percent of plants raises it to 1288 kg per hectare | kg per hectare per year | Brazilian study, https://scielo.br/j/brag/a/LjkwGpJ6WXVd43bYvsQ7bBh/?lang=pt (summary) | snippet | yield (per tree: divide by density; not sourced per tree) |
| Yield per tree per year | kg per tree per year | not found this session; budded clones against seedlings differ by a large factor in the literature | recalled | `yield_per_head_year` |
| Climate envelope: rain 2000 to 4500 mm without a marked dry season; mean temperature 23 to 28 C, not below 20 C for more than a few weeks; humidity about 80 percent; sunshine about 2000 hours a year; best below 200 m, each further 200 m adds 3 to 6 months to reach tappable size, not advisable above 600 m | envelope | Kerala Agricultural University, https://celkau.in/crops/cashcrops/rubber/climate.php (via search summary) | snippet | new `rubber` envelope, same form as the existing species envelope (`content_rules.suitability`) |
| Seeds for Asia: about 70,000 seeds shipped from Santarem in 1876, declared as academic specimens; arrived at Kew mid-June 1876; about 2,700 germinated; seedlings dispatched to Ceylon, Malaya, Singapore and Batavia; the tapping method of Ridley made lasting latex extraction possible | counts | Wikipedia "Henry Wickham (explorer)", https://en.wikipedia.org/wiki/Henry_Wickham_(explorer) | read (counts, shipping and the licence point); the count of seedlings sent to Ceylon and the Ridley method come from search summaries | snippet | test of the seed-survival chain, section 4 |

The tree has no planted-rubber node (`mat_natural_rubber` is wild tapping of African vines) and no knowledge section on nurseries and tapping, so a rubber row needs a node and a `docs/` section first (Complaint 366 "What remains").

## 2. Mechanisms

### 2a. Feed and pasture draw

A herd needs a place before it can eat. Add `location` (a tile id, or the tile ids a holder grazes on) to each herd entry in the stock ledger; the actor decides where its herd is (as it decides where its labour is). Then, each year:

    intake_needed = heads * adult_mass_kg * intake_fraction_per_day * days_in_year
    grazed_available = share of the tile's usable forage allocated to this herd
    fodder_needed = intake_needed over the days the herd cannot graze (cold or dry months)
    fed_fraction = minimum(1, (grazed_available + fodder_held) / intake_needed)

- The tile's pool is the one proposed in `food-potential-research.md` section 4 (Rule A): forage is shared among wild grazers first, then herds (the order a parameter), then the residual. Every herd on the tile draws on the same `usable_forage_kg`, split by suitability as `herd_contributions` does now, so a herd of one actor competes with the herds of another actor and with wild grazers. The existing `food_pasture` functions already compute a carrying capacity per species; the new code only moves the held herd into that sum instead of treating the pool as free.
- Grazed versus fed: days with no standing forage come from the `growing_months` and `cold_months` layers of the food report section 2. Those days are met by stored fodder (hay, straw, leaf fodder, grain) taken from the actor's material stock, or are not met. The actor chooses how many animals to carry into the cold season: a policy decision on `Option(subject=head_count, worth=value_of_animal_next_year, cost=fodder_cost)`, which is how autumn culling falls out of a value rule and not a hardcoded date.
- Shortfall feeds back through the rates: `annual_loss_effective = annual_loss + (1 - fed_fraction) * starvation_loss` and `natural_increase_effective = natural_increase * fed_fraction`. With enough feed the base rates apply, so every existing test of the plain rates still holds. `starvation_loss` is a new row field and needs a source (section 5 question 3).
- Pigs and chickens draw on a grain and residue pool (crop residue per tile from `food_crops.py`, household waste), not on the pasture pool; the row's `feed_source` field names which pool.
- What drives the outcome: forage per tile (rain, forest share, competitors), season length, stored fodder, labour for cutting hay, the holder's culling choice. Any actor holding the herd and the land does the same thing.

### 2b. Theft, raiding and smuggling

Stock is value in a small mass that can walk or be carried; taking it is a choice an actor makes when expected gain exceeds expected cost. One option for any actor (founder, firm, state, another player):

    expected_gain = value_at_destination * quantity * survival_in_transit * probability_of_not_being_caught
    expected_cost = acquisition_cost + freight + enforcement_penalty * probability_of_being_caught
    value_gap = price_where_stock_is_unavailable - price_at_source      (both calculated; no price table)

The simulator already prices the destination side (prices are calculated; a good a partner will not sell has a high or unreachable price at home). The mechanism adds:

- **Source side.** Stock held by an actor with an export policy (2c). Taking it means either (a) buying it at the domestic price through a holder who does not obey the ban (insider, corrupt official, a caravan master), or (b) taking it by force (raid, theft), which also has a loss to the victim.
- **Packability.** `value_per_kilogram` and `bulk` (kilograms or head per unit of value). Eggs and seeds are small and light; a flock is not. Detection chance rises with bulk, which is why silk eggs and seeds moved and merino flocks did not (until given). Compute from the row: `bulk = mass_per_viable_unit / value_per_unit`.
- **Transit survival.** From the row: `viability_window` (days) against the route's travel time (geography routes and freight already exist). Hevea seeds die in weeks to months; silkworm eggs hatch the following spring; tea seed loses viability in storage; a living plant needs a protected case (a technique node). Survival is a function of the technique and the route time, not a dice roll.
- **Knowledge gate.** The thief needs the nodes that grant the skills to use the stock (`holds` already encodes what a node needs). Eggs without sericulture rearing, or rubber seed without a budding nursery, produce a loss, not an industry. The same gate holds for legitimate buyers.
- **Detection.** `probability_of_being_caught = f(enforcement_effort, border_length_or_chokepoints, bulk, insiders)`. It is an expected value, matching the existing yearly stock step (no dice, saves round-trip). If a discrete event is wanted, draw from a seeded stream keyed on the save (open question 4).
- **Response.** A caught run loses the cargo and pays the penalty set by the holder's policy; the holder may retaliate (embargo, raid, war) as a state's own option, not an engine branch.
- What drives the outcome, in order: the value gap, the survival of the stock in transit, the packability, the holder's enforcement effort and reach, and whether the thief has the knowledge to use it. With the gap at zero nobody smuggles; with enforcement spending raised, the quantity smuggled falls and the price gap widens.

### 2c. An export policy any actor applies

Replace the civilisation field `will_not_sell` with a policy on the holder, stored beside its other policies (`sim/agents/policy.py`):

- `export_policy[material] = {stance: allow | tax | ban, tax_rate, penalty, enforcement_spending}`, set by whoever decides for that actor (a state's policy, a firm owner, a guild, a player). `will_not_sell` becomes the opening policy for civs whose data names it (`stance: ban`); that keeps the Han case while letting a player state, firm or guild set the same thing for its own stock.
- Enforcement cost is a running expense (guards, inspectors, informers) drawn from the holder's budget; detection chance is a function of that spending and the holder's reach (state capacity, which civilisations already carry as `state_capacity`, and the routes it controls). A holder that cannot pay, or cannot reach the source, has a ban on paper only.
- A ban with no enforcement equals open sale; the value gap it creates is the same signal that drives smuggling. A tax is the same mechanism at a lower penalty, so quotas, tariffs and bans are one parameterised policy.
- Sales by gift and dynastic exchange are outside a ban in the record (Spain to Saxony, to France); model them as a holder choosing `allow` for a particular buyer, a relationship option, not a special case.
- What drives the outcome: the holder's budget and capacity, the gap, the penalty the buyer faces, and the buyers' alternatives (a domestic industry built from smuggled stock removes the gap, which ends the ban's value and hence the spending).

### 2d. Historical cases, used as relationship tests (not scripted)

| Case | What it shows about enforceability | Source | Tag |
|---|---|---|---|
| Silkworm eggs, Byzantium: two monks (likely Nestorian, with contacts in Sogdiana) hid eggs or very young larvae in bamboo canes; expedition about two years; dated 552 or 563 depending on the account | Small, light, easy to conceal cargo; fragile adults would not survive transit; the account is disputed (eggs or larvae) and the monopoly's own penalties were not stated in the page opened | https://en.wikipedia.org/wiki/Smuggling_of_silkworm_eggs_into_the_East_Roman_Empire | read |
| Rubber seeds, Brazil to Kew: Wickham shipped about 70,000 seeds in 1876 declared as academic specimens; at the time Brazil required an export licence but no law forbade exporting seeds; about 2,700 germinated | A weak or absent legal target, a licence got by a false declaration, and a small yield of survivors (seed recalcitrance) still sufficed because propagation multiplies | https://en.wikipedia.org/wiki/Henry_Wickham_(explorer) | read |
| Tea, Fortune 1848: for the East India Company, carried plants and seeds in Wardian cases and brought Chinese tea workers; a search summary says the penalty for smuggling plants was death; most plants sent to the north-west provinces perished, while the knowledge and workers later made Assam and Ceylon industries work | Carrying living stock needs a protective technique (case) and the people who know how; the plants alone were not enough | https://en.wikipedia.org/wiki/Robert_Fortune (read); death penalty and 20,000 plant count are from a search summary and not confirmed in the opened page | read, with snippet for the penalty |
| Merino sheep, Spain: an export monopoly with capital punishment for exporting, protected by the Mesta drovers' guild; first large legal consignments went by royal gift to Saxony in 1765 and to France in 1786 (Rambouillet, a founding flock of a few hundred head) | A bulky live flock is enforceable by a capable state at its few border crossings and by a guild that controls movement; the ban eroded through diplomatic gift, not theft | https://en.wikipedia.com/wiki/Merino ; https://wool.ca/images/uploads/files/care/wool-fact-sheets-history.pdf (search summaries) | snippet |
| Arabian horses: the Ottoman government forbade export of Arab horses, with a decree in 1873 forbidding export of horses of all breeds from Baghdad, Syria and Aleppo vilayets for seven years; best stock reached the Egyptian pashas by force, negotiation or gift; later buyers needed an imperial decree | A ban binds while a state can police movement of large animals; acquisition by a more powerful buyer's pressure (gift, force) is a standing path | search summary of Cambridge excerpt https://assets.cambridge.org/97811089/95382/excerpt/9781108995382_excerpt.pdf and https://history.state.gov/historicaldocuments/frus1873p1v2/d151 | snippet |

What made a ban enforceable, from these cases: the stock is bulky (animals), movement passes few points, the holder has a capable state or a guild, penalties are severe and certain, and no outside buyer has leverage. What made it fail: small, light, high-value propagules (eggs, seeds); no legal ban on the thing actually carried; a buyer who brings the know-how; and a holder that gives the stock away for another reason. Each is a parameter of the mechanisms above.

## 3. Staged build plan with relationship tests

Tests state relationships, never values, following CLAUDE.md 4.2. Each uses a minimal scenario.

**Stage 1 (data only, no engine): source the rates, add rows.** Replace the unsourced basis of `draught_animal_kg`, `cashmere_goat_kg`, `angora_goat_kg`, `ramie_stock_kg` and others with `source` and `confidence` as the five new rows have; add rows for sheep, horse, camel, pig, chicken, llama and the two Hevea materials (`hevea_seed_kg`, `hevea_budded_stump_kg`). `python3 sim/simulator.py validate`. Tests: natural increase does not exceed the biological ceiling from litter size, births per year and share of breeding females; adult loss is at least the sourced adult mortality; seed and spore rows (eggs, jute seed, hevea seed) have increase zero and loss that tracks their viability window; every row carries a source or the heuristic label.

**Stage 2 (pure functions in `sim/world`, no engine state): feed shortfall.** A function `fed_fraction(intake_needed, grazed_available, fodder_held)` and an effective-rate function in `stock_dynamics.py`, with `intake_fraction_per_day`, `starvation_loss` and `feed_source` as row fields. Tests: more feed never lowers the herd; zero feed shrinks the herd faster than the base loss; feed above intake leaves the base rates unchanged (existing tests still pass); a pig row draws on residue, not pasture.

**Stage 3 (engine state): herd location and shared pool.** Herd entries gain a tile; the yearly step takes the tile's `usable_forage_kg` after wild grazers, splits it among all herds on the tile (any actor's), and applies Stage 2. Needs the ledger to know a herd's owner and tile, and actors to own stock (today `stock_held` is the founder's). Tests: two herds on one tile each fall when the forage cannot carry both and the total drawn equals the pool; a herd moved to a tile with more forage ends larger; a herd of a non-founder actor behaves the same as the founder's.

**Stage 4 (data and policy): export policy replaces `will_not_sell`.** Per-actor `export_policy`, with `will_not_sell` converted to an opening policy; the refusal in `foreign_economies.py` and the quote in `stock_purchase_quote` read the policy. Tests: a ban with zero enforcement spending lets sales through at open-market terms; a tax raises the quoted price by the tax; a holder with more enforcement spending has a lower probability of leakage; the same policy applies when the holder is a firm or player, with no id special-cased.

**Stage 5 (engine): smuggling and theft as `Option`s.** Build `Option(subject=route_and_material, worth=value_at_destination * survival, cost=acquisition + freight, chance=1 - detection)` and offer it to every actor's policy. Tests: quantity smuggled increases with the value gap, decreases with detection chance and enforcement spending, and is zero when the gap is zero; survival falls with route time for seed rows with a short window; a stock without the node that uses it adds no output (knowledge gate); a bulky stock has a higher detection chance than a packable one at equal value; a caught run loses cargo and pays the penalty.

**Stage 6 (content): rubber.** Write the nursery and tapping section in `docs/`, add the planted-rubber node, its `holds`, the envelope, years to first yield and the yield per tree; tests: no yield before the first-yield years; outside the climate envelope the tile gives no rubber; seeds shipped over a long route arrive fewer than over a short one.

**Stage 7: price breeding stock in `sell` and the cash-remedies path** (open item in Complaint 366): value as breeding stock when at or above the breeding minimum. Test: selling below the minimum prices at slaughter value, above it at least the same.

## 4. Ready to build now, and what needs engine state

- **Ready now (data, pure functions):** Stage 1 sourcing and new rows; Stage 2 pure functions; the export-policy data schema; the smuggling expected-value function over a plain `Option` (it takes numbers); the rubber envelope and rows once the knowledge section exists.
- **Needs engine state:** herd owner and tile (Stage 3); actors that own stock, not only the founder; a stock-holding partner as an actor (a partner "sells no more than it started holding" is a labelled heuristic today); border and route detection (a function of enforcement spending and reach, with chokepoint data from `sim/geography/` routes); `cold_months` and `growing_months` layers from the food-potential plan; a fodder material stock (hay) in the ledger.

## 5. Open questions

1. Headcount or live weight: the ledger unit is kilograms live weight, but FAO rates are per head; young animals weigh little, so the weight rate is lower than the headcount rate and a herd's age structure matters. Keep the live-weight unit with a stated conversion, or move herds to age classes (the herd model the file's `_doc` names)?
2. Which per-species intake fractions to commit: only cattle, sheep, horse have snippet-level figures; camel, pig, chicken and llama are recalled and need a handbook (NRC, FAO feeding tables) before commitment.
3. Source for `starvation_loss` (loss against fed fraction): a body-condition mortality curve, not found this session; Mongolian dzud and drought-crash papers are the likely sources.
4. Discrete or expected smuggling: expected values keep saves deterministic but give a smooth leak and no single dramatic theft; a seeded draw would match the history of rare successes. Which fits the multiplayer protocol?
5. Does a thief's partial survival (a few percent of Wickham's seeds germinated, from the counts above) plus multiplication justify a minimum viable shipment, and how is the breeding minimum handled for propagules (seeds vs living plants)?
6. Rubber per-tree yield and budwood multiplication rate are not sourced here; the Hevea source file did not open as text.
7. How does an actor set policy for goods it holds only through others (a merchant carrying eggs)? Treat the carrier as the holder and the destination as the enforcement point?
8. Disease: the epidemic report covers people; livestock plagues (murrain) need either a link to the same shock mechanism or a separate one, and are a risk the policy must see.
9. Wild-grazer competition on the shared tile pool depends on the unread Coe, Cumming and Phillipson regression (food report section 4).
