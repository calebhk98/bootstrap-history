# Research: the working year of a pre-modern labourer

Question: can `HOURS_PER_PERSON_YEAR` (`sim/unit_conversions.py`) be replaced by a sourced figure? It converts
"one worker per N iugera" (Columella 3.8, Cato via Varro 1.18) into hours per hectare in
`data/production/95_wine_oil_jars.json`, and is used by wages, staff, labour market, training, plant baskets,
working day and foreign traders (`grep -rn HOURS_PER_PERSON_YEAR sim`).

Result: no source opened supports one figure, and none is Roman. The value (2000 hours) is kept; its citation and
confidence (D -> C) now say what was found. Only sources opened in this session are cited.

## Roman sources (opened)

Columella, De Re Rustica 2.12 (LacusCurtius, https://penelope.uchicago.edu/Thayer/E/Roman/Texts/Columella/de_Re_Rustica/2*.html), section 9:
- "Forty-five days also are allowed for rainy weather and holidays, on which no ploughing is done;"
- "Thus the total amounts to eight months and ten days."
- "Still there are left of the year three months and twenty-five days,"

This is the ploughing and sowing season of a grain farm, not a whole working year, and the text gives no hours
per day ("never defines the length of a workday"). Columella 2.21 lists what is lawful on feast days (spreading manure,
cleaning ditches, hauling with oxen under Cato's view), so feast days were not fully idle. No count of feast days.
Cato 2.4 and Varro 1.18: no days-per-year or hours-per-day figure read. Scheidel, Erdkamp, Rathbone: not opened, no
source found.

## English and Danish sources (opened)

Jensen, Radu and Sharp, "Days Worked and Seasonality Patterns of Work in Eighteenth Century Denmark", SDU Discussion
Papers on Business and Economics 10/2019 (https://www.sdu.dk/-/media/files/om_sdu/institutter/ivoe/disc_papers/disc_2019/dpbe10_2019.pdf):
- "a casual worker would be employed for a full year, he would work 292 days per year" (5.6-day week).
- "Summing this, we get a value of 184,02 working days per year for casual employees." (winter seasonality)
- "from around 50 holidays at the end of the fifteenth century, only 16 were kept plus Sundays"
- 1770: "just seven, with an associated workweek of 5.9 days and a workday of 10 hours."
- Manor hours: "during the summer the working day was between 12 and 14 hours" (winter: daylight, a little over seven hours).
- Cited second-hand: "to make assumptions about days worked per year, for example 250 (Allen 2001)"; Clark and van der Werf:
  "farm laborers increased their number of days worked per year from 260 to 300 between the sixteenth and eighteenth centuries".

Allen and Weisdorf, "Was there an 'Industrious Revolution' before the Industrial Revolution?", University of Copenhagen
Discussion Paper 10-14 (https://www.economics.ku.dk/research/publications/wp/dp_2010/1014.pdf/):
- "involving less than 200 days of work per year to provide for an entire" household (late medieval farm labourers).
- "a work-load of more than 300 days per year to support a family was rarely required" between c.1315 and c.1750.
- Voth's hours converted "under the conventional assumption that workers toiled in the neighbourhood of ten hours per day".
- Blanchard's Mendip farming miners: "number of days per year spent in agriculture (135 days)" of 265 working days.

Humphries and Weisdorf (search result only, text not opened): no figure taken.

## Reading

Days a year span about 180 to 290 depending on era, place, employment type and whether idle winter days count; the
hours of a day span 7 (winter daylight) to 14 (summer manor), ten being the stated convention. Ten hours over 184 to 292
days is 1840 to 2920 hours; the present 2000 sits inside that range, below the 250-day convention (2500). The sources
differ by era and place and none is Roman, so there is no sourced Roman or per-civilisation value, and the data path
has no per-civilisation working year (one engine-wide constant), so none was built. Changing the value would move
every wage quote, staff count and hours-per-hectare in the model, and the sources do not pick a number inside the range.

Open question for the owner: choose 250 days (2500 hours, the usual convention) or keep the present value; either is a
convention. A real derivation would come from seasonal labour demand (crop calendar hours) rather than a flat year.
