# Household wealth and land concentration in pre-modern societies

Research report for Complaints 606 (the savings wish), 607 (the opening income leaks saving) and 538 (land never
changes hands). It adds to `research-pre-modern-interest-rates.md` and `research-reference-economy-models.md` and
does not replace them. Per CLAUDE.md section 6 ("Sources are read, not recalled"), every figure below carries the
source it came from and how I met it.

## Sourcing key

- OPENED: I read the text in this session. Local copies of the PDFs were kept in the session scratchpad (`refs/`).
- SNIPPET ONLY: seen only in a search-result summary; not opened. Do not copy it anywhere without opening the source.
- NO SOURCE FOUND: I looked and found nothing I could open.
- "Reading" marks my own inference from what I opened. It is not a claim by the source.
- Figures are the sources', not this project's. Per CLAUDE.md 4.1 and 4.2 none goes into the simulator as a value;
  they are validation ranges for a measured outcome, never targets.

Sources opened (short names used below):

| Short name | Source | How met |
|---|---|---|
| PZ | Piketty and Zucman, "Capital is back: wealth-income ratios in rich countries 1700-2010", Quarterly Journal of Economics 129(3), 2014, accepted version https://researchonline.lse.ac.uk/id/eprint/66106/1/Zucman_Capital%20is%20back.pdf | OPENED, section VII.A text |
| Sch19 | Scheidel, "Roman wealth and wealth inequality in comparative perspective", Stanford working paper v1, 2019, https://zenodo.org/records/3458611 | OPENED in full |
| ABS | Alfani, Bolla and Scheidel, "A comparison of income inequality in the Roman and Chinese Han empires", Nature Communications 2025, https://doi.org/10.1038/s41467-025-58581-0 (PDF https://iris.unibocconi.it/retrieve/afc74823-36a4-4b06-8c54-a5c3b19ed701/AlfaniBollaScheidel_InequalityAncientEmpires.pdf) | OPENED the text around the Gini results; not read in full |
| AGM | Alfani and Garcia Montero, "Wealth inequality in pre-industrial England: a long-term view (late thirteenth to sixteenth centuries)", Economic History Review 75(4), 2022, https://iris.unibocconi.it/retrieve/fa3452f6-419c-40e4-9c9a-03648a0365e0/Alfani%26GarciaMontero_EHR2022.pdf | OPENED, Tables 3 to 6 and the Black Death discussion |
| BR | Bekar and Reed, "Risk, asset markets and inequality: evidence from medieval England", Oxford Discussion Papers in Economic and Social History 79, 2009, https://www.nuff.ox.ac.uk/Economics/History/Paper79/Bekar%20and%20Reed%2079.pdf (published as "Land markets and inequality", European Review of Economic History 17(3), 2013) | OPENED the working paper; the journal version not opened |
| Kum | Kumon, "Wealth inequality in pre-industrial rural England", IAST working paper 124, 2021, https://publications.ut-capitole.fr/43951/1/wp_iast_124.pdf | OPENED the abstract, introduction and the Hundred Rolls section |
| CS | Carroll and Shanker, "Theoretical foundations of buffer stock saving", version 2025-12-05, https://econ-ark.github.io/BufferStockTheory/BufferStockTheory.pdf | OPENED the introduction and the assumptions list; the proofs not read |
| King | Gregory King's 1688 table as printed in Barnett (ed.), Two Tracts, 1936, via https://www.york.ac.uk/depts/maths/histstat/king.htm | OPENED (a transcription; the page text had two illegible cells) |
| Plut | Plutarch, Life of Tiberius Gracchus 8, Loeb 1921, https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Plutarch/Lives/Tiberius_Gracchus*.html | OPENED |
| App | Appian, Civil Wars 1.7 to 1.8, Loeb (White), https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Appian/Civil_Wars/1*.html | OPENED |
| Brig | Briggs, "Manorial court roll inventories as evidence for English peasant consumption and living standards, c.1270-c.1420" (summary page https://www.medievalists.net/2011/02/manorial-court-roll-inventories-as-evidence-for-english-peasant-consumption-and-living-standards-c-1270-c-1420/) | OPENED the summary page only; the paper (http://www.uv.es/consum/briggs.pdf) returned HTTP 404 |
| JBF | Jervis, Briggs, Forward et al. dataset and article, https://intarch.ac.uk/journal/issue56/14/full-text.html | OPENED; it contains no value figures |

---

## 1. Household wealth as a multiple of annual income (606, 607)

### 1.1 Headline answer

**No source found** for a household-level multiple by stratum (peasant, artisan, merchant, landowner) built from
probate inventories, dowry contracts, tomb inventories or land-sale contracts. What I could open gives (a) national
wealth over national income, with the land share, which bounds the average; (b) the distribution of wealth across
households, which says how far the median sits below the average; and (c) qualitative composition of poor
households' goods. A stratum multiple can only be a Reading from (a) and (b), and I flag it where I make one.

### 1.2 National wealth over national income (OPENED)

- PZ, section VII.A: "National wealth always seems to be between six and eight years of national income from 1700 to
  1914 in both [the United Kingdom and France], with no obvious long-run trend." They add that the raw data for those
  centuries are "insufficient to precisely compare the levels" between countries or subperiods.
- PZ, same section: "Agricultural land - including land improvement of all sorts - was between four and five years of
  national income around 1700". Net foreign assets were "virtually zero in the eighteenth century".
- PZ, same section: much of the land value "actually derived from past investment" (spending on drainage, irrigation
  and the like "could be as large as 3-4% of national income"); the "pure land value" is put around one year of
  national income (Paine 1795, in PZ footnote 57), with a stated range of under half a year to 1.5 years.
- PZ, section VII.B: agricultural land was three to four years of national income in Old Europe against one to two in
  the United States around 1770 to 1810, because land was abundant there (price effect). That is a rate-and-scarcity
  mechanism, not a constant.
- PZ states the steady-state relation wealth/income = saving rate / growth rate, and notes that for growth near 0.5 to
  1 percent "whether the net saving rate is s = 5% or s = 8% is going to matter a lot".
- Sch19 applies the French 1700 ratio (Sch19 quotes it as seven times income, with almost two thirds in agricultural
  land and the rest split between housing and other domestic capital) to Rome and obtains total wealth about seven
  times GDP, then (his own analogy-based disaggregation) agricultural land about 90, housing 20, other domestic
  capital 20 and slaves 10, out of about 140 billion sesterces. He says plainly that this is "rough and ready" and
  by analogy. He also cites Goldsmith (1987) at 8.2 times GDP with land at 5.5 times GDP, derived from "17 times annual
  yields of 6 percent". Using PZ's ratio, Sch19 gets implied saving for Rome of "a little over 1.5 percent of GDP"
  from beta 7 to 8 and growth 0.2 to 0.25 percent, "a minuscule amount", so accumulation was very slow.
- Coin share: Sch19 cites Gregory King as putting coinage "less than 4 percent of all wealth in England near the end of
  the seventeenth century" and judges Duncan-Jones's Rome figure (coin about one-seventh of wealth) "likely to be
  inflated". The same King figure is in `research-pre-modern-interest-rates.md` item 23. I did not open King's wealth
  breakdown itself; the 4 percent is Scheidel's report of it.

Reading for 606/607: a society's average wealth is several years of income and most of it is land at a capitalised
rent. Coin is a small part. So a household wish for "two years of surplus income plus a cash buffer" is not
implausible in size; what is implausible is holding it as cash. This agrees with the 2026-10-20 note in 606.

### 1.3 How unequal households' wealth was (OPENED), which sets the median against the mean

- Sch19: "top 1 percent wealth shares in several European countries ranged from about one-third to a little more than
  half of national wealth: c.35 percent in Finland, c.45 percent in France and Norway, c.50 percent in Sweden, and
  c.55 percent in Denmark and the United Kingdom" around 1770 to 1810. His working assumption for Rome is a top 1
  percent wealth share around one half and a top 1 percent income share around one fifth, both guesses constrained by
  GDP and an extraction rate.
- AGM, Table 6 (English lay subsidies, taxes on movable goods, with a reconstruction of the households below the tax
  threshold by a lognormal fit): Gini of movable wealth 0.725 in 1327 to 1332 (95 percent interval 0.723 to 0.726; 0.753
  on an alternative population) and 0.756 in 1524 to 1525. Share of the richest 10 percent 60.3 percent then 64.1
  percent; top 1 percent 21.5 then 24.5; poorest 10 percent 0.2 percent. County Ginis in 1327 to 1332 range from 0.455
  (Devon) to 0.798 (Kent), London 0.953. These are movable goods (coin, circulating capital, household goods, stock,
  grain), not land.
- AGM's observed (taxpayer-only) distributions give lower Ginis (0.423 and 0.657) because the poorest households were
  exempt; the reconstruction is the authors' modelling assumption (lognormal), which they say is a method choice.
- Reading: if the poorest tenth hold almost nothing and the richest tenth hold about three fifths of movable wealth,
  the median household's movable wealth is well under the mean. Any single "years of surplus income" figure applied
  to every household would overstate the poor's holdings, which is the observed failure of 606's wish.

### 1.4 Composition of poor and middling households' holdings

- Brig (summary page, OPENED): peasants c.1270 to c.1420 "owned many fewer household goods than their counterparts in
  later periods" and invested "in the productive side of their holdings, especially in livestock and fodder"; the
  inventories "most certainly omit objects". No figure for the share or the value is on the page that I opened. The
  paper itself: NO SOURCE FOUND (404).
- JBF (OPENED): the escheator and coroner inventories (felons' and fugitives' goods) cover some of the poorest people.
  Referee Dyer's note: written sources are biased toward valuable items such as metal pots and omit small cheap ones.
  The article gives no value totals. The underlying database is at the Archaeology Data Service (doi 10.5284/1085022);
  I did not open it. Computing inventory value over annual income from it would be a measurable project task, not a
  recalled figure.
- Roman Egypt dowries: SNIPPET ONLY, a Berlin papyrus catalogue entry of a 1,100 drachma dowry made largely of clothing
  and 100 silver drachmas, and an Oxyrhynchus contract of AD 260 with clothing at 620 drachmas
  (https://berlpap.smb.museum/heiratsvertrag/?lang=en). A median or distribution of dowries: NO SOURCE FOUND.
  Bagnall and Frier, The Demography of Roman Egypt: only the Cambridge landing pages surfaced, not the text.
- Roman Egypt prices as quoted in Sch19 footnotes (OPENED): 26 house prices from the 60s to the 170s AD "average close
  to 700 drachmas/sesterces; only 6 of them exceeded 1,000" (citing Drexhage 1991, not opened); arable farmland about 200
  drachmas per aroura (0.276 ha) in the second century (citing Scheidel 2002, not opened); Augustus's veteran grant of
  5,500 sesterces would buy 20 iugera at 275 per iugerum.
- Han tomb inventories, Han land sale contracts, Domesday valuations as household wealth, Mexica household or calpulli
  holdings by value: NO SOURCE FOUND. A Hanshu passage (Chao Cuo's memorial on valuing grain) was searched for; the
  Chinese Text Project page returned an access notice saying automated access is not authorised, and I did not
  circumvent it.

### 1.5 Income by rank, for scale (OPENED)

King (1688, England): yearly income per family 84 and 50 for two classes of freeholders, 44 for farmers, 40 for
artisans, 45 for shopkeepers and tradesmen, 200 and 400 for two classes of sea merchants, 15 for labouring people,
6.5 for cottagers and paupers, 2,800 for temporal lords. King classes 511,586 families as "increasing the wealth of
the kingdom" (average 67) and 849,000 as "decreasing" it (average 10.5). The transcription has no wealth column.
Two other transcriptions seen only in a search result differ slightly; Arkell and Allen and Lindert-Williamson
critiques were not opened. This table gives income, not savings.

### 1.6 What the modelling literature does

- Carroll and Shanker (CS, OPENED, introduction): a consumer who would otherwise run down resources "will (when shocks
  are present) experience an intensifying precautionary motive as their buffering capacity shrinks", so there is a
  "target" "defined as the point where the precautionary motive to accumulate becomes exactly strong enough to counter
  the impatience motive to decumulate" (starting with Deaton 1991). The paper states conditions ("return impatience",
  "growth impatience", "strong growth impatience") under which a consumption function and a target exist; if they fail
  the limiting consumption function can be degenerate. I did not read the proofs.
- Previous report (`research-reference-economy-models.md`, sections 2 and 3, read by a different session, not re-opened
  by me): Eurace's household rule is income plus a small fraction of the gap to a target wealth/income ratio, and its
  initial balance sheets are set from multiples of income chosen by the authors (not data); HARK solves the buffer-stock
  problem and finds the target by the zero-expected-change condition.
- No source found for a published calibration of discount factor and risk aversion for a pre-modern household. Carroll
  and Shanker's calibrations are for a modern consumer and are not a basis for the project's values.

### 1.7 What rule would make the multiple emerge

Structure only. Nothing here is a value.

1. **Desired holding is a function, not a stored multiple.** Wealth wanted = target buffer + wealth wanted for yield.
   The buffer target comes from the household's own income risk: the project already simulates harvest and weather, so
   the variance of the household's income over the years is a measurement, not a typed number. A household that can
   cover a bad year from stores and a fall in the work it can sell holds enough for that, and no more. This is the
   Carroll/Deaton target (CS), computed on the project's own harvest series.
2. **Holding by asset, with each asset's own return and liquidity.** Stores of grain (working capital the household
   needs anyway between harvests), livestock and tools (productive; Brig says peasants put saving here), coin (a
   transactions and emergency buffer, a small part by King via Sch19), house, and land title at a capitalised rent. The
   wealth to income multiple is then an output: land value = rent / rate (the interest-rate report has the rent/price
   series and the point that land is one alternative among assets), so a lower real rate or scarcer land raises it, which is
   the PZ and Sch19 mechanism (beta = s/g) and the PZ land-abundance effect.
3. **Savings flow is the gap to the target.** A household saves when wealth is below target and draws down above it,
   which gives the drawdown rule that replaces `WEALTH_DRAWDOWN_LIMIT` (Eurace's one-line version, or the full
   consumption function, are two ways).
4. **Existence check as a test.** CS's impatience conditions are inequalities on discount, rate, growth and shock
   variance. A test that a configuration has a resting point calls the rule directly (CLAUDE.md section 6).
5. **Validation, not target.** After a long run, aggregate wealth over income by the mix of land, housing and other, and
   the median-to-mean ratio of household wealth, are compared with the ranges in 1.2 and 1.3. A pre-modern run that
   holds most wealth in land at a rate near the interest rate, and has a thin top that holds around half, is within
   the sources; a run that holds it in coin is not.
6. **Where the opening starts.** The opening should hold its households at the target by assets (land titles first,
   538), so the fixed point is not at the floors. This is the direction 607 already notes (2026-10-20).

---

## 2. Land concentration (538)

All of these are validation ranges for a full-game measurement, not targets. They differ in what they measure (value
of movable goods, acres held, income) and the unit of the Gini (households, holders, adult males) and in whether the
landless are counted; the table records each.

### 2.1 Measured values (OPENED unless marked)

| Setting | Measure | Value | Source |
|---|---|---|---|
| England 1086 (Domesday), unfree and free peasants | simulation seed Gini on land, from the distribution of virgate classes | 0.135 | BR (their model's starting value, built from Domesday shares) |
| England 1086 | share of rural population and of land: villani 41 percent of population and 45 percent of land; bordars and cottars 32 and 5; free men 14 and 20; servi mostly landless | as stated | BR table note citing Miller and Hatcher 1978 |
| England 1279-80 (Hundred Rolls) | peasant land Gini, landless ignored | about 0.59 (Cambridgeshire, Huntingdonshire, Oxfordshire, Warwickshire; data from Kanzaka 2002) | Kum |
| England 1279-80 | peasant land Gini with the landless set at 47 percent of the rural population (Campbell 2008) | about 0.78 | Kum |
| England 1279-80 | share of free peasant households with holdings large enough to reach subsistence without wage income | 15 to 30 percent depending on the number of landless | BR |
| England 1279-80 | simulated Gini on land after 120 years of land sales, partible inheritance and growth, from 0.135 | 0.625 (sd 0.026), against a measured distribution of 12.8 percent large, 8.2 middle, 79 poor holdings | BR |
| England, parliamentary enclosure parishes, 18th to 19th century | land Gini including the landless; landless 40 to 50 percent of the population | 0.65 to 0.82 | Kum |
| England 1327-32 and 1524-5 | Gini of movable wealth (not land) | 0.725 to 0.756 | AGM |
| Roman Egypt, Hermopolis and Antinoopolis, c.350 AD | Gini of land held by certain urban residents | 0.715 (n=301), 0.758 (n=441) | Sch19, citing Bowman 1985 and Bagnall 1992 (not opened) |
| Roman Egypt villages | private land Gini: Karanis 308-9 AD 0.478 (n=110 villagers; 0.431 with leaseholds), 0.626 for 18 non-resident owners; Philadelphia 216 AD 0.518 (n=183); Kerkeosiris 116-115 BC 0.374 (n=63, including military allotments and crown leases); Aphrodito c.525-6 AD, 49 urban landlords 0.623 | as stated | Sch19 |
| Roman Empire c.165 AD | income Gini | 0.46 (earlier estimate 0.42 to 0.44) | ABS; Sch19 |
| Han Empire c.2 AD | income Gini | 0.48 | ABS |
| Aztec Empire c.1492 | income Gini | 0.50 | ABS |
| Roman Empire | top 1 percent: wealth share about one half, income share about one fifth | working assumption by analogy | Sch19 |
| Europe 1770 to 1810 | top 1 percent wealth share 35 to 55 percent by country | as stated | Sch19 |

Caveats the sources themselves give: Sch19 says the Egyptian registers "none ... supports a reconstruction of the
distribution of all land even for a single district"; the village figures are lower than the urban-owner ones, so
whole-district Ginis would be lower than the urban registers (his conjecture). Kum notes the Hundred Rolls give acres
not value, omit the landless (so the 47 percent is an assumption) and aggregate across villages (biasing Gini up).
The Gini for Rome, Han and Mexica is of income, not land, and is a model output from social tables.

Land-specific figures for Han China (top-decile or Gini of land), Mexica (noble against calpulli land) and Rome (land
Gini, not income): **NO SOURCE FOUND**. The Wikipedia calpulli page I opened has no land proportions; Hicks 1982 and
Carrasco were not reachable.

### 2.2 Mechanisms and what the sources say about them

- **Harvest-shock debt and distress sales (England).** BR: twelfth-century property-rights changes let peasants use
  land sales to manage risk; their simulation shows distress sales interacting with population growth raise the land
  Gini from 0.135 to 0.625. Switching off the land market leaves the demographic effect alone producing about a 54
  percent rise (0.135 to 0.208); switching off population growth leaves land trades alone producing about a 120
  percent rise (0.135 to 0.297). Reading from their text: about 15 percent of the total change is the demographic
  effect and about 33 percent the land market effect, the rest an interaction. They report the seed is built from
  Domesday classes and the target from Hundred Rolls classes, and that high-fertility large-holding households
  matter (they cite Clark and Hamilton 2006 for large holders having more children). This is the closest published
  model to what 538 builds (titles, collateral, foreclosure) and its mechanisms (partible inheritance, land market,
  fertility by holding) map onto the built pieces.
- **Partible inheritance as a counter-force.** BR: demographic effects with partible inheritance and no land market
  produce a tightly clustered middle distribution (71 percent holding 6 to 10 acres). AGM: partible inheritance
  "led to wealth being divided more evenly among the survivors" and inflated the market for real estate after 1348
  (their reading, with citations I did not open).
- **Plague and labour scarcity (England 1348 on).** AGM: observed benchmarks bracket the Black Death on either side
  (1327-32 and 1524-5), so the post-1348 trough is not measured for England: "we remain in the dark about the
  distributive consequences of the Black Death", and the decline is inferred from other European countries (their
  discussion cites higher real wages and the inheritance mechanism). My search snippets reported a 15 to 20 percent
  fall in the top decile's share elsewhere; I did not verify that in the opened text and do not rely on it.
- **Roman Republic.** Plut 8.1 to 8.3 (Loeb 1921): conquered land was made common and assigned to the poor at a small rent;
  "when the rich began to offer larger rents and drove out the poor" a law limited holdings to five hundred acres
  (jugera); the rich then "by means of fictitious personages" took the rentals over and held most of the land
  openly; the ejected poor stopped rearing children and Italy filled with "gangs of foreign slaves". App 1.7 to 1.8: a
  law that nobody should hold more than 500 jugera or pasture more than 100 cattle or 500 sheep, with a rule that a
  number of freemen be employed to watch, but "there was not the smallest consideration shown for the law or the
  oaths". These are ancient narrative accounts, not distributions; no figure for the concentration they describe is in them.
  I did not open the sources for the reform's effect after 133 BC.
- **Han China.** ABS (OPENED): Wang Mang launched "a vast program of land reform aimed at reducing inequalities in
  land ownership"; the reforms "rapidly failed, largely due to the resistance of the great landowning families and of
  local officials kin to them". The 7 BC limits under Emperor Ai: the Wikipedia article I opened describes a proposal
  capping servants (not land), and says Ai issued only a limited version, so the land-limit edict as a mechanism is
  unconfirmed in what I opened (a search snippet from a course page mentions a limit of 3,000 mu for 8 to 7 BC;
  SNIPPET ONLY).
- **Dispersion by village against owner class.** Sch19's Egyptian figures: urban owners hold far more concentrated
  land than village residents, and non-resident landlords more than residents. A model whose absentee holders lend
  and foreclose should produce this contrast.
- **Tax and unrest as a limit.** ABS argues high extraction left parts of Han China "less resilient against crises"
  and links the failure of reform to rebellion; that is the authors' argument about extraction ratios, not a measured
  land effect.

### 2.3 Reading of the ranges for the check in `sim/economy/titles_concentration.py`

The test comment says the band is "recalled, not looked up". Using only what I opened:

- Land Gini among landholders only (landless excluded), medieval English villages: around 0.6 (Kum 0.59, BR sim 0.625
  after 120 years). A generation of foreclosure from a near-equal start should climb toward that range, and should
  not stop near the seed.
- Land Gini with the landless counted: 0.65 to 0.82 (Kum, with a 40 to 50 percent landless share); the choice of
  whether the landless enter the denominator moves the figure by about 0.2 in the Hundred Rolls case (0.59 to 0.78), so the check
  must say which it computes.
- Roman Egypt private land: village 0.37 to 0.52, urban owners 0.62 to 0.76.
- Movable wealth among households: 0.7 to 0.76 for England, top decile around 60 percent.

These are what the sources show; a band for the check is a choice for the owner, made with the denominator stated.

---

## 3. How to model it (structure only)

1. **Wealth wanted is derived** (section 1.7): buffer target from the household's own income variance plus yield-seeking
   holdings in assets that exist (land titles, stores, stock, coin, house). The multiple falls out and is measured
   against sections 1.2 and 1.3 afterwards.
2. **Land is the main store of value.** Titles are priced at capitalised rent (rate-dependent, per the interest-rate
   report), and the savings wish is met by buying titles. The built titles, collateral and foreclosure mechanism
   (538) is the asset the opening lacks (606's note).
3. **Concentration comes from the BR channels**: a land market that clears with distress sales when harvests fail,
   fertility that is higher for larger holdings (the project needs households that have children and die; 538 lists
   this as missing), partible inheritance as a counter-force, and the plague or labour shock as a drop in the price
   labour accepts and a rise in land supply (inheritance and vacancy). Each channel can be switched off in a test, as
   BR do, to show its contribution.
4. **State action is a policy lever**, not a schedule: a holdings cap with an enforcement rule (Appian: freemen
   watchers; the cap was evaded through relatives and nominees, so enforcement and evasion are both mechanisms), a
   debt-relief or redistribution choice (already built as `debt_relief`), and the reform's failure through the power
   of large holders (ABS). No dated edict is encoded (CLAUDE.md 4.2, 4.7).
5. **Validation is a distribution check** run over an ensemble: land Gini with the denominator stated, share of
   households with holdings below subsistence, top-decile share, and aggregate wealth over income. Ranges from
   sections 1.2, 1.3 and 2.1; dated events are never checked.

---

## 4. Recommendation

**606 (the savings wish).** Do not keep a stored years-of-income figure. Replace it with a buffer target computed from
the household's own income variance, and a yield-seeking wish held in land titles, stores and stock; keep a coin
buffer small. Evidence for the size of the aggregate: PZ gives national wealth of six to eight years of income for
England and France 1700 to 1914 with land four to five, and Sch19 applies the same ratio to Rome. A per-household
stratum multiple has no source (probate, dowry, Han contracts, Mexica holdings: none opened). So the wealth ratio
should be validated at the aggregate and by the median-to-mean ratio (AGM), not typed. The existing statement in 606
that the wish is not implausible in size stands; the fix is the asset it is held in.

**607 (opening income leaks saving).** The leak closes by giving saving an asset: seed titles at capitalised rent and
make the opening hold its households at the derived target by assets, so the fixed point is not at the floors. Use
Eurace's initial-balance-sheet practice (read in the earlier report) only as structure: consistent stocks from ratios,
with the ratios derived from the rule above, not chosen. No source supports a specific saving rate; PZ's relation
wealth/income = saving/growth gives a consistency check (a saving rate of a few percent at near-zero growth reaches
the observed multiple) and Sch19 uses it to show how slow accumulation was.

**538 (land concentration).** The built channels (collateral, foreclosure into tenancy, partible inheritance,
management cost, debt relief) match BR's mechanisms. What is still open and now has a published reference model:
fertility by holding size (needs household birth and death), a land market that responds to harvest failure, a labour
shock that moves rents and land supply, and a cap law with enforcement and evasion. Replace the "recalled" band in
the range check with a table per denominator (section 2.3) and say which one it computes. The Han and Mexica ranges
are unsourced (**NO SOURCE FOUND**); leave their checks as "no band" instead of reusing the English one.

## 5. Not done, and the next step

- Opening the Briggs paper, the ADS database (doi 10.5284/1085022) and the Jervis et al. book (Cardiff University
  Press, 2023, https://cardiffuniversitypress.org/site/books/10.18573/book10; OAPEN blocked automated access) to compute
  inventory value over annual income by class. This is a data job and would give the first sourced peasant multiple.
- Scheidel and Friesen 2009 (Journal of Roman Studies 99), which gives household income by class for Rome: not
  opened (no free copy reached); only secondary reports of its headline figures were seen, so none is quoted.
- Alfani, "Economic inequality in preindustrial times" (JEL 2021): abstract seen only in a search result.
- Han: Hanshu Shihuozhi, Chao Cuo and Dong Zhongshu passages, and any Han land sale contract: not reached.
- Mexica: Hicks, Carrasco and Berdan on calpulli and noble land: not reached.
- Roman Egypt dowries, Bagnall and Frier chapters on property and marriage: not reached.
