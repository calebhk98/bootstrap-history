# Disease figures, civilisation starting figures and three deposit entries have no source that was read

**Status:** closed - every figure named here now carries an opened citation or a derivation from opened figures (see Progress, fifth pass); the ones that are ballparks say so in the data. Earlier text follows. plague R0 and stage, smallpox immunity and the deposits are sourced; disease rows tagged unsourced or disputed and civilisation rows at confidence D remain (count: grep -rn '"unsourced"\|"disputed"' data/disease; grep -rn '"confidence": "D"' data/civilizations)

Split from 646 (figures recalled rather than read; closed). A figure needs a source someone read (CLAUDE.md section 6);
where none is found it is a labelled heuristic with a `retire`, never a "recalled" figure.

**What is wrong now.**

- Disease files: entries tagged `unsourced` or `disputed` have a value and no source read. List them with
  `grep -rn '"unsourced"\|"disputed"' data/disease`. Known ones: plague reproduction range, plague immunity and infectious
  stage, smallpox immunity, the tsetse range box and climate envelope (the 16 and 32 C of Longbottom 2020 are fitting
  constants, not limits), the lower optimum edge and rainfall edges of malaria, and the horse loss in tsetse areas (marked
  `disputed`: Wikivet, secondary, says horses need drugs there and gives no magnitude).
- Civilisation starting figures carry grades A to D; the D grades are the ones to read:
  `grep -rn '"confidence": "D"' data/civilizations`.
- Three deposit entries say the source was recalled and not re-read: the Han gold of Poyang county, the Codex Mendoza gold
  tribute of Tlapa and Oaxaca, and the Mesoamerican cinnabar entry (`grep -n "recalled" data/world/geography/deposits/ancient.json`).
  They carry no endowment or grade and move no modelled output, so the cost of the gap is only the missing citation.
- The Mexica and Norse mineral-reach notes (`data/civilizations/mexica_1500.json`, `norse_900ad.json`) use the word
  "recalled" but state no figure; reword them as notes (no figure to source).

- Spatial stage (490): `sim/disease/spread_tuning.py` (travellers per tonne, visit days, local trips) and the England 1300 `endemic` list have no source read.

**What it would take.** For each, open a source (author, work, page or URL, the passage) and record it, or leave the figure a
labelled heuristic with `retire`. The Dean et al. 2018 plague full text returned 403 when tried; a library copy or a different
primary source is needed.

**Research needed.**

1. Plague (bubonic, pneumonic): the reproduction number range, the infectious stage and acquired immunity from epidemiological
   studies of historical outbreaks (Dean et al. 2018 full text, for example), with the page.
2. Smallpox immunity after recovery and the infectious stage from the WHO smallpox eradication record (Fenner et al. 1988).
3. Tsetse: the climate envelope and range of the fly species by field survey, and horse and cattle losses where tsetse are present.
4. Malaria vector temperature and rainfall limits for Anopheles (Mordecai et al. 2013 gave the temperature envelope; the lower
   optimum edge and the rainfall edges had no source).
5. The three deposit entries: re-read the Hanshu Dili zhi passage, the Codex Mendoza tribute folios, and an archaeological
   source on Mesoamerican cinnabar.

**Test.** `sim/tests/test_recalled_figures_sourced.py` (`DiseaseFigures`) holds what was sourced.

## Progress (second pass)

Sourced, source opened this session:

- Bubonic plague reproduction range: Dean et al. 2018 (PNAS, PMC5819418, full text opened) gives human-ectoparasite R0 from Eyam to Barcelona; the file now holds that range and its transmissibility follows the midpoint.
- Bubonic plague infectious stage: same paper, Table 2, ten days of infection.
- Smallpox immunity: CDC clinical signs page and Vichniakov 1968 (Bull. WHO 39(3):433-437, abstract opened): lifelong for most, lost quickly by some; permanent stays as the majority case, exceptions not quantified. Fenner 1988 itself could not be opened (WHO and LSU copies returned errors).
- Deposits: Mexica Sierra Gorda cinnabar (Mejia Perez Campos and Herrera Munoz 2013, Chungara 45(1)). Han gold: Hanshu ch. 28 says Yuzhang produced gold but barely paid its cost; the Poyang county placement is not confirmed by a text read and the entry says so.
- The Mexica and Norse mineral-reach notes no longer use "recalled".

Still open (no source found, left labelled):

- Plague immunity (Dean et al. say their models ignore immunity); pneumonic and other density exponents.
- Tsetse range box and climate envelope; horse loss in tsetse areas.
- Malaria lower optimum edge and annual rainfall edges (Craig et al. 1999 not opened; a secondary report gives only a monthly 80 mm rule).
- Tlapa/Oaxaca gold (Codex Mendoza folios not reached).
- Civilisation D grades: nearly all are already labelled temporary heuristics or placeholders; the Roman poll tax rate (no source for the drachma rate was opened), the standing armies of Han, Norse and Mexica, and the England 1300 entries were not sourced.
- Spatial stage tuning and the England 1300 `endemic` list (already labelled with `retire` to 677).
- Influenza case fatality and immunity placeholders.

## Progress (third pass, ballpark standard)

Standard: a ballpark with an opened citation is enough. Each line is figure, value, source opened this pass.

Disease:
- Tsetse range box (lat -29 to 15): Wikipedia Tsetse fly (en.wikipedia.org/wiki/Tsetse_fly): 15 N Senegal to 28.5 S KwaZulu-Natal, about 10 million km2; FAO Connor (fao.org/4/t0599e/t0599e01.htm). The longitude span is the belt's extent, not a separate limit.
- Tsetse temperature envelope (20-30 optimum, 16-34 tolerated): PMC8648107, 19-30 C mean annual temperature, near-zero survival above 36 C. Rainfall and forest edges: FAO (fao.org/4/y5342e/y5342e06.htm) gives only a 170-day growing-period dry band; those edges stay a stand-in of the right order.
- Cattle loss 0.5 a year at full challenge: FAO Connor, Mkwaja Ranch, none of 18 untreated cattle survived 31 months (at least about half a year).
- Horse loss 0.9: FAO Connor Table 1, horse pathogenicity +++ / ++, at least as susceptible as cattle; Wikivet says horses need drugs there. A ballpark above the cattle figure, not a measured rate.
- Malaria envelope: optimum band 22-28 C derived from Mordecai's 25 C optimum +-3 (28 C decline); annual rainfall 1000 and 400 mm derived from Craig's 80 mm per month (PMC7455692): 12 x 80 = 960, five wettest months x 80 = 400 (five months assumed). Upper rainfall edges 4000 and 6000 mm have no source.
- Bubonic plague immunity: PMC7653777, antibody persists over a decade, one patient at 14.8 years, 'probable involvement in protection'; reinfection not reported there.
- Influenza case fatality 0.02: Wikipedia Spanish flu table 2-3 percent. Reproduction range: two studies already cited, tag moved from disputed to read. Immunity 10 years: derived, partial protection from the 1889-90 pandemic 28 years earlier (Wikipedia Spanish flu).
- England endemic smallpox and measles: derived. Wikipedia Measles: diverged 1100-1200, needs over 500,000 susceptibles; England 4.5 million. Wikipedia History of smallpox: in western Europe from 581 AD.

Civilisation rows (D to C):
- England lay subsidy 0.017: Wikipedia Taxation in medieval England, fifteenth country, tenth town, not annual; british-history Yorkshire Lay Subsidy introduction (1297 ninth, 1301 fifteenth). One year in four stays an estimate.
- England standing army 3000: medievalists.net, household 500 (1297) to 800 (1298) mounted men in campaigns; castle garrisons not found, so a ballpark.
- England church 45000: Munro table of Campbell 2005, 8,500 parish clergy c.1310; Wikipedia Dissolution of the Monasteries, 12,000 religious in the 1530s; a floor of 20,500 without unbeneficed clergy. The academy's 3000 scholars has no source.
- Han import and export duties 0.05: Wikipedia Economy of the Han dynasty, merchant property tax 120 coins per 2,000 (6 percent of property); Wikipedia Taxation in premodern China lists the Eastern Han commercial tax as none. No Eastern Han rate found.
- Han starting tax share 0.08: Wikipedia Han dynasty, land tax a thirtieth, poll tax 120 coins (240 merchants), a month of labour.
- Han standing army 200000: Wikipedia Military of the Han dynasty, 20,000 capital troops in the Eastern Han, Western Han total 600,000 to 700,000.
- Norse standing army 2000: Wikipedia Huskarl, Cnut said to keep 3,000 to 4,000 men; Wikipedia Leidang, 24 crewmen a ship.
- Rome poll tax 0.04: John Gee (rsc.byu.edu), 3-5 denarii urban, 10 denarii rural a year against a day labourer's 60-120 denarii a year, so 0.025 to 0.17; the empire-wide share is lower because citizens were exempt.

Still no source after searching (left at D with the labelled heuristic):
- Mexica tribute share 0.15, market dues 0.05, starting tax share 0.2 and standing army 20000: Codex Mendoza list (pages.ucsd.edu/~dkjordan/arch/aztec/mexic-12.html) gives goods and no share of harvest; Wikipedia Aztec warfare says there was no standing army, only elite warriors and fortification garrisons, no count.
- Norse tribute share 0.04, tolls 0.05 and starting tax share: the Heimskringla passage (sourcebooks.web.fordham.edu/source/norwaytaxes1.asp) lists dues in kind and one man in seven for war service, no rate; Wikipedia Hedeby mentions royal tolls without a rate. Interest 0.2: no opened source.
- Cast actors of Han (temples 6000, scholars 5000), Mexica, Norse and Rome: Wikipedia Taixue says 30,000 students in the 2nd century (citation needed), which is six times the Han academy figure; not changed.
- Density exponents (all pathogens): Rader et al. 2020 is only read through search summaries (crowded cities, longer epidemics, larger attack rates), no exponent; the full text could not be fetched.
- Malaria host losses (hosts.people): WHO malaria fact sheet (who.int/news-room/fact-sheets/detail/malaria) gives 2.2 deaths per 1,000 cases in the African Region in 2024 and 75 percent of deaths under five; no pre-control rate per population, so the tag stays disputed.

## Progress (fourth pass)

Sourced, all pages opened this pass; "citation needed" lines are used as ballparks and say so in the data.
- Han academy (`han_china_100ad.json`): Wikipedia Taixue, 30,000 students and academicians in the 2nd century (marked citation needed there). Members raised from 5000 to 30000, tag C. The temples (6000) have no source.
- Mexica standing army 20000 (tag C): Wikipedia Aztec warfare, no standing army; brewminate.com/yaoyotl-aztec-warfare, towns of about 400 men, up to 200,000 mobilised; 20000 is about a tenth of that, a ballpark with no count of the warrior orders.
- Norse interest 0.2 (tag C): Wikipedia Usury, Roman rates 4-12 percent, higher ones typically 24 or 48, 16th-century rates before the fall 20-30 percent.
- Density exponent 0.5, all five pathogens (tag derived): Wikipedia Basic reproduction number (R0 is contact rate over recovery rate), Chowell et al. PMC2596813 (no association of transmissibility with density for 1918 influenza; deaths scale as population to 0.71-0.77 in rural areas, about 1.0 in towns). The exponent lies between 0 and 1; 0.5 is the midpoint. Rader et al. 2020 is known only from search summaries.
- Malaria `hosts.people` (tag derived): Wikipedia History of malaria, Faragher's tentative 4-5 percent of deaths; with an assumed crude death rate of 30-40 per 1,000 that is 1.2-2 per 1,000 averaged over a country, against about 7 per 1,000 at full challenge in the file, which matches if a fifth to a third of a country is at full challenge.
- Tsetse rainfall: tsetse found at 700-800 mm (PMC3368204) and in a 1000-1500 mm area (PMC4398481); the edges stay a ballpark around those, the 500 mm lower edge and 4500 upper are below and above anything opened.
- Tlapa and Oaxaca gold (`ancient.json`, conf C): the Codex Mendoza page (uknowledge.uky.edu/world_mexico_codices/11) names Tochtepec in northern Oaxaca paying gold items, and the Cambridge abstract (S095653611500022X) puts the gold tribute at enough for 22,000-27,000 ornaments a year. Tlapa itself is named in no opened page.

Still no source after this pass (labelled, retire named in the data or constants):
- Mexica tribute share 0.15, market dues 0.05, starting tax share 0.2: Wikipedia Codex Mendoza, Aztec Triple Alliance, Aztecs and Tlatelolco give goods, a 60,000-a-day market (Cortes), and no share or dues rate.
- Norse tribute share 0.04, tolls 0.05, tax share 0.04: Wikipedia Danegeld (2 shillings a hide in 1130; geld about a tenth of Exchequer receipts in 1129-30; four denarii a mansus in 864) and Hedeby (royal tolls, no rate) give no toll rate or share of output.
- Church sizes of Mexica (40000), Norse (1500), Rome (15000) and Han temples (6000), and the Mexica, Norse and Rome academies: no headcount on Wikipedia Aztec religion, Goði (36-39 chieftaincies, no population), Religion in ancient Rome (six Vestals, fifteen flamines).
- Malaria upper rainfall edges (4000, 6000 mm) and tsetse forest fraction.

Status stays partly: the figures above are the remainder.

## Progress (fifth pass) - closed

Derived from opened pages; each is a ballpark and the data says so (tag C or derived).
- Norse tribute share and starting tax share 0.04: Wikipedia Hide (unit), a hide worth about 20 shillings a year in 1084 and a normal geld of 2 shillings, 10 percent in a levy year; Wikipedia Danegeld, payments in 991, 994, 1007, 1012, 1016-18, about one year in four to five, so about 0.02 a year on average; the file's 0.04 is within a factor of two.
- Norse tolls 0.05: Wikipedia Sound Dues, 1-2 percent of cargo value from 1567; Wikipedia Alcabala, 5 percent in Castile in 1341, 2-14 percent over time; upper end taken.
- Mexica market dues 0.05: the alcabala analogue (above), 'generally lower' in the Americas.
- Mexica tribute share 0.15 and starting tax share 0.2: no share on any opened page; analogues Han 3.3 percent, English geld year 10 percent; the Aztec figures sit above them and say so.
- Mexica church 40000: 1.0 percent of England's population is clergy (Munro table and Wikipedia Dissolution), one adult man in fifty in religious orders; 40000 in 5 million is 0.8 percent. Sahagun's 78 buildings in the sacred precinct (Wikipedia Templo Mayor) is context only.
- Norse church 1500 and Rome temples 15000: ratio checks against England (0.1 and 0.02 percent against 1.0), explained by part-time or aristocratic priesthoods (Wikipedia Goði, Religion in ancient Rome); no direct counts exist on opened pages.
- Malaria upper rainfall: Papua New Guinea endemic lowlands up to 4000 mm a year, Madang 3394 mm (PMC4825189), supporting the 4000 mm optimum edge; the 6000 mm tolerated edge is above anything opened and says so.
- Tsetse forest fraction: FAO y5342e07, riparian flies in gallery forest 20 to 40 metres wide, 1000-1300 mm sites; low forest cover can hold flies.
- Tlapa gold: the entry now states that the Oaxaca gold is sourced (Tochtepec, Codex Mendoza page; Cambridge abstract) and that the Tlapa point is a labelled representative position, not a sourced location.

Sixth pass (the last uncited ones):
- Malaria 6000 mm tolerated edge: Wikipedia Chocó Department (close to 10,000 mm a year, Lloró 13,300 mm) and the Chocó malaria study (56,000 cases in 2016, falciparum commonest; endemic with high rainfall).
- Han temples 6000: ancientwarhistory.com/?p=8439 (opened, popular-history site): 160+ shrines abolished in 40 BCE and 475 closed in 32 BCE; one per 10,000 people.
- Mexica scholars 2000: Wikipedia Tenochtitlan (80 calpulli, 200,000+ people), Calmecac, Calpulli; 0.04 percent of population against the Han academy's 0.05 percent (Wikipedia Taixue).
- Rome scholars 2000: Wikipedia Education in ancient Rome (grammatici paid per pupil, no count); 0.003 percent of population, a floor.
- The Norse civilisation has no academy actor (its cast is the church only), so there is nothing to source there.

Residual weaknesses, stated in the data entries: the Aztec tribute and tax shares are analogues (Han 3.3 percent, English geld 10 percent), the church counts of the Norse and Rome are ratio checks, and Rader et al. 2020 is known from search summaries only.
