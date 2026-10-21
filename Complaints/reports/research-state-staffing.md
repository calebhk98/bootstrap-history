# Research: how many guards, mine inspectors and foresters a pre-modern state keeps (Complaint 660)

Sources opened in this session (WebFetch); passages quoted as returned.

## Guards (`PATROL_DAYS_PER_PERSON`)

- Wikipedia, "Vigiles" (https://en.wikipedia.org/wiki/Vigiles): "The Vigiles were organized into seven cohorts each 1,000 men strong." The same page also says "There were only 6,000 vigiles" and that cohorts were doubled in AD 205; it does not reconcile these. They were firefighters and night watch, so only part of their time was policing.
- Wikipedia, "Cohortes urbanae" (https://en.wikipedia.org/wiki/Cohortes_urbanae): Augustus "established three urban cohorts"; "In the time of the Flavians this was increased to four cohorts"; "Each cohort contained around five hundred men."
- Wikipedia, "Rome" (https://en.wikipedia.org/wiki/Rome): "It is generally thought the population of the city until AD 300 was 1 million (estimates range from 2 million to 750,000)."
- Wikisource, Statute of Winchester 1285, section 4 (https://en.wikisource.org/wiki/Statute_of_Winchester): watch "in every city by six men at every gate", "in every borough, by twelve men", "in every town, by six or four, according to the number of the inhabitants". No gate counts or populations, so no per-head figure follows.
- Wikipedia, "Constable": Statute of Winchester "constituted two constables in every hundred"; parish constables unpaid and elected at the court leet. No count per parish.

Arithmetic: (7000 vigiles + 3 x 500 urban cohort men) / 1,000,000 = 0.0085 staff per person; times 200 working days (2000 h / 10 h) = 1.7 guard-days per person per year.

This is one capital's density, not a state average. The value (0.02) was not changed; it is now documented as sitting under this upper bound, and a test holds it there. No source found for a state-wide ratio.

## Mine inspectors (`INSPECTION_DAYS_PER_PERSON`, `MINE_CEILING_*_SCALE_*`)

- Spanish-language Hispanopedia, "Bronces de Vipasca" (https://es.hispanopedia.com/wiki/Bronces_de_Vipasca): the second bronze covers the concession regime and "medidas de vigilancia de la explotación"; a tax is paid "ante el jefe del distrito". No staff count, no miner count, no output.
- Searches for the procurator's staff and Vipasca workforce returned no figure. No source found for inspectors per tonne or per claim. All remain labelled heuristics; `retire` added to the four `MINE_CEILING_*` declarations.

## Foresters (`FORESTER_DAYS_PER_PERSON`, `FOREST_HA_PER_MILLION_KM2_PER_SC`)

- mercian-as.co.uk, Sherwood Eyre 1287 (https://www.mercian-as.co.uk/1287.html): "There were usually 4 per forest, but in Sherwood there were 6." (verderers). It lists foresters by name but gives no total and no forest area.
- Wikipedia, "Forest of Dean": no medieval area or officer counts (only the present "more than 110 square kilometres").
- Verderers per forest is a count of judicial officers, not of keepers per hectare, so it does not convert to the constants' units. No source found for foresters per hectare or per head. Both stay labelled.

## Result

- One new function test: `sim/tests/test_order_staffing_sourced.py`.
- Only `PATROL_DAYS_PER_PERSON` gained a source-backed bound; no value changed.
- Next research would need: Rainbird on vigiles, Domergue on Aljustrel staffing, a Forest of Dean / Sherwood forester roll with acreage.
