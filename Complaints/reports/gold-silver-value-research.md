# Gold against silver: what should set the ratio (research for Complaint 442)

Design research only; no simulator code changed. Source tags: [read] a page opened and the figure seen
in it, [search] a figure from a search-result snippet only, [recalled] from memory, unverified.
Web access was thin for this report: several primary sources (Flynn and Giraldez, Duncan-Jones,
Ehrenkreutz, Redish) were reached only as titles or snippets, so most historical figures below are
[search] or [recalled] and must be verified before any test relies on them.

## 0. What the repository already has (measured by reading, branch `structural-dedupe-and-owner-decisions`)

- `sim/economy/households_store.py` already lets households keep a share of savings in "durable,
  non-spoiling goods of high value per kg", chosen by physical properties and price, not id
  (`store_candidates`, `store_value_target`, `store_bids`, `store_offers`, called from
  `households_orders.py`). Complaint 442 says there is "no demand to hold precious metal as wealth";
  that text may predate this module. First task of any build: re-measure whether gold and silver
  qualify as store goods, and what split and total they receive, with the command the complaint says
  does not exist yet (Complaint 445).
- Its parameters are all labelled heuristics (store share of savings, density multiple, storage
  cost, choice elasticity, rebalance band). The store target is a share of savings, so it does not yet
  depend on rarity, on the stock already held, or on alternatives such as land.
- `data/world/needs.json` `ornament`: unit "kg of bright durable metal equivalent", effectiveness
  "a cultural quantity, equal across the bright metals", with a transitional satiation per capita.
  This equal-per-kg effectiveness is the direct cause of the complaint: buyers pick the cheaper metal
  per kg.
- `sim/economy/mint.py` and `metal_stock.py`: the mint holds a real stock of the backing metal, buys
  to strike, sells to melt; yearly strike is capped by a labelled share of circulating metal; loss
  rates for coin and metal goods are labelled and unsourced.
- Gold supply: only two ancient gold deposits are in `data/world/geography/deposits/ancient.json`
  (`las_medulas_alluvial`, `dacia_vein_gold`, grades order-of-magnitude, confidence C) and modern ones
  in `metals.json` (Witwatersrand, Carlin, and others). There is no Nubian, Egyptian, West African,
  Anatolian, Altai, Andean or Mesoamerican placer gold. Silver has Laurion, Hispania, Rio Tinto,
  Britannia, Italy, and Potosi in `metals.json`. Gold and silver recipes in
  `data/production/20_nonferrous.json` are already derived from deposit grade, recovery and labour
  (hydraulic placer, vein, patio amalgamation, galena cupellation), which is the correct side of the
  pricing rule: supply cost emerges from deposits.

So the gap is demand and holding, plus gold-source coverage, not the production chain.

## 1. Why the two metals' values differ

### 1.1 Physical scarcity and cost of supply

- Natural abundance: silver is far more abundant in the crust than gold [recalled; USGS, Mineral
  Commodity Summaries and crustal-abundance tables]. Gold is very often native and in placers, found
  and won with gravity and, later, mercury; silver is mostly a by-product of lead (galena) and copper,
  needing smelting and cupellation, or amalgamation of sulphide ore.
- Grade and processing: ancient gold placers and veins run at grams per tonne; silver ores at hundreds
  of grams to kilograms per tonne (this repo's deposits: gold 0.0003 to 0.008 kg per tonne, silver
  0.3 to 2 kg per tonne). Rock moved per kg of metal is therefore far larger for gold, but placer
  gold needs little processing and no smelting, so cost per kg of metal does not simply scale with
  inverse grade. This is exactly what `sim/world/deposits.py` is built to compute.
- Joint production: silver supply from lead mining is driven by lead demand (the repo's galena
  recipe is already joint). The silver supply curve is therefore partly insensitive to silver's own
  price in the short run. Gold from base-metal by-products is a modern case.
- Geography decides who has which: Roman Spain and Dacia gold, Laurion and Spain silver; Nubia and
  West Africa gold with Mediterranean trade pulling it north [recalled]; Potosi and Zacatecas
  silver from 1545 [read, Wikipedia via search results].

### 1.2 Accumulated stock

Both metals are almost indestructible, so the stock is the sum of all past output less loss, and
price is set by willingness to hold the stock, not by the year's mining. Modern gold: the above-ground
stock is of the order of a couple of hundred thousand tonnes against annual mine output of a small
percentage of that, and about half is jewellery [search: World Gold Council figures via eco3min.fr and
interest.co.nz snippets, https://eco3min.fr/en/gold-demand-composition-etf-official-jewelry-bars/;
modern figures, use only as shape]. Consequences usable here:

- Price elasticity of supply to a year's flow is tiny; the stock is the buffer. A price rise releases
  jewellery and hoards (recycling) which damps spikes [search, same source]. This is the stock-to-flow
  logic the complaint asks for and the store module's `store_offers` partly implements.
- Silver differs: more of it is consumed or dispersed (industrial use is modern; in antiquity,
  silver plate, coin wear and lead-silver loss), so its stock-to-flow ratio is lower and its price is
  more flow-sensitive than gold's. This is a standard observation in precious-metals markets
  [recalled]; it is a consequence of the loss rates (`METAL_GOODS_LOSS_PER_YEAR`, coin wear) being
  possibly different by metal, which the repo currently sets as one number for all metal goods.
- Theory: for an exhaustible, storable resource the owner holds it only if its price is expected to
  rise at the interest rate (Hotelling's rule; https://en.wikipedia.org/wiki/Hotelling%27s_rule
  [search]). Gold, with a stock far above yearly output, is better described as a durable asset
  priced by portfolio demand than by Hotelling extraction; gold mining at these scales is not
  depleting a stock owners hold off the market. Hotelling is a useful warning, not a model to import.

### 1.3 Demand

- Coinage: both metals were struck. In Rome gold coin was the large-payment, state and army-pay
  metal and silver the everyday one; Duncan-Jones estimated the gold in circulation at a fraction of
  the silver by weight (reported as about 880 tonnes gold and about 5,800 tonnes silver in the 160s AD)
  though later numismatic work argues gold played a smaller role than he posited [search:
  https://resolve.cambridge.org/ snippets on Duncan-Jones; figures need verification].
- Display and gift: Han China gave gold as the high-status gift, with silk as the working currency, and
  silver rare [search: https://en.wikipedia.org/wiki/Economy_of_the_Han_dynasty, which itself says
  gold and silver were mainly prestige goods; no ratio given]. Temples and states held plate and
  treasure (Delphi, the Roman aerarium, the Han court) [recalled].
- Store of wealth: durable, dense, portable, divisible, recognised anywhere; this is the property
  that makes the metal worth holding independent of any one use [recalled, standard monetary theory].
- Trade to other regions: the Asian silver sink. In the early sixteenth century silver bought more
  gold in Ming China than in Europe, so Americas silver flowed there until ratios converged; Flynn and
  Giraldez's "arbitrage phases" [search: https://ora.ox.ac.uk/ result and
  https://en.wikipedia.org/wiki/Global_silver_trade_from_the_16th_to_19th_centuries].
- Official mint ratios and Gresham's law: the metal overvalued at the mint flows in and the other is
  hoarded, melted or exported [search: moneyness.ca and newtonandthemint.history.ox.ac.uk, already
  cited in `Complaints/reports/economy-research-extraction-and-money-metals.md`]. Rome's official
  aureus-to-denarius rate was 25 while the metal-content ratio of the coins was about 12 [search:
  https://en.wikipedia.org/wiki/Aureus], an example of a legal rate that is not the market ratio.
  The mint ratio is a policy input a state may set; it is not the emergent ratio and the model must
  keep the two apart.

## 2. Recommended mechanism

The aim: the gold-to-silver price ratio comes out of mining cost, accumulated stock and demand, with no
ratio and no preference for either metal named anywhere.

### 2.1 Components (all written against any actor)

1. **Asset demand (store of wealth), by stock held.** Each holder (household, firm, state, temple)
   wants a portfolio value in durable dense goods
   `target_value_of_store = store_share_of_wealth * (wealth - land_value - claims)` where the share
   falls with the real return on alternatives (`real_rate` from lending, rent yield on land) and rises
   with expected inflation and insecurity. It then splits among eligible goods by carrying cost
   (the existing `store_candidates` split), and must be stated as a demand for a **stock held**, so
   the bid each year is `target_value_of_store / price - quantity_already_held`, with offers when held
   exceeds target (already in `store_offers` with a rebalance band). The needed change is that the
   target depends on wealth, the alternatives and the good's own expected price change, rather than on
   savings only. Since purchase is of a stock, a year's mining adds to supply only a small fraction of
   the stock, so the price is set by the stock, as required.
2. **Display and status demand whose value rises with rarity.** Replace "ornament effectiveness
   equal per kg" by a utility for visible value: the household derives satisfaction from the money
   value of its display holdings relative to its neighbours' (positional demand), not from kilograms.
   Status goods whose value comes from scarcity are standard [recalled: Veblen 1899; Leibenstein 1950
   on bandwagon and snob effects; Bagwell and Bernheim 1996 on conspicuous consumption]. A minimal
   form: the need is satisfied by `display_units = price_per_piece_of_good * pieces / reference_wealth_scale`,
   i.e. the household buys money-value of display, with the piece mass set by physical limits (a ring,
   a cup) so a dear metal is bought in fewer grams. Then a rarer, dearer metal is held in smaller
   mass for the same display value, and the two metals are substitutes in display at the money value,
   not per kg. Silver's price falls relative to gold's when gold is rarer because less gold mass is
   needed for the same display and its supply is smaller. The two metals differ physically
   (colour, tarnish, hardness, workability, density, melting point), and these are material
   properties the data can carry; they must feed an effectiveness-per-piece, never a ratio.
3. **Coinage demand through the mint.** The mint buys metal at the issuer's mint price and holds it
   as a stock embodied in coin; a state chooses what to strike from its own treasury needs (pay,
   tax collection in kind or coin) and from the metal it can get, not from a ratio. Gresham flows then
   emerge from two metals struck at fixed face rates while the market ratio moves; `currency.py`
   backing already allows one backing good per currency, so bimetallism needs a second backing good
   or a currency pair, a later stage.
4. **Trade between regions.** Already the freight and market-area machinery; the Asian silver sink
   should emerge from different local stocks and relative demands, with gold and silver carried
   wherever carriage cost per value is below the price gap. Nothing special is added.
5. **Loss.** Per-metal wear and loss by use class (coin abrades, plate is lost, jewellery is melted
   and reworked) with the rates sourced; a lost stock is replaced only by mining, which connects the
   stock back to deposits.

### 2.2 How the ratio emerges

- Cost side: each metal's long-run supply price is its marginal deposit's cost (extraction hours per kg
  from grade and hardness, processing, Ricardian rent from `sim/world/deposits.py`), where the world
  holds many deposits at different costs.
- Stock side: the short-run price clears the demand for the existing stock (asset plus display plus
  coin metal) against the willingness of holders to sell. A big silver inflow (Potosi) raises silver's
  stock with little change in gold's, so silver's price falls against gold, until demand grows or
  trade moves silver to where it is dearer; the ratio rises, which is what is observed.
- Cross-substitution: because asset and display demand can use either metal, the ratio cannot stray
  far from the relative cost to hold the same money value of wealth in each (carrying cost, loss rate,
  portability). This pins the two prices together without authoring a ratio, and gives bimetallic
  drift.

### 2.3 What must not be authored

- No gold-to-silver ratio, mint ratio taken as market ratio, floor or ceiling on the ratio.
- No per-id demand ("gold is prestigious", "silver is currency"). Prestige and money use must follow
  from carried properties: value per unit mass, tarnish, workability, divisibility, loss rate.
- No hoard size or per-capita holding as a target (the current `satiation_per_capita_per_year` for
  ornament is an unlabelled-by-evidence heuristic and should be replaced, as its own note says).
- No yearly gold or silver output; output comes from deposits, mining recipes and prices.
- No price table. Prices stay solved; the stock sets the price through the clearing step.
- `share_of_empire_output` figures in the deposit files are authored historical shares and are
  acceptable only as a transitional split, labelled; they are the sort of historical-outcome input
  that Section 4.1 of CLAUDE.md warns about. Consider replacing with grade and endowment per deposit.

## 3. Data needed (existing files, no invented figures)

| Need | File | Status and what needs a source |
|---|---|---|
| Gold deposits (grade, endowment, hardness, depth, location) for the whole map | `data/world/geography/deposits/ancient.json`, `metals.json` | Only Las Medulas and Dacia in antiquity. Missing: Nubia and the Eastern Desert, Egyptian and Arabian placers, Pactolus and Anatolian, Colchis, Ural and Altai, West African (Bambuk, Bure), Andean and Colombian placers, Mexica and Central American, Han-era Chinese placer and lode sources, Indian (Kolar is present, check date). Each needs grade (g per tonne), endowment, working technique, first worked; sources: archaeometallurgy papers, USGS, national geological surveys. Confidence C or D until read. |
| Silver and gold grades with confidence tags | same | Many existing grades are marked order-of-magnitude. Priority: verify Las Medulas and Dacia grades and the "unspecified placeholder" silver entries (Italia, Britannia). |
| Metal-specific loss and wear | `metal_stock.py` constants | One rate for all metal goods; need rate by use class from hoard finds, coin weight-loss and shipwreck studies. |
| Material properties that drive display | goods data (`data/world/`, `needs.json` goods) | Need per good: density, tarnish and corrosion resistance, malleability, hardness, melting point for both metals, as physical facts. Replace "cultural quantity equal per kg". |
| Piece mass | goods data | Mass of typical worked piece (ring, cup, plate, coin) to turn money value into grams. Source: museum catalogues, hoard inventories. |
| Wealth portfolio shares | constants labelled in `households_store.py` | Probate inventories, temple and treasure inventories (Delphic treasuries, Egyptian temple accounts, Roman wills) to bound share of wealth in plate and bullion by wealth class. |
| Mint practice | currency data | Seigniorage and mint-price margins by state and period; mint ratios used by each state (policy input). |
| Initial stocks | opening data | Opening metal stock follows from agents' targets today (`opening_money_stock`); for display and hoard metal, derive the opening stock from the same asset demand at the opening prices rather than authoring. |
| Validation | none yet | A `simulator.py` subcommand printing the ratio, stock-to-flow and holdings by class (Complaint 445). |

## 4. Historical patterns for distribution checks (ranges and relationships, not dates)

The attested ratios, with how much to trust them:

- Roman Republic market ratio near 12 [search: Aureus page above]; empire's official coin ratio 25
  with metal content nearer 12 [search]. The ratio of face rates to market is a policy-wedge check.
- Abbasid period about 13 to 14 and about 15 dirhams to the dinar [search: Islamic-coinage snippets,
  e.g. https://jtuh.tu.edu.iq/ and Schultz 1999, https://knowledge.uchicago.edu/record/1003/files/MSR_III_1999-Schultz.pdf,
  not opened]. Medieval Europe from the high single digits to the mid teens [search: Venice 14 in the
  early fourteenth century, 9 to 10 mid-century, back near 12 in the fifteenth, from bullion-history
  popular sources; weak].
- Ming China silver dear against gold, ratio near 6 to 8 against 10 to 12 in Europe in the early
  sixteenth century [search: Flynn and Giraldez via snippets; Persia about 10, India about 8, same
  source]; arbitrage then drew silver east and narrowed the gap.
- Spanish-American silver flood: ratio rose in Europe through the sixteenth and seventeenth centuries
  [recalled: Hamilton, Flynn and Giraldez; check]. US 1792 mint ratio about 15 [search].
- Han China: gold as high-value gift, silver rare, no sourced ratio; do not test an absolute value.

Checks that generalise:
1. Across runs and civilisations, the ratio stays in a broad band above one (a sub-one ratio is a bug) and
   within roughly the order of ten, with wide dispersion between isolated regions and narrowing as
   trade links form.
2. Gold is dearer per kg than silver in every region where either is traded; the ratio is higher where
   silver is mined near and gold is far, lower where gold is native and silver is imported.
3. An exogenous silver supply increase (a rich deposit opened) raises the ratio, with a lag set by
   stock; a gold increase lowers it.
4. Stock-to-flow: the stock of each metal held is many years of its mining output; metal released from
   holdings rises with price (recycling), damping price spikes.
5. Price of metal moves less than grain year to year (Complaint 387's ordering).
6. Where mint ratio departs from market ratio, flows follow Gresham's law: the overvalued metal
   enters the mint, the other leaves coinage.

## 5. Staged build plan

Each stage lands with regression tests per CLAUDE.md section 6 and a `validate` and fingerprint check.

**Stage 0 (smallest, measure first).** Add the measurement: a `simulator.py` subcommand (Complaint 445)
printing, per civilisation and year, gold and silver price, ratio, held stock by holder class, mine
output and stock-to-flow. Tests: ratio is positive, stocks conserve (opening plus mined minus lost),
output matches deposit recipes. No behaviour change. This tells whether `households_store` already holds
either metal.

**Stage 1 (first behaviour change).** Make the ornament need money-valued and positional, not per kg:
effectiveness per piece from material properties, demand for display value, no equal-per-kg clause.
Keep the store as is. Tests: (a) with identical cost, the two metals split display demand by
properties; (b) halve gold's supply cost and gold's display mass bought rises less than silver's would;
(c) gold never prices below silver per kg in a world where gold deposit cost per kg is higher (the
regression of 325 and 334); (d) ornament purchase remains bounded by wealth, not a satiation constant.

**Stage 2.** Asset demand by stock: store target depends on wealth, land and loan alternatives, and on
the good's carried stock; per-metal loss rates. Tests: a one-year mining increase moves the price
less than a same-size demand change; sale from stock when price rises; ratio in the band across seeds.

**Stage 3.** Gold deposit coverage for all starting civilisations (data stage, needs sources first).
Tests: each civilisation's gold source is a deposit with a grade, none authored by id.

**Stage 4.** State and temple holders (treasuries as asset holders with their own targets), and mint
buying either metal to strike, with a policy mint ratio and Gresham flows. Tests: mint-ratio versus
market-ratio flow direction.

**Stage 5.** Inter-regional arbitrage checks (the silver sink) as a validation scenario, not a built
rule.

## 6. Open questions for the owner

1. Is `households_store.py` the intended home of asset demand (extend it), or should precious-metal
   holding be a separate holder-class module so states and temples share it?
2. Display demand: positional (own display against neighbours) or absolute (value per piece)? The first
   is more realistic and needs a notion of a reference group; the second is simpler.
3. May deposit `share_of_empire_output` stay as a labelled transitional input, or should the per-deposit
   split come only from grade, endowment and cost?
4. Where does gold come from for civilisations whose gold is placer or tribute (Nubia, Mexica, Norse)?
   This needs new deposits or an import and tribute route; which first?
5. Should loss rates be per metal and use class, which adds data needs, or one rate kept and labelled?
6. Do states choose bimetallic backing in this build, or one metal per currency for now?
7. Priority of sources: which gold figures should be read and cited first (grades for Las Medulas and
   Dacia, loss rates, piece masses)?

## Sources

- Hotelling's rule: https://en.wikipedia.org/wiki/Hotelling%27s_rule [search]
- Global silver trade: https://en.wikipedia.org/wiki/Global_silver_trade_from_the_16th_to_19th_centuries [search]
- Flynn and Giraldez material: https://ora.ox.ac.uk/objects/uuid:aec6d2ba-d664-4ef0-9ca1-f0918a55033d/files/rmg74qm819 and
  https://mpra.ub.uni-muenchen.de/43987/1/MPRA_paper_43987.pdf (opened; text unreadable) [search]
- Aureus: https://en.wikipedia.org/wiki/Aureus [search]
- Duncan-Jones, "Roman coinage under the Antonines revisited" and Dio, Zonaras and the aureus:
  https://resolve.cambridge.org/core/books/uncertain-past/roman-coinage-under-the-antonines-revisited/76626FBFC05664B712DC6ABE6D4790C8 [search]
- Han economy: https://en.wikipedia.org/wiki/Economy_of_the_Han_dynasty [read, no ratio]
- Chinese gold stock: https://core-cms.cambridgecore.org/core/journals/journal-of-economic-history/article/an-ancient-chinese-stock-of-gold/9B471D671B992D6D0D7FCCD6E232C12F [not opened]
- Abbasid ratio snippets and Mamluk money: https://knowledge.uchicago.edu/record/1003/files/MSR_III_1999-Schultz.pdf,
  https://jtuh.tu.edu.iq/index.php/hum/article/view/1204 [search]
- Gold stock and jewellery share: https://eco3min.fr/en/gold-demand-composition-etf-official-jewelry-bars/,
  https://www.interest.co.nz/personal-finance/121199/world-gold-council-presents-overview-available-above-ground-stock-gold [search]
- Popular ratio history (weak): https://no01.substack.com/p/the-gold-to-silver-ratio,
  https://learn.apmex.com/?p=22242
- Recalled, to verify: Veblen 1899; Leibenstein 1950; Bagwell and Bernheim 1996; Redish on medieval
  bimetallism; Hamilton on American treasure and prices; USGS crustal abundance.
