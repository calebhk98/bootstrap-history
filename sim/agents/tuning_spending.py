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
	why="The reserve a state holds against risk (a lean year, a war); what a surplus leaves beyond it "
		"buys works. Stands in for a treasury's own judgement of how much risk it carries; without a "
		"bound a state in surplus hoards for ever and no later shortfall is ever felt.")

# ---- works the state raises and keeps, each a stock with a driver -----------------------------------------
FORTIFIED_SHARE_OF_FRONTIER_PER_UNIT_THREAT = declare(
	"FORTIFIED_SHARE_OF_FRONTIER_PER_UNIT_THREAT", 5.0, kind="temporary_heuristic",
	unit="share of the frontier walled per unit of yearly sack probability", source=None, confidence="D",
	why="How much of the land frontier the state walls or fortifies while its civilisation's hazards threaten "
		"a sack (none without a threat). Stands in for a model of which crossings an enemy can use.")
WALL_MASONRY_EQUIVALENT_M2_PER_M = declare(
	"WALL_MASONRY_EQUIVALENT_M2_PER_M", 30.0, kind="temporary_heuristic",
	unit="m2 of public building per metre of wall", source=None, confidence="D",
	why="Masonry of a wall with towers and ditch, counted as the floor area of public building that takes the "
		"same mason's labour (MASONRY_PERSON_YEARS_PER_M2). Stands in for a wall's section and volume.")
WATER_MASONRY_EQUIVALENT_M2_PER_URBAN_PERSON = declare(
	"WATER_MASONRY_EQUIVALENT_M2_PER_URBAN_PERSON", 1.0, kind="temporary_heuristic",
	unit="m2 of public building per town dweller", source=None, confidence="D",
	why="Aqueduct, conduit, cistern and drain masonry per town dweller, counted as the floor area of public "
		"building that takes the same labour. Stands in for water works held as tile state.")
CAPITAL_MASONRY_M2_PER_URBAN_PERSON_PER_SPECTACLE_WEIGHT = declare(
	"CAPITAL_MASONRY_M2_PER_URBAN_PERSON_PER_SPECTACLE_WEIGHT", 5.0, kind="temporary_heuristic",
	unit="m2 per town dweller per unit of the state's weight on spectacle", source=None, confidence="D",
	why="Temples and monuments of the capital beyond ordinary public building, wanted in proportion to how much "
		"the state values spectacle; it builds toward them only from a surplus.")
GRANARY_RESERVE_YEARS_OF_URBAN_FOOD = declare(
	"GRANARY_RESERVE_YEARS_OF_URBAN_FOOD", 0.5, kind="temporary_heuristic",
	unit="years of the town dwellers' subsistence grain", source=None, confidence="D",
	why="Grain the state holds against a bad harvest, bought when the price is low. Stands in for a state's own "
		"reserve policy.")
GRANARY_LOSS_SHARE_PER_YEAR = declare(
	"GRANARY_LOSS_SHARE_PER_YEAR", 0.05, kind="temporary_heuristic",
	unit="share of the grain held, a year", source=None, confidence="D",
	why="Grain lost to damp, vermin and rot in store; stands in for the spoilage of grain by storage method.")
GRANARY_PRICE_MEMORY = declare(
	"GRANARY_PRICE_MEMORY", 0.2, kind="temporary_heuristic",
	unit="share of the gap to the quote closed each year", source=None, confidence="D",
	why="How fast the state's idea of a normal grain price follows the market's quote; it buys below that price "
		"and releases above it.")
GRANARY_RELEASE_PRICE_PREMIUM = declare(
	"GRANARY_RELEASE_PRICE_PREMIUM", 0.25, kind="temporary_heuristic",
	unit="share above the normal price", source=None, confidence="D",
	why="How dear grain must be before the state releases its reserve into the market.")
GRANARY_RELEASE_SHARE = declare(
	"GRANARY_RELEASE_SHARE", 0.25, kind="temporary_heuristic",
	unit="share of the reserve a year", source=None, confidence="D",
	why="Share of the grain reserve put on the market in a year when grain is dear.")
FARM_TAX_BASE_PER_COLLECTOR_WAGE_YEAR = declare(
	"FARM_TAX_BASE_PER_COLLECTOR_WAGE_YEAR", 200.0, kind="temporary_heuristic",
	unit="wage-years of base per collector-year, a form on the harvest", source=None, confidence="D",
	why="Money's worth of harvest, counted in years of an unskilled wage, one assessor and tithe-gatherer handles "
		"in a year. Stands in for a count of farms and threshing floors.")
POLL_TAX_BASE_PER_COLLECTOR_WAGE_YEAR = declare(
	"POLL_TAX_BASE_PER_COLLECTOR_WAGE_YEAR", 400.0, kind="temporary_heuristic",
	unit="wage-years of base per collector-year, a form on people", source=None, confidence="D",
	why="People a census-taker and collector can list and collect from in a year. Stands in for a register.")
CUSTOMS_BASE_PER_COLLECTOR_WAGE_YEAR = declare(
	"CUSTOMS_BASE_PER_COLLECTOR_WAGE_YEAR", 2000.0, kind="temporary_heuristic",
	unit="wage-years of base per collector-year, a form on trade", source=None, confidence="D",
	why="Trade, counted in wage-years, one customs man handles in a year; a post taxes many cargoes. Stands in "
		"for a count of crossings.")
PROPERTY_TAX_BASE_PER_COLLECTOR_WAGE_YEAR = declare(
	"PROPERTY_TAX_BASE_PER_COLLECTOR_WAGE_YEAR", 600.0, kind="temporary_heuristic",
	unit="wage-years of base per collector-year, a form on land, income or coin", source=None, confidence="D",
	why="Assessed property, rent or income, counted in wage-years, one assessor values and collects in a year. "
		"Stands in for a register of holdings.")
CAMPAIGN_SHARE_OF_ARMY_PER_UNIT_THREAT = declare(
	"CAMPAIGN_SHARE_OF_ARMY_PER_UNIT_THREAT", 4.0, kind="temporary_heuristic",
	unit="share of the army marching per unit of yearly sack probability", source=None, confidence="D",
	why="How much of the standing force takes the field against a threat (none without one). Stands in for a "
		"model of armies that move on the map and meet an enemy.")
MARCH_KM_PER_DAY = declare(
	"MARCH_KM_PER_DAY", 20.0, kind="temporary_heuristic",
	unit="km per day", source=None, confidence="C",
	why="Pace of a column on the march with its baggage; stands in for the carriage and terrain between tiles.")
SOLDIER_GRAIN_KG_PER_DAY = declare(
	"SOLDIER_GRAIN_KG_PER_DAY", 1.15, kind="temporary_heuristic",
	unit="kg of wheat per soldier per day", source="Polybius 6.39: about two-thirds of an Attic medimnus of wheat a month", confidence="C",
	why="Ration a legionary was issued; the grain a campaign must carry or buy for each marching soldier.")
ACCESSION_PROBABILITY_PER_YEAR = declare(
	"ACCESSION_PROBABILITY_PER_YEAR", 0.07, kind="temporary_heuristic",
	unit="per year", source=None, confidence="D",
	why="Chance in a year that the ruler dies or is replaced, so a new one accedes. Stands in for a model of "
		"rulers' lives and of succession.")
DONATIVE_SHARE_OF_ANNUAL_PAY = declare(
	"DONATIVE_SHARE_OF_ANNUAL_PAY", 1.0, kind="temporary_heuristic",
	unit="years of a soldier's pay per soldier", source=None, confidence="D",
	why="Gift a new ruler pays each soldier to secure the army's loyalty. Stands in for a model of the army's "
		"price for its allegiance.")
