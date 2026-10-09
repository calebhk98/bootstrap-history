<!-- Second pass, 2026-10-09: written without reading gold-silver-value-research.md first; read both. This one adds that a store of value already exists in sim/economy/households_store.py. -->
# Research: what sets the gold to silver value ratio, and how the sim should produce it

Written for Complaint 442 (owner direction 2026-10-06: the ratio should follow how rare each metal is
and where its mines are, through geography and deposits; research before code). Research only: no code
was changed.

Source strength key, used on every claim below:

- **[P]** primary or peer-reviewed text, and I read enough of it to quote it.
- **[S]** a search-result summary of a scholarly source. I did NOT read the paper itself; the claim is
  what the summary said. Treat as a lead to verify.
- **[W]** encyclopedia, dealer, teaching-slide or popular page. Weak.
- **[R]** from this repository's own data. Its confidence letters are the repository's, not mine.
- **[M]** background knowledge, not verified in this session.

Honest limit: WebFetch could not decode the PDFs of Ross and Bettenay (2023) or Melitz (2017), and the
CEPR seminar deck returned 403. Most of section 1 therefore rests on search summaries. Where a number
matters for a test or a data file, verify it against the named source first.

---

## 0. What the repository already has (this changes the recommendation)

Complaint 442 says there is no demand to hold precious metal as wealth. That is out of date in one
respect: a store-of-value mechanism already exists.

- `sim/economy/households_store.py` (commits a7b0e5c4 and cf10d2f4, under Complaint 404 steps 4 and 5)
  lets a household hold part of its savings in goods chosen by physical properties and price, never by
  id. A good qualifies if its service life is positive, its spoilage per year is below a cut-off, its
  mass is finite, and its price per kg is a large multiple of the cheapest staple's price per kg.
  Qualifying goods share the holding in proportion to the inverse of the yearly carrying cost (spoilage,
  wear, and storage by mass per unit of price) raised to an elasticity below one.
- The holding is bought through bids at a low priority and sold through offers (surplus over a band,
  and a discounted urgent sale when cash is short). `households_orders.goods_orders` wires it in.
- Tests exist: `sim/tests/test_economy_store_candidates.py`, `_bids.py`, `_sales.py`, `_share.py`, with
  the stub in `sim/tests/economy_store_view.py`.
- All the constants there are `temporary_heuristic`, confidence D, unsourced.
- The ornament need still lists `silver_kg` and `gold_kg` as equal per kg
  (`data/world/needs.json`, `satisfies` of 1.0 each), with a held-stock satiation heuristic.
- `COIN_WEAR_PER_YEAR` and `METAL_GOODS_LOSS_PER_YEAR` in `sim/economy/metal_stock.py` are labelled
  unsourced.

So the first job is not to build the store but to measure why it has not fixed the ratio (section 4.6).
The measured ratios in Complaint 442 may predate the store; re-measure before acting (CLAUDE.md section 3).

Deposit data present [R]: `data/world/geography/deposits/ancient.json` has historic gold at
`las_medulas_alluvial` (placer, endowment 1640 t, grade 0.0003 kg per tonne of ore), `dacia_vein_gold`,
`eastern_desert_nubian_gold`; silver at `laurion_silver`, `hispania_silver`, `rio_tinto_jarosite`
and generic placeholders for Italy and Britain. `metals.json` has `potosi_silver` (endowment 45000 t,
status historic, first worked 1545) and many modern gold mines. Each entry carries `endowment`,
`ore_grade_kg_per_tonne`, `deposit_type`, `status`, `first_worked`, and a confidence letter.
`data/world/resources.json` gives Roman-empire output of about 200 t silver and 9 t gold a year [R,
confidence C, "from memory or a secondary summary"], which is a flow ratio of mass of roughly 22 to 1,
against a Roman price ratio near 12 (section 1). That gap is the stock and demand effect the owner
wants; it is a useful sanity target for the model to land near without being set.

Data gaps I noticed [R]: no West African gold, no Japanese silver (Iwami), no Central European silver
or Hungarian gold, no Han-era Chinese or Indian placer entries by id in the two files I read. These are
the places the historical divergences (section 1) come from, so the divergence cannot emerge without
them.

---

## 1. Historical gold to silver ratio, by place and period

Convention: value of one unit of weight of gold divided by value of the same weight of silver. A higher
number means silver is relatively cheap or gold relatively dear. A ratio below one is a bug in this sim.

### 1.1 Table (with strength)

| Place and period | Ratio | Strength and source |
|---|---|---|
| Ancient world generally, about 2500 BCE to 400 CE | over 200 observed values compiled; purity gave a two to threefold spread in gold's value, but "availability" mattered more | [S] James Ross and Leigh Bettenay, "Gold and Silver: Relative Values in the Ancient Past", Cambridge Archaeological Journal, 2023, doi 10.1017/S0959774323000355. https://www.cambridge.org/core/product/406D8B078C66ACB266932D51A0E2F205/core-reader . I saw the abstract-level summary only. |
| Egypt and Near East | rose markedly after access to Nubian gold was lost about 1100 BCE | [S] same paper, summary only. This is the cleanest ancient case of a ratio following a mine's location. |
| Roman Republic, treasury gold sold for silver | about 12 | [W] Wikipedia, "Aureus", https://en.wikipedia.org/wiki/Aureus |
| Roman Empire, Augustus | Pliny gives 12.5; coin weights give about 11.97 | [S] American Numismatic Society digital library item, https://numismatics.org/digitallibrary/ark%3A/53695/nnan92614 (via search summary) |
| Roman Empire, Nero to Marcus Aurelius | about 11.7 theoretical, flat | [S] same item |
| Roman, mid third century | drifting up: about 11.9 (Alexander Severus), 12.1, 12.15, 13.0 (Decius), 13.4 (Philip); estimates depend on assumed coins per pound | [S] same item. These are coin-weight ratios, not market prices; debasement of the silver coin confounds them. |
| Han China | no reliable ratio found | [S] Academia Sinica Institute of History and Philology bulletin article (https://www1.ihp.sinica.edu.tw/Publications/Bulletin/955/Article/873) says the ratio of gold to copper coin is unknown; large gold stocks existed (about 600,000 catties in Wang Mang's treasury per Ban Gu via Dubs, via search summaries). I found no Han gold to silver number. |
| Venice and Italy, Hungary, France, Flanders, about 1284 to 1330 | about 12 after the ducat, peaking about 14.2 at Venice around 1305 | [S] Peter Munro's teaching materials summarising Frederic Lane, https://www.economics.utoronto.ca/munro5/L03AMedievalMoney.pdf and https://www.economics.utoronto.ca/munro5/MedBullionismJEH1983.pdf |
| Europe, mid fourteenth century | fell to about 10 by 1350; about 9.4 at Florence in 1347 | [S] same Munro summaries. Lane attributed it to new gold (Hungary, Italian maritime trade) and to silver used in industry and luxury, not to a silver mining decline. |
| Europe, around 1700 and 1717 | over 15; Spain's mint ratio about 16 | [W] a Newton Project / Newton and the Mint catalogue entry MINT00322 (https://newtonproject.ox.ac.uk/catalogue/record/MINT00322) and a 1734-era text, both via search summary. |
| Europe, 1722 to 1830 commercial ratio | 15.17 (1722), 15.55 (1795), 15.82 (1830) | [S] US Mint table crediting Adolf Soetbeer for 1687 to 1832, OCR text, seen via search. Check the original: Soetbeer, Edelmetall-Produktion und Werthverhaeltniss zwischen Gold und Silber seit der Entdeckung Amerikas bis zur Gegenwart, 1879. |
| Canton, 1590s | about 5.5 to 7, against about 12.5 to 14 in Spain | [W] CEPR/VoxEU MacroHistory seminar deck on East India Company silver arbitrage, https://voxeu.org/system/files/2023-05/EIC%20silver%20arbitrage%20MacroHist%20Seminar.pdf . Slides summarising Flynn and Giraldez; seen via search summary. Authors of the deck not identified by me. |
| China about 1700 | about 10 to 11, against about 15 in Europe | [W] same deck |
| Mid eighteenth century | about 8 in Japan, about 10 in China, 14 to 15 toward Europe; "more than 87 percent" gain claimed for shipping silver from England to Japan, but noted as not covering the voyage in ordinary times | [W] text attributed to Cantillon, Essay on the Nature of Commerce in General (written 1730s, published 1755), via search summary of https://abook.qq.com/read/1000794162/57 . A contemporary observation, not a modern calculation. |
| Newton 1717 | surveyed ratios across Europe, China, Japan and India; found Britain overvalued gold against all but Spain, which drew silver out toward India | [W] Newton Project MINT00322 (search summary) |
| Japan, Edo period | legal ratio about 4; market ratio about 5 by the end of the shogunate, against a world level of about 15.5 around 1870; large gold outflow in the 1850s to 1870s | [S] Nipponica entry on kinginhiritsu via Kotobank, https://kotobank.jp/word/%E9%87%91%E9%8A%80%E6%AF%94%E4%BE%A1-54075 . A late period, not the seventeenth century. |
| Japan, why it stayed low | an almost closed economy, so the ratio did not feel the outside market until the 1850s | [S] American Numismatic Society, "Gold Coinage in Pre-Meiji Japan", https://numismatics.org/pocketchange/koshu/ |
| Mughal India | gold cheap against silver; Europeans carried silver to India for gold because "the ratio is much lower in India"; no number found. About 80 percent of imports were bullion, mostly silver. | [W] Wikipedia "Economy of the Mughal Empire" (with a citation-needed tag on part) and a quoted historical text, via search summary. A seminar paper with hand-collected prices for Mocha, Bombay, Surat and Bengal, 1664 to 1811, exists (cited in the search results at https://economics.barnard.edu/sites/default/files/inline-files/Columbia%20appendix%20paper%20figures.pdf); I did not retrieve its findings. |
| Americas after 1500 | silver flooded Europe, so silver per gold rose; Spanish American mines gave a steady average of about 350 t silver a year for over 250 years; Bolivia, Peru and Mexico over 85 percent of world silver 1500 to 1800 | [S/W] Silver Institute, https://silverinstitute.org/?p=239 ; an LSE research-online paper on the global silver economy 1500 to 1800, https://researchonline.lse.ac.uk/id/eprint/119884 . Summaries only. |
| Brazil, from the 1690s | Bank of England gold reserves from 235,000 oz (1720) to 900,000 oz (1740) as Brazilian gold arrived; gold became cheaper in Britain's fixed-rate mint | [W] Wikipedia "Brazilian gold rush" plus Newton Project; the causal chain to the ratio is the search tool's own synthesis, not a source's. |
| Japan silver | Iwami Ginzan produced roughly a third of world silver at its early 1600s peak (one estimate); cupellation (haifuki) arrived from Korea in 1533; silver sold through the Portuguese to Ming China for silk | [W] MLIT tagengo-db pages on Iwami Ginzan, https://www.mlit.go.jp/tagengo-db/en/R1-02683.html ; Nippon. I did not find a Japanese gold to silver number for the sixteenth or seventeenth century. |

### 1.2 What the pattern says

1. Within one connected region and one period, the ratio sits in a narrow band. Rome sat near 12 for
   about two centuries. Europe moved between roughly 9 and 15 over four centuries, and the large moves
   have named supply causes: new Hungarian and Italian-trade gold in the 1300s [S], American silver in
   the 1500s and 1600s [S/W], Brazilian gold in the 1700s [W].
2. Between regions at the same date the ratio differed by a factor of about two or more: Canton about
   6 against Spain about 13 in the 1590s, China about 10 against Europe about 15 around 1700, Japan about
   8 or lower. Gold was cheap, in silver terms, where silver was monetary and scarce or where gold was
   locally abundant, and dear where silver mines were many [W/S, mechanism inferred, see 1.3].
3. The ancient evidence points the same way: the ratio followed which gold source a region could reach
   (Nubian gold and Egypt, [S] Ross and Bettenay 2023). This is directly the owner's hypothesis: the
   ratio follows mines and where they are.

### 1.3 Why it differed, and the arbitrage flows

- **The arbitrage account (Flynn and Giraldez).** Silver was dear in China because China used silver as
  money and had little domestic supply; Europeans and later Spanish Manila traders sold silver in China
  for gold and goods. Flows ran from Japan (1540s onward) and, from 1571, from the Americas through
  Manila to China [S: summary of their work in the search results, above; I have not read Flynn and
  Giraldez directly. Titles to read: Dennis O. Flynn and Arturo Giraldez, "Arbitrage, China and World
  Trade in the Early Modern Period", Journal of the Economic and Social History of the Orient 1995 (the
  venue was not confirmed by my searches; a chapter by this title appears in their 2002 volume
  "China and the Birth of Globalization in the Sixteenth Century"), and their 2002 theoretical essay.]
- **The dissent (Melitz).** Jacques Melitz, "Some Doubts about the Economic Analysis of the Flow of
  Silver to China in 1550-1820", CEPII working paper 2017-19, https://imap.cepii.fr/PDF_PUB/wp/2017/wp2017-19.pdf
  [P for the abstract only; the body did not decode]. He argues gold-silver arbitrage mattered only in
  one twenty-year spell, that wide geographic differences in the ratio are better read as evidence of
  high costs of arbitrage than of profitable arbitrage, and that China's history would have been much
  the same had it imported gold.
- **Why this dispute matters for the design.** Both sides agree the ratios differed. They disagree on
  whether the gap was an unexploited profit or a measure of transaction cost. The sim should therefore
  carry the differences through an explicit carriage cost, so that a gap is allowed up to the cost of
  closing it, and flows start when the gap exceeds that cost. Then the model reproduces either reading
  depending on the freight and risk data, and the data decide (CLAUDE.md 4.2).
- **Mint ratio as a target zone.** Under bimetallism the legal ratio at the mint set a band: the metal
  the mint overvalued flowed in, the other was hoarded, melted or exported. Oppers (2000) is reported to
  find that the mint ratios of the major bimetallic countries acted as regulating barriers [S: search
  summary of "A Model of the Bimetallic System", https://ideas.repec.org/p/mie/wpaper/332.html ; author
  and year of that paper not confirmed by me]. The 1792 US case: mint ratio 15, market ratio about
  15.5, gold left circulation [W: economics teaching page]. Newton 1717: Britain's mint overvalued gold,
  silver left [W, above]. Redish, Bimetallism: An Economic and Historical Analysis (Cambridge University
  Press, 2000) and Friedman, "Bimetallism Revisited", Journal of Economic Perspectives 4(4), 1990, pp.
  85-104, are the standard references; I saw only their citations.

---

## 2. What economists say sets the ratio

I could not read the primary texts; the points below are the standard account [M], with the stated
supports.

1. **Stock against flow.** Gold and silver are not consumed, so the above-ground stock is many years of
   output. Today's gold stock is about 60 years of mine output by simple division of the World Gold
   Council's end-2025 figures (about 220,000 t above ground, 3,672 t mined in 2025; the division is my
   arithmetic) [W/S: World Gold Council, https://www.gold.org/goldhub/data/how-much-gold ; full-year
   2025 supply page https://www.gold.org/goldhub/research/gold-demand-trends/gold-demand-trends-full-year-2025/supply ].
   The price is then set by willingness to hold the stock, and a year's output shifts it a little.
   This is already the claim of Complaint 442; the existing research brief gave the same point from weak
   dealer pages (`economy-research-extraction-and-money-metals.md`, section 3).
2. **Production cost at the margin sets a long-run floor.** Pre-modern mining was Ricardian (rising cost
   per unit as better sites are worked out) more than Hotelling [M; this report's predecessor made the
   same claim from background knowledge]. If the price falls below the cost at the marginal site, output
   falls and the stock stops growing. Over centuries the ratio drifts toward the ratio of marginal
   costs. Lane's finding for the 1300s, that silver mining decline did not explain the fall in the ratio
   and new gold did [S], is a case where supply of the other metal dominated.
3. **Monetary demand.** Where a metal is struck as coin, mints buy it. The mint ratio sets a band
   (section 1.3). A region on a silver standard holds silver as money, so silver is wanted there
   beyond its other uses; that is the usual explanation of China's low ratio [W/S].
4. **Store of value and prestige.** Plate, jewellery and temple treasure hold wealth in a form that does
   not rot. Modern figures show jewellery is the largest holder of gold (about 44 percent of all gold
   mined) and central banks about 18 percent [W: World Gold Council pages via a coinweek summary].
   For antiquity the Wang Mang treasury figure (60 chests of 10,000 catties, per Ban Gu via Dubs) shows
   a state holding gold as a hoard [S].
5. **Durability and loss.** Because a metal lasts, annual wear and loss of the stock (coin abrasion,
   clipping, burial, shipwreck) is the only sink, and it is a small share of the stock. The repo's
   constants for this are unsourced (`COIN_WEAR_PER_YEAR`, `METAL_GOODS_LOSS_PER_YEAR`).
6. **Carriage cost per unit of value.** Gold is worth many times silver per kg, so freight, guarding and
   insurance cost a far smaller share of its value. Two consequences [M, and implied by Melitz's
   reading above]: gold can be shipped over distances that silver cannot profitably cover, and a price
   gap between two places can persist for silver up to a larger percentage than for gold. The persistent
   gaps in section 1 are then explained as the cost of moving silver (and gold) over long routes, plus
   the monetary regime that either allowed or forbade export.
7. **Non-monetary industrial demand.** Lane's suggestion that silver used in industry and luxury goods
   also moved the 1300s ratio [S] shows the demand side is not only coin.

---

## 3. Physical facts a sim should use

| Fact | Value | Strength and source |
|---|---|---|
| Crustal abundance of gold | about 0.004 ppm by mass | [W/S] CRC Handbook table reproduced at https://www.knowledgedoor.com/2/elements_handbook/element_abundances_in_the_earth_s_crust.html and Wikipedia "Abundance of elements in Earth's crust". USGS Circular 603 (1968) gives a range of 0.001 to 0.006 ppm (via search summary). |
| Crustal abundance of silver | about 0.075 ppm | same sources. A USGS soil geochemistry report cites 0.053 mg/kg upper-crust silver, so the figure is not firm. |
| Crustal ratio, silver to gold | about 19 to 1 | [W] a dealer article (silverbullion.com.sg, "How Rare are Gold and Silver"); it is simple division of the two figures above. |
| Ore grade of Roman gold placer (Las Medulas) | the repository stores 0.0003 kg per tonne (0.3 g per tonne); one web source says "3 grams" from a tonne of excavated material, which disagrees by a factor of ten | [R] `data/world/geography/deposits/ancient.json`; [W] https://en.wikipedia.org/wiki/Las_M%C3%A9dulas . This conflict must be resolved from a primary source before the grade is used. |
| Roman gold output, Las Medulas | Pliny the Elder: 20,000 Roman pounds (about 6,560 kg) a year; about 1,600 t over about two and a half centuries; 60,000 workers in Pliny-based accounts | [W] same Wikipedia page; Pliny, Natural History book 33 (primary, not read here). Compare the repo's 9 t a year empire total [R, confidence C]. |
| Laurion silver | Athenian state had 100 talents (about 2.6 t) of silver around 480 BCE; labour estimates up to 20,000 slaves are uncertain | [W] https://en.wikipedia.org/wiki/Mines_of_Laurion |
| Spanish American silver | about 350 t a year steady average for over 250 years; Central Europe peak about 52 to 55 t a year in the 1540s; Japan peak early 1600s estimated 150 to 200 t a year | [S] LSE paper and Silver Institute pages above. |
| Mining and refining technique | cupellation separates silver from lead; pan amalgamation (patio process, invented 1554 by Bartolome de Medina; pan amalgamation at Potosi 1609) let poorer ores be worked; mercury lost about one to two times the weight of silver recovered; Huancavelica mercury found 1560 | [W] Wikipedia "Patio process", "Potosi", Britannica. The loss ratio is from a summary; verify. |
| Recovery rates by historical technique, placer against lode, grade in ounces per ton | NOT FOUND | I found no usable source. Do not put numbers in data until one is found. Candidates to search: Craddock, "Mining and Metallurgy" in Oleson (ed.), Oxford Handbook of Engineering and Technology in the Classical World, 2008 [M, not read]; Bayley and others on cupellation. |
| World annual output by era, silver and gold | NOT FOUND as a consolidated table | The standard compilations are Soetbeer 1879 (reproduced in US Mint yearbooks, OCR) and the Manning, Flynn and Wang silver-circulation series 1400 to 1900 (named in a search result, not retrieved). Treat the regional figures above as order of magnitude only. |
| Above-ground stock, gold, today | about 220,000 t (end of 2025) | [W/S] World Gold Council, above. Not a historical figure. |
| Above-ground stock by antiquity or 1500 | NOT FOUND | The sim should compute it from cumulative deposit output less loss, not look it up (CLAUDE.md 4.1, 4.5). |
| Wear and loss rate of coin and plate | NOT FOUND with a source | Both repo constants are flagged unsourced. Hoard-find and coin-weight studies are the right data, as the repo's own text says. |

---

## 4. Recommended mechanism

Aim: the ratio at any place and date is an output of cumulative mined stock (by place), holders' demand
to keep durable high-value goods, carriage cost, and monetary regime, with no ratio and no good id
written anywhere.

### 4.1 Demand to hold wealth as a durable good (mostly built; the gap is the shape of the demand)

- **Households and states each want to hold a quantity of durable high-value goods.** A good qualifies
  by its physical properties: it does not spoil, it lasts, and its value per kg is a large multiple of
  the cheapest staple's value per kg. That is what `store_candidates` does today.
- **What is missing is a demand that depends on scarcity, not only on carrying cost.** Today the value a
  household puts into the store is split among qualifying goods by inverse carrying cost. Both metals
  therefore get nearly the same value budget, and the resulting price per kg of each is that budget
  divided by the kg held of each. The ratio then equals (value budget of gold divided by value budget of
  silver) times (stock of silver in kg divided by stock of gold in kg). This is the right shape: the
  ratio follows the relative stocks, which come from deposits and history. But the budget split is
  nearly one to one by construction, which is itself a hardcoded outcome (CLAUDE.md 4.1). Replace it
  with a split that emerges from what is for sale and from the household's own reservation prices:
  each good's share follows the expected carrying return, namely the expected price change plus the
  service flow, minus storage, spoilage and wear per unit of value. Households then shift value toward
  the metal whose price looks low against its carrying return, and the split settles where the two
  returns equalise, so the budget split is an output.
- **Prestige and ornament as a flow of service from the held stock.** A held ornament yields service
  while held, and the service need is satiated by the stock held per head, not bought again each year.
  The ornament need already carries a transitional satiation of this kind; the held-stock form is the
  replacement it promises. Gold and silver should not be equal per kg; give the service a per-unit-of-value
  basis, or give none and let the store do all the work. The Complaint 442 text itself prefers the
  second.
- **States.** A state (treasury, temple) also wants a reserve of durable high-value goods against war and
  dearth. Write the mechanism against an actor, not the founder (CLAUDE.md section 5), and reuse the
  household formula with the state's own horizon. The Wang Mang hoard is the historical example [S].

### 4.2 Stock, not flow, sets the price

- The price is set by the market in which the holder sells and buys. Households sell from the stock
  when the price clears their reservation, and the reservation rises when the stock is thin. Year's
  mining adds a small amount to a large stock, so the price moves slowly. That falls out of the existing
  `store_offers` and `holding_reservation` if the holdings are large relative to the flow; make sure the
  opening stock is seeded (section 4.5), because an empty opening stock makes the first years behave
  like a flow market, which is the Complaint 442 symptom.

### 4.3 How the ratio can differ by place

- Each market area has its own price for each metal, and carriage between areas costs freight per kg
  plus a risk loading proportional to value. Then the between-area price gap for a metal can be as large
  as the carriage cost per unit of value of that metal and no larger, once traders exist (the freight
  machinery is in `sim/geography/freight_cost.py` and `cargo_cost.py`). Because gold costs much less
  per unit of value to carry, gold prices converge between areas faster than silver prices do, so the
  ratio in a remote area is pulled by the local silver price, which matches the section 1 pattern (silver
  dear and gold cheap where silver is scarce and far from the mines).
- Flows follow the gap beyond the cost. Where silver is dear in area B relative to gold, merchants carry
  silver from A to B and gold the other way, until the gap falls to the carriage cost. Nothing about
  China or Japan appears in the engine; the data are mine locations, regional stocks and routes
  (CLAUDE.md 4.7).
- **Monetary regime.** Where a mint buys one metal at a fixed rate, it adds a standing buyer of that
  metal and creates the band described in section 1.3. The currency spec already has regimes
  (`struck_coin`, `weighed_metal`, and others in `sim/economy/currency.py` and `mint.py`). Which metal a
  region mints is currency data. The sim should not need a rule that "China uses silver"; the regime
  and the mint's buying rate are inputs, and the flows follow from them.
- **Export restrictions and risk** (Melitz's point that a gap can be a cost of arbitrage) are the
  carriage cost and a legal friction, both data on a route.

### 4.4 Data each deposit needs

Existing fields (`id`, `resource`, `lat`, `lon`, `deposit_type`, `endowment`, `ore_grade_kg_per_tonne`,
`depth_class`, `status`, `first_worked`, `source`, `conf`) cover the physical stock and grade. Add or
check, each with a source or a confidence letter, never a guess:

- co-product metals of the same ore body (a lead-silver vein yields silver as a by-product of lead; a
  placer yields gold alone). The ratio of silver to lead in an ore sets how much silver the lead price
  subsidises. This is a physical fact per deposit type, not a price.
- a recovery fraction by technique per deposit type (placer washing, cupellation, amalgamation), tied to
  the technology tree, since amalgamation (1554) opened poor ores [W]. The numbers are not yet
  sourced (section 3).
- the date from which each is reachable by a given actor (first worked, and discovery state), which the
  prospecting module already models (`sim/geography/resources_prospecting.py`).
- an explicit list of the missing districts from section 0 as new entries, each with a coordinate and a
  confidence letter: West African gold, Japanese silver (Iwami and others), Central European silver
  and Hungarian gold, Indian and Chinese gold and silver. The unexplained divergences cannot appear
  without them.

### 4.5 Opening stock

The opening stock of each metal per region is an initial condition (CLAUDE.md 4.1 allows initial
conditions). Derive it by running cumulative deposit output from `first_worked` to the start year less
loss, per region, or accept one authored figure per civilisation with a confidence letter. Seeding is
essential for the stock to dominate the flow.

### 4.6 Minimal first code step and its regression test

**Step 0 (measure; no code change).** Re-run the 442 scratch driver on the current build. Report the
median ratio and what share of savings sits in each metal. The store has landed since 442 was written,
so the symptom may be partly changed. Add the printout to the health command of Complaint 445 if that
exists by then; otherwise leave it as a measurement in the complaint.

**Step 1 (smallest behaviour change).** In `sim/economy/households_store.py`, change how
`store_candidates` weights goods: replace the fixed inverse-carrying-cost split with a split that
shifts toward goods whose price looks low against their carrying return, so the budget split between
two qualifying metals is no longer set at a near one to one. Keep it a pure function on a tiny fixture.

Regression test (name it e.g. `sim/tests/test_economy_store_ratio.py`, `QUICK_TOPIC = True` because it
runs on functions and a small fixture in well under a second, per CLAUDE.md section 6):

- Fixture: reuse `sim/tests/economy_store_view.py` and `economy_fixture`, with two durable high-value
  metal goods, one dearer per kg than the other, one cohort of fixed wealth, and a stub market view that
  returns prices and stocks.
- Assert 1 (current behaviour, write first and watch it fail or pass as measured): with equal stocks of
  the two metals by mass and the same wealth, the two metals' value budgets are within a few percent.
  This shows the hardcoded near-equal split.
- Assert 2 (target behaviour): with a stock of one metal ten times the other by mass, the equilibrium
  price per kg of the scarcer metal is higher than the other's by a factor between 1 and 10 and rises
  as the stock gap widens. Solve by iterating the clearing price a fixed number of steps in the test,
  no whole-game build.
- Assert 3 (no ids): swapping the two good ids changes nothing about the result.
- Assert 4 (carriage): add a second market area with a freight cost per kg; the gap between the two
  areas' prices for the dearer-per-kg metal in percentage terms is smaller than for the cheaper one.

Assert 4 can be a second small test (still quick) if the first grows. A whole-game check, that Rome's
ratio lands in a plausible band over an ensemble of seeds, belongs to a slow topic and to the
fingerprint, never a target set in code (CLAUDE.md 4.2).

### 4.7 Risks to test for

- A flow market masquerading as a stock market if the opening stock is zero: gold's price will swing by
  more than its own value (the Complaint 442 symptom). Seeding cures it; test that the first ten years'
  price movement is smaller than the second ten years' of a flow-only model.
- A one-metal lock-in: the metal overvalued by the mint takes all coin demand and the other is hoarded.
  Historically correct (Gresham, section 1.3) but it looks like a bug; document it.
- The unit-elastic trap: the existing `assert STORE_CHOICE_ELASTICITY < 1.0` guards against a price rise
  raising its own demand. Keep it for any new weighting.
- Hidden outcome through data: do not author a ratio in any file, and do not choose stocks to hit one.
  A cross-check against the section 1 band is a validation, not an input.

---

## 5. Source list (all fetched or surfaced in this session)

Read to the extent stated; ordered by how much weight to give them.

1. James Ross and Leigh Bettenay, "Gold and Silver: Relative Values in the Ancient Past", Cambridge
   Archaeological Journal, online 28 Nov 2023. https://www.cambridge.org/core/product/406D8B078C66ACB266932D51A0E2F205/core-reader
   (summary only; full text did not decode).
2. Jacques Melitz, "Some Doubts about the Economic Analysis of the Flow of Silver to China in 1550-1820",
   CEPII working paper 2017-19. https://imap.cepii.fr/PDF_PUB/wp/2017/wp2017-19.pdf (abstract only).
3. Peter Munro (Toronto), medieval money teaching notes citing Frederic Lane.
   https://www.economics.utoronto.ca/munro5/L03AMedievalMoney.pdf (search summary).
4. American Numismatic Society, Roman ratio table by emperor.
   https://numismatics.org/digitallibrary/ark%3A/53695/nnan92614 (search summary).
5. Newton Project, Isaac Newton, report to the Treasury, 21 September 1717 (MINT00322).
   https://newtonproject.ox.ac.uk/catalogue/record/MINT00322 (catalogue entry via search summary).
6. Nipponica / Kotobank entry on the gold-silver ratio in Japan.
   https://kotobank.jp/word/%E9%87%91%E9%8A%80%E6%AF%94%E4%BE%A1-54075 (search summary).
7. American Numismatic Society, "Gold Coinage in Pre-Meiji Japan". https://numismatics.org/pocketchange/koshu/
8. CEPR/VoxEU MacroHistory seminar deck, East India Company silver arbitrage (authors not identified).
   https://voxeu.org/system/files/2023-05/EIC%20silver%20arbitrage%20MacroHist%20Seminar.pdf (summary;
   direct fetch returned 403).
9. World Gold Council gold supply and stock pages. https://www.gold.org/goldhub/data/how-much-gold
10. Silver Institute, "Silver Mining in History". https://silverinstitute.org/?p=239 ; LSE, "The new
    world and the global silver economy, 1500-1800". https://researchonline.lse.ac.uk/id/eprint/119884
11. Wikipedia: Aureus, Las Medulas, Mines of Laurion, Patio process, Potosi, Brazilian gold rush,
    Economy of the Mughal Empire, Han dynasty coinage, Abundance of elements in Earth's crust (weak).
12. Academia Sinica IHP bulletin article on Han gold. https://www1.ihp.sinica.edu.tw/Publications/Bulletin/955/Article/873
13. To read before relying on any number: Flynn and Giraldez (1995, 2002); Soetbeer (1879); Redish
    (2000); Friedman (1990); Spufford, Money and its Use in Medieval Europe (1988) (search could not
    open its text); the Manning, Flynn and Wang silver-circulation series; Pliny, Natural History 33.

## 6. Open items

- Resolve the Las Medulas grade conflict (0.3 g per tonne in the repo against "3 grams" in one web
  source) from a primary source.
- Find a sourced Han (and other early Chinese) gold to silver or gold to copper relation; searches
  found none.
- Find recovery rates by technique and an era-by-era world output table; searches found none.
- Read Flynn and Giraldez and Melitz in full before fixing any freight or risk parameters for
  silver routes.
