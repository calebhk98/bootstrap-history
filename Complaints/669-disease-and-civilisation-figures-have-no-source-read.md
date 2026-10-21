# Disease figures, civilisation starting figures and three deposit entries have no source that was read

**Status:** open

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
