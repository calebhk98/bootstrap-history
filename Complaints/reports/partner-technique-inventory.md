# Partner technique inventory: what each civilisation and its trading partners could make at the start date

Scope: research only. No code or data changed; the test suite was not run. Branch `partner-technique-inventory-research`, cut from `structural-dedupe-and-owner-decisions`, read on 2026-10-06. It supports Complaints 382 (step 4) and 407 (foreign countries need their own techniques) and follows `Complaints/reports/gated-materials-research.md`.

Source tags: **[snippet]** only a web-search summary was seen, link given; **[recalled]** the author's background knowledge of the history of technology, no source opened; **[repo]** read in this repository. No web page was opened in full, so nothing below is tagged read. Treat every historical row as a lead to confirm before it becomes data (CLAUDE.md 4.1 allows what is known at the start date as an initial condition, but a wrong initial condition is still a wrong one).

## 1. How a known set is declared, and what that means here

`starting_techs` in each `data/civilizations/<id>.json` is "exhaustive, duplicate-free" (`data/civilizations/_SCHEMA.md`). The engine never infers ownership. A node whose `pre` the civilisation does not hold needs a `prerequisite_gaps` entry with a reason, or `validate` errors. A partner's solvable materials are exactly what its `starting_techs` gate (`sim/engine/foreign_economies.py`, per the earlier report). So a technique the file omits is a technique the partner cannot trade.

Two structural facts found while reading:

1. `data/world/foreign_economies.json` lists one economy: `han_china_100ad`, years -202 to 220. For England 1300, Norse 900 and Mexica 1500 there is therefore no trading partner at all today, and for Rome there is one.
2. Production entries are gated by a specific node, not by the "material" node. Measured with a throwaway read of `data/production/*.json` (`requires_node`): `paper_kg` needs `prn_hand_papermaking`, `porcelain_kg` needs `mat_porcelain`, `cast_iron_kg` and `pig_iron_kg` need `blast_furnace`, `silk_kg` needs `tx2_sericulture`, `steel_plate_kg` needs `cementation_steel`, `iron_bar_kg` needs `finery_puddling`, `pepper_kg` needs `fud_pepper_cultivation`, `sugar_cane_sett_kg` needs `ag2_sugar_voyage`, `camphor_kg` needs `distillation_alcohol`, `dye_kg` needs `tex_dye_madder`, `glass_raw_kg` needs `mat_glass_soda`, `cassia_kg` has no gate. Han already lists `mat_paper` (with a `prerequisite_gaps` reason) but not `prn_hand_papermaking`, which is why Han cannot make `paper_kg`. Han lists neither `mat_porcelain` nor any stoneware node.

## 2. Tree gaps found (no node exists, so no file can list the technique)

| Technique | Where it matters | Evidence it is missing |
|---|---|---|
| Chinese finery (fining cast iron to wrought iron or steel, "chaogang") | Han 100 AD | `finery_puddling` is Cort's reverberatory puddling, pre `blast_furnace` and `cap_heat_1300`; its note is about 1780s coal. [repo] Han practice is the older finery. [snippet](https://donwagner.dk/arch-iron/eu/co-fusion-eu.html) |
| Co-fusion and solid-state decarburisation of cast iron | Han | No node. [snippet](https://donwagner.dk/arch-iron/eu/co-fusion-eu.html), [snippet](https://cir.nii.ac.jp/crid/1130000793875981696) |
| Wootz and Central Asian crucible steel (charcoal fired, small sealed crucibles) | India, Persia, Central Asia, Norse imports | `crucible_steel` is Huntsman's, pre `cementation_steel`, `coal_coke`, `cap_heat_1600`. [repo] The older process: [snippet](https://archive.madrasmusings.com/Vol%2024%20No%2017/a-2500-year-old-industrial-estate.html), [snippet](https://hmsjournal.org/index.php/home/article/view/314) |
| Lacquer (urushi, Rhus verniciflua) | Han, Kushan trade | No node; grep of `data/branches` finds only `mat_shellac`. Han state lacquer workshops: [snippet](https://www.worldhistory.org/article/1090/chinese-lacquerware/.md); Chinese lacquer bowls at Begram: [snippet](https://www.cambridge.org/core/journals/international-journal-of-asian-studies/article/abs/chinese-lacquerwares-from-begram-date-and-provenance/84D79F1D25F4D15015F3B12FD84C22AA) |
| Bark paper (amate) | Mexica | `prn_hand_papermaking` is linen rag. [repo] Amate: [snippet](https://en.wikipedia.org/wiki/Amate) |
| Cochineal dye | Mexica | No node. [snippet](https://greekreporter.com/2026/07/10/bowls-show-aztec-women-colored-textiles/) |
| Lead-barium glass | Han | Only soda-lime nodes exist. [snippet](https://en.wikipedia.org/wiki/Ancient_Chinese_glass) |
| Basic windmill (post mill) | England 1300 | Only `pwr_windmill_fantail` and `en_windmill_fantail`, both later. [repo]; windmills as a medieval invention [snippet](https://www.medievalists.net/2023/06/medieval-inventions-world) |
| Fritware, lustre and tin glaze | Islamic world 1300 | `mt2_stoneware`, `mt2_bone_china`, `mfg_enamelling` exist; no tin-glaze or lustre node. [repo]; [snippet](https://muslimheritage.com/filling-gap-history-pre-mod-industry/) |
| Spices other than pepper (cinnamon, clove, nutmeg, ginger, saffron) and incense (frankincense, myrrh) | Rome, England, Aksum, India | Only `fud_pepper_cultivation` and `cassia_kg` (no gate). [repo] England spice list: [snippet](https://www.homemade-dessert-recipes.com/history-of-sugar-in-england.html) |
| Crystallised sugar by an Indian-style process before the voyage nodes | Islamic world 1300 | `ag2_sugar_voyage` and `fud_sugar_cane_cultivation` exist, but the Islamic world held sugar refining by 1300. [snippet](https://muslimheritage.com/filling-gap-history-pre-mod-industry/) |

Duplicate pairs to resolve before listing ids (so a file lists the one the production data gates on): `lnd_stirrup` and `tl_stirrup`; `sea_sternpost_rudder` and `tr_sternpost_rudder`; `rag_paper`, `mat_paper`, `if_rag_paper`; `fud_sugar_cane_cultivation` and `ag2_sugar_voyage`. [repo]

## 3. Han China 100 AD (file: `han_china_100ad`, enabled partner)

| Technique | Node id | In file? | Source and tag |
|---|---|---|---|
| Paper (hemp, rag, bark), Fangmatan fragment about 179 BC, Baqiao hemp paper, Cai Lun 105 AD | `rag_paper`, `prn_hand_papermaking`, `mat_paper` | `mat_paper` yes; `rag_paper` and `prn_hand_papermaking` MISSING | [snippet](https://en.wikipedia.org/wiki/History_of_paper) |
| High-fired glazed stoneware, proto-porcelain (Zhejiang) | `mt2_stoneware` | MISSING | [snippet](https://www.koh-antique.com/yue1/yue.html) |
| Mature celadon "porcelain", Shangyu, late Eastern Han | `mat_porcelain` | MISSING (see open question 1) | [snippet](https://www.koh-antique.com/yue1/yue.html) |
| Fired brick and tile, earthenware | `civ_brick_tile`, `mt2_earthenware` | MISSING both | [recalled] |
| Blast furnace, cast iron | `blast_furnace`, `mat_cast_iron` | yes | [repo]; [snippet](https://archaeology.pku.edu.cn/2018An-iron-production-and-exchange-system-at-the-center-of-the-Western-Han-Empire.pdf) |
| Grey, white and malleable cast iron | `mt2_grey_cast_iron`, `mt2_white_cast_iron`, `mt2_malleable_cast_iron` | MISSING | [snippet](https://cir.nii.ac.jp/crid/1130000793875981696) |
| Decarburised cast iron, "chaogang" finery, co-fusion steel | no node (section 2) | n/a | [snippet](https://donwagner.dk/arch-iron/eu/co-fusion-eu.html) |
| Water-driven bellows | `bellows_water_blown` | yes (with gap) | [repo] |
| Water-powered trip hammer and crank-and-rod | `met_trip_hammer`, `crank_conrod` | MISSING both | [recalled]; low confidence on the crank node's modern-engine prerequisites |
| Silk (sericulture, reeling, weaving), ramie | `tx2_sericulture`, `tx2_silk_fibre`, `mat_silk`, `tex_silk_trade`, `tx2_ramie_fibre` | yes | [repo]; Silk Road [snippet](https://en.wikipedia.org/wiki/Science_and_technology_of_the_han_dynasty) |
| Hemp fibre and retting (the commoner cloth) | `tx2_hemp_fibre`, `tx2_retting` | MISSING both | [recalled] |
| Looms: heddle, shed, beam, selvedge (Han drawlooms) | `tx2_heddle`, `tx2_shed`, `tx2_beam`, `tx2_selvedge` | MISSING all four | [recalled] |
| Dyeing in fibre, yarn, piece; scouring | `tx2_dyeing_fibre`, `tx2_dyeing_yarn`, `tx2_dyeing_piece`, `tx2_scouring` | MISSING all | [snippet](https://blog.fabrics-store.com/?p=20240), [recalled] |
| Indigo from Polygonum and Strobilanthes | `tex_indigo` (pre `tex_dye_woad`, `mat_lime`) | MISSING; the woad prerequisite is wrong for China | [snippet](https://blog.fabrics-store.com/?p=20240) |
| Resist dyeing (wax, paste) | `tx2_resist_dyeing` (pre `tex_mordanting`) | MISSING | [snippet](https://blog.fabrics-store.com/?p=20240) |
| Cotton (south and west fringe; not a staple) | `tex_cotton_trade` | yes | [snippet](https://www.lse.ac.uk/Economic-History/Assets/Documents/Research/GEHN/Helsinki/HELSINKIZurndorfer.pdf) |
| Lacquer | no node | n/a | [snippet](https://www.worldhistory.org/article/1090/chinese-lacquerware/.md) |
| Glass (lead-barium, small scale) | no matching node | file says almost none (`briefing_absent`) | [snippet](https://en.wikipedia.org/wiki/Ancient_Chinese_glass) |
| Wet rice | `fud_rice_cultivation` | MISSING | [recalled] |
| Sugar cane (juice and syrup only) | `fud_sugar_cane_cultivation` | MISSING; crystallised sugar is later (open question 4) | [recalled] |
| Sternpost rudder (tomb models) | `sea_sternpost_rudder` | MISSING | [recalled] |
| Shellac, camphor, cassia | `mat_shellac`, `mat_camphor`, `cassia_kg` | `mat_shellac`, `mat_camphor` yes; `cassia_kg` ungated | [repo] |

## 4. Rome 100 AD (file: `rome_100ad`)

| Technique | Node id | In file? | Source and tag |
|---|---|---|---|
| Blown soda-lime glass, window glass | `mat_glass_soda`, `civ_glass_windows` | yes | [repo]; [recalled] |
| Terra sigillata (slip, no true glaze), brick and tile | `mt2_earthenware`, `civ_brick_tile` | yes | [snippet](https://en.wikipedia.org/wiki/Terra_sigillata) |
| Noric steel, bloomery iron | `mat_wrought_iron`, `met_bloomery_bog_iron`, `steel_noric_kg` | yes | [repo]; [recalled] |
| Brass (cementation of calamine), amalgam | `mat_brass`, `mat_calamine`, `mt2_amalgamation` | yes | [recalled] |
| Imported silk, cotton, pepper, indigo, shellac, camphor, natron | `tex_silk_trade`, `tex_cotton_trade`, `tex_indigo`, `mat_shellac`, `mat_camphor`, `mat_natron` | yes | [snippet](https://en.wikipedia.org/wiki/Indo-Roman_relations) (see the earlier report) |
| Water mill, screw press, treadmill | `cap_power_water`, `pwr_screw_press_power`, `pwr_animal_treadmill` | yes | [repo] |
| Flax, retting, rope laying (Rome ropes and linen) | `tx2_flax_fibre`, `tx2_retting`, `tx2_rope_lay` | MISSING all three; England and Norse hold them | [recalled] |
| Hemp (rope, sailcloth) | `tx2_hemp_fibre` | MISSING | [recalled] |
| Sun bleaching, shed and selvedge | `tx2_bleaching_sun`, `tx2_shed`, `tx2_selvedge` | MISSING | [recalled] |
| Cast iron, paper, porcelain, crystallised sugar, lacquer | none held | correctly absent | [recalled] |

Rome needs almost no additions; the gaps are textile basics that England and Norse already list. The point for the partner design is the opposite one: Rome is the buyer and what it cannot make must come from partners (sections 3, 8, 9, 10).

## 5. England 1300 (file: `england_1300`)

| Technique | Node id | In file? | Source and tag |
|---|---|---|---|
| Paper imported (Italy, Spain); first English mill 1490s | `mat_paper` | yes, with a gap reason; production gate `prn_hand_papermaking` correctly absent | [snippet](https://www.cam.ac.uk/research/features/from-pulp-to-fiction-our-love-affair-with-paper) |
| Forest glass (Wealden), potash glass | `mat_glass_soda`, `civ_glass_windows`, `ag2_potash` | yes (the node is soda-lime; forest glass is potash, which is a tree-modelling question) | [snippet](https://surreycc.gov.uk/culture-and-leisure/archaeology/archaeological-unit/recent-archaeology-projects/investigating-the-wealden-glass-industry) |
| Stoneware: imported Rhenish, not made | `mt2_stoneware` | absent, correct | [snippet](https://archaeologydataservice.ac.uk/catalogue/adsdata/arch-5456-1/dissemination/1995/MedievalCeramics_1995-19_19-28.pdf) |
| Earthenware, glazed and unglazed | `mt2_earthenware` | yes | [repo] |
| Wrought iron, no blast furnace until the 1490s | `mat_wrought_iron`, `civ_iron_wrought` | yes | [recalled] |
| Stirrup, horse collar | `lnd_stirrup` (pre `horse_collar`, `mat_wrought_iron`) | `horse_collar` yes; `lnd_stirrup` MISSING | [recalled] |
| Mechanical clock | `clock_mechanical_escapement` | yes | [snippet](https://www.medievalists.net/2026/06/medieval-inventions-shaped-modern-world/) |
| Gunpowder, early guns (about 1326) | `gunpowder`, `mil_gunpowder_base` | absent | [snippet](https://www.cambridge.org/core/books/royal-and-urban-gunpowder-weapons-in-late-medieval-england/analysis-of-guns/C989F0C253657C6459DCF25390A9171E); open question 6 |
| Windmill | no node | n/a | [snippet](https://www.medievalists.net/2023/06/medieval-inventions-world) |
| Sugar and spices, imported | `fud_sugar_cane_cultivation`, `fud_pepper_cultivation` | absent, correct (trade goods; no node for them) | [snippet](https://www.homemade-dessert-recipes.com/history-of-sugar-in-england.html) |
| Silk (Lucca, import), cotton (import) | `mat_silk`, `tex_silk_trade`, `tex_cotton_trade` | yes | [recalled] |
| Dyes: woad, madder; mordanting; fulling | `tex_dye_woad`, `tex_dye_madder`, `tex_mordanting`, `tx2_fulling` | yes | [recalled] |
| Compass | `sea_magnetic_compass` | `sea_lodestone` listed, compass MISSING | [recalled]; open question 6 |

Listed but doubtful at this date (check, do not remove blindly): `tex_indigo` (European indigo is later; the woad vat is the same chemistry), `mat_papyrus` (gone from the Latin West), `mat_obsidian_blade`, `sea_lead_sheathing`. [recalled]

## 6. Norse 900 (file: `norse_900ad`)

| Technique | Node id | In file? | Source and tag |
|---|---|---|---|
| Bog iron bloomery, pattern-welded and Ulfberht blades | `met_bloomery_bog_iron`, `mat_wrought_iron` | yes | [repo]; [snippet](https://en.wikipedia.org/wiki/Ulfberht_swords) |
| Crucible steel for Ulfberht blades: imported ingots, Volga route | no node (section 2) | n/a | [snippet](https://en.wikipedia.org/wiki/Ulfberht_swords) |
| Clinker hull, keel, square sail | `sea_clinker_hull`, `sea_keel_deep`, `sea_square_sail` | yes | [repo] |
| Stirrup | `lnd_stirrup` (pre `horse_collar`, not held by Norse) | MISSING; needs a gap reason | [recalled] |
| Glass beads (made from imported cullet and Persian beads) | `mat_glass_soda` | listed | [snippet](https://vikingr.org/stories/the-silver-tide) |
| Silk, spices, silver imported from Byzantium and the caliphate | `tex_silk_trade` | listed; `mat_silk` MISSING (England has it) | [snippet](https://en.wikipedia.org/wiki/Trade_during_the_Viking_Age) |
| Wool, felting, linen, hemp, sailcloth, rope | `tx2_hemp_fibre`, `tx2_rope_lay`, `tex_sailcloth` | yes | [repo] |
| Soapstone, amber, walrus ivory, furs | no nodes | n/a | [snippet](https://en.wikipedia.org/wiki/Trade_during_the_Viking_Age) |

## 7. Mexica 1500 (file: `mexica_1500`)

| Technique | Node id | In file? | Source and tag |
|---|---|---|---|
| Bark paper (amate) | no node | n/a | [snippet](https://en.wikipedia.org/wiki/Amate) |
| Cochineal and other dyes | no node | n/a | [snippet](https://greekreporter.com/2026/07/10/bowls-show-aztec-women-colored-textiles/) |
| Cotton (tribute), backstrap loom, hand ginning | `tex_cotton_trade`, `tex_backstrap_loom`, `tex_hand_ginning` | first two yes; `tex_hand_ginning` MISSING | [snippet](https://www.historyskills.com/classroom/year-8/aztec-clothes/) |
| Obsidian blades and macuahuitl | `mat_obsidian_blade` | yes | [snippet](https://www.worldhistory.org/article/2060) |
| Copper, tin and arsenic bronze, casting of bells (Tarascan centre) | `mat_bronze`, `met_investment_casting` | `mat_bronze` yes; lost-wax casting node MISSING | [snippet](https://www.ancientamericas.org/sites/default/files/02063Maldonado01.pdf) |
| Natural rubber (balls, from Gulf lowlands) | `mat_natural_rubber` | MISSING | [snippet](https://en.wikipedia.org/wiki/Mesoamerican_rubber_balls) |
| Unglazed polychrome earthenware | `mt2_earthenware` | MISSING | [snippet](https://nativeamericanmuseum.org/how-did-natives-decorate-pottery-without-glaze/) |
| Cacao, maize, chinampa | `fud_cacao`, `fud_maize`, `fud_chinampa` | yes (with gaps) | [repo] |

Listed but doubtful: `tex_wool` (no sheep before contact), `tex_dye_madder`, `mat_alum`. [recalled]. Metallurgy beyond bronze (no iron) is already handled by `briefing_absent`.

## 8. Partners for Rome: Parthia, Kushan, India, Aksum

Source for the trade structure: Parthia as intermediary to China [snippet](https://historia-scribere-journal.uibk.ac.at/historia_scribere/article/view/2922); Kushan as middleman with Chinese lacquer, glass and ivory at Begram [snippet](https://www.iranicaonline.org/articles/begram); Barygaza and Barbaricum exports in the Periplus [snippet](https://sourcebooks.web.fordham.edu/ancient/periplus.asp).

| Partner | Technique (at about 100 AD) | Node id | Needs a file? | Source and tag |
|---|---|---|---|---|
| Parthia | Re-export of silk; glass and metalwork on Mesopotamian bases; no distinct frontier technique | `tex_silk_trade`, `mat_glass_soda` | Yes, but thin: mostly a re-export economy | [snippet](https://historia-scribere-journal.uibk.ac.at/historia_scribere/article/view/2922) |
| Kushan | Cotton and silk transit, glass, ivory; wootz and Indian iron arrive via the Indus ports | `tex_cotton_trade`, `tex_silk_trade` | Yes | [snippet](https://www.iranicaonline.org/articles/begram) |
| South and west India (Tamilakam, Satavahana ports) | Wootz at Kodumanal, cotton cloth, indigo, pepper, lac, ivory; Indian iron and steel at Barygaza | `fud_pepper_cultivation`, `tex_cotton_trade`, `tex_indigo`, `mat_shellac`; wootz has no node | Yes: the most useful new partner for Rome | [snippet](https://archive.madrasmusings.com/Vol%2024%20No%2017/a-2500-year-old-industrial-estate.html), [snippet](https://sourcebooks.web.fordham.edu/ancient/periplus.asp) |
| Aksum | Ivory, incense, gold, obsidian; imports glass, iron, cloth, wine; own coinage | none of the tree's techniques; mostly raw exports | Optional; low priority | [snippet](https://www.newworldencyclopedia.org/entry/Aksumite_Empire) |

## 9. Partners for England 1300: the Islamic world and Yuan China

| Partner | Technique | Node id | Source and tag |
|---|---|---|---|
| Mamluk Egypt and Syria, Ilkhanate | Paper mills with water-driven stampers | `rag_paper`, `prn_hand_papermaking`, `mat_paper` | [snippet](https://muslimheritage.com/filling-gap-history-pre-mod-industry/) |
| | Sugar refining at scale | `ag2_sugar_refining`, `fud_sugar_cane_cultivation`; node set needs a check | [snippet](https://muslimheritage.com/filling-gap-history-pre-mod-industry/) |
| | Indigo, lacquer, oils, textiles | `tex_indigo`, `tex_dye_madder`, `tx2_dyeing_piece` | [snippet](https://muslimheritage.com/filling-gap-history-pre-mod-industry/) |
| | Damascus steel, crucible steel (Merv, Central Asia) | wootz node absent | [snippet](https://hmsjournal.org/index.php/home/article/view/314) |
| | Enamelled and coloured glass, Syria | `mat_glass_soda`, `mfg_enamelling` | [snippet](https://muslimheritage.com/filling-gap-history-pre-mod-industry/) |
| | Distillation (alcohol, essential oils), cotton trade | `distillation_alcohol`, `tex_cotton_trade` | [recalled] |
| Yuan China (1271-1368, optional) | Porcelain (Jingdezhen), paper, silk, cast iron | `mat_porcelain`, `rag_paper`, `blast_furnace` | [recalled] |

Needs a file: a Mamluk or generic Islamic-world file (it can reuse the shape of Rome's file) is the one partner that gives England paper, sugar, indigo, glass and steel; Yuan China is a second step.

## 10. Partners for Norse 900: Byzantium, the Abbasid caliphate, Rus and Volga Bulgars

| Partner | Technique | Node id | Source and tag |
|---|---|---|---|
| Byzantium | Silk weaving (raw silk mostly imported to the 10th century; sericulture solid only from the 11th); glass workshops; parchment manuscripts | `tx2_sericulture`, `tx2_silk_fibre`, `mat_silk`, `mat_glass_soda`, `prn_parchment_sheets` | [snippet](https://www.cambridge.org/core/product/02D1206F9D324A6102B3D05A7674C807/core-reader), [snippet](https://www.metmuseum.org/ru/essays/the-art-of-the-book-in-the-middle-ages) |
| Abbasid caliphate and Central Asia | Dirhams (silver coinage), glass beads, crucible steel ingots, paper | `fin_coined_money`, `mat_silver`, `rag_paper`; wootz node absent | [snippet](https://vikingr.org/stories/the-silver-tide), [snippet](https://en.wikipedia.org/wiki/Ulfberht_swords) |
| Rus and Volga Bulgars, Frankish Rhineland | Furs, amber, beeswax, slaves; Rhenish wine and glass | no tree nodes | [snippet](https://en.wikipedia.org/wiki/Trade_during_the_Viking_Age) |

Needs a file: an Abbasid-plus-Byzantium pair would be the minimum; the Abbasid file matters most because it is the only source of the crucible steel the Norse actually bought.

## 11. Partners for Mexica 1500

No partner with a tree-modelled technique is in contact: the Tarascan state (copper alloys, a rival, not an ally) and the Maya and Gulf coast (rubber, cacao, cotton) fit the model only as raw-goods suppliers. [snippet](https://www.ancientamericas.org/sites/default/files/02063Maldonado01.pdf). The Mexica scenario needs no foreign file for the first version; an Old World partner would only arrive with contact, which the tree already models as `exp_americas_factory`. [repo]

## 12. Node ids each civilisation file should add

Order is by confidence. Every id needs a `validate` run and, where its `pre` is not held, a `prerequisite_gaps` reason.

**Han China 100 AD**
- Paper: `rag_paper`, `prn_hand_papermaking` (gap reasons: `water_power_scale`, `workshop_first`; the existing `mat_paper` reason already covers hand pestles).
- Ceramics and masonry: `mt2_stoneware`, `mt2_earthenware`, `civ_brick_tile`. `mat_porcelain` only after open question 1.
- Iron: `mt2_grey_cast_iron`, `mt2_white_cast_iron`, `mt2_malleable_cast_iron`. `met_trip_hammer` and `crank_conrod` need a prerequisite check. A Chinese finery node must be authored first.
- Fibre and cloth: `tx2_hemp_fibre`, `tx2_retting`, `tx2_heddle`, `tx2_shed`, `tx2_beam`, `tx2_selvedge`, `tx2_scouring`, `tx2_dyeing_fibre`, `tx2_dyeing_yarn`, `tx2_dyeing_piece`, `tx2_resist_dyeing`, `tex_indigo` (gap reason: no woad).
- Other: `fud_rice_cultivation`, `sea_sternpost_rudder`.

**Rome 100 AD**: `tx2_flax_fibre`, `tx2_retting`, `tx2_rope_lay`, `tx2_hemp_fibre`, `tx2_bleaching_sun`, `tx2_shed`, `tx2_selvedge`.

**England 1300**: `lnd_stirrup`, `sea_magnetic_compass` (after open question 6); consider removing the doubtful entries in section 5.

**Norse 900**: `lnd_stirrup` (with a gap reason, since `horse_collar` is not held), `mat_silk`.

**Mexica 1500**: `mt2_earthenware`, `tex_hand_ginning`, `mat_natural_rubber`, `met_investment_casting`; add nodes for amate and cochineal; review `tex_wool`.

## 13. Partners that would need a new civilisation file

| Civilisation | Scenario it serves | Years | Priority |
|---|---|---|---|
| South and west India (Tamilakam, Satavahana) | Rome 100 AD, Han | about 100 BC to 300 AD | High: wootz, cotton, indigo, pepper, lac |
| Kushan | Rome, Han | about 30 to 375 | Medium |
| Parthia, then Sasanian Persia | Rome, Han | 247 BC to 224 AD, then 224 to 651 | Medium: intermediary, little own technique |
| Aksum | Rome | about 100 to 940 | Low |
| Mamluk or generic Islamic world (Abbasid before 1258) | England 1300; Abbasid for Norse 900 | 750 to 1517 | High: paper, sugar, indigo, glass, steel |
| Byzantium | Norse 900, England | 330 to 1453 | Medium |
| Yuan China | England 1300 | 1271 to 1368 | Optional |
| Tarascan state, Maya and Gulf coast | Mexica 1500 | about 1300 to 1530 | Optional |

Each needs the full civilisation schema (`coin_standard`, `starting_techs`, `cast`, and so on) and an entry in `data/world/foreign_economies.json`. The `from_year` and `until_year` fields on that entry are what make a partner exist for a given start date.

## 14. Open questions

1. **Han proto-porcelain versus true porcelain.** High-fired glazed stoneware (proto-porcelain) is older than the Han; mature celadon porcelain appears in Zhejiang near the end of the Eastern Han, which is after 100 AD. [snippet](https://www.koh-antique.com/yue1/yue.html). The tree's `mat_porcelain` is kaolin plus feldspar at about 1300 C (the later, Jingdezhen-style definition). Decide whether `mat_porcelain` is "Yue celadon porcelain stone" (then Han can hold it, possibly with a late-date flag) or the later kaolin ware (then Han holds only `mt2_stoneware` at 100 AD). The production entry `porcelain_kg` takes `clay_kg`, `sand_quartz_kg`, `wood_kg`; check whether that reads as porcelain stone.
2. **Paper inputs.** `paper_kg` takes `linen_rag_kg` and wood ash. Han paper was hemp, rag, bark and netting; whether a second recipe is needed.
3. **Chinese finery and wootz nodes.** Whether to author them as separate nodes (recommended: they are the real techniques of the period) or widen `finery_puddling` and `crucible_steel`.
4. **Han sugar and tea.** Cane juice and syrup were known; crystallised sugar came with Indian technology later. Tea drinking in Sichuan was early. The tree's sugar and tea nodes are about crystallisation and import channels, so the right Han entry is unclear. [recalled]
5. **Cotton in Han China.** Real but marginal (south, west and the Silk Road fringe); `tex_cotton_trade` is already listed. Whether a Han cotton output should be capped by data is a design question.
6. **England 1300 timing.** Gunpowder (known in writing from the 1260s, English guns by the 1320s), the compass (in use in the North Sea by 1300) and spectacles (Italy about 1286) are all at the edge of the date. Decide whether the file holds them at start or leaves them for the game to reach.
7. **Potash glass.** Wealden glass is potash-lime; the tree has `mat_glass_soda`. Whether England's file needs a separate potash-glass node.
8. **Doubtful entries already in files** (section 5 and 7 lists): confirm and remove or justify each.
9. **Partner depth.** A partner with no own labour market (Complaint 407) will price its goods from the tree's recipes at its wage index. Adding techniques to a file before 407 lands makes the partner's prices visible but not its output.
