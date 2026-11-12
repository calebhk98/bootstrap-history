# Disease figures, civilisation starting figures and three deposit entries have no source that was read

**Status:** partly (third pass sourced the figures listed under Progress, third pass; the rest are listed at its end) - plague R0 and stage, smallpox immunity and the deposits are sourced; disease rows tagged unsourced or disputed and civilisation rows at confidence D remain (count: grep -rn '"unsourced"\|"disputed"' data/disease; grep -rn '"confidence": "D"' data/civilizations)

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
