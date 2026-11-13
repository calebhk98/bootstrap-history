"""Numbers behind awareness and staged adoption, each a rough ballpark from an opened source (see each `source`)."""
from sim.constants import declare

AWARENESS_RATE_PER_CONTACT = declare(
	"AWARENESS_RATE_PER_CONTACT", 0.38, kind="engineering_estimate",
	unit="per unit of contact volume per year", confidence="C",
	source="Bass coefficient of imitation q, average 0.38 per year (range 0.3 to 0.5), Mahajan, Muller and Bass 1995, as stated on "
		"https://en.wikipedia.org/wiki/Bass_diffusion_model . Cross-check: printing went from 1 place (1450) to 110 places (1480), "
		"ln(110)/30 = 0.16 per year per place, a floor since setting up a press is slower than hearing of one "
		"(https://en.wikipedia.org/wiki/Printing_press).",
	why="Chance per year, per unit of contact volume with a holder, that an actor learns a technique exists: "
		"hazard = 1 - exp(-rate * volume). A rough ballpark: one unit of contact is a neighbouring holder in reach.")
CONTACT_FADE_PER_YEAR = declare(
	"CONTACT_FADE_PER_YEAR", 0.25, kind="engineering_estimate",
	unit="share kept each year", confidence="C",
	source="Dunbar: without time invested a relationship's emotional quality decays within at most six months "
		"(https://spectrum.ieee.org/telecom/internet/how-many-friends-can-you-really-have); taken as a half-life of six months, "
		"so 0.5 ^ (12 / 6) = 0.25 kept after a year.",
	why="How much of a one-off contact (a new route, a conquest, a migration) still counts a year later.")
DEMONSTRATION_VOLUME = declare(
	"DEMONSTRATION_VOLUME", 0.5, kind="engineering_estimate",
	unit="contact volume at full exposure", confidence="C",
	source="J-PAL Bangladesh rice trial: villages hosting a demonstration plot raised awareness by 7.2 points on a base of about "
		"60 per cent (7.2 / 0.12), so 7.2 / 40 = 18 per cent of the unaware learned in a year "
		"(https://www.povertyactionlab.org/evaluation/impact-demonstration-plots-adoption-new-rice-varieties-bangladesh). "
		"Volume = -ln(1 - 0.18) / AWARENESS_RATE_PER_CONTACT (0.38) = 0.52, rounded to 0.5.",
	why="Contact volume a founder's working demonstration gives an onlooker who sees all of it. The plots were seen by "
		"a share of the village only, so this is a floor for full exposure.")
TRADE_TONNES_FOR_UNIT_CONTACT = declare(
	"TRADE_TONNES_FOR_UNIT_CONTACT", 1000.0, kind="engineering_estimate",
	unit="tonnes a year", confidence="C",
	source="A pack animal carries 0.1 to 0.3 tonne (camel up to about 300 kg, mule about 91 kg by the US Army guideline, "
		"https://en.wikipedia.org/wiki/Pack_animal) and a drover handles a few, so one tonne is about one trader's visit; "
		"1000 tonnes a year is about 1000 visits, three a day, taken as the contact one neighbouring holder gives.",
	why="Tonnes carried a year between two places that count as one unit of contact between their people.")
PILOT_SHARE = declare(
	"PILOT_SHARE", 0.02, kind="engineering_estimate",
	unit="share of the actor's production", confidence="C",
	source="Kenyan fertilizer trials used three adjacent 30 square metre plots per farm against 0.93 acre (3764 square metres) of "
		"maize on average: 90 / 3764 = 2.4 per cent, one plot 0.8 per cent "
		"(Duflo, Kremer and Robinson, https://economics.mit.edu/sites/default/files/2022-08/fertilizerjan7_2008_501pm.pdf ; "
		"acreage https://www.povertyactionlab.org/print/pdf/node/1465).",
	why="Share of its production an actor puts on a technique while it tries it: a pilot plot or a few hands.")
TRIAL_YEARS = declare(
	"TRIAL_YEARS", 2, kind="engineering_estimate",
	unit="years", confidence="C",
	source="One crop cycle is the floor; two span a good and a bad year, since Iowa's yields in 1934 and 1936 were depressed by drought "
		"(Sutch, https://www.nber.org/system/files/chapters/c11987/c11987.pdf) and a hybrid's gain was only 7 to 9 per cent. "
		"Consistent with Ryan and Gross: 9 years on average from first knowledge to adoption "
		"(https://www.encyclopedia.com/social-sciences/encyclopedias-almanacs-transcripts-and-maps/agricultural-innovation).",
	why="Years an actor tries a technique before judging its realised margin.")
ADOPTION_SPEED_PER_MARGIN_GAP = declare(
	"ADOPTION_SPEED_PER_MARGIN_GAP", 8.0, kind="engineering_estimate",
	unit="logistic slope per year per unit of relative margin gap", confidence="C",
	source="Hybrid corn, USDA acreage via Sutch (https://www.nber.org/system/files/chapters/c11987/c11987.pdf): 0.1 per cent in 1933, "
		"70 per cent about a decade later, so the logit rose (0.85 + 6.91) / 10 = 0.78 per year; the yield gain was 7 to 15 per cent "
		"(Iowa tests 7 to 9, plant breeders 10 to 15, https://www.nber.org/papers/w14141), take 0.10: 0.78 / 0.10 = 7.8, rounded to 8.",
	why="Slope of the logistic adoption curve, share' = speed * gap * share * (1 - share): the form is "
		"Griliches's, the proportionality of slope to profitability is his finding. The national figure includes supply lags, "
		"so it is a floor on how fast a single district moves.")
CONQUEST_CONTACT_VOLUME = declare(
	"CONQUEST_CONTACT_VOLUME", 5.0, kind="engineering_estimate",
	unit="contact volume per conquest", confidence="C",
	source="A late-republican legion was about 5200 men (https://en.wikipedia.org/wiki/Roman_legion); at "
		"MIGRANT_CONTACT_VOLUME_PER_PERSON (0.001 per person) one legion is 5.2 units, rounded to 5.",
	why="Contact a conquest gives the winner's actors with the places of the people they overran: one army of occupation "
		"counted as settlers.")
MIGRANT_CONTACT_VOLUME_PER_PERSON = declare(
	"MIGRANT_CONTACT_VOLUME_PER_PERSON", 0.001, kind="engineering_estimate",
	unit="contact volume per migrant", confidence="C",
	source="One person is one traveller's visit, the same as one tonne in TRADE_TONNES_FOR_UNIT_CONTACT (a trader carries about "
		"a tonne, https://en.wikipedia.org/wiki/Pack_animal ), so 1 / 1000 = 0.001 per person; a settler stays and keeps the link, "
		"so this is a floor.",
	why="Contact each working-age migrant gives the actors where they arrive with the place they left.")
