"""Ballpark numbers behind the guards, inspectors and foresters a state keeps; each cites the pages it was read from."""
from sim.constants import declare

PATROL_DAYS_PER_PERSON = declare(
	"PATROL_DAYS_PER_PERSON", 0.34, kind="engineering_estimate",
	unit="guard-days per person per year",
	source="Staff per head of opened anchors (a working year is 200 days, so 0.34 days is 0.0017 staff per head): Oxyrhynchus "
		"60 phylakes for 36,000 inhabitants = 0.00167 (P. Oxy. I 43 verso, via Pelcer, sehepunkte 7, 2007, Nr. 10); Rome's "
		"vigiles 7 x 1,000 plus 3 urban cohorts x 500 for about 1 million = 0.0085 (Wikipedia 'Vigiles', 'Cohortes urbanae', "
		"'Rome'); modern states: median 300 police per 100,000, India 155, Bangladesh 127 "
		"(https://en.wikipedia.org/wiki/List_of_countries_by_number_of_police_officers, opened 2026-11); Qing county yamen of "
		"about 500 clerks, runners, jailers and others for 100,000 to 200,000 people = 0.0025 to 0.005, runners being a part "
		"(https://en.wikipedia.org/wiki/County_magistrate, opened 2026-11).",
	confidence="C",
	why="Guard time a state keeps per person of the people it governs for watch, patrol and answering an alarm. "
		"Set at the Oxyrhynchus density, 0.00167 staff per head, which is also near the low end of modern states (India 0.00155) "
		"and a part of the Qing county's whole staff (0.0025 to 0.005): a ballpark for a state-wide average, below a capital's "
		"0.0085. Guards should still follow the crimes of a district (Complaint 660).")
INSPECTION_DAYS_PER_PERSON = declare(
	"INSPECTION_DAYS_PER_PERSON", 0.002, kind="engineering_estimate",
	unit="inspector-days per person per year",
	source="Derived from opened pages. GAO-03-945 (https://www.govinfo.gov/content/pkg/GAOREPORTS-GAO-03-945/html/GAOREPORTS-GAO-03-945.htm): "
		"about 350 inspectors for coal mines employing about 45,500 underground and 62,000 surface workers in 2002, so "
		"350 / 107,500 = 0.0033 inspectors per miner. Miners per head: Wikipedia 'Las Medulas' (60,000 free workers at one "
		"gold district) against Wikipedia 'Demography of the Roman Empire' (59 to 76 million people) is 0.0008 to 0.001 for that "
		"district alone; taking about three such districts (a stated assumption, no count of Roman miners was found) gives "
		"0.003 miners per head. 0.0033 * 0.003 * 200 working days = 0.002 inspector-days per person per year.",
	confidence="C",
	why="Inspector time a state keeps per person of the people it governs for checking claims and workings of mines "
		"against the registry. Modern coal-mine inspector density applied to a pre-modern miner share; the share of "
		"miners is the loose input (no Roman mining workforce total was found). Inspectors should follow the claims on the "
		"registry (Complaint 660).")
FORESTER_DAYS_PER_PERSON = declare(
	"FORESTER_DAYS_PER_PERSON", 0.28, kind="engineering_estimate",
	unit="forester-days per person per year",
	source="Derived from opened pages. Woodland and wood-pasture about 15 per cent of England at Domesday "
		"(Royal Forestry Society, 'A Brief History of British Woodlands', https://rfs.org.uk/wp-content/uploads/2021/05/7.-A-Brief-History-of-British-Woodlands.pdf); "
		"England 132,932 km2 (Wikipedia 'England'), so 0.15 * 13.29 million ha = 1.99 million ha; population 1.2 to 1.6 million "
		"(Darby, Wikipedia 'Domesday Book'), 1.4 million used, so 1.42 ha per person. At the high point a third of southern "
		"England was royal forest (Wikipedia 'Royal forest'): 1.42 / 3 = 0.47 ha of forest-law woodland per person. One forest "
		"guard covers more than 340 ha of reserved forest in Bangladesh today (https://www.tbsnews.net/environment/green-coverage-grows-not-enough-guards-protect-it-88987). "
		"0.47 / 340 = 0.0014 foresters per head * 200 working days = 0.28 forester-days per person per year.",
	confidence="C",
	why="Forester time a state keeps per person of the people it governs for marking boundaries, watching felling "
		"and keeping tenure of coppice. Medieval English woodland per head and the share held under forest law, over a modern "
		"low-capacity guard's beat (Bangladesh, 340 ha); a ballpark, since a Norman forester's beat is not given. Foresters "
		"should follow the woodland held under tenure (Complaint 660).")
