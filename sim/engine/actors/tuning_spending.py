"""Provisional numbers behind what a state keeps up, each awaiting a derivation."""
from sim.constants import declare

THREAT_ARMY_RESPONSE = declare(
	"THREAT_ARMY_RESPONSE", 3.0, kind="temporary_heuristic",
	unit="share of the opening army per unit of yearly sack probability", source=None,
	confidence="D",
	why="How much larger a force the state wants while its civilisation's own hazards "
		"threaten a sack. Stands in for a model of rival states' strength and of "
		"campaigns; the probability itself is the civilisation's declared hazard.")
ROAD_UPKEEP_PERSON_YEARS_PER_KM = declare(
	"ROAD_UPKEEP_PERSON_YEARS_PER_KM", 0.05, kind="temporary_heuristic",
	unit="person-years per km per year", source=None, confidence="D",
	why="Labour to keep a kilometre of main road drained, repaired and cleared, "
		"for the road length the map gives. Stands in for a stock of road by "
		"surface and traffic.")
PUBLIC_FLOOR_AREA_PER_URBAN_PERSON_M2 = declare(
	"PUBLIC_FLOOR_AREA_PER_URBAN_PERSON_M2", 2.0, kind="temporary_heuristic",
	unit="m2 per urban person", source=None, confidence="D",
	why="Floor area of walls, baths, aqueduct works, granaries, barracks and "
		"temples the state holds per town dweller. Stands in for a stock of "
		"buildings that grows as towns are built.")
MASONRY_PERSON_YEARS_PER_M2 = declare(
	"MASONRY_PERSON_YEARS_PER_M2", 0.15, kind="temporary_heuristic",
	unit="person-years per m2 of public building", source=None, confidence="D",
	why="Mason's labour to raise a square metre of public stone building; "
		"maintenance replaces the stock once per life.")
PUBLIC_BUILDING_LIFE_YEARS = declare(
	"PUBLIC_BUILDING_LIFE_YEARS", 100.0, kind="temporary_heuristic",
	unit="years", source=None, confidence="D",
	why="Years a public building lasts under upkeep; the yearly upkeep is the stock "
		"divided by this.")
COURT_RETAINERS_PER_OFFICIAL = declare(
	"COURT_RETAINERS_PER_OFFICIAL", 2.0, kind="temporary_heuristic",
	unit="people per official", source=None, confidence="D",
	why="People the ruler's household keeps (guards, servants, stewards) for each "
		"paid official. Stands in for a model of the ruling household.")
DOLE_SHARE_OF_URBAN_PEOPLE = declare(
	"DOLE_SHARE_OF_URBAN_PEOPLE", 0.05, kind="temporary_heuristic",
	unit="share of town dwellers", source=None, confidence="D",
	why="Share of the town-dwelling people the state feeds to keep the towns quiet "
		"(each at a subsistence ration of grain). Stands in for a model of urban "
		"poverty and of what unfed towns do.")
COAST_KM_PER_SHIP = declare(
	"COAST_KM_PER_SHIP", 100.0, kind="temporary_heuristic",
	unit="km of coast per ship", source=None, confidence="D",
	why="Coast one warship keeps clear of pirates and raiders. Stands in for a "
		"model of sea control.")
CREW_PER_SHIP = declare(
	"CREW_PER_SHIP", 60.0, kind="temporary_heuristic",
	unit="sailors per ship", source=None, confidence="D",
	why="Sailors and rowers a warship needs; with the carpenters below, the people "
		"a fleet keeps.")
CARPENTERS_PER_SHIP = declare(
	"CARPENTERS_PER_SHIP", 4.0, kind="temporary_heuristic",
	unit="carpenters per ship", source=None, confidence="D",
	why="Shipwrights who keep a hull sound and refit it; stands in for hull "
		"timber and decay.")
MAX_STATE_SHARE_OF_TRADE = declare(
	"MAX_STATE_SHARE_OF_TRADE", 0.25, kind="temporary_heuristic",
	unit="share of a skilled trade's people in the country", source=None, confidence="D",
	why="The most of a skilled trade the state can keep on its lines; beyond it the "
		"trade's private customers go unserved and its people leave. Stands in for a "
		"model of how a state competes with private demand for craftsmen.")
RESERVE_CEILING_YEARS_OF_NEED = declare(
	"RESERVE_CEILING_YEARS_OF_NEED", 2.0, kind="temporary_heuristic",
	unit="years of the standing need", source=None, confidence="D",
	why="The most reserve a state keeps; what a surplus leaves beyond it goes on things the "
		"budget does not name (campaigns, building beyond upkeep, gifts, waste). Stands in for "
		"those lines; without it a state in surplus hoards for ever and no later shortfall "
		"is ever felt.")
