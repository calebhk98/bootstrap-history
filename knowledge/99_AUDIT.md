# 99 - Adversarial Audit of Modules 10, 20, 30, 40

Audited on 2026-09-09. Findings ranked by severity.

## CONFIRMED ERRORS

### 1. The blackbody colour-temperature scale contradicts itself between modules

`10_metallurgy.md`, `refractory_fireclay` (and reused verbatim by `cementation_steel`,
`case_hardening`, `high_temp_furnace`):

> "dull red ~600-700 °C, cherry red ~800-900 °C, orange ~1000-1100 °C, yellow
> ~1200-1300 °C, whitish-yellow above roughly 1400 °C"

`30_glass_optics.md`, "The pyrometer problem" (barometer entry):

> "dull red around 500-600°C, cherry red around 700-800°C, orange around
> 900-1000°C, yellow around 1000-1100°C, dazzling white above roughly
> 1300°C"

These are two different scales for the same set of colour names, offset by roughly
100-200 °C at every rung, worst at "yellow" (1200-1300 °C in Module 10 vs.
1000-1100 °C in Module 30, a 200 °C gap). A reader using Module 10 to judge a
cementation-steel hold (950-1100 °C, described there as "bright orange-red") and
the same reader later cross-checking with Module 30's chart would classify the
same furnace as two different colours. Standard published blacksmithing
temperature/colour charts (e.g. the widely used Tempil-style chart) place cherry
red around 700-800 °C and yellow around 1000-1150 °C, which is much closer to
Module 30's numbers than Module 10's. Module 20's `lab_apparatus` entry then
compounds this by calling 1000-1100 °C "cherry-orange," which fits neither
chart cleanly. Pick one scale, cite a source for it, and use it everywhere. This
does not appear to affect the *process* temperatures given elsewhere (cast-iron
eutectic 1147 °C, cementation 950-1100 °C, hardening ~800-900 °C are all
independently correct against real metallurgical data); it is specifically the
colour-name-to-temperature mapping that disagrees with itself.

## LIKELY ERRORS (high confidence but not certain)

### 2. Sodium electrolysis: NaCl is not "the original historical route"

`20_chemistry.md`, `electrolysis_chemistry`:

> "Sodium metal: electrolyse molten NaCl or NaOH, the original historical
> route to isolated sodium."

Humphry Davy first isolated metallic sodium in October 1807 by electrolysing
molten (slightly moistened) **caustic soda (NaOH)**, not molten NaCl. Molten
NaOH melts around 318 °C, reachable with Davy's era of equipment; molten NaCl
melts at 801 °C and was not electrolysed at scale for sodium until the Castner
and then Downs cell processes of the late 19th/early 20th century. Presenting
"NaCl or NaOH" as interchangeably "the original historical route" blurs two
different processes separated by roughly a century. This does not affect the
guide's practical advice (either salt works chemically), only the historical
framing.

### 3. `steam_atmospheric`'s cast-iron claim sits awkwardly against Module 10's own tech tree

`40_power_precision.md`, `steam_atmospheric`:

> "Rome has no cast iron in the West, bloomery wrought iron only, so bronze
> is the practical cylinder metal here"

This is true of ambient Rome, but Module 10 spends an entire entry
(`blast_furnace_cast_iron`) building exactly this capability, and cast iron
sits mid-chain in Module 10's own dependency list (item 5 of 14), well before
the precision-machining ladder in Module 40 that a steam engine needs (three-
plate flatness, lead screw, boring mill). A reader who has followed the guide
in order would very likely already have cast iron available long before
reaching `steam_atmospheric`. The choice of bronze over cast iron for the
cylinder may still be the right call (Module 40 elsewhere admits "18th century
cast iron somewhat exceeds early Roman foundry quality"), but the stated
reason ("Rome has no cast iron") is not really the operative constraint at
that point in the guide's own sequence, and the entry should say so rather
than imply the metal is simply unavailable.

### 4. Orpiment and realgar as "pigments" cited to the wrong Pliny books

`10_metallurgy.md`, `antimony_arsenic_bismuth`:

> "orpiment and realgar (arsenic sulfides, pigments, Pliny NH XXXIII-XXXIV)"

Pliny's *Naturalis Historia* discusses gold and silver in Book 33 and copper/
lead/iron in Book 34, but his systematic discussion of painters' pigments
(including sandaracha/realgar and auripigmentum/orpiment specifically *as
pigments*) is in Book 35, not 33-34. Orpiment does get a mention in Book 33 in
passing (grouped with gold-coloured minerals), which may be the source of the
confusion, but citing both minerals as "pigments" under XXXIII-XXXIV rather
than pointing to Book 35 looks like a misattribution. Flagged as likely rather
than confirmed because I cannot rule out that Pliny also treats them in 33-34
in a context I have not independently checked passage-by-passage.

## OVERCLAIMS AND MISSING CAVEATS

Overall this pair of modules is unusually well-hedged already (ESTIMATED/
MEASURED/DERIVED tags are used consistently and the guide explicitly flags its
own weakest links). Two smaller notes:

- `30_glass_optics.md`, `glass_bead_microscope` gives "roughly 100-300x
  magnification" in the main description but "the ~100-270x range" in the
  confidence note two paragraphs later. Not a substantive contradiction
  (both are hedged approximations of the same historical fact), but worth
  tightening to one number so it does not read as two different claims.
- The horse-collar entry (`40_power_precision.md`, `horse_collar_harness`)
  and the lead-exposure framing (`10_metallurgy.md`,
  `lead_silver_cupellation`) both correctly avoid the two classic overclaims
  named in this audit's brief (the "collar tripled draught power" myth and
  the "Roman lead pipes poisoned the population" myth). Noted here as a
  positive, not a fault: the guide clearly went out of its way to get these
  right, and it shows.

## UNVERIFIABLE CITATIONS

I could not independently confirm exact book/chapter wording for the
following; the source text itself already flags most of these as
"attributed, unverified," which is the right call and I am not overriding it,
only listing them so the record is explicit:

- Pliny, *Naturalis Historia* XXXIII, for litharge (*spuma argenti*)
  (`10_metallurgy.md`, `lead_silver_cupellation`).
- Pliny NH XXXI, on a salt from the region of the Ammon oracle possibly
  equal to sal ammoniac (`10_metallurgy.md`, `tin_bronze_solder`); the text
  itself already calls this disputed.
- Dioscorides and Pliny on vitriolic minerals, cited without a specific
  chapter (`20_chemistry.md`, `sulfuric_acid_retort`).
- Pliny's exact vitriol/nitrum passages generally (`20_chemistry.md`,
  closing sources section, already self-flagged as unverified).
- Seneca, *Naturalis Quaestiones* I.6, on a water-filled glass globe
  magnifying letters (`30_glass_optics.md`, `glass_bead_microscope`). This
  passage and citation are commonly repeated in history-of-optics writing in
  roughly this form, but I have not checked it against a critical edition.
- The Boulton quotation about Wilkinson's bored cylinder erring by no more
  than "the thickness of a worn shilling coin" (`40_power_precision.md`,
  `boring_mill`). Versions of this anecdote circulate with different coins
  (I have also seen it rendered as "a thin sixpence"); the module already
  flags it as "treat as the attested claim, not an exact figure," which is
  the right level of caution.
- Solinus's account of a perpetual "black stone" fire at Aquae Sulis
  (`10_metallurgy.md`, `coal_and_coke`), already self-flagged as
  "attributed, unverified as to exact wording/date."

## THINGS I CHECKED AND FOUND CORRECT

- Zinc: melting point 419.5 °C, boiling point 907 °C, and the "reduction
  starts above the metal's own boiling point" trap that kept zinc
  unisolated while brass-making flourished.
- Mercury: boiling point 356.7 °C, freezing point about -39 °C.
- Iron/steel: pure iron melting point 1538 °C; cast-iron eutectic at 4.3%
  carbon, 1147 °C; platinum 1768 °C; tungsten 3422 °C.
- Temper colours (pale straw ~230 °C, brown ~255 °C, purple ~280 °C, blue
  ~300 °C) match standard published temper charts closely.
- Gunpowder ratio 75:15:10 (saltpetre:charcoal:sulfur) matches the
  historically settled ratio.
- Ethanol-water azeotrope, 95.6% by weight / ~97% by volume, boiling
  ~78.2 °C, matches standard references.
- Nitric acid azeotrope at 68% by weight, boiling ~121 °C; HCl's ~38-40%
  ceiling in water at room temperature; lead-chamber acid at ~35-40% as
  collected, concentrable toward the high 70s with a Glover tower. All
  match standard historical/physical-chemistry figures.
- Anhydrous HF boiling point ~19.5 °C.
- Acetic acid freezing point ~16.6 °C.
- All balanced chemical equations checked by hand (FeSO4 decomposition,
  KNO3+H2SO4 routes to nitric acid, NaCl+H2SO4 routes to HCl, CaF2+H2SO4 to
  HF, SiO2+4HF, MnO2+4HCl to chlorine, 2HgO to mercury+oxygen, 2KClO3 to
  KCl+O2, chlor-alkali electrolysis, water electrolysis) balance correctly.
- The nitrogen-oxide catalytic cycle for the lead-chamber process (NO2
  oxidises SO2 to SO3, is reduced to NO, is reoxidised by O2) is correctly
  described.
- Roman *nitrum*/natron correctly and consistently identified as sodium
  carbonate throughout, never conflated with saltpetre.
- The "reverse anachronism" traps are all handled correctly: near-colourless
  Roman glass, manganese/pyrolusite as a decolouriser, hydraulic concrete,
  water mills, the screw press, force pumps (with the real Bolsena/
  Silchester pump attestation), mercury, and Antikythera-grade gear cutting
  are all correctly credited as pre-existing Roman capability rather than
  denied.
- No crank/connecting rod before the Hierapolis sawmill relief (3rd century
  AD) is stated consistently in both Module 10 and Module 40.
- No true paper (Cai Lun, 105 AD, China; not traded west) correctly noted in
  Module 40's `screw_cutting_lathe`.
- Chinese cast iron from roughly the 5th century BC and Du Shi's
  water-powered bellows recorded in the Hou Han Shu at 31 AD; European blast
  furnaces not before roughly the 12th-13th century AD.
- The Antikythera mechanism's largest gear having 223 teeth, and the roughly
  150-100 BC dating, match current scholarship.
- Historical dates: tungsten isolated 1783 (Elhuyar brothers), chromium 1797
  (Vauquelin), Huntsman crucible steel 1740s, Cort's puddling process 1784,
  Siemens regenerative furnace 1856, Wilkinson's boring machine 1774,
  Smeaton's wheel-efficiency trials 1759, Torricelli's barometer 1643,
  Wedgwood's clay pyrometer 1780s, Fraunhofer's solar lines 1814, Newton's
  *Opticks* 1704, spectacles in Italy circa late 13th century, Babbitt's
  bearing-alloy patent 1839, Portsmouth Block Mills circa early 1800s. All
  check out against standard history-of-technology references.
- The horse-collar entry correctly cites the Lefebvre des Noëttes thesis and
  its revision by Spruytte and Raepsaet, and gives a hedged 20-50% range
  instead of the old debunked multiple-hundred-percent claim.
- P = ρgQHη arithmetic in `water_power_scaleup` (3 m head, 0.3 m³/s, 60%
  efficiency ≈ 5,300 W ≈ 7 hp) computes correctly.
- Standard sodium/potassium/copper flame-test colours in both
  `analytical_chemistry` and `spectroscope` are correct and consistent with
  each other.

## COVERAGE

Checked: all four assigned files in full, every explicit number the audit
brief asked me to verify (zinc boiling point, gunpowder ratio, ethanol
azeotrope, temper colours, the nitrogen-oxide sulfuric acid cycle, the
three-plate flatness argument, the bead-microscope magnification
relationship), every balanced chemical equation in Modules 10 and 20, and
cross-module consistency of shared figures (furnace temperatures, colour
scales, zinc/mercury physical constants).

Not checked, and why: Modules 50, 70, 75, 80, `00_NONOBVIOUS_TRICKS.md`, and
`README.md` are out of scope for this audit. I did not verify germanium's
melting point (938 °C) because no such figure actually appears anywhere in
these four files, only a speculative note about germanium recovery from zinc
flue dust, already self-flagged LOW confidence. I did not attempt to check
every Pliny/Dioscorides/Vitruvius citation against a critical edition
chapter-by-chapter; where the source text already flags a citation as
"attributed, unverified" I generally trusted that self-assessment rather than
re-deriving it, except where I had specific reason to doubt the citation
(the orpiment/realgar case above). I did not independently verify every
ESTIMATED labour-cost or yield figure (charcoal yields, artisan-day counts,
crucible attrition rates, etc.), since these are consistently and honestly
flagged as estimates throughout and are not presented as settled fact.


---

# RESOLUTION (added by the project author after the audit)

Every finding above was acted on. This section records what was changed, so that
a later reader can tell which parts of the audit are still live.

| Finding | Status | What was done |
|---|---|---|
| Colour-temperature scale contradicts itself between modules 10 and 30 | **FIXED** | A single canonical scale is now stated in `10_metallurgy.md#refractory_fireclay` and referenced from `30_glass_optics.md`. Both were replaced with: faint red 500-550, dull red 600-700, cherry red 700-800, bright cherry 800-900, orange 900-1000, yellow 1000-1150, white above 1300 C. An ambient-light caveat and a calibration instruction (silver melts at 962 C, copper at 1085 C) were added, because this scale genuinely does read 100 C or more differently in daylight than in a dark shop. Module 20's ambiguous "cherry-orange" was replaced with an explicit temperature. |
| "Molten NaCl or NaOH" given jointly as the historical route to sodium | **FIXED** | Davy's 1807 route was molten NaOH. NaCl electrolysis is the Downs process, 1924, and needs a much hotter cell and a calcium chloride flux. Module 20 now says so and warns against planning around it. |
| Module 40 justifies bronze cylinders by saying Rome has no cast iron | **FIXED** | True of Rome as you find it, false by the time you can build an engine, since the tech tree puts the blast furnace long before `steam_atmospheric`. The entry now says cast iron is the better choice and bronze is the fallback. |
| Orpiment and realgar cited to Pliny NH XXXIII-XXXIV | **FIXED** | Changed to NH 33 and 35. Pliny discusses auripigmentum and sandaraca in Book 33 and the painters' pigments systematically in Book 35. |
| Unverifiable citations | **LEFT AS FLAGGED** | The auditor could not confirm several Pliny and Seneca references. Most were already marked "attributed, unverified" in the modules themselves. That flag is the correct treatment and it has been left in place rather than converted into a false claim of verification in either direction. |

## What this audit did NOT cover

Modules 50, 55, 60, 70, 75, 80 and 85 were written after this audit ran and have
not been adversarially checked. Treat any single number in them as `[C]` unless
it carries its own MEASURED tag. The audit also did not check `data/tech_tree.json`
or `data/prices.json`, whose cost figures are the author's estimates throughout
and are the weakest part of the project. See `../README.md`.
