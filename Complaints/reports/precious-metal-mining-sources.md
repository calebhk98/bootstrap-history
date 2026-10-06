# Precious-metal mining: sources for Complaint 349 and the gold deposit gap

Research report. No data file was edited. Every figure below is a candidate input, not a decision; CLAUDE.md 4.1 and 4.5 apply (a yield is a physical fact, never moved to reach an attested price or wage).

## How to read this report

Provenance tags, used in the "Read" column of every table:

- **READ**: I opened the full text (PDF or page) and took the figure from it. Page or table given.
- **READ-2**: read in a full text, but that text quotes another author; the primary was not opened.
- **SNIPPET**: seen only in a web search result summary. Not verified in the text. Treat as a lead.
- **RECALLED**: from memory, not looked up this session. Must be checked before use.

Confidence letters follow `data/production/_SCHEMA.md`: A well attested, B probable, C the author's estimate (the deposit files also use D for a figure seen only in a snippet). The letter given is the one I would assign to the figure as a replacement value, not the source's own quality.

Full texts read in this session:

- Bettenay, L. 2022. Geological and Mining Constraints on Historical Mine Production: The Case of Early Medieval Lead-Silver Mining at Melle, France. Metalla 26.2, 67-86. https://metalla.org/index.php/METALLA/en/article/download/9777/9276/8260 (READ, all pages; tables 1 to 4 and the processing and workforce sections).
- Klemm, D., Klemm, R., Murr, A. 2001. Gold of the Pharaohs: 6000 years of gold mining in Egypt and Nubia. Journal of African Earth Sciences 33, 643-659. https://personal.utdallas.edu/~rjstern/egypt/PDFs/CE%20Desert/KlemmAU.JAES01.pdf (READ, all pages).
- Strabo, Geography 3.2.9-10 (Jones translation, Thayer text). https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Strabo/3B*.html (READ, the two passages quoted).
- Delgado Dominguez et al. 2021. Study of isotopic lead in one ingot ... Riotinto. Revista Onoba 9, 33-50. https://bura.brunel.ac.uk/bitstream/2438/29918/1/FullText.pdf (READ, introduction and discussion).
- Mussche, H. 2006. More about the Silver-rich Lead of Ancient Laurion. L'Antiquite Classique 75, 225-230 (READ, but the scan was fragmentary and it is a methodological critique; no usable grade or labour figure came out of it).

Not obtainable (HTTP 403 from the host, or no open copy): Anguilano et al. 2010 (ArcheoSciences 34), Rehren's Laurion washery papers, Cauuet's Rosia Montana papers, the Polish Las Medulas paper, Domergue 1990, Davies 1935, Healy 1978, Craddock 1995. Everything attributed to them below is SNIPPET or RECALLED.

## 1. Ore grades

### 1.1 Lead and silver (argentiferous galena, jarosite)

| Deposit | Figure | Units | Source (exact) | Read | Conf | Replaces or adds |
|---|---|---|---|---|---|---|
| Melle (MVT lead-silver), mined grade as presented to crushing | 14 / 10 / 6 (extreme / optimistic / realistic) | weight % galena | Bettenay 2022, Table 4, row "Average grade of ore (weight % galena) as presented for crushing" | READ | B (modelled, not assayed; the author states there is no way to establish the grade actually mined) | Reference case only; does not set a Roman deposit. Cross-check for `hispania_lead.ore_grade_kg_per_tonne` and `britannia_lead` in `data/world/geography/deposits/ancient.json` (those hold 180 and 150 kg of lead per tonne, i.e. about 21 and 17 % galena equivalent; the realistic Melle case is about 5 % lead). |
| Melle, Pb to Ag ratio in ore | 300 / 450 / 530 | mass ratio | Bettenay 2022, Table 4, note 6 (equals the remnant ore value and the mid-point of reported Melle galena) | READ | B | `byproducts[].kg_per_tonne_of_primary_metal` for a Melle-type MVT galena: 1000/530 = about 1.9 kg silver per tonne of lead (derived). No Melle deposit exists in the data. |
| Melle, silver in ore | 1 to 3 per mille Ag by weight in the galena, a published typo corrected from percent; 60-80 g Ag per tonne stated maximum grades; 10 to 161 g/t cited for the wider region | per mille; g/t | Bettenay 2022, section "Geology" (text quoting Tereygeol 2007, Karnay et al. 2004 p. 65) | READ-2 | B | Context for the above. |
| Rio Tinto, jarosite ore at base of the iron cap | about 0.2 | % Ag | Bettenay 2022, supergene-enrichment section (about p. 70; citing Anguilano 2012): "Roman silver mining at Rio Tinto ... silver at grades of about 0.2 % in jarosite ore" | READ-2 (an independent second mention of the repo's existing 2.0 kg/t, which was only an abstract before) | C, upgraded from D because two independent secondary mentions agree; the primary (Anguilano 2010) was still not opened | `rio_tinto_jarosite.ore_grade_kg_per_tonne` (currently 2.0, conf D): value stands, raise conf to C and cite Bettenay supergene section. |
| Rio Tinto, Roman silver ingots from reduced litharge | 63 to 98 | ppm Ag in lead | Delgado et al. 2021, Onoba 9, discussion (low-silver ingot found at Masa Planes; contrasted with a 346 ppm maximum and "400 ppm or higher" for lead worth cupelling) | READ | B | Not a deposit grade; evidence that cupelled lead was recycled as collector (supports `silver_jarosite_kg` using `lead_kg` as input). |
| Rio Tinto, slag mass | more than 20 million | tonnes of slag | Delgado et al. 2021, p. 35, citing Salkield 1970, 85-90 | READ-2 | C (slag volume is a ceiling on the smelted charge, not an ore grade) | Order-of-magnitude check on `endowment` for `rio_tinto_jarosite` (no endowment key now). |
| Laurion, lead silver content | 0.1 to 0.2 | % Ag in the lead metal (Conophagos); silver ore described as about 0.1 % | Bettenay 2022 cites Conophagos for ~3,500 t silver (Greek Classical period); Mussche 2006 and a Wikipedia summary say "nearer one tenth of a percent than one percent" | READ-2 and SNIPPET | C | `laurion_lead.byproducts[0].kg_per_tonne_of_primary_metal` (currently 2.0 kg Ag per tonne Pb, conf D): the Conophagos range is 1.0 to 2.0 kg Ag per tonne Pb (0.1 to 0.2 %), so 2.0 is the top of the range, not a mid value. |
| Laurion, total ancient yield | about 3,500 t silver; about 13 million t ore; about 1.4 million t lead | tonnes | Bettenay 2022 (silver, citing Conophagos); ore and lead totals SNIPPET from a UCL/Rehren-linked search summary | READ-2 / SNIPPET | C | `laurion_silver.endowment` (currently 3,500, matches). Implied ore per tonne lead is about 9; implied silver per tonne ore about 270 g (derived from the SNIPPET figures; check before use). |
| Laurion, modern remnant ore (French and Greek companies 1865 to 1982) | about 3 % Pb, 140 g/t Ag; about 30 million t mined | % ; g/t; t | Wikipedia/UCL summary seen in search | SNIPPET | D (modern, low-grade dumps, not Classical grade) | Upper bound on how poor Roman-era Laurion ore could have become; do not use as the Classical grade. |
| Cartagena / Sierra Morena, ore grade | no assay found | n/a | Domergue 1990, Davies 1935, Healy 1978 not opened. Strabo 3.2.10 says the lead of Castulo "has a slight quantity of silver mixed with it, though not enough to make the refining of it profitable" | READ (Strabo only) | D | `hispania_lead.byproducts` and `hispania_silver.ore_grade_kg_per_tonne`: no source found; keep as is, flagged C/B for reasons already in the file. Strabo's note is a useful qualitative bound: some Iberian lead is too low in silver to cupel. |

Reading across: the only quantified mined-ore galena grade in a source I read is Melle's modelled range. The repo's `hispania_lead` (about 18 % lead) is above the best Melle case; that is not an error for Spain (Melle is a poor MVT deposit, Bettenay says so), but it means no open source supports the round figure. Do not change it until Domergue or Davies is read.

### 1.2 Gold (placer and vein)

| Deposit | Figure | Units | Source (exact) | Read | Conf | Replaces or adds |
|---|---|---|---|---|---|---|
| Las Medulas, gold in the Tertiary conglomerate | base 5 m of conglomerate up to 0.3; most gold-bearing basal series 20 to 100 mg per m3, locally 60 to 300 mg per m3 | g or mg per m3 | Polish geology paper on Las Medulas (geojournals.pgi.gov.pl, article 28291) via a search summary; host returned 403 so not opened | SNIPPET | D | `las_medulas_alluvial.ore_grade_kg_per_tonne` (currently 0.0003 kg/t = 0.3 g/t): the existing value equals the top of the base-layer range. A bulk value near 20 to 100 mg/m3 would be about a tenth to a third of it. |
| Las Medulas, cross-check from output and volume | 93.5 million m3 removed; Pliny 20,000 Roman pounds per year; 1.64 million kg in 250 years; other estimates 800 t and 1,626 t total | m3; kg; t | Wikipedia (Las Medulas), Lewis and Jones 1970 (JRS 60), and a search summary | SNIPPET | D | 1.64e6 kg / 93.5e6 m3 = about 17.5 mg per m3 (derived, assuming the two totals refer to the same ground). The existing `endowment` of 1,640 t (marked "probably generous" in the file) and a 0.3 g/t grade are inconsistent with the stated volume: 0.3 g/t over 93.5 million m3 (about 2 t/m3 bulk) would be tens of thousands of tonnes of gold. Resolve before any change. |
| Eastern Desert and Nubian quartz-vein ore, mined grade | maximum concentration mined about 15; recovery assumed 10 | g/t Au | Klemm et al. 2001, p. 658 ("Assuming a recovery of 10 g/t, which is about two thirds of the maximum concentration mined") | READ | B | New deposit `eastern_desert_nubian_gold` (see 4). |
| Ancient tailings, residual grade | 3 to 5 | g/t Au | Klemm et al. 2001, p. 652 | READ | B | Lower bound on the grade ancient ore had before milling; use with the above for a vein range. |
| Eastern Desert leached SEDEX cap | up to 50 ppm Au in leached silica residue; 0.5 ppm average in underlying pyrite | ppm | Klemm et al. 2001, p. 647 (Gidami-type sponge ore) | READ | B | Lower-priority variant. |
| Rosia Montana (Alburnus Maior), modern resource average | 1.46 g/t Au, 6.9 g/t Ag; 214.9 million t | g/t; t | EMC2012 abstract (copernicus) via search | SNIPPET | C | Not the Roman mined grade (the Romans took the richest stopes). `dacia_vein_gold.ore_grade_kg_per_tonne` (currently 0.008 = 8 g/t, conf C, "order of magnitude"): the Klemm Eastern Desert 10 g/t recovery case is the same order, so 8 g/t is defensible as a selective-working grade, but no Rosia Montana Roman grade was found. Keep as C. |
| Rosia Montana, Roman production | about 500 t gold over 166 years from 106 CE | t | UNESCO inscription text 1552 via search summary (host 403) | SNIPPET | D | `dacia_vein_gold.endowment` (currently 500, same figure; source note says "from memory": replace with the UNESCO reference, still D). |

## 2. Labour per tonne of ore, support work, dressing, smelting, fuel

All entries here are derived from Bettenay's Realistic case (Table 4 and the workforce section) unless stated. Derivations use his stated inputs and the arithmetic is shown so the maintainer can check it.

| Item | Figure | Units | Source and derivation | Read | Conf | Replaces or adds |
|---|---|---|---|---|---|---|
| Rock broken per face miner per day | 150 (realistic); 250 (optimistic); 425 (extreme) | kg rock | Bettenay 2022, Table 4 row 2 | READ | B | Cross-check on `breaking` rate in `sim/world/deposits.py` (not read this session). |
| Classical Laurion face rate | 145 | kg rock per miner per day, 12-hour day, density 2.8 | Bettenay 2022, Table 2, citing Ardaillon 1897 (third-contact limestone block 12 x 12 x 60 cm in about two hours) | READ-2 | C | Independent cross-check for hard-rock breaking in `deposits.py`; supports a 12-hour day. |
| Ore share of all rock broken | 50 (realistic); 60; 65 | % | Bettenay 2022, Table 4 row 4 (note 4: "probably insufficient" allowance for sinking, exploration, waste in the face) | READ | B | `ORE_SHARE_OF_ROCK_BROKEN_BY_DEPTH` in `sim/world/mine_works.py` (value not changed; compare). |
| Face miners as share of mine staff | 40 to 70 | % | Bettenay 2022, workforce section (about p. 77), citing Berg 1988 and Vozar 2000 | READ-2 | B | Check on the support-work ratio in `mine_works.py` (the complaint says it comes out just under what 40 to 70 % implies). |
| Ore processing staff relative to mine staff | about as many as at the mine; 30 % (early Kongsberg) to 50-65 % of total staff (Slovak operations) | ratio | Bettenay 2022, workforce section | READ-2 | B | Processing labour (dressing plus smelting plus refining) in `labour_hours` of `lead_kg`, `silver_jarosite_kg` and the dressing constants in `sim/world/ore_dressing.py`. |
| Wood-sourcing staff | as many people may supply wood as work the mine itself; 1 to 1.5 green t of wood per forest worker per day realistic; 2.5 to 5 upper estimate | green t per worker-day | Bettenay 2022, workforce section (pp. 76-77), from Bryant 1923 (US lumber) and Klepac and Rummer 2002 | READ-2 | C | Fire-setting and charcoal fuel labour (complaint items: fire-setting share, roast fuel). |
| Fire-setting wood yield | rock per wood by weight: 0.3 to 1.2 (Fournel, mean 0.6); 0.7 (Melle, 4 experiments); up to 2.8 (Melle, Tereygeol and Dubois 2003); 0.4 (Kongsberg); 0.8 to 3 (Great Orme); 2.1 (Pantywrach); rock per fire 7 to 401 kg | kg rock per kg wood | Bettenay 2022, Table 1 and Table 2 ("0.25 to 2.5, most 0.4 to 0.8") | READ | B | The fire-setting wood input in `sim/world/mine_fire_setting.py` (not opened); medium-rock share still "none" per 344: this table gives rock:wood data by site but not by rock hardness, so it does not settle 344. |
| Total ore tonnes per tonne of lead metal | 2,250 t ore per 52 t lead = about 43 | t ore per t Pb | Bettenay 2022, Table 4 (realistic): total ore mined and final lead after cupelling and re-smelting; derived by division | READ (derived) | B for Melle; not transferable to Spain | The complaint already states this ratio; confirmed. |
| Smelting and refining losses | Pb lost in smelting to slag and air 30 (realistic) / 20 / 10; Pb lost in cupelling and re-smelting litharge 15 / 15 / 5; Pliny puts the cupellation loss at 2/9 (about 22 %); early modern as low as 5 % | % | Bettenay 2022, Table 4 rows 7-9 and note 9 (Pliny NH 34.47, Bostock and Riley 1855) | READ | B | Recovery factors of `lead_kg` (cupellation recovery 0.92 is used for silver; check against Table 4 silver loss rows: 1 / 2 / 5 % in smelting and 0 / 1 / 2 % in cupelling). |
| Crushing and gravity-concentration loss | 10 / 20 / 25 % of silver-bearing galena | % | Bettenay 2022, Table 4 row 7; note: 30 to 40 % "quite possible"; supported by Broken Hill gravity mills recovering about two thirds of the lead and under half the silver around 1900 | READ | B | Dressing recovery in `sim/world/ore_dressing.py` (currently a heuristic) and `lead_kg.inputs.galena_kg` (1,770 kg galena per tonne lead). |
| Whole-workforce silver productivity benchmarks | 1.4 to 2.33 kg silver per worker-year (Bere Ferrers, Kutna Hora, Kremnica, Banska Stiavnica, Kongsberg, long-run); up to 9 (early Kongsberg, near-surface); 4.3 (Himmelsfurst c. 1800) | kg Ag per worker-year | Bettenay 2022, Table 3 | READ | B | Benchmark for the complaint's "all workers" figure; the table is the source of the 1,000 to 1,700 hours per kg range. |
| Melle model hours per kg silver (derived) | 250 to 300 workers x 300 days x 12 hours / 150 kg silver per year gives 6,000 to 7,200 hours per kg of silver (joint with 52 t of lead) | hours per kg Ag | Bettenay 2022, Table 4 and workforce section; the 12-hour day is Table 2's Laurion assumption, not Bettenay's own for Melle | READ (derived) | C | Upper reference for Melle only; the lead is a co-product, so this is not a silver-only cost. |
| Strabo-Polybius, Carthago Nova | 40,000 workmen; 25,000 drachmae per day to the Roman exchequer; mines about 20 stadia from the city, 400 stadia in circuit | men; drachmae per day | Strabo 3.2.10 | READ | C (revenue, not output; the drachma silver weight and any cost share are not stated, so silver mass needs an assumed fineness and a revenue-to-metal conversion not given by the source) | `hispania_silver.source` already cites it; no new field. Implied hours per kg is outside what I can derive from the passage alone. |
| Laurion workforce | about 20,000 slaves at the peak; about 700 ancient shafts; about 200 ore processing stations | people; count | Wikipedia (Mines of Laurion) and history-site summaries; Conophagos and Lauffer 1979 are the primaries | SNIPPET | D | Cross-check for staff counts only. |
| Laurion washery crew | about 33 workers per washery | people | Search summary of a Laurion history site (Kakavoyannis 1996 likely primary) | SNIPPET | D | Dressing labour per tonne cannot be derived without throughput; not enough to replace the 20-hours-per-tonne heuristic. |
| Eastern Desert dressing method | hand crushing to bean size with a 0.5 to 2 kg pestle, grinding on flour-type mills up to 80 x 50 cm, washing on inclined tables | description | Klemm et al. 2001, pp. 651-653 | READ | B | Process description for `gold_lode_ore_kg` dressing; no hours per tonne in the paper. |

Gap: no source opened gives hours per tonne of ore for hauling, hoisting, timbering or ventilation separately. Bettenay gives only the staff share (40 to 70 % face). The dead-work and timbering constants in `sim/world/mine_works.py` therefore have no opened source.

## 3. Water inflow and drainage

| Item | Figure | Units | Source (exact) | Read | Conf | Replaces or adds |
|---|---|---|---|---|---|---|
| Egyptian screw used to draw off water in Turdetanian shafts | qualitative: shafts cut "aslant and deep"; streams "oftentimes" drawn off with the Egyptian screw | text | Strabo 3.2.9 | READ | B (qualitative) | Evidence that drainage by screw is period-correct for Iberia; no rate. |
| Rio Tinto drainage wheels | one installation with 16 wheels in pairs; each pair lifts water about 3.5 m; total lift about 30 m; wheels worked by men treading slats | count; m | Wikipedia (Reverse overshot water wheel), summarising Healy 1978 and Davies 1935 | SNIPPET | C | Would replace `WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH` only if a wheel flow and a treading crew size are found; neither is given. |
| Rosia Montana drainage | four wheel chambers in series at Paru Carpeni; a treadmill wheel system at Catalina Monulesti | count | Search summaries of Cauuet and UNESCO text | SNIPPET | C | Confirms that wheel chains were the Dacian drainage method. |
| Horizontal adit drainage | favoured where the vein is in mountainous terrain: allows draining and hauling without lifting against gravity | qualitative | Bettenay 2022, supergene section | READ | B | Supports adding an adit option to the mine-works model; no cost. |
| Water inflow per tonne of ore | none found | n/a | none | n/a | none | `WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH` stays unsourced. Not ready. |

## 4. Gold deposits missing from the data

Present in `ancient.json`: `las_medulas_alluvial` (placer), `dacia_vein_gold` (vein). Present in `metals.json`: modern and nineteenth-century gold only. Missing for antiquity, with the best source I found for each:

| Candidate | Lat, lon | Type | Period worked | Output or grade estimate | Source | Read | Conf | Data file and fields to add |
|---|---|---|---|---|---|---|---|---|
| Eastern Desert and Nubia (e.g. Bir Umm el-Fawakhir, Wadi Allaqi, Wadi Hammamat; several districts) | about 26.0 N, 33.6 E (Fawakhir) and 22.7 N, 33.3 E (Allaqi); coordinates RECALLED | quartz vein plus wadi-worked alluvial and eluvial | Predynastic to about 1350 CE; peak New Kingdom; Ptolemaic and Arab times equal shares of the remainder | about 400,000 to 600,000 t of quartz ore mined; recovery of 10 g/t gives at most 6,000 kg Au from veins; wadi works of the same order or at most double; total at most 18 t; about 7 t in Pharaonic times; mined concentrations up to about 15 g/t, tailings 3 to 5 g/t | Klemm et al. 2001, pp. 643, 652, 657-658 | READ | B for output and grade; C for coordinates (RECALLED, must be checked and the district chosen) | `data/world/geography/deposits/ancient.json` entries: id, resource gold, lat, lon, deposit_type `orogenic_quartz_vein_gold`, `ore_grade_kg_per_tonne` 0.010, `material_moved` ore, `depth_class` shallow to deep_vein (workings were limited by oxygen at depth, see Klemm p. 650), `hardness_class` hard, `endowment` 18 t (upper bound, Klemm) with `endowment_source`, `first_worked`; `share_of_empire_output` is not applicable to Egypt-Nubia as no region key exists (same limitation as the file's `_doc` notes for dacia). |
| Sardis and the Pactolus (Lydia) | about 38.49 N, 28.04 E (Sardis, RECALLED) | alluvial electrum | sixth century BCE, Croesus; Lydian gold refinery of the first half of that century | no output figure found; electrum separated by cementation and cupellation | Ramage and Craddock 2000, King Croesus' Gold (Harvard); Sardis expedition essay | SNIPPET | D | New `ancient.json` entry would need a grade; none found. Not ready. Note: electrum is a gold-silver mixture, so it also needs a silver byproduct ratio, which the data model's `byproducts` could carry. |
| Bambuk and Bure (West Africa) | about 13.5 N, 11.5 W (Bambuk) and 11.3 N, 9.2 W (Bure); RECALLED | alluvial and shallow pit working | medieval trade peak; two-thirds of the gold moving around the medieval Mediterranean is a SNIPPET claim | no sourced output or grade found; Garrard and Bovill are the primaries and were not opened | search summaries only | SNIPPET | D | Not ready. Note: dates outside the Roman start; relevant for a later scenario. |
| Andes (Carabaya, Sandia, Curimayo; Inca) | about 14 S, 70 W; RECALLED | placer | pre-Columbian to colonial | no figure found | search summaries only | SNIPPET | D | Not ready. |
| Thrace and Macedon (Mount Pangaion, Thasos) | about 41 N, 24 E; RECALLED | vein plus placer | fifth century BCE onward | no figure opened | not searched effectively | RECALLED | D | Not ready; Healy 1978 and Herodotus 6.46-47 are the places to look. |

## 5. Existing entries: what the sources say about them

| Entry | Existing figure and conf | What the sources add |
|---|---|---|
| `rio_tinto_jarosite` grade | 2.0 kg/t, D | Second independent mention at about 0.2 % (Bettenay supergene section). Raise to C. Surveyed coordinates in the file (37.7 N, -6.6 E) are the source-checked values; the game lat and lon are placeholders per `_doc`. |
| `laurion_lead` silver byproduct | 2.0 kg silver per tonne lead, D | Conophagos range 0.1 to 0.2 % Ag in lead metal (1.0 to 2.0 kg per tonne lead). 2.0 is the maximum; a midpoint is 1.5. Not ready to move because the Wood et al. figure the file cites was only seen in a snippet; read Wood 2022 first. |
| `las_medulas_alluvial` grade vs endowment | 0.0003 kg/t with 1,640 t endowment | Mutually inconsistent with the 93.5 million m3 figure (see 1.2). Needs a decision on which is the physical fact. |
| `dacia_vein_gold` | 0.008 kg/t, 500 t | Endowment now has a UNESCO figure (SNIPPET). Grade stands. |
| `hispania_lead` grade | 180 kg/t, C | No opened source supports or contradicts it. Strabo notes some Iberian lead is silver-poor. |

## 6. Which data changes are ready now, and which are not

### Ready (well enough sourced to edit now)

1. Add an Eastern Desert and Nubian gold deposit to `data/world/geography/deposits/ancient.json`, with grade, endowment ceiling and period from Klemm et al. 2001 (READ, conf B). The coordinates must be checked against a map before the edit; I could not confirm them.
2. Raise `rio_tinto_jarosite.conf` from D to C and add Bettenay 2022 p. 72 to its source note. The value is unchanged.
3. Record the Melle model as a reference (Bettenay Table 4, READ) in the notes of `lead_kg` and `galena_kg` as an independent bound on ore per tonne of lead and on dressing and smelting losses. This changes yield_basis text only, not numbers.
4. Record the Melle hours-per-kg derivation and the staff-share ratios (Bettenay pp. 76-77) in Complaint 349 as the target the support-work and processing constants are compared with, since the complaint already uses them.

### Not ready (do not edit yet)

- Any change to `hispania_lead`, `hispania_silver`, `laurion_lead` or `laurion_silver` grade: the sources opened give Melle only; Domergue, Davies, Healy, Conophagos and Wood 2022 need to be read.
- `las_medulas_alluvial` grade and endowment: the two figures in the file contradict each other against the stated volume, and the grade source is a snippet. Needs the Polish paper or Lewis and Jones 1970 opened.
- Water inflow per tonne (`WATER_LIFTED_TONNES_PER_TONNE_ORE_BY_DEPTH`): no source found with a flow rate. Wheel counts are snippet-level.
- Hauling, hoisting, timbering and ventilation hours: no source gives a per-tonne figure.
- Dressing hours per tonne: only crew counts at Laurion washeries (SNIPPET), no throughput.
- Gold deposits for Lydia, West Africa, the Andes and Thrace: no grade or output found; locations RECALLED.
- Fuel per tonne of ore for roasting and smelting: Bettenay gives wood per rock broken in fire-setting but no charcoal per tonne of ore or per tonne of lead; the existing `lead_kg` charcoal input (640 kg per tonne lead) has no opened source.
- Cartagena and Rio Tinto labour per tonne or per kg of silver: the Strabo passage gives workforce and revenue only.

## 7. Suggested reading order to close the gaps

1. Wood 2022 (Archaeometry), the grade source already cited by the data, to confirm the silver-to-lead ratios.
2. Domergue, C. 1990, Les mines de la peninsule iberique dans l'antiquite romaine (Rome: Ecole francaise de Rome) for Sierra Morena and Cartagena grades, ore tonnage, and ore-to-lead ratios.
3. Healy, J.F. 1978, Mining and Metallurgy in the Greek and Roman World, for Laurion labour and drainage.
4. Conophagos, C. 1980, Le Laurium antique, for Laurion grades and washery throughput.
5. Lewis, P.R. and Jones, G.D.B. 1970, Roman Gold-Mining in North-West Spain, JRS 60, 169-185, for Las Medulas volume and recovery.
6. Cauuet and Tamas on Rosia Montana for the Roman grade and stope labour.
7. Anguilano et al. 2010, ArcheoSciences 34, 269-276, to verify the jarosite grade and lead flux.
