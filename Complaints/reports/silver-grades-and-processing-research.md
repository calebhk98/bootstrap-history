# Silver grades and processing: second research pass for Complaint 349

Research report. No code or data was edited. Every figure is a candidate input, not a decision. CLAUDE.md 4.1 and 4.5 apply: a grade or a yield is a physical fact and is never moved to reach an attested wage or hours-per-kilogram figure.

This extends, and does not repeat, `precious-metal-mining-sources.md` (Bettenay 2022 tables, Strabo, Klemm, Agricola and Pryce figures, Rio Tinto at about 0.2 percent silver in jarosite). Read that first. What is new here: Merkel 2020 on silver grades by district, Cordella 1893 assays of ancient Laurion dumps and slimes, Wood et al. 2021 on Laurion ore assays, summary-level wheel and screw lift rates from Landels via a web page, a check of what Domergue, Davies, Hopper and Conophagos can and cannot be shown to say from sources reachable here, and a sensitivity run of the model.

## Provenance tags

- **READ**: I opened the text (PDF converted to text, or the full page) and took the figure from it. Page, section or table given.
- **READ-2**: read in a full text that quotes another author; the primary was not opened.
- **SUMMARY**: seen in a web page that summarises a primary I could not open. Treat as a lead.
- **SNIPPET**: seen only in a search-result summary. Not verified.
- **DERIVED**: my arithmetic from the cited inputs; the inputs are shown.
- **RECALLED**: from memory; must be checked.

Confidence letters follow `data/production/_SCHEMA.md` (A well attested, B probable, C estimate, D lead only), assigned to the figure as a replacement value.

Opened in full this pass:

- Merkel, S. 2020. The Richness of Silver Ore in the Middle Ages: A Comparative Study of Historical Descriptions and the Archaeological Evidence. Der Anschnitt, Beiheft 45, pp. 39-44. https://omp.ub.rub.de/index.php/DBM/catalog/download/170/146/1251?inline=1 (READ, all six pages).
- Cordella, A. 1893. The Mining and Metallurgical Industries of Laurium, for the Exhibition of Chicago. https://archive.org/details/miningmetallurgi00cord (READ via the archive.org OCR text; the pamphlet is about 17 kilobytes, pp. 3-9 used).
- Wood, J. R., Hsu, Y.-T., Bell, C. 2021. Sending Laurion Back to the Future: Bronze Age Silver and the Source of Confusion. Internet Archaeology 56. https://intarch.ac.uk/journal/issue56/9/full-text.html (READ for characters 0 to 200,000 of 261,000; the last 61,000 were not read).
- Morin-Hamon, H. 2023. Flat-bedded washeries at Laurion (Greece): a buddling model. Der Anschnitt, Beiheft 50, pp. 213-233. https://omp.ub.rub.de/index.php/DBM/catalog/download/264/241/1502?inline=1 (READ; it contains only dimensions of a single washery, no throughput, water volume or grade, so nothing usable came out).
- Hirt, A. M. Gold and Silver Mining in the Roman Empire. https://livrepository.liverpool.ac.uk/3066254/3/Hirt%20Warwick%20Publ.%20III%20(revised).pdf (READ; institutional and legal, no grades, labour or drainage quantities).
- Burghardt, I. 2018. Der saechsisch-meissnische Silberbergbau im Spaetmittelalter (1350-1470). Der Anschnitt 2018/5. https://www.bergbaumuseum.de/fileadmin/forschung/zeitschriften/der-anschnitt/2018/2018-05/anschnitt-5-2018-ivonne-burghardt-der-saechsisch-meissnische-silberbergbau-im-spaetmittelalter-1350-147.pdf (READ; economic history, no ore grade; one workforce figure).

Not obtainable (HTTP 403, bot wall, or no open copy): Davies 1935 (Roman Mines in Europe), Domergue 1987 and 1990, Hopper 1968, Healy 1978, Conophagos 1980 (Le Laurium antique), Kakavogianni et al. 2008, Anguilano et al. 2010 and 2012 (the UCL and Huelva repository copies returned 403 or an Anubis wall), Bakewell 1975, 1977 and 1984 on Potosi (publisher 403), Berg 1988 on Kongsberg, Kora 1950 on Kutna Hora, the Heidelberg Ming-Qing silver notes (site down). Everything below attributed to these is therefore SUMMARY or SNIPPET.

## 1. What the named authors actually say

The complaint names Davies, Domergue and Hopper. None of their primary texts was reachable. What could be established:

| Author | What was seen | Strength |
|---|---|---|
| Domergue 1990 (Les mines de la peninsule iberique) | Cited by a CSIC paper (Mines, Territorial Organization, and Social ..., https://digital.csic.es/bitstream/10261/345333/1/Mines_Territorial_Organization.pdf, pp. 241-77 of Domergue) for a yield statement. The extracted text was garbled; as best read it says silver of 1,000 to 1,500 grams per tonne of lead. I could not confirm the basis. | SNIPPET |
| Domergue 1987 | Cited on an ancient-mining page (https://earthsci.org/mineral/mindep/ancient_mine/deep-vein_mining.html) for the Plasenzuela silver-lead district being exploited for about 100 years, from about 20 BC to about 80 AD. No grade given there. | SUMMARY |
| Davies 1935 | Cited on the same page for: ore buckets holding about 150 litres (p. 25), curved iron picks with 8 to 9 inch blades (p. 32), screw angles (p. 28), nine wheels found at San Domingos (pp. 26-27). No grade, labour per tonne or inflow. | SUMMARY |
| Healy 1978 | Same page: temperature rises about 1 degree Celsius per 30 m of depth (p. 82); hammers of 5 to 10 pounds (p. 100). | SUMMARY |
| Hopper 1968 | Cited in Wood et al. 2021 only for general claims; no numbers in the text read. | READ (no figures) |
| Conophagos 1980 | Cited in Wood et al. 2021 as a bibliography entry and in Bettenay 2022 (via the prior report) for 0.1 to 0.2 percent silver in Laurion lead metal. No other number found in anything opened. | READ (no figures) |
| Kakavogianni et al. 2008 | Cited in Wood et al. 2021 only for slag finds in the Mesogeia. | READ (no figures) |

Plain conclusion: the complaint's suggestion that Davies, Domergue and Hopper hold the Spanish and Laurion ore grades cannot be settled from open sources. Domergue 1990 (and his 2008 Les mines antiques) is the one text to obtain by interlibrary loan; no open copy turned up.

## 2. Ore grade, by district

Unit warning: much of the archaeometallurgical literature quotes silver as a percentage of the lead metal, not of the ore. The model's `ore_grade_kg_per_tonne` is metal per tonne of ore as presented to dressing. Converting needs the lead content of the ore (galena fraction), shown where used.

| District | Value | Unit and basis | Source | Strength | Notes for the model |
|---|---|---|---|---|---|
| Laurion, hand-picked ore samples | 70 to 4,760 ppm Ag, mean 1,357, median 610; lead assumed about 86 percent (pure galena) | ppm Ag in galena-rich sample | Wood et al. 2021, section 3.2, Table 3, from Gale et al. 1980 | READ | Pure-galena specimens, so an upper bound for run-of-mine ore, which carries gangue. Median 610 ppm is 0.61 kg per tonne of galena. |
| Laurion, mass balance | at least 210 kg of argentiferous ore, or 169 kg of smelted lead, per kilogram of silver at the richest sample (4,760 ppm Ag) | kg ore per kg Ag | Wood et al. 2021, section 3.4 | READ | Best case. DERIVED check: 1 / 4.76 kg per tonne = 210 kg, matches. At the median 610 ppm the same arithmetic gives about 1,640 kg of galena per kilogram of silver (DERIVED). |
| Laurion, viability threshold of the smelted lead | 700-800 ppm Ag (Early Cycladic), 400-600 ppm (Middle and Late Bronze Age), as low as 200 ppm (6th to 4th centuries BCE) | ppm Ag in lead metal | Wood et al. 2021, section 3.4, after Gale and Stos-Gale 1981a | READ-2 | The lower the smelted lead, the more lead per kilogram of silver. 200 ppm in lead is 0.2 kg Ag per tonne of lead, ten times below the model's `laurion_lead` byproduct of 2.0. |
| Laurion, lead from Thorikos | 437 ppm Ag in lead metal, 246 ppm in litharge | ppm | Wood et al. 2021, section 3.5, Table 8 | READ | "Not particularly argentiferous", lower limit of Late Bronze Age viability. |
| Laurion, ancient ecbolades (waste dumps of the old mines) | 4 to 8 percent lead; 1,000 to 1,300 grams of silver per tonne of lead; one dump estimate 105 million tonnes | per tonne of dump | Cordella 1893, p. 4 | READ (19th-century assay and an old tonnage; the tonnage looks too large and is not used) | DERIVED silver per tonne of dump: 60 kg lead x 1.0 to 1.3 g per kg lead = about 60 to 80 g per tonne. Ancient miners left rock this rich on the dump, so the ore they sent to the washery was richer. The model's `laurion_silver` at 0.4 kg per tonne is well above this waste and at the low end of Agricola's floor (below). |
| Laurion, ancient ore-washing slimes | 10 to 12 percent lead; 1,500 to 1,800 grams of silver per tonne of lead | per tonne of slime | Cordella 1893, p. 9 | READ | The washery tailings still held this much lead, which is direct evidence of large dressing losses. DERIVED silver per tonne of slime: 100 to 120 kg lead x 1.5 to 1.8 g per kg = about 150 to 220 g per tonne. |
| Laurion, ancient slag | 8 to 13 percent lead; 400 to 600 grams of silver per tonne of lead | per tonne of slag | Cordella 1893, p. 9 | READ | Lead left in slag is the smelting loss. Compare Bettenay's 30 percent realistic loss (prior report). |
| Laurion, ancient output total | about 15,000 slaves; about three centuries; 2,100,000 tonnes of lead mixed with silver | people; tonnes | Cordella 1893, p. 3 | READ (old estimate, unsourced there) | Order-of-magnitude cross-check on lead only; no modern source confirmed it. |
| Laurion, modern remnant | 3 percent lead and 140 g per tonne silver over about 30 million tonnes (1865 to 1982) | modern production | Wikipedia and a UCL summary, via search | SNIPPET | Not Classical grade. |
| Laurion, sources saying 0.1 percent | "silver content of extracted ore is only 0.1%" | percent | World Archaeology 2005 as quoted on Wikipedia (https://en.wikipedia.org/wiki/Mines_of_Laurion) | SUMMARY | Possibly the 0.1 to 0.2 percent in lead metal misread as ore. Do not use as an ore grade. |
| Agricola, lowest extractable silver | 0.5 to 1 uncia of silver per 100 pounds of ore, which is 378 to 756 g per short ton, about 417 to 837 ppm or 0.04 to 0.08 percent | of ore | Agricola 1950 edition p. 388, converted in Merkel 2020, Table 2A | READ-2 | A 16th-century Saxon smelting floor. Hispania silver at 1,000 ppm sits above it; Laurion silver at 400 ppm just at it. |
| Agricola, argentiferous lead | 3.5 unciae per 100 pounds of lead, about 0.29 percent | of lead | Agricola 1950 p. 475, Merkel 2020, Table 2B | READ-2 | Matches the model's byproduct ratio of 2.0 to 2.3 kg per tonne lead (0.2 to 0.23 percent) within a third. |
| Agricola, rich/poor boundary | 3 percent silver | of ore | as reported in Merkel 2020, p. 42 | READ-2 | Shows that "silver ore" in the sources means native-silver and acanthite ore too, not only galena. |
| Silver in smelted lead, ancient sites | Sifnos up to 0.5 percent, often half or less; Thasos galena up to 0.4 percent and lead 0.1 to 0.2 percent; Laurion, Rio Tinto and Kosmaj similar; Melle typically 0.15 percent, maximum 0.5, experimental lead 0.24; Rammelsberg lead about 0.2; slags of Rammelsberg and others 0.17 percent average | percent Ag in lead | Merkel 2020, pp. 41-42, citing Vavelidis 1985, Hauptmann et al. 1988, Merkel 2007, Teryeygeol 2002 and 2014, Asmus 2012 | READ-2 | The consistent number is 0.1 to 0.5 percent silver in lead metal. |
| Tylecote economic floor | 0.06 percent Ag in argentiferous lead (Roman), 0.1 percent (medieval) | percent | Tylecote 1986, pp. 61 and 71, as quoted in Merkel 2020, p. 40 | READ-2 | A lower bound on what was worth cupelling. |
| Bachmann 1993 | silver-bearing lead ores of half a percent, rarely 1 to 3 percent | percent Ag | Bachmann 1993, p. 489, as quoted in Merkel 2020, p. 40 | READ-2 | Merkel argues this is the archaeometallurgist's view and understates rich ore that never reached a slag heap (his pp. 42-43). |
| Cartagena and Sierra Morena | no assay found | n/a | n/a | none | Only Strabo 3.2.10 (lead of Castulo has little silver) and the garbled Domergue yield above. The model's `hispania_silver` 1.0 kg per tonne and `hispania_lead` 180 kg per tonne rest on no opened assay. |
| Rio Tinto jarosite | about 0.2 percent Ag | of ore | Bettenay 2022 (supergene section) via the prior report; Anguilano et al. abstract | READ-2 | Unchanged. |
| Melle | 1 to 3 per mille Ag in galena; 60 to 80 g per tonne stated maximum | per galena; per ore | Bettenay 2022 via the prior report; Merkel 2020 agrees (0.15 typical in lead) | READ | Poor deposit. |
| Kutna Hora | northern ore zones about 200 to 300 g per tonne silver, thick veins, 16th century; output estimates 6 to 7 tonnes a year, 20 tonnes a year 1300 to 1340, 2 to 4 tonnes a year in the 16th-century revival; district total about 2,500 tonnes; about 3,000 miners at one time | g per tonne; tonnes | Pribram and Kutna Hora mining districts (ResearchGate 360411442, via search) and Kora 1950 as shown in a ResearchGate figure | SNIPPET | The only medieval ore grade found outside Melle. Open the paper before use. Processing and smelting losses of 20 to 30 percent from rich ores are reported from a Metalla review of the same compilation (SNIPPET). |
| Freiberg | no medieval ore grade found; silver bought at the Freiberg mint was about 1 tonne a year by 1363; about 250 miners remained in 1453; exhaustion of the "upper ore bodies" and inability to drain are named as causes of decline | tonnes; people | Burghardt 2018, sections on decline (citing Ermisch) | READ for the two workforce and cause statements; the 1 tonne a year is from a search summary | Grade gap stays. Districts total about 5,000 to 8,000 tonnes over centuries (SNIPPET). |
| Kongsberg | native silver in calcite veins; total over 1.3 million kg (about 1,350 tonnes) over about three centuries; 1,370 Germans and 1,600 Norwegians in 1636; 1,500 and 2,400 in 1648; over 4,000 in the 1770s | kg; people | Wikipedia (Kongsberg and Kongsberg Silver Mines), Berg and Nordrum 2004 (Swiss Journal of Geosciences / Naturalis repository) | SNIPPET | No ore grade (grade is the vein, not a bulk assay). Workforce supports Bettenay's per-worker productivity table. |
| Potosi | ore quality fell with depth and time (Bakewell 1975); mita labour up to 13,400 per year; Wikipedia says "up to 40 percent silver" at peak; one source gives 3,200 labourers and five million troy ounces a year in 1560 | n/a | Bakewell 1975 (conclusion only, via search); Wikipedia; a heritage-site summary | SNIPPET | The 40 percent is not a bulk grade. The 3,200-worker figure divided into five million ounces gives about 48 kg per worker-year, 20 times Bettenay's long-run benchmark, so the worker count almost certainly excludes the processing and wood staff. Do not use. |
| Japan (Iwami Ginzan) | cupellation (haifuki) introduced 1533; annual output sources disagree: 1,000 to 2,000 kg a year in the 17th century, falling to about 100 kg by the mid-19th century (UNESCO French text), versus 38 or 150 tonnes elsewhere; deeper digging after the 1640s made drainage costly | kg per year | UNESCO nomination text and travel and wiki pages, via search | SNIPPET | No ore grade, no miner count. The drainage-cost remark is qualitative support for modelling deep water. |
| China (Song, about 1200, Fujian and Zhejiang) | 2 to 3 liang of silver per basket of 25 jin, down to 3 to 4 qian; converted by the Heidelberg note to 7,500 to 5,000 g per tonne (rich) and 1,000 to 750 g per tonne (poor) | g per tonne | Heidelberg Silver mines in the Far Southwest project note (zo.uni-heidelberg.de), via search | SNIPPET | The note calls the yields surprisingly low. These are very high compared with Laurion, so they likely describe hand-sorted ore. Needs the page itself (site was down). Ming and Qing Yunnan: none found. |

## 3. Labour per tonne of ore

The prior report holds the Bettenay ratios (face 40 to 70 percent of mine staff; processing staff about equal to mine staff; wood supply as many again) and the Cornish and Saxon early-modern rates. New in this pass:

| Item | Figure | Source | Strength | Use |
|---|---|---|---|---|
| Whole-workforce hours per kilogram of silver, Carthago Nova, from Polybius | DERIVED: 40,000 workers x 300 days x 12 hours / 35,000 kg per year = about 4,100 hours per kg | Strabo 3.2.10 (40,000 workers); the 35 tonnes a year is an inference by Kay 2014 from the 25,000 drachmae a day, reported in an OUP chapter (Mining Revenues, https://academic.oup.com/book/2823/chapter/143376936) and the Geochemical Perspectives Letters article https://www.geochemicalperspectivesletters.org/article1613/. The 300 days and 12 hours are the Bettenay Melle convention, not Polybius. | C (a revenue converted to metal, with assumed days) | Matches the 3,700 hours per kg already in the complaint to within about 10 percent. The weakness is the conversion of drachmae to kilograms. |
| Laurion workforce | about 15,000 slaves (Cordella 1893); almost 20,000 (a Wikipedia summary of Bressan 2018 citing Forbes) | as stated | READ (old), SUMMARY | Staff count only; no output per year, so no hours per kg. |
| Laurion washery crew | about 33 workers per washery | search summary of Kakavogianni 1996 (prior report) | SNIPPET | Not enough to derive dressing hours per tonne: no throughput. |
| Washery throughput | none found | Morin-Hamon 2023 read; only dimensions (one tank 2.10 m long, 0.75 m wide, 0.60 m deep) and the buddle method; 18th and 19th-century French mining-school buddle descriptions are cited, not quoted | READ (no rates) | The single most useful missing source: the French School of Mines buddle reports it cites (Ecole des Mines de Paris, 18th and 19th century) would give tonnes of ore per washing-day per worker. |
| Dressing loss, direct evidence | ancient slimes still 10 to 12 percent lead (Cordella 1893) | as above | READ | Compatible with Bettenay's 10, 20 and 25 percent galena loss cases and his remark that 30 to 40 percent is quite possible. |
| Smelting loss, direct evidence | ancient slag 8 to 13 percent lead (Cordella 1893) | as above | READ | Compatible with Bettenay's 30, 20 and 10 percent smelting loss. |
| Rock broken per face miner per day, Laurion | 145 kg, from Ardaillon 1897 | Bettenay 2022, Table 2 (prior report) | READ-2 | Already held. |
| Water-lift human power | about 0.1 horsepower needed for a treadmill wheel lifting 19 gallons per minute through 12 feet | Landels 1978 p. 69, as summarised at https://earthsci.org/mineral/mindep/ancient_mine/deep-vein_mining.html | SUMMARY | Cross-check below. |

## 4. Water inflow and drainage

Nobody in the sources I could open publishes an inflow in tonnes of water per tonne of ore for an ancient mine. What exists is lift capacity per machine, which bounds the inflow a battery could have handled but does not give it.

| Item | Figure | Source | Strength |
|---|---|---|---|
| Archimedean screw delivery | 35 to 40 gallons per minute at 40 to 50 percent efficiency | Landels 1978 p. 63, via earthsci.org summary | SUMMARY; the gallon (imperial or US) is not stated. DERIVED conversion: imperial gives 9.5 to 10.9 cubic metres per hour; US gives 7.9 to 9.1. |
| Screw dimensions | Sotiel Coronada 3.6 m long, 48 cm diameter (Forbes p. 214); Centenillo 5 m long, 59 cm diameter, 20 cm core (Shepherd p. 40); angles 15 to 20 degrees at Coronada, 35 at Centenillo, Vitruvius 37; a 3 m screw lifts water about 1 m (Craddock pp. 78-79) | same page | SUMMARY |
| Wheel delivery | 19 gallons per minute through a 12 foot rise; lift about three quarters of wheel height; wheels 4 to 6 m across with 20 to 24 compartments (Shepherd pp. 37-38) | Landels p. 69, same page | SUMMARY; DERIVED about 5.2 cubic metres per hour if imperial gallons, 4.3 if US |
| Rio Tinto battery | 16 wheels in 8 pairs in series, total lift about 30 m (Forbes p. 217); other accounts 30 wheels, up to 115 feet, or about 50 wheels reaching more than 80 m to an adit | same page; Wikipedia (Reverse overshot water wheel), search summaries | SUMMARY, SNIPPET |
| Cross-check of the model's lift cost | the model's `_lift_hours_per_tonne_metre` is 0.0727 labourer-hours per tonne-metre (output of `python3 -I` call to `sim.world.deposits._lift_hours_per_tonne_metre()` run for this report). DERIVED from Landels: 19 gallons per minute through 12 feet needs about 52 watts hydraulic (imperial: 5.2 cubic metres per hour x 3.66 m x 9.81 / 3600) and, at 0.1 horsepower of human input (75 watts), that is 0.0524 hours per tonne-metre of hydraulic work delivered. | this report | DERIVED | The model's figure is within about 40 percent of the Landels-derived one. The lift cost per tonne-metre is therefore not where the drainage uncertainty sits; the tonnes of water are. |
| Plasenzuela, Roman depth | at least 137 m, about 80 m below the water table; oxidised zone upper 60 m | Domergue 1987 as cited at the earthsci page | SUMMARY | Shows ancient drainage reached at least 80 m below the water table, so deep inflow was handled. |
| Shaft and gallery sizes | shafts 1 to 2 m square, deepest about 200 m (Rickard, Metals p. 447); galleries 1 to 1.5 m high, about 1 m wide (Shepherd p. 17) | same page | SUMMARY |
| Water inflow per tonne of ore | none found | none | none; `WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH` stays unsourced |
| Kongsberg and Iwami | drainage cost named as the reason deep working stopped paying (Iwami after the 1640s; Freiberg's "inability to solve the mine water problem", Burghardt 2018 citing Ermisch) | UNESCO text via search; Burghardt 2018 | SNIPPET; READ for Freiberg | Qualitative only. |

One bound can be stated from the Rio Tinto row: a single battery lifting one stream through all its stages delivers only the flow of one wheel, about 5 cubic metres an hour, or about 125 cubic metres a day if run continuously (DERIVED from Landels). To turn that into water per tonne of ore needs the ore raised per day at Rio Tinto, which no opened source gives.

## 5. Per-field table for the model

"Model" is the value in the repo today (read from `sim/world/mine_works.py` and `data/world/geography/deposits/ancient.json`). A blank "best sourced" means nothing opened supports a value.

| Field | Model | Best sourced value or range | Source | Strength | Gap |
|---|---|---|---|---|---|
| `laurion_silver.ore_grade_kg_per_tonne` | 0.4 | Hand-picked galena ore 0.07 to 4.8 kg per tonne, median 0.61; ancient dump rock about 0.06 to 0.08; ancient slimes (tailings) about 0.15 to 0.22 | Wood et al. 2021 Table 3; Cordella 1893 pp. 4 and 9 | READ | No bulk run-of-mine assay of the ore actually worked. |
| `laurion_lead.ore_grade_kg_per_tonne` (lead) | 80 | dump rock 40 to 80 kg lead per tonne; slimes 100 to 120 | Cordella 1893 | READ | Ore actually dressed is richer than the dump and leaner than pure galena (860 kg per tonne). |
| `laurion_lead` silver byproduct | 2.0 kg per tonne lead | 0.2 (6th-4th c. BCE threshold) to 1.0-1.3 (dumps), 1.5-1.8 (slimes), 0.4-0.6 (slag); 0.1 to 0.5 percent in smelted lead across ancient sites | Wood 2021 s3.4; Cordella 1893; Merkel 2020 | READ, READ-2 | Spread of a factor of ten; the model's 2.0 is the upper half. |
| `hispania_silver.ore_grade_kg_per_tonne` | 1.0 | none opened | none | none | No Cartagena or Sierra Morena assay. Shape check only, not a source: the model's lead-ore grade (0.18 tonne of lead per tonne of ore) times Merkel's 0.1 to 0.5 percent silver in lead (1.0 to 5.0 kg silver per tonne of lead) gives 0.18 to 0.9 kg silver per tonne of ore. |
| `hispania_lead.ore_grade_kg_per_tonne` | 180 | none opened; Melle 43 tonnes ore per tonne lead (prior report) | none | none | Domergue 1990. |
| `rio_tinto_jarosite` | 2.0 | about 2 kg per tonne | Anguilano via Bettenay | READ-2 | Primary paper. |
| Melle-type poor ore | n/a | 0.06 to 0.08 | Bettenay via prior report | READ | Already in report. |
| Medieval Central Europe | n/a | 0.2 to 0.3 (Kutna Hora north, 16th c.) | ResearchGate summary | SNIPPET | Primary. |
| Agricola smelting floor | n/a | 0.42 to 0.84 | Merkel 2020 Table 2A | READ-2 | Direct reading of Agricola p. 388. |
| `ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH` | 1.0 / 0.65 / 0.5 | 0.5 to 0.65 (Melle only) | Bettenay Table 4 | READ | Nothing for a rich wide vein. |
| `WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH` | 0 / 0.5 / 3.0 | none | none | none | See section 4. |
| `_lift_hours_per_tonne_metre` | 0.0727 | about 0.052 (hydraulic work, treadmill wheel) | Landels via earthsci summary, DERIVED | SUMMARY | Primary Landels. |
| Archimedean screw flow | not modelled | 35 to 40 gallons per minute | Landels p. 63 summary | SUMMARY | Gallon unit. |
| Dressing loss | heuristic | direct evidence: tailings 10 to 12 percent lead | Cordella 1893 | READ | Tonnes per washing-day. |
| Smelting loss to slag | heuristic | direct evidence: slag 8 to 13 percent lead | Cordella 1893 | READ | Slag mass per tonne of lead. |
| Staff shares | see prior report | Bettenay 40 to 70, processing about equal, wood about equal | Bettenay 2022 | READ-2 | Primaries: Berg 1988, Vozar 2000. |
| Whole-workforce hours per kg silver | 379 (complaint) | about 1,000 to 1,700 (Bettenay Table 3); about 4,100 DERIVED from Polybius | Bettenay; Strabo; Kay 2014 | READ-2, C | Drachma conversion. |
| `HAUL_DISTANCE_METRES_BY_DEPTH`, `TIMBERED_SHARE...`, `TIMBER_FITTING_HOURS...` | 100/150/400 m etc. | none (Pliny 33.97 gallery length only; gallery section 1 to 1.5 m by about 1 m) | Pliny; Shepherd via earthsci | SUMMARY | Plan layouts. |
| Roast fuel and slag handling, lamp oil, overburden | not charged | none found | none | none | Nobody has published. |

## 6. Which single term moves the hours per kilogram most

The model's mining hours per kilogram of silver, run for this report with `sim.world.deposits.load_deposits('silver')`, `vein_hours_per_tonne_ore` and `total_cost_labour_hours_per_kg` (the full command: `python3 -I -` with those calls, repository on the path):

| Deposit | Hours per tonne of ore | Hours per kg (mining, deposit-side) | Grade, kg per tonne | Drainage share |
|---|---|---|---|---|
| hispania_silver | 90.5 | 91.4 | 1.0 | drainage 21.8 of the 90.5 hours (24 percent) |
| laurion_silver | 48.0 | 121.6 | 0.4 | drainage 21.8 of 48.0 hours (45 percent) |
| rio_tinto_jarosite | 8.8 | 4.4 | 2.0 | none |

Because hours per kilogram of metal is hours per tonne of ore divided by kilograms of metal per tonne of ore, the grade enters as a pure reciprocal. Across the sources opened, plausible silver per tonne of ore for lead-silver working ranges from about 0.06 kg (Laurion dump rock) to 1.0 kg (the model's `hispania_silver`) to 4.8 kg (the richest Laurion hand-picked sample), a spread of well over an order of magnitude with the model's values inside it. Every other term varies by far less in the evidence: the lift cost per tonne-metre is within 40 percent of a physics-derived figure; staff shares span a factor of about two (40 to 70 percent face miners); a change of drainage from 3.0 to 0.5 tonnes of water per tonne of ore would change `hispania_silver` hours per tonne by roughly 18 of 90.5 (DERIVED: 21.8 x 2.5 / 3.0 = 18.2) and would remove about 38 percent of the hours per tonne for `laurion_silver` (18.2 of 48.0, DERIVED).

So the term that moves hours per kilogram of silver most is the silver grade of the ore actually dressed (kilograms of silver per tonne of ore), followed, for deep working, by the unsourced water inflow. The grade is also the term with the least support in the open record: Cartagena and the Sierra Morena have no opened assay, and the strongest assays (Gale et al. 1980 as shown in Wood 2021) describe hand-picked pure galena rather than run-of-mine ore. Because the model's silver grade is not derived from a lead grade, a correct treatment of the unit warning in section 2 (silver as a fraction of the lead metal, 0.1 to 0.5 percent, versus as a fraction of the ore) is itself a candidate error to check before any new number is used: `hispania_silver` says "0.1% Ag" of ore, while the sources that give 0.1 percent give it in lead metal.

Second after grade: the dressing and smelting recovery, since the ancient tailings (10 to 12 percent lead) and slag (8 to 13 percent lead) in Cordella mean that a real fraction of the lead and silver was lost between face and metal, and a model of about 100 percent recovery divides the real hours per kilogram by that factor.

## 7. Gaps nobody has published (as far as opened sources show)

- Run-of-mine ore grade for Cartagena, Sierra Morena, Rio Tinto lead-silver and Laurion in Roman and Classical conditions: the primaries are Domergue 1990, Davies 1935, Healy 1978, Conophagos 1980.
- Water inflow per tonne of ore for any ancient or medieval silver mine.
- Tonnes of ore washed per worker-day in a Laurion washery (needs the French School of Mines buddle reports cited by Morin-Hamon 2023).
- Charcoal per tonne of lead and per kilogram of silver, and the fuel for roasting.
- Hauling and hoisting hours per tonne in a pre-engine mine (no text opened).
- Medieval ore grade for Freiberg, Kongsberg (bulk), Schwaz and Banska Stiavnica.
- A Ming-Qing Yunnan silver grade and miner count.
- A bulk Potosi ore grade over time (Bakewell 1975 and 1984 are the sources).

## 8. Suggested next reading, in order of how much each would close

1. Domergue, C. 1990, Les mines de la peninsule iberique dans l'antiquite romaine (Ecole francaise de Rome): grades, ore tonnage, ore-to-lead.
2. Conophagos, C. E. 1980, Le Laurium antique et la technique grecque de la production de l'argent: Laurion ore, washing and cupellation yields.
3. Landels, J. G. 1978, Engineering in the Ancient World, pp. 63 and 69: confirm the gallon and the screw and wheel rates.
4. Kora 1950 or the Pribram and Kutna Hora paper: Kutna Hora ore grades.
5. Morin-Hamon's cited Ecole des Mines buddle reports, for washing throughput.
6. Berg 1988 and Vozar 2000: the primaries of Bettenay's staff shares.
7. Bakewell 1984, Miners of the Red Mountain: Potosi grades and labour.
