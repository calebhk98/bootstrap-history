# Research: where each civilisation's coin metal came from, and which mines the catalogue lacks

Branch `coin-metal-deposits`. Sources were opened in this session unless a line says "not opened". Quotes are verbatim from the page or PDF read.

How the catalogue turns a row into output (read in `sim/geography/resources_sites.py` and measured with `worked_deposits`): a row on a civilisation's tile whose `first_worked` is not after the start year is a worked deposit. Its size is the row's `endowment` when it has one, else the geological model's expectation (`expected_for_deposit_type:` or `expected_across_types_of:`), and its yearly rate is size times the parameter `resources_working_share_per_year` (0.004). `contained_tonnes` is read by no code. A row with the placeholder type `unspecified_placeholder` gets no size for silver, lead and tin but does get one for copper. The shares (`share_of_empire_output`, `share_of_reference_output`) are not used for the rows added here.

## England 1300 (struck silver penny)

Money: silver sterling (civilisation file `coin_standard`).

Where the silver came from:
- Mostly imported. Allen, "Silver production and the money supply in England and Wales, 1086-c.1500", Economic History Review 64(1), 2011, abstract (read at https://ehs.org.uk/article/silver-production-and-the-money-supply-in-england-and-wales-1086-c-1500/): "Imported silver was usually a greater source of the metal in the English currency than locally mined silver." Same abstract: "Devon silver made a significant but not predominant contribution to mint output at times of bullion scarcity in the 1290s". Full text and figures not opened (abstract only).
- Claughton and Smart, "The Crown silver mines in Devon: capital, labour and landscape in the late medieval period", Historical Metallurgy 44(2), 2010, https://www.hmsjournal.org/index.php/home/article/download/152/148 (PDF read): "beyond the end of the 12th century England was relying almost entirely on silver drawn into the economy as a result of increased exports, particularly wool, textiles and tin." Also: "Between 500,000 and 600,000 pounds was in circulation by 1280, possibly rising to over 1,000,000 by the early part of the 14th century" (the paper cites Allen 2001; the pound sign is lost in the text extraction).
- Home mines at about 1300: the Crown's Devon mines. Same paper: "For over 50 years, from 1292 to 1349, the mines were worked by the English Crown under direct management. They provided work for up to 400 miners"; "the simultaneous opening of silver mines at either extremity of the county in 1292, at Combe Martin on the north coast, and at Bere Ferrers in the Tamar Valley"; "The mines at Combe Martin were abandoned by the Crown within four years but those at Bere Ferrers were worked by the Crown"; "production rising rapidly to over 23,000 ounces in 1297" (about 0.7 t of silver that year; 23,000 x 31.1 g = 715 kg). The ore was "silver-bearing lead ore", smelted and the lead "refined ... to extract silver". The Frescobaldi leased the mines in April 1299 for under a year and gave them up "on the grounds that they could not make a profit". Exeter project page (https://www.exeter.ac.uk/research/projects/archaeology/silvermining/): "silver was worked under the direct management of Crown officers from 1292 to 1349 ... with over 300 men employed on wages and piecework".
- Northern Pennines (Alston Moor, "silver mines of Carlisle"): the same paper says the twelfth-century output is "a matter for debate" (Blanchard up to "24 tonnes in one year", geologists "inclined towards a low silver yield"). Allen's abstract calls the idea that they were the principal source of late twelfth-century silver "untenable". Wikipedia, Alston, Cumbria (read): "silver mines of Carlisle" in the 13th century, "Silver was found in high proportions in smelted lead", and in 1296 Edward I "reclaimed the Scottish estates" including Alston Moor. No page opened gives silver output there in 1300.

Catalogue had (tiles of england_1300): `britannia_silver_generic` (united_kingdom_02, a Roman-era placeholder with no date or size, no size in the engine), `britannia_lead` (united_kingdom_02, Mendip), `gaul_germania_lead_generic` (france_05), `rammelsberg` (germany_01); tin `cornish_tin_streaming` (united_kingdom_01, 2,000,000 t, 8,000 t a year by the engine) and `gaul_germania_tin_generic`; copper generic rows; no gold, no mercury.

Added (file `data/world/geography/deposits/reference_output_sites.json`):
- `bere_ferrers_silver` (silver, united_kingdom_01, first_worked 1292, no size). Engine result after the edit: size 290 t from the geological model, 1.16 t a year, against the one recorded year of about 0.7 t (1297).
- `bere_ferrers_lead` (lead, united_kingdom_01, first_worked 1292, no size), the same working, since the silver was won from lead. The engine sizes it at 7,199 t, 28.8 t a year; no source gives a lead weight.

Not added:
- Combe Martin: the paper says the Crown abandoned it within four years of 1292; later leasing is stated only for after 1350, so a working at 1300 is not shown.
- Alston Moor silver or lead: no output or 1300 working read (see above).
- Gold: no source opened says gold was mined in England in 1300. `Gold_mining_in_the_United_Kingdom` on Wikipedia returned 404, and Claughton and Smart mention only a 1260s report of an ore "allegedly containing copper, gold and silver" at "la Hole" in Devon, "unsuccessful". Nothing added. English gold at this date is not shown to be home-mined.
- Mercury: the civilisation file already says imported.

## Norse 900 AD (weighed silver)

Money: hack-silver and ingots by weight.

Source: CORDIS record of the ERC project SILVER (Silver and the Origins of the Viking Age, grant 802349, University of Oxford), https://cordis.europa.eu/project/id/802349/reporting: "Since no silver was mined in Scandinavia during this period, it had to be imported." Science Norway, Biornstad, 20 November 2025, https://www.sciencenorway.no/viking-age-archaeology-natural-science/over-a-span-of-150-years-a-billion-islamic-silver-coins-may-have-flowed-into-the-viking-world/2577163: "Perhaps a billion silver dirhams flowed into Scandinavia and the Viking world between 800 and 950," says Gullbekk; "Some of that silver likely also came from Europe, particularly from the Carolingian Empire". Kongsberg (Wikipedia, Kongsberg Silver Mines): "Silver was first discovered between the 1 July and 5 July 1623" (with a venture in 1539 and a "Argenti Fodinae" reference in 1532, both centuries after 900). The catalogue's own Sala rows are dated 1400.

Catalogue had on norse tiles: `falun_copper` only (sweden_03); no silver, lead, tin, gold, mercury. The civilisation file's `imported_ores` already states silver, tin, gold, lead and mercury as imported.

Added: nothing. Silver was imported (Islamic dirhams via the eastern route, Carolingian and English coin and hack-silver). Tin, gold and lead: no source opened shows Norse home mining; I opened nothing on Norse tin or gold beyond the civilisation file's own notes (which carry no figure). Lead: I did not find a source on Scandinavian lead in 900 (Sala is dated 1400 in the catalogue).

## Han China 100 AD (cast bronze cash)

Money: wu zhu cash of about 3 g, state cast (civilisation file).

Coin scale: Wikipedia, Han dynasty coinage (read first 100,000 characters), https://en.wikipedia.org/wiki/Han_dynasty_coinage: "average annual production of 220,000,000 bronze cash coins minted (or 220,000 strings of 1,000 cash coins)"; the Mintage section says the government "minted over 28,000,000,000 cash coins" from 118 BC to 5 AD, annual average 220,000,000 (Nishijima 1986, p. 588, note 78; Hartill 2005, p. 85). This is a Western Han average, not a figure for AD 100. At 3 g a piece that is about 660 t of bronze a year (220,000,000 x 3 g); the share that is copper is not read here.

Copper districts named by sources opened:
- Yandao (Yingjing County, Sichuan): same Wikipedia article: Emperor Wen granted Deng Tong the right to "exploit the revenue of a copper mine in Yandao". Added as `yandao_copper`.
- Tonglushan (Daye, Hubei): in the catalogue (`tonglushan_copper`). China Daily, 16 June 2026 (read): "produced about 400,000 metric tons of ancient slag, yielding between 80,000 and 120,000 tons of crude copper"; the article gives no operating dates, so working in AD 100 is not shown by it.
- Danyang and Zhang mountain: Hanshu ch. 28 (zh.wikisource.org, 漢書/卷028下, read) says of the Wu region 吳東有海鹽章山之銅 ("east of Wu there is the copper of Zhang mountain in Haiyan"). I did not open a source locating Zhang mountain on a modern map, and the Danyang copper mirror inscriptions came only from a search summary, not a page I read. Not added.
- Gejiu (Yunnan): Wikipedia, Tin mining (read): Yunnan deposits "were not mined until around 700 BC, but by the Han dynasty had become the main source of tin in China." The Heidelberg Gejiu page was unreachable.

Catalogue and engine for han tiles (measured with `worked_deposits`, working share 0.004):

| Resource | Row | Tile | Size t (engine) | Basis | Rate t per year |
|---|---|---|---|---|---|
| copper | `tonglushan_copper` | china_21 | 59,629 | model expectation across copper types | 239 |
| tin | `gejiu_tin` | china_02 | 3,409 | model expectation across tin types | 13.6 |
| silver | `huize_silver` | china_08 | 525 | model | 2.1 |
| lead | `shuikoushan_lead` | china_11 | 155,150 | model | 621 |
| gold | `han_poyang_placer_gold` | china_22 | 0.44 | model | 0.0018 |

The catalogue's `contained_tonnes` is 100,000 t for Tonglushan and 2,220,000 t for Gejiu, but no code reads those, so the engine's sizes above are the model's, not the catalogue's. Two readings for the orchestrator: (a) the copper rate (239 t a year, 477 with Yandao) is below the Western Han coin average of about 660 t of bronze a year; (b) the tin rate of 13.6 t a year is the only tin on the tiles. Whether bronze cash was alloyed at a share that makes tin binding is not read here.

Added: `yandao_copper` (copper, china_18, no date, placeholder type, conf D). It is sized by the model like `tonglushan_copper` (59,629 t, 239 t a year), so it doubles the Han copper rate on evidence that names the place and the grant only. The source dates the grant to Emperor Wen's reign and says nothing about AD 100. Drop it if that is too weak.

## Mexica 1500 (cacao)

Money is a crop, not a metal, so the question here is only where metals came from.

- Silver: López Luján and Ruvalcaba Sil, "Mexica Gold" (in the Golden Kingdoms exhibition volume, mesoweb PDF https://www.mesoweb.com/es/articulos/sub/MexicaGold.pdf, text read): silver "was rarely used in Mesoamerican metalworking. Although sixteenth-century sources mention its sale in the most important markets of the Aztec Empire, it is significant that ... silver does not appear in the lists of items periodically paid in tribute to Tenochtitlan ... after forty years of excavations at the Templo Mayor, only this small silver piece has been recovered." Wikipedia, Traditional metal working in Mexico: "As silver rarely appeared on the surface it was almost exclusively mined." Mexico News Daily (5 facts about Taxco; a news article): "historians have suggested that the mine was pre-Columbian, exploited by the Indigenous Chontal of Guerrero ... in the 1400s", from INAH exploration of a mine found in Taxco. Wikipedia, Taxco: Spanish silver lodes "in around 1532".
- Gold: same Mexica Gold paper: "native gold was obtained from placer deposits"; Moteuczoma named the main placers as "Zozolan, Tochtepec, and Malinaltepec, and ... Coatlecamac, which lay beyond the southern border of the empire in the lands of Chinantla. Local peoples exploited these sources, sending the gold to Tenochtitlan"; "Eleven provinces paid gold in tribute".

Catalogue has on mexica tiles: `mexica_tlapa_placer_gold` (mexico_02, unsized, engine size 0.44 t), `taxco_silver` (mexico_02, dated 1532 so not worked in 1500), `taxco_tin` (mexico_02), copper, lead, mercury. 

Added: nothing. Silver is shown to be scarce, absent from tribute and, in the sources read, not a mined output at scale. The one pre-Columbian Taxco silver mine claim rests on a news article and has no tonnage or date beyond "1400s". Gold placers are already represented by the Tlapa row; Tochtepec (Tuxtepec) and Malinaltepec are named but I did not open coordinates for them, so no separate rows.

## Rome 100 AD (denarius)

Money: silver denarius (about 80 percent fine at the reform, civilisation file). Not probed.

Catalogue has on Roman tiles: `hispania_silver` (spain_02, Cartagena, 10,780 t contained, working_unknown, no size in the engine), `rio_tinto_jarosite` (spain_01, no size in the engine), `laurion_silver` (greece_01, 3,500 t, 14 t a year), `britannia_silver_generic`, `italia_silver_generic` (both unsized). The engine's silver rate at the Roman tiles sums to 14 t a year, all from Laurion. Reading for the orchestrator, not an engine conclusion: the Cartagena row carries the 35 t a year figure (Kay 2014, via the Geochemical Perspectives Letters article already cited in the row) only in prose.

Searches this session: Wikipedia, Roman metallurgy (read): Iberia, Gaul, Laurion (Greece), Asia Minor listed for silver; Spain's "40% share in world production" is attached to the lead row. A search summary mentioned Castulo near Linares; I did not open a page for it. Added: nothing.

## Not found or not opened

- No page opened gives silver output for Bere Ferrers in any year other than 1297, or for Combe Martin, Alston Moor or Wales in 1300.
- Claughton, Mining in a Medieval Landscape (Exeter UP), Claughton's 2003 Exeter thesis, Allen's full 2011 article and Allen's book (chapter 8 on the sources of bullion): not opened (abstracts and a search summary only).
- Hanshu locating Zhang mountain and Danyang copper; Shiji on Deng Tong's Yandao mine; the Heidelberg Gejiu and copper pages (unreachable); the Springer Gejiu Han-period article (login redirect).
- The pre-Hispanic Taxco silver mine (news article only), Tochtepec and Malinaltepec coordinates.
- A source on Scandinavian lead or tin working in 900.
- Alston Moor working in 1300 and the Pennine silver share.
- Roman Sierra Morena and Castulo silver pages.
